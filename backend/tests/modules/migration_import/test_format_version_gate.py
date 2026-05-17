"""Format-version gate — refuses ``>=1.0`` files."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from app.modules.migration_import.dpmf.reader import DpmfFormatError
from app.modules.migration_import.service import ImportJobService


def _build_dpmf(path: Path, *, format_version: str) -> None:
    conn = sqlite3.connect(path)
    try:
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
        meta = {
            "format_version": format_version,
            "source_system": "gesden",
            "exporter_tool": "dental-bridge",
            "exporter_version": "0.1.0",
            "exported_at": "2026-05-17T00:00:00Z",
            "tenant_label": "test",
            "source_schema_fingerprint": "sha256:test",
            "source_adapter_version": "0.0.1",
            "integrity_hash_algo": "sha256",
            "integrity_hash": "",
        }
        conn.executemany("INSERT INTO _meta VALUES (?, ?)", list(meta.items()))
        conn.commit()
    finally:
        conn.close()


def test_check_format_version_accepts_minor_patch_in_0_series() -> None:
    # Should not raise.
    ImportJobService._check_format_version({"format_version": "0.5.12"})


def test_check_format_version_refuses_1_0() -> None:
    with pytest.raises(DpmfFormatError):
        ImportJobService._check_format_version({"format_version": "1.0.0"})


def test_check_format_version_refuses_invalid() -> None:
    with pytest.raises(DpmfFormatError):
        ImportJobService._check_format_version({"format_version": ""})
    with pytest.raises(DpmfFormatError):
        ImportJobService._check_format_version({})
