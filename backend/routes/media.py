import os
import subprocess
from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
from database import get_db
from routes.auth import get_current_user
from config import UPLOAD_FOLDER

media_bp = Blueprint("media", __name__)


def require_auth():
    user = get_current_user()
    if not user:
        return None, jsonify({"error": "Unauthorized"}), 401
    return user, None, None


def _safe_media_path(user_path):
    """Resolve *user_path* safely inside UPLOAD_FOLDER.

    Returns an absolute canonical path if the resolved result is within the
    uploads directory, otherwise returns ``None``.
    """
    joined = os.path.join(UPLOAD_FOLDER, user_path)
    resolved = os.path.realpath(joined)
    upload_base = os.path.realpath(UPLOAD_FOLDER)
    if not resolved.startswith(upload_base + os.sep) and resolved != upload_base:
        return None
    return resolved


@media_bp.route("", methods=["GET"])
def list_media():
    user, err, code = require_auth()
    if err:
        return err, code

    conn = get_db()
    rows = conn.execute(
        "SELECT m.*, u.username as uploader_name FROM media m "
        "LEFT JOIN users u ON m.uploader_id = u.id ORDER BY m.uploaded_at DESC"
    ).fetchall()
    conn.close()

    return jsonify([dict(r) for r in rows])


@media_bp.route("/upload", methods=["POST"])
def upload_file():
    user, err, code = require_auth()
    if err:
        return err, code

    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    f = request.files["file"]
    if not f.filename:
        return jsonify({"error": "Empty filename"}), 400

    # [VULN-12] Unrestricted File Upload: only original filename is secured for
    # path traversal, but no MIME type or extension validation is performed.
    # Attackers can upload .py, .php, or other executable files.
    filename = secure_filename(f.filename)
    save_path = os.path.join(UPLOAD_FOLDER, filename)
    f.save(save_path)

    size = os.path.getsize(save_path)
    mime = f.content_type or "application/octet-stream"

    conn = get_db()
    cur = conn.execute(
        "INSERT INTO media (filename, original_name, mime_type, size, uploader_id) VALUES (?,?,?,?,?)",
        (filename, f.filename, mime, size, user["user_id"]),
    )
    media_id = cur.lastrowid
    conn.commit()
    conn.close()

    return jsonify({"message": "File uploaded", "id": media_id, "filename": filename}), 201


@media_bp.route("/download", methods=["GET"])
def download_file():
    user, err, code = require_auth()
    if err:
        return err, code

    filename = request.args.get("file", "")
    if not filename:
        return jsonify({"error": "Filename required"}), 400

    file_path = _safe_media_path(filename)
    if file_path is None:
        return jsonify({"error": "Invalid file path"}), 400

    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404

    return send_file(file_path, as_attachment=True)


@media_bp.route("/preview", methods=["GET"])
def preview_file():
    user, err, code = require_auth()
    if err:
        return err, code

    path = request.args.get("path", "")
    if not path:
        return jsonify({"error": "Path required"}), 400

    file_path = _safe_media_path(path)
    if file_path is None:
        return jsonify({"error": "Invalid path"}), 400

    if not os.path.exists(file_path):
        return jsonify({"error": "Not found"}), 404

    return send_file(file_path)


@media_bp.route("/thumbnail", methods=["POST"])
def generate_thumbnail():
    user, err, code = require_auth()
    if err:
        return err, code

    data = request.json or {}
    filename = data.get("filename", "")
    # [VULN-13] Command Injection: filename and size from client inserted directly
    # into a shell command via os.system. Payload: filename = "a.jpg; id > /tmp/pwn"
    size = data.get("size", "150x150")

    src = os.path.join(UPLOAD_FOLDER, filename)
    dst = os.path.join(UPLOAD_FOLDER, f"thumb_{filename}")

    cmd = f"convert {src} -resize {size} {dst}"
    ret = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    if ret.returncode != 0:
        return jsonify({"error": "Thumbnail generation failed", "detail": ret.stderr}), 500

    return jsonify({"message": "Thumbnail created", "thumbnail": f"thumb_{filename}"})


@media_bp.route("/<int:media_id>", methods=["DELETE"])
def delete_media(media_id):
    user, err, code = require_auth()
    if err:
        return err, code

    conn = get_db()
    row = conn.execute("SELECT * FROM media WHERE id=?", (media_id,)).fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "Not found"}), 404

    try:
        os.remove(os.path.join(UPLOAD_FOLDER, row["filename"]))
    except OSError:
        pass

    conn.execute("DELETE FROM media WHERE id=?", (media_id,))
    conn.commit()
    conn.close()

    return jsonify({"message": "File deleted"})
