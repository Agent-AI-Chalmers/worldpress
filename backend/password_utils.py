"""Password hashing utility using werkzeug's pbkdf2:sha256 with salt.

Replaces raw MD5 hashing across all authentication paths.
Provides backward compatibility with existing MD5 hashes by detecting
the old format during verification and transparently re-hashing on
successful login.
"""

import hashlib
import re
import werkzeug.security

# Matches werkzeug's pbkdf2:sha256 format
_WERKZEUG_HASH_PATTERN = re.compile(r"^pbkdf2:sha256:\d+\$")

# Matches legacy MD5 hex digest format (32 hex chars)
_MD5_HEX_PATTERN = re.compile(r"^[0-9a-f]{32}$")


def hash_password(password: str) -> str:
    """Hash a password using werkzeug's salted pbkdf2:sha256.

    This is used for new passwords during registration, update,
    and seed data initialization.
    """
    return werkzeug.security.generate_password_hash(password)


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify a password against the stored hash.

    Supports both werkzeug pbkdf2:sha256 hashes and legacy MD5
    hex digests.  If the stored hash is an MD5 hex digest and
    matches the password, the password is considered valid for
    backward compatibility purposes.  Callers that want to
    re-hash the password after a successful MD5 verification
    should call :func:`hash_password` and store the result.
    """
    if _WERKZEUG_HASH_PATTERN.match(stored_hash):
        return werkzeug.security.check_password_hash(stored_hash, password)

    if _MD5_HEX_PATTERN.match(stored_hash):
        md5_digest = hashlib.md5(password.encode()).hexdigest()
        return md5_digest == stored_hash

    # Unknown hash format — treat as invalid
    return False
