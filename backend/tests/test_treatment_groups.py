"""Tests for multi-tooth treatment group endpoints."""

from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.models import Clinic, ClinicMembership


@pytest.fixture
async def odontogram_setup(
    db_session: AsyncSession, auth_headers: dict[str, str], client: AsyncClient
) -> dict:
    """Set up a clinic with a patient for treatment group tests."""
    response = await client.get("/api/v1/auth/me", headers=auth_headers)
    user_id = response.json()["data"]["user"]["id"]

    clinic = Clinic(
        id=uuid4(),
        name="Test Dental Clinic",
        tax_id="B12345678",
        address={"street": "Test St", "city": "Madrid"},
        settings={"slot_duration_min": 15},
        cabinets=[{"name": "Gabinete 1", "color": "#3B82F6"}],
    )
    db_session.add(clinic)
    await db_session.flush()

    membership = ClinicMembership(
        id=uuid4(),
        user_id=user_id,
        clinic_id=clinic.id,
        role="dentist",
    )
    db_session.add(membership)
    await db_session.commit()

    patient_response = await client.post(
        "/api/v1/clinical/patients",
        headers=auth_headers,
        json={
            "first_name": "Ana",
            "last_name": "Martinez",
            "phone": "+34666987654",
        },
    )
    patient_id = patient_response.json()["data"]["id"]

    return {
        "clinic_id": str(clinic.id),
        "user_id": user_id,
        "patient_id": patient_id,
    }


async def _create_group(
    client: AsyncClient, auth_headers: dict[str, str], patient_id: str, payload: dict
):
    return await client.post(
        f"/api/v1/odontogram/patients/{patient_id}/treatment-groups",
        headers=auth_headers,
        json=payload,
    )


# ============================================================================
# Creation: bridge mode
# ============================================================================


@pytest.mark.asyncio
async def test_create_bridge_auto_assigns_roles(
    client: AsyncClient, auth_headers: dict[str, str], odontogram_setup: dict
) -> None:
    """Bridge mode: first and last teeth become abutments, middle teeth become pontics."""
    patient_id = odontogram_setup["patient_id"]

    response = await _create_group(
        client,
        auth_headers,
        patient_id,
        {"mode": "bridge", "tooth_numbers": [14, 15, 16], "status": "planned"},
    )
    assert response.status_code == 201, response.text

    data = response.json()["data"]
    assert len(data) == 3

    group_ids = {t["treatment_group_id"] for t in data}
    assert len(group_ids) == 1
    assert None not in group_ids

    by_tooth = {t["tooth_number"]: t["treatment_type"] for t in data}
    assert by_tooth == {
        14: "bridge_abutment",
        15: "pontic",
        16: "bridge_abutment",
    }

    # All should share same clinical category and planned status
    assert all(t["status"] == "planned" for t in data)
    assert all(t["treatment_category"] == "whole_tooth" for t in data)


@pytest.mark.asyncio
async def test_bridge_with_status_existing_sets_performed_fields(
    client: AsyncClient, auth_headers: dict[str, str], odontogram_setup: dict
) -> None:
    """status=existing marks treatments as performed (used for diagnostic registration)."""
    patient_id = odontogram_setup["patient_id"]

    response = await _create_group(
        client,
        auth_headers,
        patient_id,
        {"mode": "bridge", "tooth_numbers": [24, 25, 26], "status": "existing"},
    )
    assert response.status_code == 201
    data = response.json()["data"]
    for t in data:
        assert t["status"] == "existing"
        assert t["performed_at"] is not None
        assert t["performed_by"] is not None


@pytest.mark.asyncio
async def test_bridge_requires_at_least_three_teeth(
    client: AsyncClient, auth_headers: dict[str, str], odontogram_setup: dict
) -> None:
    response = await _create_group(
        client,
        auth_headers,
        odontogram_setup["patient_id"],
        {"mode": "bridge", "tooth_numbers": [14, 15]},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_bridge_rejects_treatment_type_param(
    client: AsyncClient, auth_headers: dict[str, str], odontogram_setup: dict
) -> None:
    """In bridge mode the backend assigns roles, so treatment_type must not be set."""
    response = await _create_group(
        client,
        auth_headers,
        odontogram_setup["patient_id"],
        {
            "mode": "bridge",
            "tooth_numbers": [14, 15, 16],
            "treatment_type": "crown",
        },
    )
    assert response.status_code == 422


# ============================================================================
# Creation: uniform mode
# ============================================================================


@pytest.mark.asyncio
async def test_uniform_mode_assigns_same_type_to_all(
    client: AsyncClient, auth_headers: dict[str, str], odontogram_setup: dict
) -> None:
    patient_id = odontogram_setup["patient_id"]

    response = await _create_group(
        client,
        auth_headers,
        patient_id,
        {
            "mode": "uniform",
            "tooth_numbers": [31, 32, 33, 41],
            "treatment_type": "splint",
            "status": "planned",
        },
    )
    assert response.status_code == 201
    data = response.json()["data"]
    assert len(data) == 4
    assert all(t["treatment_type"] == "splint" for t in data)
    group_ids = {t["treatment_group_id"] for t in data}
    assert len(group_ids) == 1


@pytest.mark.asyncio
async def test_uniform_requires_treatment_type(
    client: AsyncClient, auth_headers: dict[str, str], odontogram_setup: dict
) -> None:
    response = await _create_group(
        client,
        auth_headers,
        odontogram_setup["patient_id"],
        {"mode": "uniform", "tooth_numbers": [14, 15]},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_uniform_requires_at_least_two_teeth(
    client: AsyncClient, auth_headers: dict[str, str], odontogram_setup: dict
) -> None:
    response = await _create_group(
        client,
        auth_headers,
        odontogram_setup["patient_id"],
        {"mode": "uniform", "tooth_numbers": [14], "treatment_type": "crown"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_uniform_rejects_invalid_treatment_type(
    client: AsyncClient, auth_headers: dict[str, str], odontogram_setup: dict
) -> None:
    response = await _create_group(
        client,
        auth_headers,
        odontogram_setup["patient_id"],
        {
            "mode": "uniform",
            "tooth_numbers": [14, 15],
            "treatment_type": "not_a_real_treatment",
        },
    )
    assert response.status_code == 422


# ============================================================================
# Shared validators
# ============================================================================


@pytest.mark.asyncio
async def test_duplicate_teeth_rejected(
    client: AsyncClient, auth_headers: dict[str, str], odontogram_setup: dict
) -> None:
    response = await _create_group(
        client,
        auth_headers,
        odontogram_setup["patient_id"],
        {"mode": "bridge", "tooth_numbers": [14, 14, 16]},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_invalid_tooth_number_rejected(
    client: AsyncClient, auth_headers: dict[str, str], odontogram_setup: dict
) -> None:
    response = await _create_group(
        client,
        auth_headers,
        odontogram_setup["patient_id"],
        {"mode": "bridge", "tooth_numbers": [14, 15, 999]},
    )
    assert response.status_code == 422


# ============================================================================
# Perform group
# ============================================================================


@pytest.mark.asyncio
async def test_perform_group_marks_all_members_existing(
    client: AsyncClient, auth_headers: dict[str, str], odontogram_setup: dict
) -> None:
    patient_id = odontogram_setup["patient_id"]

    create = await _create_group(
        client,
        auth_headers,
        patient_id,
        {"mode": "bridge", "tooth_numbers": [14, 15, 16], "status": "planned"},
    )
    group_id = create.json()["data"][0]["treatment_group_id"]

    response = await client.patch(
        f"/api/v1/odontogram/treatment-groups/{group_id}/perform",
        headers=auth_headers,
        json={"notes": "Colocado hoy"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 3
    for t in data:
        assert t["status"] == "existing"
        assert t["performed_at"] is not None
        assert t["performed_by"] is not None


@pytest.mark.asyncio
async def test_perform_unknown_group_returns_404(
    client: AsyncClient, auth_headers: dict[str, str], odontogram_setup: dict
) -> None:
    response = await client.patch(
        f"/api/v1/odontogram/treatment-groups/{uuid4()}/perform",
        headers=auth_headers,
        json={},
    )
    assert response.status_code == 404


# ============================================================================
# Delete group
# ============================================================================


@pytest.mark.asyncio
async def test_delete_group_soft_deletes_all_members(
    client: AsyncClient, auth_headers: dict[str, str], odontogram_setup: dict
) -> None:
    patient_id = odontogram_setup["patient_id"]

    create = await _create_group(
        client,
        auth_headers,
        patient_id,
        {
            "mode": "uniform",
            "tooth_numbers": [12, 13],
            "treatment_type": "veneer",
            "status": "planned",
        },
    )
    group_id = create.json()["data"][0]["treatment_group_id"]

    response = await client.delete(
        f"/api/v1/odontogram/treatment-groups/{group_id}",
        headers=auth_headers,
    )
    assert response.status_code == 204

    # Listing by group_id should now return zero active members
    listing = await client.get(
        f"/api/v1/odontogram/patients/{patient_id}/treatments",
        headers=auth_headers,
        params={"treatment_group_id": group_id},
    )
    assert listing.status_code == 200
    assert listing.json()["total"] == 0


@pytest.mark.asyncio
async def test_delete_unknown_group_returns_404(
    client: AsyncClient, auth_headers: dict[str, str], odontogram_setup: dict
) -> None:
    response = await client.delete(
        f"/api/v1/odontogram/treatment-groups/{uuid4()}",
        headers=auth_headers,
    )
    assert response.status_code == 404


# ============================================================================
# List filter by treatment_group_id
# ============================================================================


@pytest.mark.asyncio
async def test_list_filter_by_group_id_isolates_members(
    client: AsyncClient, auth_headers: dict[str, str], odontogram_setup: dict
) -> None:
    patient_id = odontogram_setup["patient_id"]

    # Create a bridge group and an individual treatment alongside it
    create = await _create_group(
        client,
        auth_headers,
        patient_id,
        {"mode": "bridge", "tooth_numbers": [14, 15, 16], "status": "planned"},
    )
    group_id = create.json()["data"][0]["treatment_group_id"]

    # Standalone treatment in a different tooth
    await client.post(
        f"/api/v1/odontogram/patients/{patient_id}/teeth/21/treatments",
        headers=auth_headers,
        json={"treatment_type": "crown", "status": "planned"},
    )

    # Without filter: 4 treatments total
    all_listing = await client.get(
        f"/api/v1/odontogram/patients/{patient_id}/treatments",
        headers=auth_headers,
    )
    assert all_listing.json()["total"] == 4

    # With filter: only the 3 bridge members
    group_listing = await client.get(
        f"/api/v1/odontogram/patients/{patient_id}/treatments",
        headers=auth_headers,
        params={"treatment_group_id": group_id},
    )
    assert group_listing.status_code == 200
    payload = group_listing.json()
    assert payload["total"] == 3
    teeth = sorted(t["tooth_number"] for t in payload["data"])
    assert teeth == [14, 15, 16]
