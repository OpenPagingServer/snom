import os
import pymysql
import requests
import xml.sax.saxutils as saxutils
import threading
from requests.auth import HTTPBasicAuth, HTTPDigestAuth

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME")
ENDPOINT_TABLE = "endpoints-output-snom"

def db():
    return pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, database=DB_NAME, cursorclass=pymysql.cursors.DictCursor)

def xml_snom_text(title, text):
    safe_title = saxutils.escape(str(title or "Alert"))
    safe_text = saxutils.escape(str(text or ""))
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<SnomIPPhoneText>
    <Title>{safe_title}</Title>
    <Text>{safe_text}</Text>
    <Prompt>Press cancel to exit</Prompt>
</SnomIPPhoneText>"""

def push_to_snom(endpoint, xml_payload):
    ip = endpoint.get("ipv4")
    username = endpoint.get("http_username")
    password = endpoint.get("http_password")
    
    url = f"http://{ip}/minibrowser.htm"
    headers = {"Content-Type": "text/xml"}
    
    try:
        # First try unauthenticated / basic auth
        auth = HTTPBasicAuth(username, password) if username else None
        response = requests.post(url, data=xml_payload, headers=headers, auth=auth, timeout=5)
        
        # SNOM triggers 401 if it specifically wants Digest auth
        if response.status_code == 401 and username:
            auth = HTTPDigestAuth(username, password)
            response = requests.post(url, data=xml_payload, headers=headers, auth=auth, timeout=5)
            
        return response.status_code in (200, 204)
    except requests.exceptions.RequestException as e:
        print(f"Failed to push to SNOM {ip}: {e}")
        return False

def handle_dispatch(action, stream_id, msg_id, targets):
    # Only process preparation phase for visuals
    if action != "prepare_audio" and action != "prepare_livepage":
        return

    conn = db()
    try:
        with conn.cursor() as cur:
            # Get targeted endpoints
            placeholders = ",".join(["%s"] * len(targets))
            cur.execute(f"SELECT macaddr, ipv4, http_username, http_password, visual FROM `{ENDPOINT_TABLE}` WHERE macaddr IN ({placeholders})", tuple(targets))
            endpoints = cur.fetchall()
            
            # Fetch broadcast message details
            cur.execute("SELECT name, shortmessage, longmessage FROM broadcasts WHERE id=%s", (msg_id,))
            message = cur.fetchone() or {"name": "Alert", "shortmessage": "Incoming Broadcast", "longmessage": ""}
    finally:
        conn.close()

    if not endpoints:
        return

    # Build the SNOM XML Payload
    display_text = message.get("longmessage") or message.get("shortmessage")
    xml_payload = xml_snom_text(message.get("name"), display_text)

    # Fire off POST requests concurrently to avoid blocking
    threads = []
    for ep in endpoints:
        if ep.get("visual") != "None":
            t = threading.Thread(target=push_to_snom, args=(ep, xml_payload), daemon=True)
            t.start()
            threads.append(t)
            
    for t in threads:
        t.join()
