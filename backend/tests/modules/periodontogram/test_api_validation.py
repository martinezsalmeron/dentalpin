"""Pydantic + service validation guards for the periodontogram API."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.modules.patients.models import Patient

pytestmark = pytest.mark.asyncio


async def _draft_id(client: AsyncClient, headers: dict[str, str], patient_id: str) -> str:
    response = await client.post(
        f"/api/v1/periodontogram/patients/{patient_id}/draft",
        headers=headers,
    )
    return response.json()["data"]["id"]


async def test_invalid_probing_depth_returns_422(
    client: AsyncClient,
    auth_headers: dict[str, str],
    test_patient: Patient,
) -> None:
    snap_id = await _draft_id(client, auth_headers, str(test_patient.id))
    response = await client.patch(
        f"/api/v1/periodontogram/snapshots/{snap_id}/teeth/11/sites/MV",
        headers=auth_headers,
        json={"probing_depth_mm": 99},  # > 15
    )
    assert response.status_code == 422


async def test_unknown_site_code_returns_422(
    client: AsyncClient,
    auth_headers: dict[str, str],
    test_patient: Patient,
) -> None:
    snap_id = await _draft_id(client, auth_headers, str(test_patient.id))
    response = await client.patch(
        f"/api/v1/periodontogram/snapshots/{snap_id}/teeth/11/sites/XX",
        headers=auth_headers,
        json={"probing_depth_mm": 3},
    )
    # Service raises HTTPException(422) for unknown codes before touching DB.
    assert response.status_code == 422


async def test_deciduous_tooth_number_returns_422(
    client: AsyncClient,
    auth_headers: dict[str, str],
    test_patient: Patient,
) -> None:
    snap_id = await _draft_id(client, auth_headers, str(test_patient.id))
    response = await client.patch(
        f"/api/v1/periodontogram/snapshots/{snap_id}/teeth/51",  # deciduous
        headers=auth_headers,
        json={"mobility": 1},
    )
    # FDI 51 fails the path-level validator (tooth_number is int, but the
    # tooth is not part of the seeded draft).
    assert response.status_code in (404, 422)


async def test_mobility_out_of_range_returns_422(
    client: AsyncClient,
    auth_headers: dict[str, str],
    test_patient: Patient,
) -> None:
    snap_id = await _draft_id(client, auth_headers, str(test_patient.id))
    response = await client.patch(
        f"/api/v1/periodontogram/snapshots/{snap_id}/teeth/11",
        headers=auth_headers,
        json={"mobility": 7},  # > 3
    )
    assert response.status_code == 422
