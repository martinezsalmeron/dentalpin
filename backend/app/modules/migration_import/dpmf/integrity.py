"""Logical integrity hash — byte-for-byte compatible with dental-bridge.

Per spec §"Integrity verification", the hash is computed over the
*logical content* of the DPMF, not over the SQLite file bytes (those
are not stable across page layouts). The line format must match
``DpmfWriter._compute_logical_hash`` exactly.
"""

from __future__ import annotations

import hashlib
import sqlite3


def _discover_entity_tables(conn: sqlite3.Connection) -> list[str]:
    """Return entity table names in the DPMF, sorted.

    The writer maintains an in-memory ``_known_entity_tables`` set; we
    discover via ``_entities`` instead because it is part of the spec.
    """
    cursor = conn.execute("SELECT entity_type FROM _entities ORDER BY entity_type")
    return [row[0] for row in cursor.fetchall()]


def compute_logical_hash(conn: sqlite3.Connection) -> str:
    """Reproduce dental-bridge's ``_compute_logical_hash`` algorithm.

    Importers MUST get the same digest the writer stored — any drift
    in the line format breaks interop.
    """
    hasher = hashlib.sha256()

    for row in conn.execute(
        "SELECT entity_type, row_count, schema_version FROM _entities ORDER BY entity_type"
    ):
        hasher.update(f"_entities|{row[0]}|{row[1]}|{row[2]}\n".encode())

    for entity_type in _discover_entity_tables(conn):
        # The table name is interpolated; entity_type comes from a
        # PRIMARY KEY column populated by the writer, which itself
        # validates the identifier shape.
        for row in conn.execute(
            f"SELECT canonical_uuid, source_id, source_system, payload, raw_source_data "
            f'FROM "{entity_type}" ORDER BY canonical_uuid'
        ):
            hasher.update(f"{entity_type}|{row[0]}|{row[1]}|{row[2]}|{row[3]}|{row[4]}\n".encode())

    for row in conn.execute(
        "SELECT canonical_uuid, parent_entity_type, parent_canonical_uuid, "
        "relative_path, declared_size_bytes, sha256, mime_hint "
        "FROM _files ORDER BY canonical_uuid"
    ):
        hasher.update(("_files|" + "|".join(str(v) for v in row) + "\n").encode("utf-8"))

    for row in conn.execute(
        "SELECT id, entity_type, source_id, severity, code, message, raw_data "
        "FROM _warnings ORDER BY id"
    ):
        hasher.update(("_warnings|" + "|".join(str(v) for v in row) + "\n").encode("utf-8"))

    return hasher.hexdigest()
