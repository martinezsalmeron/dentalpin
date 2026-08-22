"""Alembic branch-isolation round-trip for india_gst (issue: new module).

Mirrors ``backend/tests/test_uninstall_roundtrip.py``: install → uninstall
→ reinstall drops/restores only india_gst's own tables, leaving every
other module's schema untouched. Marked ``alembic_roundtrip`` and
excluded from the default pytest run.
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

INDIA_GST_TABLES = {
    "india_gst_settings",
    "india_gst_catalog_items",
    "india_gst_invoice_items",
    "india_gst_document_sequences",
    "india_gst_einvoice_submissions",
}


def _alembic(*args: str) -> None:
    subprocess.run(["alembic", "-c", str(ALEMBIC_INI), *args], cwd=BACKEND_ROOT, check=True)


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


def test_india_gst_uninstall_roundtrip_is_branch_scoped() -> None:
    _alembic("upgrade", "heads")
    before = _list_tables()
    assert INDIA_GST_TABLES.issubset(before), (
        f"expected india_gst tables at heads; missing: {INDIA_GST_TABLES - before}"
    )
    baseline_non_india_gst = before - INDIA_GST_TABLES

    _alembic("downgrade", "india_gst@-1")

    after_down = _list_tables()
    assert INDIA_GST_TABLES.isdisjoint(after_down), (
        f"india_gst tables survived downgrade: {INDIA_GST_TABLES & after_down}"
    )
    assert baseline_non_india_gst <= after_down, (
        "downgrade leaked into other modules; missing tables: "
        f"{baseline_non_india_gst - after_down}"
    )

    _alembic("upgrade", "india_gst@head")
    after_up = _list_tables()
    assert before <= after_up, (
        f"reinstall did not restore every table; missing: {before - after_up}"
    )
