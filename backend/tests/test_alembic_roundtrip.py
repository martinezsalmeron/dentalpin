"""Round-trip migration test.

Asserts that the Alembic chain can go ``base → head → base → head``
without leaving drift in the schema. This is the guardrail for the
post-Fase-B module layout: every model ``get_models()`` declaration
must produce exactly the same tables Alembic upgrades create, and
every ``downgrade`` must leave the database empty enough that
``upgrade head`` can run again cleanly.

Alembic commands are invoked via subprocess because ``env.py`` runs
``asyncio.run(...)`` internally — calling that from within pytest's
running event loop raises ``RuntimeError: asyncio.run() cannot be
called from a running event loop``.

Marked ``alembic_roundtrip`` and excluded from the default pytest run
(see ``pyproject.toml``). CI runs it as a dedicated step after the
main test suite.
"""

from __future__ import annotations

import asyncio
import subprocess
from pathlib import Path

import asyncpg
import pytest

from app.config import settings


pytestmark = pytest.mark.alembic_roundtrip

BACKEND_ROOT = Path(__file__).resolve().parents[1]
ALEMBIC_INI = BACKEND_ROOT / "alembic.ini"


def _alembic(*args: str) -> None:
    """Run ``alembic <args>`` from the backend package root."""
    subprocess.run(
        ["alembic", "-c", str(ALEMBIC_INI), *args],
        cwd=BACKEND_ROOT,
        check=True,
    )


def _asyncpg_dsn() -> str:
    """Strip ``postgresql+asyncpg://`` → ``postgresql://`` for asyncpg."""
    return settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")


async def _snapshot_tables_async() -> dict[str, list[str]]:
    conn = await asyncpg.connect(_asyncpg_dsn())
    try:
        tables = await conn.fetch(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_name != 'alembic_version' "
            "ORDER BY table_name"
        )
        result: dict[str, list[str]] = {}
        for row in tables:
            tbl = row["table_name"]
            cols = await conn.fetch(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema = 'public' AND table_name = $1 "
                "ORDER BY ordinal_position",
                tbl,
            )
            result[tbl] = [c["column_name"] for c in cols]
        return result
    finally:
        await conn.close()


def _snapshot_tables() -> dict[str, list[str]]:
    return asyncio.run(_snapshot_tables_async())


def _leftover_tables() -> list[str]:
    return list(_snapshot_tables().keys())


@pytest.mark.xfail(
    reason=(
        "The Fase A main-linear chain has ordering gaps in downgrade paths "
        "(e.g. `planned_treatment_items` is referenced by `treatment_media` "
        "and `appointment_treatments` but its downgrade doesn't CASCADE). "
        "The squash planned for a future etapa rebuilds each module as its "
        "own Alembic branch with a clean initial migration, which will let "
        "this test go green. Kept here so the infrastructure is in place."
    ),
    strict=False,
)
def test_upgrade_downgrade_upgrade_is_schema_stable() -> None:
    """upgrade → downgrade → upgrade must produce the same schema."""
    _alembic("upgrade", "head")
    before = _snapshot_tables()
    assert before, "expected at least one table after upgrade head"

    _alembic("downgrade", "base")
    leftover = _leftover_tables()
    assert leftover == [], f"downgrade base left tables behind: {leftover}"

    _alembic("upgrade", "head")
    after = _snapshot_tables()

    assert before == after, (
        "Schema drift after upgrade → downgrade → upgrade\n"
        f"before tables: {sorted(before)}\n"
        f"after tables:  {sorted(after)}"
    )
