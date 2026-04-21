"""Multi-tenant isolation: clinic A cannot see clinic B's overrides."""

from __future__ import annotations

from datetime import date
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.models import Clinic
from app.modules.schedules.models import ClinicOverride


@pytest.mark.asyncio
async def test_override_from_other_clinic_not_listed(
    client: AsyncClient,
    auth_headers: dict,
    db_session: AsyncSession,
    test_clinic: Clinic,
):
    # Foreign clinic with its own override.
    other = Clinic(
        id=uuid4(),
        name="Other Clinic",
        tax_id="B99999999",
        address={},
        settings={},
    )
    db_session.add(other)
    await db_session.flush()
    db_session.add(
        ClinicOverride(
            clinic_id=other.id,
            start_date=date(2026, 12, 25),
            end_date=date(2026, 12, 26),
            kind="closed",
            reason="Other clinic holiday",
        )
    )
    await db_session.commit()

    res = await client.get("/api/v1/schedules/clinic-overrides", headers=auth_headers)
    assert res.status_code == 200
    assert all(o.get("reason") != "Other clinic holiday" for o in res.json()["data"])
