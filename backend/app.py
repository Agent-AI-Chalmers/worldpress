from flask import Flask, jsonify
from flask_cors import CORS
from database import init_db
from routes.auth import auth_bp
from routes.users import users_bp
from routes.posts import posts_bp
from routes.media import media_bp
from routes.settings import settings_bp

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(users_bp, url_prefix="/api/users")
app.register_blueprint(posts_bp, url_prefix="/api/posts")
app.register_blueprint(media_bp, url_prefix="/api/media")
app.register_blueprint(settings_bp, url_prefix="/api/settings")


# [VULN-18] Information Disclosure: unhandled exceptions expose full stack traces
# and internal module paths to the client in a JSON response.
# Fixed: Return generic error message instead of internal details.
@app.errorhandler(Exception)
def handle_exception(e):
    return jsonify({
        "error": "An internal error occurred",
    }), 500


@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "version": "1.0.0"})


if __name__ == "__main__":
    init_db()
    # Debug mode must be disabled in production
    app.run(host="0.0.0.0", port=5000, debug=False)
