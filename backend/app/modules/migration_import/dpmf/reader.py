"""High-level DPMF reader — opens any layering and exposes a handle.

Pipeline:

1. Read the first 4 bytes — magic.
2. If ``DPME``: decrypt to a temp file (needs passphrase). The header
   tells us whether the inner layout is raw or zstd-wrapped.
3. If ``28 b5 2f fd``: zstd-decompress to a temp file.
4. Open the (now plain) SQLite file read-only.

All intermediate temp files live under a single ``tempfile.TemporaryDirectory``
that the context manager wipes on exit, so failed decrypts/decompressions
don't leave plaintext copies on disk.
"""

from __future__ import annotations

import enum
import logging
import sqlite3
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from .compress import ZSTD_MAGIC, decompress_to
from .crypto import DPME_MAGIC, DpmeError, decrypt_to
from .integrity import compute_logical_hash

logger = logging.getLogger(__name__)

SQLITE_MAGIC = b"SQLi"  # full string is "SQLite format 3\0", first 4 bytes are SQLi


class Layering(enum.Enum):
    """Detected outer layering of a DPMF file."""

    RAW = "raw"
    ZSTD = "zstd"
    ENCRYPTED = "encrypted"


class DpmfFormatError(ValueError):
    """Raised when a file fails magic detection or format-version check."""


def detect_layering(path: Path) -> Layering:
    """Read the first 4 bytes of ``path`` and classify the wrapping."""
    with path.open("rb") as f:
        magic = f.read(4)
    if magic.startswith(SQLITE_MAGIC):
        return Layering.RAW
    if magic == ZSTD_MAGIC:
        return Layering.ZSTD
    if magic == DPME_MAGIC:
        return Layering.ENCRYPTED
    raise DpmfFormatError(f"unknown DPMF magic bytes: {magic!r}")


class DpmfHandle:
    """Opened DPMF — read-only SQLite + integrity helpers.

    Constructed by :func:`open_dpmf`. Holds the active connection plus
    the parsed ``_meta`` snapshot so call sites don't need to re-query.
    """

    def __init__(self, conn: sqlite3.Connection, meta: dict[str, str]) -> None:
        self._conn = conn
        self.meta = meta

    @property
    def connection(self) -> sqlite3.Connection:
        return self._conn

    def format_version(self) -> str:
        return self.meta.get("format_version", "")

    def source_system(self) -> str:
        return self.meta.get("source_system", "")

    def declared_integrity_hash(self) -> str:
        return self.meta.get("integrity_hash", "")

    def recompute_integrity_hash(self) -> str:
        return compute_logical_hash(self._conn)

    def entity_counts(self) -> dict[str, int]:
        rows = self._conn.execute(
            "SELECT entity_type, row_count FROM _entities ORDER BY entity_type"
        ).fetchall()
        return {row[0]: int(row[1]) for row in rows}

    def warnings_iter(self) -> Iterator[tuple[str | None, str | None, str, str, str, str | None]]:
        """Yield ``(entity_type, source_id, severity, code, message, raw_data)`` in insertion order."""
        cursor = self._conn.execute(
            "SELECT entity_type, source_id, severity, code, message, raw_data "
            "FROM _warnings ORDER BY id"
        )
        yield from cursor

    def files_iter(
        self,
    ) -> Iterator[tuple[str, str, str, str, int | None, str | None, str | None]]:
        """Yield ``(canonical_uuid, parent_entity_type, parent_canonical_uuid,
        relative_path, declared_size_bytes, sha256, mime_hint)``."""
        cursor = self._conn.execute(
            "SELECT canonical_uuid, parent_entity_type, parent_canonical_uuid, "
            "relative_path, declared_size_bytes, sha256, mime_hint "
            "FROM _files ORDER BY canonical_uuid"
        )
        yield from cursor

    def entity_iter(self, entity_type: str) -> Iterator[tuple[str, str, str, str, str, str]]:
        """Stream all rows of one entity table.

        Yields ``(canonical_uuid, source_id, source_system, payload,
        raw_source_data, extracted_at)``. ``payload`` / ``raw_source_data``
        remain as JSON strings — callers decode on demand to avoid
        materialising large tables in memory.
        """
        # Validate identifier before interpolation — defence in depth even
        # though entity_type came from _entities (writer side validated).
        if not _is_safe_identifier(entity_type):
            raise DpmfFormatError(f"unsafe entity_type identifier: {entity_type!r}")
        cursor = self._conn.execute(
            f"SELECT canonical_uuid, source_id, source_system, payload, raw_source_data, "
            f'extracted_at FROM "{entity_type}" ORDER BY canonical_uuid'
        )
        yield from cursor


@contextmanager
def open_dpmf(path: Path, *, passphrase: str | None = None) -> Iterator[DpmfHandle]:
    """Open a DPMF file regardless of layering.

    Yields a :class:`DpmfHandle`. Temporary plaintext (post-decrypt /
    post-decompress) is wiped on exit — including on exception paths.

    ``passphrase`` is required for encrypted files. Pass ``None`` for
    raw / zstd files; a ``DpmeError`` is raised if ``DPME`` magic is
    detected without a passphrase.
    """
    layering = detect_layering(path)

    with tempfile.TemporaryDirectory(prefix="dpmf-") as tmpdir_str:
        tmpdir = Path(tmpdir_str)

        if layering is Layering.RAW:
            sqlite_path = path
        elif layering is Layering.ZSTD:
            sqlite_path = tmpdir / "inner.sqlite"
            decompress_to(path, sqlite_path)
        elif layering is Layering.ENCRYPTED:
            if not passphrase:
                raise DpmeError("encrypted DPMF requires a passphrase")
            inner_path = tmpdir / "decrypted.bin"
            header = decrypt_to(path, inner_path, passphrase=passphrase)
            if header.inner_layout == "zstd":
                sqlite_path = tmpdir / "inner.sqlite"
                decompress_to(inner_path, sqlite_path)
            else:
                sqlite_path = inner_path
        else:
            raise DpmfFormatError(f"unhandled layering: {layering}")

        # Read-only connection: prevents accidental writes to the DPMF
        # (uri=True so we can pass ``mode=ro``).
        conn = sqlite3.connect(f"file:{sqlite_path}?mode=ro", uri=True)
        try:
            meta = _read_meta(conn)
            handle = DpmfHandle(conn, meta)
            yield handle
        finally:
            conn.close()


def _read_meta(conn: sqlite3.Connection) -> dict[str, str]:
    try:
        rows = conn.execute("SELECT key, value FROM _meta").fetchall()
    except sqlite3.DatabaseError as exc:
        raise DpmfFormatError(f"failed to read DPMF _meta table: {exc}") from exc
    return {row[0]: row[1] for row in rows}


def _is_safe_identifier(name: str) -> bool:
    if not name:
        return False
    return all(ch.islower() or ch.isdigit() or ch == "_" for ch in name) and name[0].isalpha()
