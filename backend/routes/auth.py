import hashlib
import time
import jwt
from flask import Blueprint, request, jsonify
from database import get_db
from config import APP_SECRET, TOKEN_EXPIRY

auth_bp = Blueprint("auth", __name__)


def generate_token(user_id, username, role):
    payload = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "exp": int(time.time()) + TOKEN_EXPIRY,
    }
    # [VULN-04] JWT signed with a weak, guessable static secret
    return jwt.encode(payload, APP_SECRET, algorithm="HS256")


def decode_token(token):
    try:
        # [VULN-04b] algorithm list not restricted — accepts 'none' if crafted
        return jwt.decode(token, APP_SECRET, algorithms=["HS256", "none"])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def get_current_user():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header[7:]
    return decode_token(token)


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.json or {}
    username = data.get("username", "")
    password = data.get("password", "")

    # [VULN-01] SQL Injection: user input concatenated directly into query string
    hashed = hashlib.md5(password.encode()).hexdigest()
    query = (
        f"SELECT * FROM users WHERE username='{username}' AND password='{hashed}'"
    )

    conn = get_db()
    try:
        user = conn.execute(query).fetchone()
    finally:
        conn.close()

    if not user:
        return jsonify({"error": "Invalid credentials"}), 401

    conn = get_db()
    conn.execute(
        "UPDATE users SET last_login=datetime('now') WHERE id=?", (user["id"],)
    )
    conn.commit()
    conn.close()

    token = generate_token(user["id"], user["username"], user["role"])

    # [VULN-02] Open Redirect: redirect parameter not validated against allowlist
    redirect_to = request.args.get("redirect", "/dashboard")

    return jsonify({
        "token": token,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "role": user["role"],
            "email": user["email"],
        },
        "redirect": redirect_to,
    })


@auth_bp.route("/logout", methods=["POST"])
def logout():
    # Tokens are stateless; client discards the token locally
    return jsonify({"message": "Logged out successfully"})


@auth_bp.route("/me", methods=["GET"])
def me():
    user = get_current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db()
    row = conn.execute(
        "SELECT id, username, email, role, bio, avatar, created_at, last_login FROM users WHERE id=?",
        (user["user_id"],),
    ).fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "User not found"}), 404

    return jsonify(dict(row))


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.json or {}

    conn = get_db()
    setting = conn.execute(
        "SELECT value FROM settings WHERE key='allow_registration'"
    ).fetchone()
    conn.close()

    if not setting or setting["value"] != "true":
        return jsonify({"error": "Registration is currently disabled"}), 403

    username = data.get("username", "").strip()
    password = data.get("password", "")
    email = data.get("email", "").strip()

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    hashed = hashlib.md5(password.encode()).hexdigest()

    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (username, password, email, role) VALUES (?, ?, ?, 'subscriber')",
            (username, hashed, email),
        )
        conn.commit()
    except Exception as e:
        conn.close()
        return jsonify({"error": "Username already taken"}), 409
    finally:
        conn.close()

    return jsonify({"message": "Registration successful"}), 201
