"""Tests for the treatment_plan module."""

from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.models import Clinic, ClinicMembership
from app.modules.catalog.models import TreatmentCatalogItem, TreatmentCategory, VatType
from app.modules.clinical.models import Patient
from app.modules.odontogram.models import ToothRecord, ToothTreatment


@pytest.fixture
async def treatment_plan_setup(
    db_session: AsyncSession, auth_headers: dict[str, str], client: AsyncClient
) -> dict:
    """Set up a clinic with patient and catalog for treatment plan tests."""
    from datetime import UTC, datetime

    # Get user from /me endpoint
    response = await client.get("/api/v1/auth/me", headers=auth_headers)
    user_id = response.json()["data"]["user"]["id"]

    # Create clinic
    clinic = Clinic(
        id=uuid4(),
        name="Treatment Plan Test Clinic",
        tax_id="B77777777",
        address={"street": "Plan St", "city": "Madrid"},
        settings={"slot_duration_min": 15},
        cabinets=[{"name": "Gabinete 1", "color": "#3B82F6"}],
    )
    db_session.add(clinic)
    await db_session.flush()

    # Create admin membership
    membership = ClinicMembership(
        id=uuid4(),
        user_id=user_id,
        clinic_id=clinic.id,
        role="admin",
    )
    db_session.add(membership)

    # Create VAT type
    vat_type = VatType(
        id=uuid4(),
        clinic_id=clinic.id,
        names={"es": "Exento", "en": "Exempt"},
        rate=0.0,
        is_default=True,
        is_system=True,
    )
    db_session.add(vat_type)
    await db_session.flush()

    # Create category
    category = TreatmentCategory(
        id=uuid4(),
        clinic_id=clinic.id,
        key="test_category",
        names={"es": "Test", "en": "Test"},
        display_order=1,
        is_active=True,
        is_system=False,
    )
    db_session.add(category)
    await db_session.flush()

    # Create catalog item
    catalog_item = TreatmentCatalogItem(
        id=uuid4(),
        clinic_id=clinic.id,
        category_id=category.id,
        internal_code="CROWN-001",
        names={"es": "Corona", "en": "Crown"},
        descriptions={"es": "Corona dental", "en": "Dental crown"},
        default_price=500.00,
        currency="EUR",
        vat_type_id=vat_type.id,
        treatment_scope="whole_tooth",
        is_diagnostic=False,
        is_active=True,
        is_system=False,
    )
    db_session.add(catalog_item)

    # Create patient
    patient = Patient(
        id=uuid4(),
        clinic_id=clinic.id,
        first_name="Test",
        last_name="Patient",
        email="patient@test.com",
        phone="+34600000000",
        status="active",
    )
    db_session.add(patient)
    await db_session.flush()

    # Create tooth record
    tooth_record = ToothRecord(
        id=uuid4(),
        clinic_id=clinic.id,
        patient_id=patient.id,
        tooth_number=16,
        tooth_type="permanent",
        general_condition="healthy",
        surfaces={},
    )
    db_session.add(tooth_record)
    await db_session.flush()

    # Create tooth treatment
    tooth_treatment = ToothTreatment(
        id=uuid4(),
        clinic_id=clinic.id,
        patient_id=patient.id,
        tooth_record_id=tooth_record.id,
        tooth_number=16,
        treatment_type="crown",
        treatment_category="whole_tooth",
        status="planned",
        recorded_at=datetime.now(UTC),
        catalog_item_id=catalog_item.id,
    )
    db_session.add(tooth_treatment)

    await db_session.commit()

    return {
        "clinic_id": str(clinic.id),
        "user_id": user_id,
        "patient_id": str(patient.id),
        "catalog_item_id": str(catalog_item.id),
        "tooth_treatment_id": str(tooth_treatment.id),
        "vat_type_id": str(vat_type.id),
    }


# ============================================================================
# Treatment Plan CRUD Tests
# ============================================================================


@pytest.mark.asyncio
async def test_list_treatment_plans(
    client: AsyncClient, auth_headers: dict, treatment_plan_setup: dict
):
    """Test listing treatment plans."""
    response = await client.get(
        "/api/v1/treatment_plan/treatment-plans",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert isinstance(data["data"], list)
    assert "total" in data
    assert "page" in data


@pytest.mark.asyncio
async def test_create_treatment_plan(
    client: AsyncClient, auth_headers: dict, treatment_plan_setup: dict
):
    """Test creating a treatment plan."""
    response = await client.post(
        "/api/v1/treatment_plan/treatment-plans",
        json={
            "patient_id": treatment_plan_setup["patient_id"],
            "title": "Treatment Plan for Patient",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["patient_id"] == treatment_plan_setup["patient_id"]
    assert data["status"] == "draft"
    assert data["title"] == "Treatment Plan for Patient"
    assert "plan_number" in data
    assert data["plan_number"].startswith("PLAN-")


@pytest.mark.asyncio
async def test_get_treatment_plan(
    client: AsyncClient, auth_headers: dict, treatment_plan_setup: dict
):
    """Test getting a treatment plan by ID."""
    # First create a plan
    create_response = await client.post(
        "/api/v1/treatment_plan/treatment-plans",
        json={
            "patient_id": treatment_plan_setup["patient_id"],
            "title": "Test Plan",
        },
        headers=auth_headers,
    )
    plan_id = create_response.json()["data"]["id"]

    # Get the plan
    response = await client.get(
        f"/api/v1/treatment_plan/treatment-plans/{plan_id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["id"] == plan_id
    assert data["title"] == "Test Plan"
    assert "items" in data
    assert isinstance(data["items"], list)


@pytest.mark.asyncio
async def test_update_treatment_plan(
    client: AsyncClient, auth_headers: dict, treatment_plan_setup: dict
):
    """Test updating a treatment plan."""
    # Create plan
    create_response = await client.post(
        "/api/v1/treatment_plan/treatment-plans",
        json={
            "patient_id": treatment_plan_setup["patient_id"],
            "title": "Original Title",
        },
        headers=auth_headers,
    )
    plan_id = create_response.json()["data"]["id"]

    # Update plan
    response = await client.put(
        f"/api/v1/treatment_plan/treatment-plans/{plan_id}",
        json={
            "title": "Updated Title",
            "diagnosis_notes": "Patient has caries on #16",
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["title"] == "Updated Title"


@pytest.mark.asyncio
async def test_update_plan_status(
    client: AsyncClient, auth_headers: dict, treatment_plan_setup: dict
):
    """Test updating treatment plan status."""
    # Create plan
    create_response = await client.post(
        "/api/v1/treatment_plan/treatment-plans",
        json={
            "patient_id": treatment_plan_setup["patient_id"],
        },
        headers=auth_headers,
    )
    plan_id = create_response.json()["data"]["id"]

    # Add item to plan (required to activate)
    await client.post(
        f"/api/v1/treatment_plan/treatment-plans/{plan_id}/items",
        json={
            "catalog_item_id": treatment_plan_setup["catalog_item_id"],
        },
        headers=auth_headers,
    )

    # Update status from draft to active
    response = await client.patch(
        f"/api/v1/treatment_plan/treatment-plans/{plan_id}/status",
        json={"status": "active"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "active"


@pytest.mark.asyncio
async def test_invalid_status_transition(
    client: AsyncClient, auth_headers: dict, treatment_plan_setup: dict
):
    """Test that invalid status transitions are rejected."""
    # Create plan
    create_response = await client.post(
        "/api/v1/treatment_plan/treatment-plans",
        json={
            "patient_id": treatment_plan_setup["patient_id"],
        },
        headers=auth_headers,
    )
    plan_id = create_response.json()["data"]["id"]

    # Try to go from draft directly to completed (should fail)
    response = await client.patch(
        f"/api/v1/treatment_plan/treatment-plans/{plan_id}/status",
        json={"status": "completed"},
        headers=auth_headers,
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_delete_treatment_plan(
    client: AsyncClient, auth_headers: dict, treatment_plan_setup: dict
):
    """Test soft deleting a treatment plan."""
    # Create plan
    create_response = await client.post(
        "/api/v1/treatment_plan/treatment-plans",
        json={
            "patient_id": treatment_plan_setup["patient_id"],
        },
        headers=auth_headers,
    )
    plan_id = create_response.json()["data"]["id"]

    # Delete plan
    response = await client.delete(
        f"/api/v1/treatment_plan/treatment-plans/{plan_id}",
        headers=auth_headers,
    )
    assert response.status_code == 204

    # Verify it's not returned in list
    list_response = await client.get(
        "/api/v1/treatment_plan/treatment-plans",
        headers=auth_headers,
    )
    plan_ids = [p["id"] for p in list_response.json()["data"]]
    assert plan_id not in plan_ids


# ============================================================================
# Plan Items Tests
# ============================================================================


@pytest.mark.asyncio
async def test_add_tooth_treatment_to_plan(
    client: AsyncClient, auth_headers: dict, treatment_plan_setup: dict
):
    """Test adding a tooth treatment to a plan."""
    # Create plan
    create_response = await client.post(
        "/api/v1/treatment_plan/treatment-plans",
        json={
            "patient_id": treatment_plan_setup["patient_id"],
        },
        headers=auth_headers,
    )
    plan_id = create_response.json()["data"]["id"]

    # Add item
    response = await client.post(
        f"/api/v1/treatment_plan/treatment-plans/{plan_id}/items",
        json={
            "tooth_treatment_id": treatment_plan_setup["tooth_treatment_id"],
            "catalog_item_id": treatment_plan_setup["catalog_item_id"],
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["tooth_treatment_id"] == treatment_plan_setup["tooth_treatment_id"]
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_add_global_treatment_to_plan(
    client: AsyncClient, auth_headers: dict, treatment_plan_setup: dict
):
    """Test adding a global treatment (without tooth) to a plan."""
    # Create plan
    create_response = await client.post(
        "/api/v1/treatment_plan/treatment-plans",
        json={
            "patient_id": treatment_plan_setup["patient_id"],
        },
        headers=auth_headers,
    )
    plan_id = create_response.json()["data"]["id"]

    # Add global item
    response = await client.post(
        f"/api/v1/treatment_plan/treatment-plans/{plan_id}/items",
        json={
            "catalog_item_id": treatment_plan_setup["catalog_item_id"],
            "is_global": True,
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["is_global"] is True
    assert data["tooth_treatment_id"] is None


@pytest.mark.asyncio
async def test_complete_item(
    client: AsyncClient, auth_headers: dict, treatment_plan_setup: dict
):
    """Test marking a treatment item as completed."""
    # Create plan
    create_response = await client.post(
        "/api/v1/treatment_plan/treatment-plans",
        json={
            "patient_id": treatment_plan_setup["patient_id"],
        },
        headers=auth_headers,
    )
    plan_id = create_response.json()["data"]["id"]

    # Add item
    item_response = await client.post(
        f"/api/v1/treatment_plan/treatment-plans/{plan_id}/items",
        json={
            "catalog_item_id": treatment_plan_setup["catalog_item_id"],
            "is_global": True,
        },
        headers=auth_headers,
    )
    item_id = item_response.json()["data"]["id"]

    # Complete item
    response = await client.patch(
        f"/api/v1/treatment_plan/treatment-plans/{plan_id}/items/{item_id}/complete",
        json={"completed_without_appointment": True},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "completed"
    assert data["completed_without_appointment"] is True
    assert data["completed_at"] is not None


@pytest.mark.asyncio
async def test_remove_item(
    client: AsyncClient, auth_headers: dict, treatment_plan_setup: dict
):
    """Test removing an item from a plan."""
    # Create plan
    create_response = await client.post(
        "/api/v1/treatment_plan/treatment-plans",
        json={
            "patient_id": treatment_plan_setup["patient_id"],
        },
        headers=auth_headers,
    )
    plan_id = create_response.json()["data"]["id"]

    # Add item
    item_response = await client.post(
        f"/api/v1/treatment_plan/treatment-plans/{plan_id}/items",
        json={
            "catalog_item_id": treatment_plan_setup["catalog_item_id"],
            "is_global": True,
        },
        headers=auth_headers,
    )
    item_id = item_response.json()["data"]["id"]

    # Remove item
    response = await client.delete(
        f"/api/v1/treatment_plan/treatment-plans/{plan_id}/items/{item_id}",
        headers=auth_headers,
    )
    assert response.status_code == 204

    # Verify item is removed
    plan_response = await client.get(
        f"/api/v1/treatment_plan/treatment-plans/{plan_id}",
        headers=auth_headers,
    )
    item_ids = [i["id"] for i in plan_response.json()["data"]["items"]]
    assert item_id not in item_ids


# ============================================================================
# Patient Plans Tests
# ============================================================================


@pytest.mark.asyncio
async def test_list_patient_plans(
    client: AsyncClient, auth_headers: dict, treatment_plan_setup: dict
):
    """Test listing plans for a specific patient."""
    patient_id = treatment_plan_setup["patient_id"]

    # Create two plans for the patient
    await client.post(
        "/api/v1/treatment_plan/treatment-plans",
        json={"patient_id": patient_id, "title": "Plan 1"},
        headers=auth_headers,
    )
    await client.post(
        "/api/v1/treatment_plan/treatment-plans",
        json={"patient_id": patient_id, "title": "Plan 2"},
        headers=auth_headers,
    )

    # List plans for patient
    response = await client.get(
        f"/api/v1/treatment_plan/treatment-plans/patient/{patient_id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) >= 2
    assert all(p["patient_id"] == patient_id for p in data["data"])


# ============================================================================
# Auto-Completion Tests
# ============================================================================


@pytest.mark.asyncio
async def test_plan_auto_completes_when_all_items_completed(
    client: AsyncClient, auth_headers: dict, treatment_plan_setup: dict
):
    """Test that an active plan auto-completes when all items are marked completed."""
    # Create plan with two items
    create_response = await client.post(
        "/api/v1/treatment_plan/treatment-plans",
        json={
            "patient_id": treatment_plan_setup["patient_id"],
        },
        headers=auth_headers,
    )
    plan_id = create_response.json()["data"]["id"]

    # Add first item
    item1_response = await client.post(
        f"/api/v1/treatment_plan/treatment-plans/{plan_id}/items",
        json={
            "catalog_item_id": treatment_plan_setup["catalog_item_id"],
            "is_global": True,
        },
        headers=auth_headers,
    )
    item1_id = item1_response.json()["data"]["id"]

    # Add second item
    item2_response = await client.post(
        f"/api/v1/treatment_plan/treatment-plans/{plan_id}/items",
        json={
            "catalog_item_id": treatment_plan_setup["catalog_item_id"],
            "is_global": True,
        },
        headers=auth_headers,
    )
    item2_id = item2_response.json()["data"]["id"]

    # Activate the plan
    await client.patch(
        f"/api/v1/treatment_plan/treatment-plans/{plan_id}/status",
        json={"status": "active"},
        headers=auth_headers,
    )

    # Complete first item - plan should stay active
    await client.patch(
        f"/api/v1/treatment_plan/treatment-plans/{plan_id}/items/{item1_id}/complete",
        json={},
        headers=auth_headers,
    )

    # Verify plan still active
    plan_response = await client.get(
        f"/api/v1/treatment_plan/treatment-plans/{plan_id}",
        headers=auth_headers,
    )
    assert plan_response.json()["data"]["status"] == "active"

    # Complete second item - plan should auto-complete
    await client.patch(
        f"/api/v1/treatment_plan/treatment-plans/{plan_id}/items/{item2_id}/complete",
        json={},
        headers=auth_headers,
    )

    # Verify plan is now completed
    plan_response = await client.get(
        f"/api/v1/treatment_plan/treatment-plans/{plan_id}",
        headers=auth_headers,
    )
    assert plan_response.json()["data"]["status"] == "completed"


@pytest.mark.asyncio
async def test_plan_does_not_auto_complete_if_not_active(
    client: AsyncClient, auth_headers: dict, treatment_plan_setup: dict
):
    """Test that a draft plan does not auto-complete when items are completed."""
    # Create plan with one item (stays in draft)
    create_response = await client.post(
        "/api/v1/treatment_plan/treatment-plans",
        json={
            "patient_id": treatment_plan_setup["patient_id"],
        },
        headers=auth_headers,
    )
    plan_id = create_response.json()["data"]["id"]

    # Add item
    item_response = await client.post(
        f"/api/v1/treatment_plan/treatment-plans/{plan_id}/items",
        json={
            "catalog_item_id": treatment_plan_setup["catalog_item_id"],
            "is_global": True,
        },
        headers=auth_headers,
    )
    item_id = item_response.json()["data"]["id"]

    # Complete item while plan is still in draft
    await client.patch(
        f"/api/v1/treatment_plan/treatment-plans/{plan_id}/items/{item_id}/complete",
        json={},
        headers=auth_headers,
    )

    # Verify plan stays in draft (not auto-completed)
    plan_response = await client.get(
        f"/api/v1/treatment_plan/treatment-plans/{plan_id}",
        headers=auth_headers,
    )
    assert plan_response.json()["data"]["status"] == "draft"
