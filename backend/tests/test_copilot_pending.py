"""Copilot "Pendientes" feed (IA redesign Fase 2, ADR 0015).

Aggregates open work (overdue recalls, budgets awaiting response) via the
tool registry with the caller's role permissions — read-only, deep-links
to the owning module. Here we just assert the endpoint runs and shapes
results; the underlying tools have their own tests.
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.agents.models import AgentSession
from app.database import engine


@pytest_asyncio.fixture(autouse=True)
async def _dispose_global_pool():
    await engine.dispose()
    yield
    await engine.dispose()


@pytest.mark.asyncio
async def test_pending_runs_and_returns_list(
    client: AsyncClient, auth_headers: dict, test_clinic
) -> None:
    res = await client.get("/api/v1/copilot/pending", headers=auth_headers)
    assert res.status_code == 200, res.text
    data = res.json()["data"]
    assert isinstance(data, list)
    # Every item carries a kind + a deep-link.
    for item in data:
        assert item["kind"] in ("recall", "budget")
        assert item["link"]


@pytest.mark.asyncio
async def test_pending_reuses_single_session(
    db_session: AsyncSession, client: AsyncClient, auth_headers: dict, test_clinic
) -> None:
    """Repeated drawer opens must not insert a session row each time."""
    await client.get("/api/v1/copilot/pending", headers=auth_headers)
    await client.get("/api/v1/copilot/pending", headers=auth_headers)
    await client.get("/api/v1/copilot/pending", headers=auth_headers)

    sessions = list(
        await db_session.scalars(
            select(AgentSession).where(AgentSession.clinic_id == test_clinic.id)
        )
    )
    pending = [
        s for s in sessions if (s.session_metadata or {}).get("surface") == "copilot_pending"
    ]
    assert len(pending) == 1
