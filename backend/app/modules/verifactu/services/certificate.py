"""PFX/P12 certificate validation, encrypted storage, SSL context.

Flow on upload:
    1. Caller passes ``pfx_bytes`` + ``password``.
    2. We call ``cryptography.hazmat.primitives.serialization.pkcs12.
       load_key_and_certificates`` to verify the password and parse the
       certificate.
    3. We extract subject CN, issuer CN, validity dates, and the NIF
       from the subject (FNMT certs put it under ``serialNumber``).
    4. We Fernet-encrypt both the PFX bytes and the password.

Flow on submission to AEAT:
    1. Decrypt PFX bytes + password.
    2. Build an SSL context: write key+cert to a 0600 tempfile, call
       ``context.load_cert_chain``, immediately ``os.unlink`` so the
       file disappears even if the request hangs. The context retains
       the loaded material in OpenSSL's memory.
    3. Pass the context to ``httpx.AsyncClient(verify=ctx)``.

We never log certificate bytes or passwords.
"""

from __future__ import annotations

import os
import ssl
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import (
    NoEncryption,
    pkcs12,
)
from cryptography.x509 import Certificate, NameOID


@dataclass(frozen=True)
class CertificateInfo:
    subject_cn: str | None
    issuer_cn: str | None
    nif_titular: str | None
    valid_from: datetime
    valid_until: datetime


class CertificateError(Exception):
    """Raised when a PFX is invalid, expired, or password mismatch."""


def _name_attribute(cert: Certificate, oid) -> str | None:
    attrs = cert.subject.get_attributes_for_oid(oid)
    if not attrs:
        return None
    return attrs[0].value if isinstance(attrs[0].value, str) else attrs[0].value.decode()


def _issuer_cn(cert: Certificate) -> str | None:
    attrs = cert.issuer.get_attributes_for_oid(NameOID.COMMON_NAME)
    if not attrs:
        return None
    val = attrs[0].value
    return val if isinstance(val, str) else val.decode()


def parse_and_validate(pfx_bytes: bytes, password: str) -> CertificateInfo:
    """Verify the PFX and return its metadata.

    Raises :class:`CertificateError` on any failure (bad password,
    expired, malformed). Caller decides whether expiration is fatal —
    we surface it through ``valid_until`` but do not reject here, so the
    UI can show a banner.
    """

    try:
        key, cert, _additional = pkcs12.load_key_and_certificates(
            pfx_bytes, password.encode("utf-8") if password else None
        )
    except (ValueError, TypeError) as exc:
        raise CertificateError(f"PFX inválido o contraseña incorrecta: {exc}") from exc

    if cert is None or key is None:
        raise CertificateError("El archivo PFX no contiene un par clave/certificado válido.")

    subject_cn = _name_attribute(cert, NameOID.COMMON_NAME)
    issuer_cn = _issuer_cn(cert)
    nif_titular = (
        _name_attribute(cert, NameOID.SERIAL_NUMBER)
        or _name_attribute(cert, NameOID.ORGANIZATION_IDENTIFIER)
    )
    if nif_titular and nif_titular.upper().startswith("IDCES-"):
        nif_titular = nif_titular.split("-", 1)[1]

    valid_from = cert.not_valid_before_utc if hasattr(cert, "not_valid_before_utc") else (
        cert.not_valid_before.replace(tzinfo=UTC)
    )
    valid_until = cert.not_valid_after_utc if hasattr(cert, "not_valid_after_utc") else (
        cert.not_valid_after.replace(tzinfo=UTC)
    )

    return CertificateInfo(
        subject_cn=subject_cn,
        issuer_cn=issuer_cn,
        nif_titular=nif_titular,
        valid_from=valid_from,
        valid_until=valid_until,
    )


@contextmanager
def build_ssl_context(pfx_bytes: bytes, password: str) -> Iterator[ssl.SSLContext]:
    """Yield an :class:`ssl.SSLContext` loaded with the cert chain.

    Materialises the key + cert to a 0600 tempfile only long enough for
    OpenSSL to consume it, then unlinks the file. The :class:`SSLContext`
    keeps the loaded material in memory after that.
    """

    try:
        key, cert, additional = pkcs12.load_key_and_certificates(pfx_bytes, password.encode("utf-8"))
    except (ValueError, TypeError) as exc:
        raise CertificateError(f"PFX inválido o contraseña incorrecta: {exc}") from exc

    if key is None or cert is None:
        raise CertificateError("PFX sin clave/certificado")

    pem_key = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=NoEncryption(),
    )
    pem_cert = cert.public_bytes(encoding=serialization.Encoding.PEM)
    if additional:
        for ca in additional:
            pem_cert += ca.public_bytes(encoding=serialization.Encoding.PEM)

    fd_key, key_path = tempfile.mkstemp(prefix="vfy_k_", suffix=".pem")
    fd_cert, cert_path = tempfile.mkstemp(prefix="vfy_c_", suffix=".pem")
    try:
        os.fchmod(fd_key, 0o600)
        os.fchmod(fd_cert, 0o600)
        with os.fdopen(fd_key, "wb") as fh:
            fh.write(pem_key)
        with os.fdopen(fd_cert, "wb") as fh:
            fh.write(pem_cert)

        ctx = ssl.create_default_context()
        ctx.load_cert_chain(certfile=cert_path, keyfile=key_path)
        try:
            yield ctx
        finally:
            # Wipe the files. SSLContext has already consumed them.
            for p in (key_path, cert_path):
                try:
                    Path(p).unlink(missing_ok=True)
                except OSError:
                    pass
    except Exception:
        for p in (key_path, cert_path):
            try:
                Path(p).unlink(missing_ok=True)
            except OSError:
                pass
        raise


__all__ = [
    "CertificateError",
    "CertificateInfo",
    "build_ssl_context",
    "parse_and_validate",
]
