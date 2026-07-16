"""
SNOM message-send runtime.

NOTE: your original message_send.py (the Polycom RTP/PTT version) wasn't
part of the upload, only the files that imported it. This is a fresh
implementation written to match the interface page_handler.py and
index.py call into (debug_log, parse_targets, send_ready_signal,
handle_api, receive_audio, end_stream), with the Polycom-specific
"ensure_stream"/"fetch_ptt_targets" audio plumbing replaced by SNOM
text-popup delivery. If your paging core expects a specific
send_ready_signal/handle_api wire format, tell me and I'll match it
exactly - the versions below are reasonable stand-ins, flagged where
they're a guess.
"""

import os
import html
import json
from pathlib import Path

import pymysql
import requests
from dotenv import load_dotenv

import popup_server

BASE_DIR = Path(__file__).resolve().parent
DEBUG = os.getenv("DEBUG", "").strip().lower() == "true"

ENV_PATH = BASE_DIR.parent.parent / ".env"
load_dotenv(ENV_PATH)

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME")

PUSH_TABLE = "endpoints-output-snom-push"

REQUEST_TIMEOUT_SECONDS = 3
DEFAULT_MELODY = "3"  # attention tone; set metadata["melody"] to override, or "" for none


def debug_log(message):
    if DEBUG:
        print(f"snom_message_send {message}")


def db():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor,
    )


def parse_targets(normalized_targets):
    """
    Targets arrive as endpoint ids in the `snom-<ipv4>` form used by
    get_endpoint_status(). Strip the prefix and drop anything that isn't
    ours to handle - unprefixed values are also accepted as raw ipv4s
    in case the core passes those through directly.
    """
    ipv4s = []
    for target in normalized_targets:
        token = str(target).strip()
        if token.startswith("snom-"):
            token = token[len("snom-"):]
        elif "-" in token:
            # Belongs to a different endpoint module (e.g. a different
            # push/PTT device type) - not ours to page.
            continue
        if token and token not in ipv4s:
            ipv4s.append(token)
    return ipv4s


def fetch_snom_targets(ipv4s):
    """Resolve target ipv4s to full endpoint rows (address, port, auth)."""
    if not ipv4s:
        return []
    conn = db()
    try:
        with conn.cursor() as cur:
            placeholders = ",".join(["%s"] * len(ipv4s))
            cur.execute(
                f"SELECT ipv4, port, use_https, username, password, status "
                f"FROM `{PUSH_TABLE}` WHERE ipv4 IN ({placeholders})",
                tuple(ipv4s),
            )
            return cur.fetchall()
    finally:
        conn.close()


def _xml_escape(value):
    return html.escape("" if value is None else str(value), quote=True)


def build_popup_xml(title, text, prompt=None, melody=None):
    parts = ["<?xml version=\"1.0\" encoding=\"UTF-8\"?>", "<SnomIPPhoneText>"]
    parts.append(f"<Title>{_xml_escape(title)}</Title>")
    parts.append(f"<Text>{_xml_escape(text)}</Text>")
    if prompt:
        parts.append(f"<Prompt>{_xml_escape(prompt)}</Prompt>")
    if melody:
        parts.append(f"<Melody>{_xml_escape(melody)}</Melody>")
    parts.append("</SnomIPPhoneText>")
    return "".join(parts)


def _trigger_endpoint(endpoint, popup_url):
    scheme = "https" if endpoint.get("use_https") else "http"
    port = endpoint.get("port") or (443 if endpoint.get("use_https") else 80)
    trigger_url = f"{scheme}://{endpoint['ipv4']}:{port}/minibrowser.htm"
    auth = None
    if endpoint.get("username"):
        auth = (endpoint.get("username"), endpoint.get("password") or "")
    try:
        response = requests.get(
            trigger_url,
            params={"url": popup_url},
            auth=auth,
            timeout=REQUEST_TIMEOUT_SECONDS,
            verify=False,
        )
        ok = response.status_code < 400
        debug_log(f"trigger endpoint={endpoint['ipv4']} status={response.status_code}")
        return ok
    except Exception as exc:
        debug_log(f"trigger endpoint={endpoint['ipv4']} error={exc}")
        return False


def send_text_popup(endpoints, title, text, prompt=None, melody=None):
    """
    Push a SnomIPPhoneText popup to each endpoint. Publishes one shared
    XML document and triggers every phone against it independently, so
    one unreachable phone doesn't block the rest.
    """
    if not endpoints:
        return []
    xml_body = build_popup_xml(title, text, prompt=prompt, melody=melody)
    popup_url = popup_server.publish(xml_body)
    results = []
    for endpoint in endpoints:
        ok = _trigger_endpoint(endpoint, popup_url)
        results.append({"ipv4": endpoint["ipv4"], "ok": ok})
    return results


def send_ready_signal(module_name, stream_id):
    """
    Signals the paging core that this module has finished handling the
    dispatch for stream_id. The Polycom version's wire format wasn't in
    your upload, so this logs by default; set PAGING_CORE_CALLBACK_URL
    to have it POST instead, or tell me the real callback shape and
    I'll wire it up directly.
    """
    debug_log(f"ready module={module_name} stream={stream_id}")
    callback_url = os.getenv("PAGING_CORE_CALLBACK_URL")
    if not callback_url:
        return
    try:
        requests.post(
            callback_url,
            json={"module": module_name, "stream_id": stream_id, "status": "ready"},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    except Exception as exc:
        debug_log(f"ready signal error={exc}")


def handle_api(command_string):
    """
    Entry point for module-specific API commands (mirrors index.py's
    api_endpoint -> message_send.handle_api). Expects a JSON string:
      {"targets": ["snom-10.0.0.5", ...], "title": "...", "text": "...", "prompt": "..."}
    """
    try:
        payload = json.loads(command_string)
    except Exception as exc:
        debug_log(f"handle_api invalid payload error={exc}")
        return
    targets = payload.get("targets") or []
    ipv4s = parse_targets(targets)
    endpoints = fetch_snom_targets(ipv4s)
    if not endpoints:
        debug_log(f"handle_api no matching endpoints targets={targets}")
        return
    send_text_popup(
        endpoints,
        payload.get("title") or "Message",
        payload.get("text") or "",
        prompt=payload.get("prompt"),
        melody=payload.get("melody", DEFAULT_MELODY),
    )


def handle_dispatch(action, stream_id, msg_id, targets):
    """Non-livepage dispatch actions land here (mirrors the Polycom module's contract). No-op for SNOM text-only paging."""
    debug_log(f"handle_dispatch ignored action={action} stream={stream_id} msg={msg_id} targets={targets}")


def receive_audio(chunk, stream_id):
    # SNOM text popups carry no audio - nothing to do.
    pass


def end_stream(stream_id):
    # No audio stream was ever opened for a text popup.
    pass
