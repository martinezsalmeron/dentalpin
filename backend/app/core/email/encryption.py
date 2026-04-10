"""Password encryption utilities for SMTP settings.

Uses Fernet symmetric encryption derived from the application's SECRET_KEY.
"""

import base64
import hashlib
import logging

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)

# Cache the Fernet instance
_fernet: Fernet | None = None


def _get_fernet() -> Fernet:
    """Get or create Fernet instance derived from SECRET_KEY."""
    global _fernet
    if _fernet is None:
        from app.config import settings

        # Derive a 32-byte key from SECRET_KEY using SHA-256
        # Then encode it as base64 for Fernet
        key_bytes = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
        fernet_key = base64.urlsafe_b64encode(key_bytes)
        _fernet = Fernet(fernet_key)

    return _fernet


def encrypt_password(password: str) -> str:
    """Encrypt a password for storage.

    Args:
        password: The plaintext password to encrypt.

    Returns:
        The encrypted password as a base64-encoded string.
    """
    if not password:
        return ""

    fernet = _get_fernet()
    encrypted = fernet.encrypt(password.encode())
    return encrypted.decode()


def decrypt_password(encrypted_password: str) -> str | None:
    """Decrypt a stored password.

    Args:
        encrypted_password: The encrypted password string.

    Returns:
        The decrypted plaintext password, or None if decryption fails.
    """
    if not encrypted_password:
        return None

    try:
        fernet = _get_fernet()
        decrypted = fernet.decrypt(encrypted_password.encode())
        return decrypted.decode()
    except InvalidToken:
        logger.error("Failed to decrypt password: invalid token")
        return None
    except Exception as e:
        logger.error(f"Failed to decrypt password: {e}")
        return None
