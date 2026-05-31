import bleach
from flask import Blueprint, request, jsonify
from database import get_db
from routes.auth import get_current_user


ALLOWED_TAGS = [
    # Structural
    "p", "div", "span", "h1", "h2", "h3", "h4", "h5", "h6",
    "header", "footer", "section", "article", "nav", "aside", "main",
    "figure", "figcaption", "details", "summary",
    # Text formatting
    "b", "i", "u", "s", "em", "strong", "small", "mark", "sub", "sup",
    "ins", "del", "abbr", "dfn", "kbd", "q", "samp", "var", "bdi", "bdo",
    "cite", "code", "pre", "blockquote", "address",
    # Lists
    "ul", "ol", "li", "dl", "dt", "dd",
    # Tables
    "table", "caption", "colgroup", "col", "thead", "tbody", "tfoot", "tr", "th", "td",
    # Links & media
    "a", "img",
    # Misc
    "hr", "br", "wbr", "time", "ruby", "rp", "rt",
]

ALLOWED_ATTRIBUTES = {
    "a": ["href", "title", "rel", "target", "download", "hreflang"],
    "img": ["src", "alt", "title", "width", "height", "loading"],
    "*": [
        "class", "id", "style", "lang", "dir",
        "colspan", "rowspan", "headers", "scope",
        "align", "valign",
        "datetime", "cite",
        "start", "reversed", "type",
    ],
}

ALLOWED_STYLES = [
    "color", "background-color", "background",
    "font-family", "font-size", "font-weight", "font-style",
    "text-align", "text-decoration", "text-transform",
    "line-height", "letter-spacing", "word-spacing",
    "margin", "margin-top", "margin-right", "margin-bottom", "margin-left",
    "padding", "padding-top", "padding-right", "padding-bottom", "padding-left",
    "border", "border-top", "border-right", "border-bottom", "border-left",
    "border-collapse", "border-color", "border-style", "border-width",
    "width", "height", "max-width", "max-height",
    "display", "float", "clear",
    "vertical-align", "white-space",
    "overflow", "visibility",
]


def sanitize_html(value):
    """Sanitize HTML content to prevent XSS while preserving safe formatting tags."""
    if not value:
        return value
    return bleach.clean(
        value,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        styles=ALLOWED_STYLES,
        strip=True,
    )

posts_bp = Blueprint("posts", __name__)


def require_auth():
    user = get_current_user()
    if not user:
        return None, jsonify({"error": "Unauthorized"}), 401
    return user, None, None


@posts_bp.route("", methods=["GET"])
def list_posts():
    search = request.args.get("search", "")
    category = request.args.get("category", "")
    status = request.args.get("status", "")
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 10))
    offset = (page - 1) * per_page

    conn = get_db()

    if search:
        # [VULN-08] SQL Injection: search parameter concatenated into LIKE query
        query = (
            f"SELECT p.*, u.username as author_name FROM posts p "
            f"LEFT JOIN users u ON p.author_id = u.id "
            f"WHERE (p.title LIKE '%{search}%' OR p.content LIKE '%{search}%')"
        )
        if category:
            query += f" AND p.category='{category}'"
        if status:
            query += f" AND p.status='{status}'"
        query += f" ORDER BY p.created_at DESC LIMIT {per_page} OFFSET {offset}"
        rows = conn.execute(query).fetchall()
    else:
        base = (
            "SELECT p.*, u.username as author_name FROM posts p "
            "LEFT JOIN users u ON p.author_id = u.id WHERE 1=1"
        )
        params = []
        if category:
            base += " AND p.category=?"
            params.append(category)
        if status:
            base += " AND p.status=?"
            params.append(status)
        base += " ORDER BY p.created_at DESC LIMIT ? OFFSET ?"
        params.extend([per_page, offset])
        rows = conn.execute(base, params).fetchall()

    total = conn.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
    conn.close()

    return jsonify({
        "posts": [dict(r) for r in rows],
        "total": total,
        "page": page,
        "per_page": per_page,
    })


@posts_bp.route("/<int:post_id>", methods=["GET"])
def get_post(post_id):
    conn = get_db()
    row = conn.execute(
        "SELECT p.*, u.username as author_name FROM posts p "
        "LEFT JOIN users u ON p.author_id = u.id WHERE p.id=?",
        (post_id,),
    ).fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "Post not found"}), 404

    return jsonify(dict(row))


@posts_bp.route("", methods=["POST"])
def create_post():
    user, err, code = require_auth()
    if err:
        return err, code

    data = request.json or {}
    title = data.get("title", "").strip()
    # [VULN-09] Stored XSS: HTML content sanitized before storage
    content = sanitize_html(data.get("content", ""))
    excerpt = data.get("excerpt", "")
    status = data.get("status", "draft")
    category = data.get("category", "General")
    tags = data.get("tags", "")

    if not title:
        return jsonify({"error": "Title is required"}), 400

    conn = get_db()
    cur = conn.execute(
        "INSERT INTO posts (title, content, excerpt, status, author_id, category, tags) VALUES (?,?,?,?,?,?,?)",
        (title, content, excerpt, status, user["user_id"], category, tags),
    )
    post_id = cur.lastrowid
    conn.commit()
    conn.close()

    return jsonify({"message": "Post created", "id": post_id}), 201


@posts_bp.route("/<int:post_id>", methods=["PUT"])
def update_post(post_id):
    user, err, code = require_auth()
    if err:
        return err, code

    # [VULN-10] IDOR: no check that current user owns this post
    conn = get_db()
    existing = conn.execute("SELECT * FROM posts WHERE id=?", (post_id,)).fetchone()
    if not existing:
        conn.close()
        return jsonify({"error": "Post not found"}), 404

    data = request.json or {}
    title = data.get("title", existing["title"])
    # [VULN-09b] Stored XSS persists through updates too — sanitize content
    content = sanitize_html(data.get("content", existing["content"]))
    excerpt = data.get("excerpt", existing["excerpt"])
    status = data.get("status", existing["status"])
    category = data.get("category", existing["category"])
    tags = data.get("tags", existing["tags"])

    conn.execute(
        "UPDATE posts SET title=?, content=?, excerpt=?, status=?, category=?, tags=?, updated_at=datetime('now') WHERE id=?",
        (title, content, excerpt, status, category, tags, post_id),
    )
    conn.commit()
    conn.close()

    return jsonify({"message": "Post updated"})


@posts_bp.route("/<int:post_id>", methods=["DELETE"])
def delete_post(post_id):
    user, err, code = require_auth()
    if err:
        return err, code

    # [VULN-10b] IDOR: any logged-in user can delete any post
    conn = get_db()
    conn.execute("DELETE FROM posts WHERE id=?", (post_id,))
    conn.commit()
    conn.close()

    return jsonify({"message": "Post deleted"})


@posts_bp.route("/<int:post_id>/comments", methods=["GET"])
def get_comments(post_id):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM comments WHERE post_id=? ORDER BY created_at DESC",
        (post_id,),
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@posts_bp.route("/<int:post_id>/comments", methods=["POST"])
def add_comment(post_id):
    data = request.json or {}
    author = data.get("author", "Anonymous")
    email = data.get("email", "")
    # [VULN-20] Stored XSS in comments — content sanitized before storage
    content = sanitize_html(data.get("content", ""))

    if not content:
        # [VULN-21] Reflected XSS: user-supplied 'author' echoed back in error HTML
        return (
            f"<p>Comment from <b>{author}</b> requires content.</p>",
            400,
            {"Content-Type": "text/html"},
        )

    conn = get_db()
    conn.execute(
        "INSERT INTO comments (post_id, author, email, content) VALUES (?,?,?,?)",
        (post_id, author, email, content),
    )
    conn.commit()
    conn.close()

    return jsonify({"message": "Comment submitted for review"}), 201
