"""
Tiny local HTTP server that hosts generated SnomIPPhoneText XML documents.

Why this exists:
Snom phones don't accept an XML payload pushed directly in the trigger
request. The trigger is a GET to the phone's own /minibrowser.htm?url=...
endpoint, and the phone then turns around and fetches that URL itself
(see the "HTTP GET (Pull via Push)" delivery mechanism). So we need
something on our side, reachable by the phones, to serve the XML
document at a short-lived URL.

This mirrors the icon_server.py pattern used by the original Polycom
module (referenced in index.py but not part of your upload) - a small
background HTTP server managed by this module's init()/shutdown().
"""

import os
import socket
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

DEBUG = os.getenv("DEBUG", "").strip().lower() == "true"

_lock = threading.Lock()
_documents = {}  # doc_id -> {"xml": str, "expires": float}
_server = None
_thread = None
_port = None

DOCUMENT_TTL_SECONDS = 120
CLEANUP_INTERVAL_SECONDS = 30


def _log(message):
    if DEBUG:
        print(f"snom_popup_server {message}")


def _purge_expired():
    now = time.monotonic()
    with _lock:
        expired = [doc_id for doc_id, doc in _documents.items() if doc["expires"] <= now]
        for doc_id in expired:
            _documents.pop(doc_id, None)


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        if DEBUG:
            _log(fmt % args)

    def do_GET(self):
        _purge_expired()
        path = self.path.split("?", 1)[0]
        if not path.startswith("/popup/") or not path.endswith(".xml"):
            self.send_response(404)
            self.end_headers()
            return
        doc_id = path[len("/popup/"):-len(".xml")]
        with _lock:
            doc = _documents.get(doc_id)
        if doc is None:
            self.send_response(404)
            self.end_headers()
            return
        body = doc["xml"].encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/xml; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def _pick_local_ip():
    # Best-effort discovery of the LAN-facing IP so the URL we hand to
    # phones is actually reachable (not 127.0.0.1).
    override = os.getenv("SNOM_POPUP_SERVER_HOST")
    if override:
        return override
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        sock.close()


def start(preferred_port=0):
    global _server, _thread, _port
    if _server is not None:
        return _port
    bind_port = int(os.getenv("SNOM_POPUP_SERVER_PORT", str(preferred_port)) or 0)
    _server = ThreadingHTTPServer(("0.0.0.0", bind_port), _Handler)
    _port = _server.server_address[1]
    _thread = threading.Thread(target=_server.serve_forever, daemon=True)
    _thread.start()
    _log(f"started port={_port}")
    return _port


def stop():
    global _server, _thread, _port
    if _server is not None:
        _server.shutdown()
        _server.server_close()
    _server = None
    _thread = None
    _port = None


def publish(xml_text):
    """Store an XML document and return the URL a phone can GET it from."""
    if _server is None:
        start()
    doc_id = uuid.uuid4().hex
    with _lock:
        _documents[doc_id] = {"xml": xml_text, "expires": time.monotonic() + DOCUMENT_TTL_SECONDS}
    host = _pick_local_ip()
    scheme = "https" if os.getenv("SNOM_POPUP_SERVER_HTTPS", "").strip().lower() == "true" else "http"
    return f"{scheme}://{host}:{_port}/popup/{doc_id}.xml"
