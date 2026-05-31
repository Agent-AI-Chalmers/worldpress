import os

DATABASE_PATH = os.path.join(os.path.dirname(__file__), "data.db")
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")

# Application signing key for token generation
APP_SECRET = "wp_secret_2024"

# Default administrator credentials for initial setup
# Override via environment variables: WP_ADMIN_USER, WP_ADMIN_PASS
DEFAULT_ADMIN_USER = os.environ.get("WP_ADMIN_USER", "admin")
DEFAULT_ADMIN_PASS = os.environ.get("WP_ADMIN_PASS", "admin123")

# Allowed file size limit (bytes)
MAX_CONTENT_LENGTH = 16 * 1024 * 1024

# Token expiration in seconds
TOKEN_EXPIRY = 86400
