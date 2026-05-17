"""DPMF reader interop tests.

These tests do **not** touch the database. They hand-roll a minimal
DPMF SQLite container that follows the v0.1 spec, then exercise the
reader's classification + integrity-hash + format-version surface.

If the integrity hash diverges from dental-bridge's writer, callers
will refuse legitimately-produced files in production. The fixture
below mirrors the writer's line format byte-for-byte; updating the
algorithm requires updating dental-bridge in lockstep (major version
bump).
"""

from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

import pytest

from app.modules.migration_import.dpmf import (
    Layering,
    detect_layering,
    open_dpmf,
)
from app.modules.migration_import.dpmf.compress import ZSTD_MAGIC
from app.modules.migration_import.dpmf.reader import (
    SQLITE_MAGIC,
    DpmfFormatError,
)


def _build_minimal_dpmf(path: Path, *, format_version: str = "0.1.0") -> str:
    """Build a tiny but spec-compliant DPMF file. Returns its integrity hash."""
    conn = sqlite3.connect(path)
    try:
        conn.execute("PRAGMA user_version = 1")
        conn.execute("CREATE TABLE _meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        conn.execute(
            "CREATE TABLE _entities (entity_type TEXT PRIMARY KEY, row_count INTEGER NOT NULL, schema_version TEXT NOT NULL)"
        )
        conn.execute(
            "CREATE TABLE _files (canonical_uuid TEXT PRIMARY KEY, parent_entity_type TEXT NOT NULL, "
            "parent_canonical_uuid TEXT NOT NULL, relative_path TEXT NOT NULL, "
            "declared_size_bytes INTEGER, sha256 TEXT, mime_hint TEXT)"
        )
        conn.execute(
            "CREATE TABLE _warnings (id INTEGER PRIMARY KEY AUTOINCREMENT, entity_type TEXT, "
            "source_id TEXT, severity TEXT NOT NULL, code TEXT NOT NULL, message TEXT NOT NULL, raw_data TEXT)"
        )
        conn.execute(
            'CREATE TABLE "patient" (canonical_uuid TEXT PRIMARY KEY, source_id TEXT NOT NULL, '
            "source_system TEXT NOT NULL, payload TEXT NOT NULL, raw_source_data TEXT NOT NULL, "
            "extracted_at TEXT NOT NULL)"
        )
        # _meta — integrity_hash gets overwritten after we compute it.
        meta_rows = {
            "format_version": format_version,
            "source_system": "gesden",
            "source_adapter_version": "0.0.1",
            "exporter_tool": "dental-bridge",
            "exporter_version": "0.1.0",
            "exported_at": "2026-05-17T00:00:00Z",
            "tenant_label": "test",
            "source_schema_fingerprint": "sha256:test",
            "integrity_hash_algo": "sha256",
            "integrity_hash": "PENDING",
        }
        conn.executemany("INSERT INTO _meta (key, value) VALUES (?, ?)", list(meta_rows.items()))

        # One patient + one _files manifest entry.
        conn.execute(
            "INSERT INTO _entities (entity_type, row_count, schema_version) VALUES (?, ?, ?)",
            ("patient", 1, "0.1.0"),
        )
        payload = '{"given_name":"Ana","family_name":"Lopez","sex":"female"}'
        raw = '{"Nombre":"Ana","Apellidos":"Lopez"}'
        conn.execute(
            'INSERT INTO "patient" VALUES (?, ?, ?, ?, ?, ?)',
            ("uuid-1", "1", "gesden", payload, raw, "2026-05-17T00:00:00Z"),
        )
        conn.commit()

        # Compute integrity hash with the canonical algorithm.
        hasher = hashlib.sha256()
        for row in conn.execute(
            "SELECT entity_type, row_count, schema_version FROM _entities ORDER BY entity_type"
        ):
            hasher.update(f"_entities|{row[0]}|{row[1]}|{row[2]}\n".encode())
        for row in conn.execute(
            "SELECT canonical_uuid, source_id, source_system, payload, raw_source_data "
            'FROM "patient" ORDER BY canonical_uuid'
        ):
            hasher.update(f"patient|{row[0]}|{row[1]}|{row[2]}|{row[3]}|{row[4]}\n".encode())
        # No _files or _warnings.
        digest = hasher.hexdigest()
        conn.execute("UPDATE _meta SET value = ? WHERE key = 'integrity_hash'", (digest,))
        conn.commit()
        return digest
    finally:
        conn.close()


def test_detect_layering_raw(tmp_path: Path) -> None:
    dpmf = tmp_path / "raw.dpm"
    _build_minimal_dpmf(dpmf)
    assert detect_layering(dpmf) is Layering.RAW
    with dpmf.open("rb") as f:
        assert f.read(4).startswith(SQLITE_MAGIC)


def test_detect_layering_unknown_magic_raises(tmp_path: Path) -> None:
    bad = tmp_path / "bad"
    bad.write_bytes(b"GIF87aXXXXXX")
    with pytest.raises(DpmfFormatError):
        detect_layering(bad)


def test_open_raw_reads_meta_and_recomputes_hash(tmp_path: Path) -> None:
    dpmf = tmp_path / "raw.dpm"
    expected_hash = _build_minimal_dpmf(dpmf)
    with open_dpmf(dpmf) as handle:
        assert handle.format_version() == "0.1.0"
        assert handle.source_system() == "gesden"
        assert handle.entity_counts() == {"patient": 1}
        computed = handle.recompute_integrity_hash()
        assert computed == expected_hash
        assert handle.declared_integrity_hash() == expected_hash


def test_open_zstd_layer(tmp_path: Path) -> None:
    """Round-trip through the zstd layer."""
    import zstandard

    raw = tmp_path / "raw.dpm"
    expected_hash = _build_minimal_dpmf(raw)
    zst = tmp_path / "wrapped.dpm.zst"
    cctx = zstandard.ZstdCompressor()
    with raw.open("rb") as src, zst.open("wb") as dst:
        cctx.copy_stream(src, dst)
    # Confirm magic
    with zst.open("rb") as f:
        assert f.read(4) == ZSTD_MAGIC
    assert detect_layering(zst) is Layering.ZSTD
    with open_dpmf(zst) as handle:
        assert handle.recompute_integrity_hash() == expected_hash


def test_open_encrypted_layer_roundtrip(tmp_path: Path) -> None:
    """Encrypt → decrypt → verify hash."""
    import base64
    import json
    import os
    import struct

    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

    raw = tmp_path / "raw.dpm"
    expected_hash = _build_minimal_dpmf(raw)
    body = raw.read_bytes()

    passphrase = "reference-vector"
    salt = os.urandom(16)
    iv = os.urandom(12)
    kdf = Scrypt(salt=salt, length=32, n=1 << 17, r=8, p=1)
    key = kdf.derive(passphrase.encode("utf-8"))

    header = json.dumps(
        {
            "v": 1,
            "kdf": "scrypt",
            "kdf_params": {
                "n": 1 << 17,
                "r": 8,
                "p": 1,
                "salt": base64.b64encode(salt).decode("ascii"),
            },
            "cipher": "AES-256-GCM",
            "iv": base64.b64encode(iv).decode("ascii"),
            "inner_layout": "raw",
        },
        sort_keys=False,
    ).encode("utf-8")
    aead = AESGCM(key)
    ciphertext = aead.encrypt(iv, body, header)

    enc = tmp_path / "wrapped.dpm.enc"
    with enc.open("wb") as f:
        f.write(b"DPME")
        f.write(struct.pack("<I", len(header)))
        f.write(header)
        f.write(ciphertext)

    assert detect_layering(enc) is Layering.ENCRYPTED
    with open_dpmf(enc, passphrase=passphrase) as handle:
        assert handle.recompute_integrity_hash() == expected_hash


def test_wrong_passphrase_raises(tmp_path: Path) -> None:
    """Wrong key → cryptography raises InvalidTag, mapped to DpmeError."""
    from app.modules.migration_import.dpmf.crypto import DpmeError

    # Build encrypted file with key A, then try to open with key B.
    test_open_encrypted_layer_roundtrip(tmp_path)
    enc = tmp_path / "wrapped.dpm.enc"
    with pytest.raises(DpmeError):
        with open_dpmf(enc, passphrase="wrong-passphrase"):
            pass
