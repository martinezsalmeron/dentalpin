"""Fernet encryption for binary blobs (PFX bytes).

The core helper at ``app.core.email.encryption`` only handles strings;
PFX certificates are arbitrary binary data, so we add ``encrypt_bytes``
and ``decrypt_bytes`` here. Same key derivation (SHA-256 of
``settings.SECRET_KEY``) so values encrypted by either helper are
mutually decryptable.
"""

from __future__ import annotations

import logging

from cryptography.fernet import InvalidToken

from app.core.email.encryption import _get_fernet, decrypt_password, encrypt_password

logger = logging.getLogger(__name__)


def encrypt_bytes(data: bytes) -> bytes:
    if not data:
        return b""
    fernet = _get_fernet()
    return fernet.encrypt(data)


def decrypt_bytes(token: bytes) -> bytes | None:
    if not token:
        return None
    try:
        fernet = _get_fernet()
        return fernet.decrypt(token)
    except InvalidToken:
        logger.error("Failed to decrypt PFX bytes: invalid token")
        return None


__all__ = ["encrypt_bytes", "decrypt_bytes", "encrypt_password", "decrypt_password"]
