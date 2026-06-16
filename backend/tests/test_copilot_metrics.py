"""Copilot observability metrics (admin dashboard, read-only).

The metrics endpoint aggregates the existing ``agent_audit_logs``
(filtered to copilot agents) plus the budget counters — no new table.
Driving a morning digest is the cheapest way to generate copilot tool
calls in a test.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import engine
from app.modules.copilot.service import CopilotSettingsService
from app.modules.copilot.tasks import send_morning_digests


@pytest_asyncio.fixture(autouse=True)
async def _dispose_global_pool():
    await engine.dispose()
    yield
    await engine.dispose()


async def _set_clinic_tz(db: AsyncSession, clinic_id, tz: str) -> None:
    await db.execute(
        text("UPDATE clinics SET timezone = :tz WHERE id = :id"), {"tz": tz, "id": clinic_id}
    )
    await db.commit()


@pytest.mark.asyncio
async def test_metrics_counts_copilot_tool_calls(
    db_session: AsyncSession, client: AsyncClient, auth_headers: dict, test_clinic
) -> None:
    me = await client.get("/api/v1/auth/me", headers=auth_headers)
    await _set_clinic_tz(db_session, test_clinic.id, "UTC")
    await CopilotSettingsService.update(
        db_session,
        test_clinic.id,
        {"digest_enabled": True, "digest_hour": 8},
        acting_user_id=UUID(me.json()["data"]["user"]["id"]),
    )
    await db_session.commit()

    # Generates copilot audit rows (get_day_overview, list_due_recalls, …).
    await send_morning_digests(datetime(2032, 1, 5, 8, 0, tzinfo=UTC))

    res = await client.get("/api/v1/copilot/metrics?days=30", headers=auth_headers)
    assert res.status_code == 200, res.text
    data = res.json()["data"]
    assert data["window_days"] == 30
    assert data["total_tool_calls"] >= 3
    names = {t["tool_name"] for t in data["top_tools"]}
    assert "agenda.get_day_overview" in names


@pytest.mark.asyncio
async def test_metrics_empty_when_no_usage(
    client: AsyncClient, auth_headers: dict, test_clinic
) -> None:
    res = await client.get("/api/v1/copilot/metrics", headers=auth_headers)
    assert res.status_code == 200, res.text
    data = res.json()["data"]
    assert data["total_tool_calls"] == 0
    assert data["error_rate"] == 0.0
    assert data["top_tools"] == []
