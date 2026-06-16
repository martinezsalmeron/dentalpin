"""Copilot proactive nudges (ADR 0014 §Deferred).

The ``appointment.cancelled`` handler creates a "fill the freed slot"
nudge; the drawer lists active ones and can dismiss them. Deduped per
clinic, gated per viewer permission, same-day TTL.
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import engine
from app.modules.copilot.events import on_appointment_cancelled
from app.modules.copilot.service import NudgeService


@pytest_asyncio.fixture(autouse=True)
async def _dispose_global_pool():
    await engine.dispose()
    yield
    await engine.dispose()


def _cancel_payload(clinic_id, appt="11111111-1111-1111-1111-111111111111") -> dict:
    return {
        "appointment_id": appt,
        "clinic_id": str(clinic_id),
        "patient_id": "22222222-2222-2222-2222-222222222222",
        "professional_id": "33333333-3333-3333-3333-333333333333",
        "start_time": "2032-01-05T10:00:00+00:00",
    }


@pytest.mark.asyncio
async def test_cancellation_creates_listable_nudge(
    db_session: AsyncSession, client: AsyncClient, auth_headers: dict, test_clinic
) -> None:
    await on_appointment_cancelled(_cancel_payload(test_clinic.id))

    res = await client.get("/api/v1/copilot/nudges", headers=auth_headers)
    assert res.status_code == 200, res.text
    data = res.json()["data"]
    assert len(data) == 1
    assert data[0]["kind"] == "appointment_cancelled"
    assert data[0]["payload"]["appointment_id"] == "11111111-1111-1111-1111-111111111111"


@pytest.mark.asyncio
async def test_cancellation_nudge_is_deduped(
    db_session: AsyncSession, client: AsyncClient, auth_headers: dict, test_clinic
) -> None:
    payload = _cancel_payload(test_clinic.id)
    await on_appointment_cancelled(payload)
    await on_appointment_cancelled(payload)  # replay

    res = await client.get("/api/v1/copilot/nudges", headers=auth_headers)
    assert len(res.json()["data"]) == 1


@pytest.mark.asyncio
async def test_dismiss_removes_nudge_from_list(
    db_session: AsyncSession, client: AsyncClient, auth_headers: dict, test_clinic
) -> None:
    await on_appointment_cancelled(_cancel_payload(test_clinic.id))
    res = await client.get("/api/v1/copilot/nudges", headers=auth_headers)
    nudge_id = res.json()["data"][0]["id"]

    dismissed = await client.post(
        f"/api/v1/copilot/nudges/{nudge_id}/dismiss", headers=auth_headers
    )
    assert dismissed.status_code == 204

    after = await client.get("/api/v1/copilot/nudges", headers=auth_headers)
    assert after.json()["data"] == []


@pytest.mark.asyncio
async def test_nudge_gated_by_required_permission(db_session: AsyncSession, test_clinic) -> None:
    """A permission-gated nudge is hidden from a role that lacks it."""
    from datetime import UTC, datetime, timedelta

    await NudgeService.create(
        db_session,
        clinic_id=test_clinic.id,
        kind="appointment_cancelled",
        dedupe_key="appointment_cancelled:x",
        payload={},
        # A permission no standard role grants.
        required_permission="zzz.totally.fake",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )
    await db_session.commit()

    # admin role ("*") sees it; a non-admin role without the perm does not.
    assert len(await NudgeService.list_active(db_session, test_clinic.id, role="admin")) == 1
    assert await NudgeService.list_active(db_session, test_clinic.id, role="hygienist") == []
