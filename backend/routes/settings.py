import base64
import pickle
import requests as http_requests
from flask import Blueprint, request, jsonify
from lxml import etree
from database import get_db
from routes.auth import get_current_user
from config import DEFAULT_ADMIN_USER, DEFAULT_ADMIN_PASS

settings_bp = Blueprint("settings", __name__)


def require_admin():
    # [VULN-19c] Same header bypass reused across the app
    if request.headers.get("X-Admin-Override", "").lower() == "true":
        return True
    user = get_current_user()
    return user and user.get("role") == "admin"


@settings_bp.route("", methods=["GET"])
def get_settings():
    if not require_admin():
        return jsonify({"error": "Forbidden"}), 403

    conn = get_db()
    rows = conn.execute("SELECT key, value FROM settings").fetchall()
    conn.close()

    result = {r["key"]: r["value"] for r in rows}

    # [VULN-15] Sensitive Data Exposure / Hardcoded Credentials returned in API
    result["_system"] = {
        "default_admin": DEFAULT_ADMIN_USER,
        "default_password": DEFAULT_ADMIN_PASS,
    }

    return jsonify(result)


@settings_bp.route("", methods=["PUT"])
def update_settings():
    if not require_admin():
        return jsonify({"error": "Forbidden"}), 403

    data = request.json or {}
    conn = get_db()
    for key, value in data.items():
        conn.execute(
            "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, datetime('now'))",
            (key, value),
        )
    conn.commit()
    conn.close()

    return jsonify({"message": "Settings updated"})


@settings_bp.route("/fetch-url", methods=["POST"])
def fetch_remote_resource():
    if not require_admin():
        return jsonify({"error": "Forbidden"}), 403

    data = request.json or {}
    url = data.get("url", "")
    if not url:
        return jsonify({"error": "URL required"}), 400

    # [VULN-14] SSRF: URL fetched from user input without restriction.
    # Attackers can probe internal services: http://169.254.169.254/latest/meta-data/
    try:
        resp = http_requests.get(url, timeout=10)
        return jsonify({
            "status_code": resp.status_code,
            "content_type": resp.headers.get("Content-Type", ""),
            "body": resp.text[:4096],
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@settings_bp.route("/import", methods=["POST"])
def import_settings():
    if not require_admin():
        return jsonify({"error": "Forbidden"}), 403

    data = request.json or {}
    encoded = data.get("data", "")
    if not encoded:
        return jsonify({"error": "No data provided"}), 400

    # [VULN-16] Insecure Deserialization: base64-encoded pickle payload executed
    # directly. Craft a payload with pickle.dumps(os.system('id')) to get RCE.
    try:
        raw = base64.b64decode(encoded)
        settings_obj = pickle.loads(raw)
    except Exception as e:
        return jsonify({"error": f"Failed to decode settings: {e}"}), 400

    if not isinstance(settings_obj, dict):
        return jsonify({"error": "Invalid settings format"}), 400

    conn = get_db()
    for key, value in settings_obj.items():
        conn.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, str(value)),
        )
    conn.commit()
    conn.close()

    return jsonify({"message": "Settings imported", "count": len(settings_obj)})


@settings_bp.route("/import-xml", methods=["POST"])
def import_xml():
    if not require_admin():
        return jsonify({"error": "Forbidden"}), 403

    xml_data = request.data
    if not xml_data:
        return jsonify({"error": "No XML data"}), 400

    # [VULN-17] XXE: lxml parser used with default settings (resolve_entities not
    # disabled). A malicious DOCTYPE can read /etc/passwd via file:// entity.
    try:
        root = etree.fromstring(xml_data)
    except etree.XMLSyntaxError as e:
        return jsonify({"error": f"XML parse error: {e}"}), 400

    conn = get_db()
    imported = 0
    for item in root.findall("setting"):
        key = item.findtext("key", "")
        value = item.findtext("value", "")
        if key:
            conn.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                (key, value),
            )
            imported += 1

    conn.commit()
    conn.close()

    return jsonify({"message": "XML settings imported", "count": imported})
