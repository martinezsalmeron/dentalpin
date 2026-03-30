"""Tests for clinical module endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.models import Clinic, ClinicMembership


@pytest.fixture
async def clinic_setup(
    db_session: AsyncSession, auth_headers: dict[str, str], client: AsyncClient
) -> dict:
    """Set up a clinic with the test user as admin."""
    from uuid import uuid4

    # Get user from /me endpoint
    response = await client.get("/api/v1/auth/me", headers=auth_headers)
    user_id = response.json()["user"]["id"]

    # Create clinic
    clinic = Clinic(
        id=uuid4(),
        name="Test Clinic",
        tax_id="B12345678",
        address={"street": "Test St", "city": "Madrid"},
        settings={"slot_duration_min": 15},
        cabinets=[{"name": "Gabinete 1", "color": "#3B82F6"}],
    )
    db_session.add(clinic)
    await db_session.flush()

    # Create membership
    membership = ClinicMembership(
        id=uuid4(),
        user_id=user_id,
        clinic_id=clinic.id,
        role="admin",
    )
    db_session.add(membership)
    await db_session.commit()

    return {"clinic_id": str(clinic.id), "user_id": user_id}


@pytest.mark.asyncio
async def test_list_clinics(
    client: AsyncClient, auth_headers: dict[str, str], clinic_setup: dict
) -> None:
    """Test listing clinics."""
    response = await client.get("/api/v1/clinical/clinics", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Test Clinic"


@pytest.mark.asyncio
async def test_create_patient(
    client: AsyncClient, auth_headers: dict[str, str], clinic_setup: dict
) -> None:
    """Test creating a patient."""
    response = await client.post(
        "/api/v1/clinical/patients",
        headers=auth_headers,
        json={
            "first_name": "Juan",
            "last_name": "Garcia",
            "phone": "+34666123456",
            "email": "juan@example.com",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["first_name"] == "Juan"
    assert data["last_name"] == "Garcia"
    assert data["status"] == "active"
    assert data["clinic_id"] == clinic_setup["clinic_id"]


@pytest.mark.asyncio
async def test_list_patients(
    client: AsyncClient, auth_headers: dict[str, str], clinic_setup: dict
) -> None:
    """Test listing patients with pagination."""
    # Create a patient first
    await client.post(
        "/api/v1/clinical/patients",
        headers=auth_headers,
        json={"first_name": "Maria", "last_name": "Lopez"},
    )

    response = await client.get("/api/v1/clinical/patients", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["page"] == 1
    assert len(data["data"]) == 1


@pytest.mark.asyncio
async def test_search_patients(
    client: AsyncClient, auth_headers: dict[str, str], clinic_setup: dict
) -> None:
    """Test searching patients by name."""
    # Create patients
    await client.post(
        "/api/v1/clinical/patients",
        headers=auth_headers,
        json={"first_name": "Juan", "last_name": "Garcia"},
    )
    await client.post(
        "/api/v1/clinical/patients",
        headers=auth_headers,
        json={"first_name": "Maria", "last_name": "Lopez"},
    )

    # Search for Juan
    response = await client.get(
        "/api/v1/clinical/patients", headers=auth_headers, params={"search": "Juan"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["data"][0]["first_name"] == "Juan"


@pytest.mark.asyncio
async def test_get_patient_not_found(
    client: AsyncClient, auth_headers: dict[str, str], clinic_setup: dict
) -> None:
    """Test getting a non-existent patient."""
    response = await client.get(
        "/api/v1/clinical/patients/00000000-0000-0000-0000-000000000000",
        headers=auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_appointment(
    client: AsyncClient, auth_headers: dict[str, str], clinic_setup: dict
) -> None:
    """Test creating an appointment."""
    # Create patient first
    patient_response = await client.post(
        "/api/v1/clinical/patients",
        headers=auth_headers,
        json={"first_name": "Test", "last_name": "Patient"},
    )
    patient_id = patient_response.json()["id"]

    # Create appointment
    response = await client.post(
        "/api/v1/clinical/appointments",
        headers=auth_headers,
        json={
            "patient_id": patient_id,
            "professional_id": clinic_setup["user_id"],
            "cabinet": "Gabinete 1",
            "start_time": "2026-04-01T10:00:00Z",
            "end_time": "2026-04-01T10:30:00Z",
            "treatment_type": "Revision",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "scheduled"
    assert data["patient"]["first_name"] == "Test"


@pytest.mark.asyncio
async def test_appointment_time_conflict(
    client: AsyncClient, auth_headers: dict[str, str], clinic_setup: dict
) -> None:
    """Test that overlapping appointments are rejected."""
    # Create patient
    patient_response = await client.post(
        "/api/v1/clinical/patients",
        headers=auth_headers,
        json={"first_name": "Test", "last_name": "Patient"},
    )
    patient_id = patient_response.json()["id"]

    appointment_data = {
        "patient_id": patient_id,
        "professional_id": clinic_setup["user_id"],
        "cabinet": "Gabinete 1",
        "start_time": "2026-04-02T10:00:00Z",
        "end_time": "2026-04-02T10:30:00Z",
    }

    # First appointment should succeed
    response = await client.post(
        "/api/v1/clinical/appointments",
        headers=auth_headers,
        json=appointment_data,
    )
    assert response.status_code == 201

    # Second appointment at same time should fail
    response = await client.post(
        "/api/v1/clinical/appointments",
        headers=auth_headers,
        json=appointment_data,
    )
    assert response.status_code == 409
    assert "occupied" in response.json()["detail"]
