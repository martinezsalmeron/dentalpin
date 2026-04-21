"""API test for the /availability endpoint."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_availability_default_24_7_shape(
    client: AsyncClient, auth_headers: dict, test_clinic
):
    # conftest does not seed the 24/7 row (Base.metadata.create_all,
    # not Alembic). So we first call GET clinic-hours which triggers
    # get_or_create_weekly → gives us an empty weekly. With no shifts,
    # availability returns full-day clinic_closed.
    await client.get("/api/v1/schedules/clinic-hours", headers=auth_headers)
    res = await client.get(
        "/api/v1/schedules/availability?start=2026-04-22&end=2026-04-22",
        headers=auth_headers,
    )
    assert res.status_code == 200
    data = res.json()["data"]
    assert "timezone" in data
    assert isinstance(data["ranges"], list)


@pytest.mark.asyncio
async def test_availability_end_before_start_rejected(
    client: AsyncClient, auth_headers: dict, test_clinic
):
    res = await client.get(
        "/api/v1/schedules/availability?start=2026-04-22&end=2026-04-20",
        headers=auth_headers,
    )
    assert res.status_code == 400
