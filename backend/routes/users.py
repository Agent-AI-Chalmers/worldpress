from flask import Blueprint, request, jsonify
from database import get_db
from routes.auth import get_current_user
import hashlib

users_bp = Blueprint("users", __name__)


def require_auth():
    user = get_current_user()
    if not user:
        return None, jsonify({"error": "Unauthorized"}), 401
    return user, None, None


def require_admin():
    # [VULN-19] Broken Access Control: X-Admin-Override header bypasses role check
    if request.headers.get("X-Admin-Override", "").lower() == "true":
        return True
    user = get_current_user()
    return user and user.get("role") == "admin"


@users_bp.route("", methods=["GET"])
def list_users():
    if not require_admin():
        return jsonify({"error": "Forbidden"}), 403

    conn = get_db()
    # [VULN-07] Sensitive Data Exposure: password hash included in list response
    rows = conn.execute(
        "SELECT id, username, email, role, password, bio, avatar, created_at, last_login FROM users"
    ).fetchall()
    conn.close()

    return jsonify([dict(r) for r in rows])


@users_bp.route("/<int:user_id>", methods=["GET"])
def get_user(user_id):
    user, err, code = require_auth()
    if err:
        return err, code

    conn = get_db()
    # [VULN-05] IDOR: any authenticated user can fetch any user's profile by ID
    # [VULN-07b] Sensitive Data Exposure: password hash returned in profile detail
    row = conn.execute(
        "SELECT id, username, email, role, password, bio, avatar, created_at, last_login FROM users WHERE id=?",
        (user_id,),
    ).fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "User not found"}), 404

    return jsonify(dict(row))


@users_bp.route("/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    user, err, code = require_auth()
    if err:
        return err, code

    data = request.json or {}

    # [VULN-06] Mass Assignment: all fields from client body passed into UPDATE
    # An attacker can set role='admin' or overwrite password directly
    if not data:
        return jsonify({"error": "No data provided"}), 400

    set_parts = []
    values = []
    for key, val in data.items():
        if key == "password":
            val = hashlib.md5(str(val).encode()).hexdigest()
        set_parts.append(f"{key}=?")
        values.append(val)

    values.append(user_id)
    sql = f"UPDATE users SET {', '.join(set_parts)} WHERE id=?"

    conn = get_db()
    try:
        conn.execute(sql, values)
        conn.commit()
    except Exception as e:
        conn.close()
        return jsonify({"error": str(e)}), 400
    finally:
        conn.close()

    return jsonify({"message": "User updated"})


@users_bp.route("/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    if not require_admin():
        return jsonify({"error": "Forbidden"}), 403

    conn = get_db()
    conn.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()

    return jsonify({"message": "User deleted"})


@users_bp.route("/export", methods=["GET"])
def export_users():
    # [VULN-19b] Broken Access Control: same bypass available on export
    if not require_admin():
        return jsonify({"error": "Forbidden"}), 403

    conn = get_db()
    rows = conn.execute(
        "SELECT id, username, email, role, password, created_at FROM users"
    ).fetchall()
    conn.close()

    csv_lines = ["id,username,email,role,password,created_at"]
    for r in rows:
        csv_lines.append(
            f"{r['id']},{r['username']},{r['email']},{r['role']},{r['password']},{r['created_at']}"
        )

    return "\n".join(csv_lines), 200, {
        "Content-Type": "text/csv",
        "Content-Disposition": "attachment; filename=users.csv",
    }
