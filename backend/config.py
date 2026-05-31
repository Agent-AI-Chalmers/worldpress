import os

DATABASE_PATH = os.path.join(os.path.dirname(__file__), "data.db")
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")

# Application signing key for token generation — MUST be set via environment variable
_jwt_secret = os.environ.get("JWT_SECRET")
if not _jwt_secret:
    raise RuntimeError(
        "JWT_SECRET environment variable is not set. "
        "Generate a cryptographically strong random secret (e.g., via "
        "`python3 -c \"import secrets; print(secrets.token_hex(32))\"`) "
        "and export it before starting the application."
    )
APP_SECRET = _jwt_secret

# Default administrator credentials for initial setup
DEFAULT_ADMIN_USER = "admin"
DEFAULT_ADMIN_PASS = "admin123"

# Allowed file size limit (bytes)
MAX_CONTENT_LENGTH = 16 * 1024 * 1024

# Token expiration in seconds
TOKEN_EXPIRY = 86400
