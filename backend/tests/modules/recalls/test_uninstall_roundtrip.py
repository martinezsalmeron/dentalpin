"""Recalls round-trip uninstall test (issue #62).

Mirrors ``backend/tests/test_uninstall_roundtrip.py``'s schedules
scenario: install → uninstall → reinstall must drop only the recalls
tables and leave every other module untouched.

Marked ``alembic_roundtrip`` and excluded from the default pytest run
(same policy as the other migration round-trip suites).
"""

from __future__ import annotations

import asyncio
import subprocess
from pathlib import Path

import asyncpg
import pytest

from app.config import settings

pytestmark = pytest.mark.alembic_roundtrip

BACKEND_ROOT = Path(__file__).resolve().parents[3]
ALEMBIC_INI = BACKEND_ROOT / "alembic.ini"

RECALLS_TABLES = {
    "recalls",
    "recall_contact_attempts",
    "recall_settings",
}


def _alembic(*args: str) -> None:
    subprocess.run(
        ["alembic", "-c", str(ALEMBIC_INI), *args],
        cwd=BACKEND_ROOT,
        check=True,
    )


def _dsn() -> str:
    return settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")


async def _list_tables_async() -> set[str]:
    conn = await asyncpg.connect(_dsn())
    try:
        rows = await conn.fetch(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_name != 'alembic_version'"
        )
        return {row["table_name"] for row in rows}
    finally:
        await conn.close()


def _list_tables() -> set[str]:
    return asyncio.run(_list_tables_async())


def test_recalls_uninstall_roundtrip_is_branch_scoped() -> None:
    """install → uninstall → reinstall drops only recalls tables."""
    _alembic("upgrade", "heads")
    before = _list_tables()
    assert RECALLS_TABLES.issubset(before), (
        f"expected recalls tables at heads; missing: {RECALLS_TABLES - before}"
    )
    baseline_other = before - RECALLS_TABLES

    _alembic("downgrade", "recalls@-1")

    after_down = _list_tables()
    assert RECALLS_TABLES.isdisjoint(after_down), (
        f"recalls tables survived downgrade: {RECALLS_TABLES & after_down}"
    )
    assert baseline_other <= after_down, (
        "downgrade leaked into other modules; missing: "
        f"{baseline_other - after_down}"
    )

    _alembic("upgrade", "recalls@head")
    after_up = _list_tables()
    assert before <= after_up, (
        f"reinstall did not restore every table; missing: {before - after_up}"
    )
