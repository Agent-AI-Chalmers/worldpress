import os

DATABASE_PATH = os.path.join(os.path.dirname(__file__), "data.db")
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")

# Application signing key for token generation
APP_SECRET = "wp_secret_2024"

# Default administrator credentials for initial setup
DEFAULT_ADMIN_USER = "admin"
DEFAULT_ADMIN_PASS = "admin123"

# Allowed file size limit (bytes)
MAX_CONTENT_LENGTH = 16 * 1024 * 1024

# Token expiration in seconds
TOKEN_EXPIRY = 86400
