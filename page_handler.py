import importlib
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DEBUG = os.getenv("DEBUG", "").strip().lower() == "true"


def load_message_send():
    return importlib.import_module("snom_message_send_runtime")


message_send = load_message_send()


def page_debug(message):
    if DEBUG:
        message_send.debug_log(f"page_handler {message}")


def handle_dispatch(action, stream_id, group_id, targets, metadata=None):
    """
    The paging core still calls this with action="prepare_livepage" (that
    contract is fixed upstream), but for SNOM there's no live audio to
    prepare - we just resolve the targets and fire a text popup at them.
    """
    page_debug(f"handle_dispatch_start action={action} stream={stream_id} group={group_id} targets={targets} metadata={metadata}")
    if action != "prepare_livepage":
        return

    normalized_targets = []
    for target in targets:
        token = str(target).strip()
        if token and token not in normalized_targets:
            normalized_targets.append(token)

    if not normalized_targets:
        page_debug(f"handle_dispatch_no_targets stream={stream_id}")
        message_send.send_ready_signal("snom", stream_id)
        return

    metadata = metadata or {}
    sender = str(metadata.get("sender") or "").strip()
    text = str(metadata.get("text") or metadata.get("message") or "").strip()
    if not text:
        text = f"Page from {sender}" if sender else "You have a page."
    title = str(metadata.get("title") or "").strip() or (f"Page from {sender}" if sender else "Live Page")
    prompt = metadata.get("prompt")
    melody = metadata.get("melody", message_send.DEFAULT_MELODY)

    ipv4s = message_send.parse_targets(normalized_targets)
    endpoints = message_send.fetch_snom_targets(ipv4s)
    page_debug(f"handle_dispatch_targets stream={stream_id} ipv4s={ipv4s} endpoints={[e['ipv4'] for e in endpoints]} sender={sender!r}")

    if endpoints:
        results = message_send.send_text_popup(endpoints, title, text, prompt=prompt, melody=melody)
        page_debug(f"handle_dispatch_results stream={stream_id} results={results}")
    else:
        page_debug(f"handle_dispatch_no_matching_endpoints stream={stream_id}")

    page_debug(f"handle_dispatch_ready stream={stream_id}")
    message_send.send_ready_signal("snom", stream_id)
