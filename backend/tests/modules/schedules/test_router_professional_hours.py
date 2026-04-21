"""API tests for professional-hours endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.core.auth.models import User


@pytest.mark.asyncio
async def test_get_professional_hours(
    client: AsyncClient, auth_headers: dict, test_clinic, dentist_user: User
):
    res = await client.get(
        f"/api/v1/schedules/professionals/{dentist_user.id}/hours",
        headers=auth_headers,
    )
    assert res.status_code == 200
    assert res.json()["data"]["user_id"] == str(dentist_user.id)


@pytest.mark.asyncio
async def test_get_professional_hours_rejects_non_professional(
    client: AsyncClient, auth_headers: dict, test_clinic, receptionist_user: User
):
    res = await client.get(
        f"/api/v1/schedules/professionals/{receptionist_user.id}/hours",
        headers=auth_headers,
    )
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_update_professional_hours(
    client: AsyncClient, auth_headers: dict, test_clinic, dentist_user: User
):
    payload = {
        "days": [
            {
                "weekday": 1,
                "shifts": [{"start_time": "10:00:00", "end_time": "12:00:00"}],
            }
        ]
    }
    res = await client.put(
        f"/api/v1/schedules/professionals/{dentist_user.id}/hours",
        json=payload,
        headers=auth_headers,
    )
    assert res.status_code == 200
    tuesday = next(d for d in res.json()["data"]["days"] if d["weekday"] == 1)
    assert len(tuesday["shifts"]) == 1


@pytest.mark.asyncio
async def test_professional_override_lifecycle(
    client: AsyncClient, auth_headers: dict, test_clinic, dentist_user: User
):
    create_res = await client.post(
        f"/api/v1/schedules/professionals/{dentist_user.id}/overrides",
        json={
            "start_date": "2026-08-01",
            "end_date": "2026-08-15",
            "kind": "unavailable",
            "reason": "Vacaciones verano",
            "shifts": [],
        },
        headers=auth_headers,
    )
    assert create_res.status_code == 201
    override_id = create_res.json()["data"]["id"]

    del_res = await client.delete(
        f"/api/v1/schedules/professionals/{dentist_user.id}/overrides/{override_id}",
        headers=auth_headers,
    )
    assert del_res.status_code == 204
