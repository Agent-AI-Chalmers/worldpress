import base64
import ipaddress
import pickle
import socket
from urllib.parse import urlparse

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


# SSRF validation for fetch_remote_resource
_BLOCKED_INTERNAL_TLDS = (".internal", ".local", ".localhost", ".localdomain")

_BLOCKED_HOSTNAMES = frozenset({
    "localhost",
    "127.0.0.1",
    "::1",      # IPv6 loopback
    "::",       # IPv6 unspecified (urlparse.hostname returns '::' without brackets)
    "0.0.0.0",
})


def _validate_url(url):
    """Validate a URL for SSRF safety. Returns (is_valid, error_message)."""
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()

    # Restrict to http / https only
    if scheme not in ("http", "https"):
        return False, "Only http and https URLs are allowed"

    hostname = parsed.hostname
    if not hostname:
        return False, "URL must have a hostname"

    lower_hostname = hostname.lower()

    # Block known internal hostname literals
    if lower_hostname in _BLOCKED_HOSTNAMES:
        return False, "URL hostname is not allowed"

    # Block internal-only TLDs
    if lower_hostname.endswith(_BLOCKED_INTERNAL_TLDS):
        return False, "URL hostname is not allowed"

    # Resolve hostname to IP addresses and validate each
    try:
        addrs = socket.getaddrinfo(hostname, None)
    except OSError:
        return False, "Could not resolve hostname"

    for family, _, _, _, sockaddr in addrs:
        ip_str = sockaddr[0]
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            return False, f"Invalid IP address: {ip_str}"

        if _is_ip_blocked(ip):
            return False, "URL resolves to an internal IP address"

    return True, None


def _is_ip_blocked(ip):
    """Check whether an IP address is internal / private / link-local / loopback.

    Handles both plain IPv4/IPv6 and IPv4-mapped IPv6 addresses (e.g.
    ``::ffff:10.0.0.1``) where the embedded IPv4 is checked directly.
    """
    # IPv4-mapped IPv6 — check the embedded IPv4 address
    if ip.version == 6 and ip.ipv4_mapped is not None:
        mapped = ip.ipv4_mapped
        return (
            mapped.is_private
            or mapped.is_loopback
            or mapped.is_link_local
            or mapped.is_unspecified
            or mapped.is_multicast
        )

    # Standard IPv4 or native IPv6
    return (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_unspecified
        or ip.is_multicast
    )


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
    #
    # Mitigation: validate URL before making the request.
    valid, err = _validate_url(url)
    if not valid:
        return jsonify({"error": err}), 400

    try:
        resp = http_requests.get(url, timeout=10, allow_redirects=False)
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

    # [VULN-17] XXE: parser explicitly configured to load DTD and resolve external
    # entities. A malicious DOCTYPE can read /etc/passwd via file:// entity.
    try:
        parser = etree.XMLParser(load_dtd=True, resolve_entities=True, no_network=False)
        root = etree.fromstring(xml_data, parser)
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
