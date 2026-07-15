import html
import re
import ipaddress

ENTERPRISE_TABLE = "endpoints-output-snom"
MODELS = ["D785", "D735", "D717", "D385", "D335", "D120"]
AUDIO_MODES = ["Multicast", "Unicast", "Disabled"]
VISUAL_MODES = ["None", "Text", "Image"]

def h(value):
    return html.escape("" if value is None else str(value), quote=True)

def normalize_macaddr(value):
    cleaned = re.sub(r"[^A-Fa-f0-9]", "", str(value or "")).upper()
    if len(cleaned) != 12:
        raise ValueError("Enter a valid 12-digit hexadecimal MAC address.")
    return cleaned

def validate_host_or_ip(value):
    host = str(value or "").strip()
    if not host:
        raise ValueError("Hostname or IP is required.")
    return host

def execute(conn_factory, sql, params=()):
    conn = conn_factory()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
        conn.commit()
    finally:
        conn.close()

def forms():
    return {
        "snom-endpoint": {
            "label": "SNOM Endpoint",
            "description": "Send audio and visual XML push messages to SNOM D-Series phones.",
        }
    }

def render_form(form_type, request, conn_factory, page, user):
    if form_type != "snom-endpoint":
        return page("Form Not Found", "<h1>Error</h1>", "endpoints", user, status=404)

    message, error = "", ""
    values = {
        "macaddr": "", "name": "", "ipv4": "", "http_username": "admin", 
        "http_password": "", "model": "D785", "audio": "Multicast", "visual": "Text"
    }

    if request.method == "POST":
        try:
            for key in values:
                values[key] = str(request.form.get(key, values[key]) or "").strip()
            
            macaddr = normalize_macaddr(values["macaddr"])
            host = validate_host_or_ip(values["ipv4"])
            
            execute(
                conn_factory,
                f"INSERT INTO `{ENTERPRISE_TABLE}` (macaddr, name, ipv4, http_username, http_password, status, audio, model, visual) VALUES (%s,%s,%s,%s,%s,'Unchecked',%s,%s,%s)",
                (macaddr, values["name"], host, values["http_username"], values["http_password"], values["audio"], values["model"], values["visual"]),
            )
            message = "SNOM endpoint added successfully."
        except Exception as exc:
            error = str(exc)

    body = f"""
    <style>body{{font-family:Tahoma,sans-serif;padding:18px;}}.grid{{display:grid;gap:12px}}.row{{display:grid;gap:6px}}.control{{padding:10px;border:1px solid #ddd;border-radius:4px}}.button{{background:#1976D2;color:#fff;padding:10px;border:0;border-radius:4px;cursor:pointer}}</style>
    {'<div style="color:green;margin-bottom:10px;">'+h(message)+'</div>' if message else ''}
    {'<div style="color:red;margin-bottom:10px;">'+h(error)+'</div>' if error else ''}
    <form method='post' class='grid'>
        <div class='row'><label>MAC Address</label><input class='control' name='macaddr' value='{h(values['macaddr'])}' required></div>
        <div class='row'><label>Name</label><input class='control' name='name' value='{h(values['name'])}'></div>
        <div class='row'><label>Phone IP Address</label><input class='control' name='ipv4' value='{h(values['ipv4'])}' required></div>
        <div class='row'><label>HTTP Username</label><input class='control' name='http_username' value='{h(values['http_username'])}'></div>
        <div class='row'><label>HTTP Password</label><input class='control' type='password' name='http_password' value='{h(values['http_password'])}'></div>
        <div class='row'><label>Visual Mode</label><select class='control' name='visual'>
            <option value='Text'>Text</option><option value='Image'>Image</option><option value='None'>None</option>
        </select></div>
        <button class='button' type='submit'>Add SNOM Endpoint</button>
    </form>
    """
    return page("SNOM Endpoint", body, "endpoints", user)
