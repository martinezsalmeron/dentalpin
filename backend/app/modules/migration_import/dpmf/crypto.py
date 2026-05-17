"""DPME envelope reader — AES-256-GCM with scrypt-derived key.

Mirrors the layout produced by ``dental_bridge.core.dpmf.crypto``. The
key is derived on every decrypt — we never persist or cache it.

On-disk:

    +--------+-------------------+-------------------+-----------------------+
    | 'DPME' | header_length (u4)| header (JSON utf8)| ciphertext + GCM tag  |
    +--------+-------------------+-------------------+-----------------------+
"""

from __future__ import annotations

import base64
import json
import struct
from dataclasses import dataclass
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

DPME_MAGIC = b"DPME"
_SCRYPT_N = 1 << 17  # 131072 — must match writer
_SCRYPT_R = 8
_SCRYPT_P = 1
_KEY_LEN = 32  # AES-256
_HEADER_VERSION = 1


class DpmeError(ValueError):
    """Raised for any malformed envelope, unsupported parameters or
    failed authentication (wrong passphrase / tampered ciphertext)."""


@dataclass(slots=True, frozen=True)
class EnvelopeHeader:
    inner_layout: str  # "raw" or "zstd"
    salt: bytes
    iv: bytes

    @classmethod
    def from_json(cls, blob: bytes) -> EnvelopeHeader:
        try:
            payload = json.loads(blob.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise DpmeError("DPME header is not valid UTF-8 JSON") from exc
        if payload.get("v") != _HEADER_VERSION:
            raise DpmeError(f"unsupported DPME header version: {payload.get('v')!r}")
        if payload.get("cipher") != "AES-256-GCM":
            raise DpmeError(f"unsupported cipher: {payload.get('cipher')!r}")
        if payload.get("kdf") != "scrypt":
            raise DpmeError(f"unsupported kdf: {payload.get('kdf')!r}")
        inner_layout = payload.get("inner_layout")
        if inner_layout not in ("raw", "zstd"):
            raise DpmeError(f"invalid inner_layout: {inner_layout!r}")
        try:
            return cls(
                inner_layout=inner_layout,
                salt=base64.b64decode(payload["kdf_params"]["salt"]),
                iv=base64.b64decode(payload["iv"]),
            )
        except (KeyError, ValueError) as exc:
            raise DpmeError(f"DPME header missing/invalid field: {exc}") from exc


def _derive_key(passphrase: str, salt: bytes) -> bytes:
    kdf = Scrypt(salt=salt, length=_KEY_LEN, n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P)
    return kdf.derive(passphrase.encode("utf-8"))


def decrypt_to(encrypted: Path, destination: Path, *, passphrase: str) -> EnvelopeHeader:
    """Decrypt ``encrypted`` into ``destination``.

    Returns the parsed envelope header so the caller knows whether to
    follow up with zstd decompression (``header.inner_layout == "zstd"``).

    Raises :class:`DpmeError` on any structural problem or failed
    authentication. Catch this exception type at the API boundary and
    return a 422 to the operator — never re-raise as a 500.
    """
    with encrypted.open("rb") as f:
        magic = f.read(4)
        if magic != DPME_MAGIC:
            raise DpmeError("file is not a DPME envelope")
        raw_len = f.read(4)
        if len(raw_len) != 4:
            raise DpmeError("DPME header length truncated")
        (header_len,) = struct.unpack("<I", raw_len)
        if header_len > 64 * 1024:
            # Defensive — real headers are a few hundred bytes. A massive
            # value means a malformed file, don't try to allocate it.
            raise DpmeError(f"DPME header length implausibly large: {header_len}")
        header_blob = f.read(header_len)
        if len(header_blob) != header_len:
            raise DpmeError("DPME header truncated")
        header = EnvelopeHeader.from_json(header_blob)
        ciphertext = f.read()

    key = _derive_key(passphrase, header.salt)
    aead = AESGCM(key)
    try:
        plaintext = aead.decrypt(header.iv, ciphertext, header_blob)
    except Exception as exc:  # cryptography raises InvalidTag; map to ours
        raise DpmeError("DPMF decryption failed (wrong passphrase or corrupted file)") from exc

    destination.write_bytes(plaintext)
    return header
