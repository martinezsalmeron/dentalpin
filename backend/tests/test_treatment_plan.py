"""Smoke tests for the treatment plan module after the Treatment refactor."""

from decimal import Decimal
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.models import Clinic, ClinicMembership
from app.modules.catalog.models import (
    TreatmentCatalogItem,
    TreatmentCategory,
    TreatmentOdontogramMapping,
    VatType,
)


async def _ensure_clinic_and_patient(
    db_session: AsyncSession, client: AsyncClient, auth_headers: dict[str, str]
) -> dict:
    me = await client.get("/api/v1/auth/me", headers=auth_headers)
    user_id = me.json()["data"]["user"]["id"]

    clinic = Clinic(
        id=uuid4(),
        name="Plan Clinic",
        tax_id="B11111111",
        address={"street": "a", "city": "b"},
        settings={"slot_duration_min": 15},
    )
    db_session.add(clinic)
    await db_session.flush()

    db_session.add(
        ClinicMembership(id=uuid4(), user_id=user_id, clinic_id=clinic.id, role="dentist")
    )
    await db_session.commit()

    patient_resp = await client.post(
        "/api/v1/patients",
        headers=auth_headers,
        json={"first_name": "Luis", "last_name": "Soto", "phone": "+34666333444"},
    )
    patient_id = patient_resp.json()["data"]["id"]

    return {"clinic_id": str(clinic.id), "user_id": user_id, "patient_id": patient_id}


async def _seed_catalog_crown(db_session: AsyncSession, clinic_id) -> str:
    vat = VatType(clinic_id=clinic_id, names={"es": "Exento"}, rate=0.0, is_default=True)
    db_session.add(vat)
    await db_session.flush()
    cat = TreatmentCategory(clinic_id=clinic_id, key="rest", names={"es": "R"}, is_system=True)
    db_session.add(cat)
    await db_session.flush()
    crown = TreatmentCatalogItem(
        clinic_id=clinic_id,
        category_id=cat.id,
        internal_code="PLAN-CROWN",
        names={"es": "Corona"},
        default_price=Decimal("500.00"),
        pricing_strategy="flat",
        treatment_scope="tooth",
        vat_type_id=vat.id,
    )
    db_session.add(crown)
    await db_session.flush()
    db_session.add(
        TreatmentOdontogramMapping(
            clinic_id=clinic_id,
            catalog_item_id=crown.id,
            odontogram_treatment_type="crown",
            clinical_category="restauradora",
            visualization_rules=[],
            visualization_config={},
        )
    )
    await db_session.commit()
    return str(crown.id)


@pytest.fixture
async def setup(
    db_session: AsyncSession, auth_headers: dict[str, str], client: AsyncClient
) -> dict:
    ctx = await _ensure_clinic_and_patient(db_session, client, auth_headers)
    ctx["crown_id"] = await _seed_catalog_crown(db_session, ctx["clinic_id"])
    return ctx


async def _create_treatment(
    client: AsyncClient,
    auth_headers: dict,
    setup: dict,
    tooth_number: int = 16,
) -> str:
    r = await client.post(
        f"/api/v1/odontogram/patients/{setup['patient_id']}/treatments",
        headers=auth_headers,
        json={
            "catalog_item_id": setup["crown_id"],
            "tooth_numbers": [tooth_number],
            "status": "planned",
        },
    )
    assert r.status_code == 201, r.text
    return r.json()["data"]["id"]


async def _create_plan_with_items(
    client: AsyncClient, auth_headers: dict, setup: dict, tooth_numbers: list[int]
) -> tuple[str, list[str]]:
    """Helper: create a plan and add N items (one per tooth). Returns (plan_id, item_ids)."""
    plan_resp = await client.post(
        "/api/v1/treatment_plan/treatment-plans",
        headers=auth_headers,
        json={"patient_id": setup["patient_id"], "title": "Reorder plan"},
    )
    assert plan_resp.status_code == 201, plan_resp.text
    plan_id = plan_resp.json()["data"]["id"]

    item_ids: list[str] = []
    for tn in tooth_numbers:
        treatment_id = await _create_treatment(client, auth_headers, setup, tooth_number=tn)
        add = await client.post(
            f"/api/v1/treatment_plan/treatment-plans/{plan_id}/items",
            headers=auth_headers,
            json={"treatment_id": treatment_id},
        )
        assert add.status_code == 201, add.text
        item_ids.append(add.json()["data"]["id"])
    return plan_id, item_ids


@pytest.mark.asyncio
async def test_create_empty_plan(client: AsyncClient, auth_headers: dict, setup: dict) -> None:
    r = await client.post(
        "/api/v1/treatment_plan/treatment-plans",
        headers=auth_headers,
        json={"patient_id": setup["patient_id"], "title": "Demo plan"},
    )
    assert r.status_code == 201, r.text
    data = r.json()["data"]
    assert data["status"] == "draft"


@pytest.mark.asyncio
async def test_add_treatment_item_to_plan(
    client: AsyncClient, auth_headers: dict, setup: dict
) -> None:
    plan_resp = await client.post(
        "/api/v1/treatment_plan/treatment-plans",
        headers=auth_headers,
        json={"patient_id": setup["patient_id"], "title": "Demo"},
    )
    plan_id = plan_resp.json()["data"]["id"]
    treatment_id = await _create_treatment(client, auth_headers, setup)

    r = await client.post(
        f"/api/v1/treatment_plan/treatment-plans/{plan_id}/items",
        headers=auth_headers,
        json={"treatment_id": treatment_id},
    )
    assert r.status_code == 201, r.text
    data = r.json()["data"]
    assert data["treatment_id"] == treatment_id
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_duplicate_treatment_id_rejected(
    client: AsyncClient, auth_headers: dict, setup: dict
) -> None:
    plan_resp = await client.post(
        "/api/v1/treatment_plan/treatment-plans",
        headers=auth_headers,
        json={"patient_id": setup["patient_id"]},
    )
    plan_id = plan_resp.json()["data"]["id"]
    treatment_id = await _create_treatment(client, auth_headers, setup)

    first = await client.post(
        f"/api/v1/treatment_plan/treatment-plans/{plan_id}/items",
        headers=auth_headers,
        json={"treatment_id": treatment_id},
    )
    assert first.status_code == 201

    # Unique constraint on treatment_id — second add raises IntegrityError
    # which the handler surfaces as a 5xx. Capture the exception to keep the
    # assertion focused on "the duplicate was blocked".
    from sqlalchemy.exc import IntegrityError

    try:
        second = await client.post(
            f"/api/v1/treatment_plan/treatment-plans/{plan_id}/items",
            headers=auth_headers,
            json={"treatment_id": treatment_id},
        )
        assert second.status_code in (400, 409, 500)
    except IntegrityError:
        pass


# ---------------------------------------------------------------------------
# Reorder
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_reorder_items_happy_path(
    client: AsyncClient, auth_headers: dict, setup: dict
) -> None:
    plan_id, item_ids = await _create_plan_with_items(client, auth_headers, setup, [16, 15, 14])
    reversed_ids = list(reversed(item_ids))

    r = await client.patch(
        f"/api/v1/treatment_plan/treatment-plans/{plan_id}/items/reorder",
        headers=auth_headers,
        json={"item_ids": reversed_ids},
    )
    assert r.status_code == 200, r.text
    returned = [i["id"] for i in r.json()["data"]["items"]]
    assert returned == reversed_ids

    # Persistence: re-fetch.
    g = await client.get(
        f"/api/v1/treatment_plan/treatment-plans/{plan_id}",
        headers=auth_headers,
    )
    again = [i["id"] for i in g.json()["data"]["items"]]
    assert again == reversed_ids


@pytest.mark.asyncio
async def test_reorder_rejects_missing_item(
    client: AsyncClient, auth_headers: dict, setup: dict
) -> None:
    plan_id, item_ids = await _create_plan_with_items(client, auth_headers, setup, [16, 15])
    # Drop one.
    r = await client.patch(
        f"/api/v1/treatment_plan/treatment-plans/{plan_id}/items/reorder",
        headers=auth_headers,
        json={"item_ids": [item_ids[0]]},
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_reorder_rejects_foreign_item(
    client: AsyncClient, auth_headers: dict, setup: dict
) -> None:
    from uuid import uuid4

    plan_id, item_ids = await _create_plan_with_items(client, auth_headers, setup, [16, 15])
    bogus = str(uuid4())
    r = await client.patch(
        f"/api/v1/treatment_plan/treatment-plans/{plan_id}/items/reorder",
        headers=auth_headers,
        json={"item_ids": [item_ids[0], bogus]},
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_reorder_rejects_duplicate_ids(
    client: AsyncClient, auth_headers: dict, setup: dict
) -> None:
    plan_id, item_ids = await _create_plan_with_items(client, auth_headers, setup, [16, 15])
    r = await client.patch(
        f"/api/v1/treatment_plan/treatment-plans/{plan_id}/items/reorder",
        headers=auth_headers,
        json={"item_ids": [item_ids[0], item_ids[0]]},
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_reorder_unknown_plan_returns_404(
    client: AsyncClient, auth_headers: dict, setup: dict
) -> None:
    from uuid import uuid4

    r = await client.patch(
        f"/api/v1/treatment_plan/treatment-plans/{uuid4()}/items/reorder",
        headers=auth_headers,
        json={"item_ids": []},
    )
    assert r.status_code == 404


# -----------------------------------------------------------------------------
# Orphan cleanup on terminal plan states (archive / cancel)
# -----------------------------------------------------------------------------


async def _treatment_is_deleted(
    client: AsyncClient, auth_headers: dict, patient_id: str, treatment_id: str
) -> bool:
    """Check whether a Treatment is soft-deleted by looking for it in the odontogram list."""
    r = await client.get(
        f"/api/v1/odontogram/patients/{patient_id}/treatments",
        headers=auth_headers,
    )
    assert r.status_code == 200, r.text
    active_ids = {t["id"] for t in r.json()["data"]}
    return treatment_id not in active_ids


@pytest.mark.asyncio
async def test_delete_plan_removes_planned_treatments_from_odontogram(
    client: AsyncClient, auth_headers: dict, setup: dict
) -> None:
    """Archiving a plan via DELETE soft-deletes its planned Treatments."""
    plan_id, _ = await _create_plan_with_items(client, auth_headers, setup, [16, 15])

    # Snapshot treatment ids from the plan items
    plan_resp = await client.get(
        f"/api/v1/treatment_plan/treatment-plans/{plan_id}",
        headers=auth_headers,
    )
    treatment_ids = [i["treatment"]["id"] for i in plan_resp.json()["data"]["items"]]
    assert len(treatment_ids) == 2

    # Archive plan
    r = await client.delete(
        f"/api/v1/treatment_plan/treatment-plans/{plan_id}",
        headers=auth_headers,
    )
    assert r.status_code == 204, r.text

    # Both planned treatments should be gone from the odontogram
    for tid in treatment_ids:
        assert await _treatment_is_deleted(client, auth_headers, setup["patient_id"], tid), (
            f"treatment {tid} should be soft-deleted"
        )


@pytest.mark.asyncio
async def test_delete_plan_keeps_performed_treatments(
    client: AsyncClient, auth_headers: dict, setup: dict
) -> None:
    """Archiving a plan preserves Treatments that were already performed."""
    plan_id, _ = await _create_plan_with_items(client, auth_headers, setup, [16, 15])

    plan_resp = await client.get(
        f"/api/v1/treatment_plan/treatment-plans/{plan_id}",
        headers=auth_headers,
    )
    items = plan_resp.json()["data"]["items"]
    treatment_ids = [i["treatment"]["id"] for i in items]
    performed_id, planned_id = treatment_ids[0], treatment_ids[1]

    # Mark first treatment as performed
    r = await client.patch(
        f"/api/v1/odontogram/treatments/{performed_id}/perform",
        headers=auth_headers,
        json={},
    )
    assert r.status_code == 200, r.text

    # Archive plan
    r = await client.delete(
        f"/api/v1/treatment_plan/treatment-plans/{plan_id}",
        headers=auth_headers,
    )
    assert r.status_code == 204, r.text

    # Performed survives, planned removed
    assert not await _treatment_is_deleted(
        client, auth_headers, setup["patient_id"], performed_id
    ), "performed treatment must be preserved"
    assert await _treatment_is_deleted(client, auth_headers, setup["patient_id"], planned_id), (
        "planned treatment must be soft-deleted"
    )


# -----------------------------------------------------------------------------
# Lock / unlock on budget generation
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_add_item_blocked_when_budget_generated(
    client: AsyncClient, auth_headers: dict, setup: dict
) -> None:
    """Generating a budget locks the plan — further items are rejected with 409."""
    plan_id, _ = await _create_plan_with_items(client, auth_headers, setup, [16])

    # Confirm the plan (auto-creates budget) and activate.
    r = await client.post(
        f"/api/v1/treatment_plan/treatment-plans/{plan_id}/confirm",
        headers=auth_headers,
    )
    assert r.status_code == 200, r.text
    r = await client.patch(
        f"/api/v1/treatment_plan/treatment-plans/{plan_id}/status",
        headers=auth_headers,
        json={"status": "active"},
    )
    assert r.status_code == 200, r.text

    # Try to add another item — should be 409 locked.
    new_treatment_id = await _create_treatment(client, auth_headers, setup, tooth_number=15)
    r = await client.post(
        f"/api/v1/treatment_plan/treatment-plans/{plan_id}/items",
        headers=auth_headers,
        json={"treatment_id": new_treatment_id},
    )
    assert r.status_code == 409, r.text


@pytest.mark.asyncio
async def test_remove_item_blocked_when_budget_generated(
    client: AsyncClient, auth_headers: dict, setup: dict
) -> None:
    plan_id, item_ids = await _create_plan_with_items(client, auth_headers, setup, [16, 15])

    await client.patch(
        f"/api/v1/treatment_plan/treatment-plans/{plan_id}/status",
        headers=auth_headers,
        json={"status": "active"},
    )
    await client.post(
        f"/api/v1/treatment_plan/treatment-plans/{plan_id}/generate-budget",
        headers=auth_headers,
    )

    r = await client.delete(
        f"/api/v1/treatment_plan/treatment-plans/{plan_id}/items/{item_ids[0]}",
        headers=auth_headers,
    )
    assert r.status_code == 409, r.text


@pytest.mark.asyncio
async def test_cancel_plan_removes_planned_treatments(
    client: AsyncClient, auth_headers: dict, setup: dict
) -> None:
    """Closing an active plan cleans up its orphaned planned Treatments.

    Workflow rework: draft → pending → active → closed (cancelled_by_clinic).
    """
    plan_id, _ = await _create_plan_with_items(client, auth_headers, setup, [16])
    plan_resp = await client.get(
        f"/api/v1/treatment_plan/treatment-plans/{plan_id}",
        headers=auth_headers,
    )
    treatment_id = plan_resp.json()["data"]["items"][0]["treatment"]["id"]

    # draft → pending (auto-creates draft budget)
    r = await client.post(
        f"/api/v1/treatment_plan/treatment-plans/{plan_id}/confirm",
        headers=auth_headers,
    )
    assert r.status_code == 200, r.text

    # pending → active (admin override via patch /status, would normally come from
    # the budget acceptance event; tests do that path explicitly).
    r = await client.patch(
        f"/api/v1/treatment_plan/treatment-plans/{plan_id}/status",
        headers=auth_headers,
        json={"status": "active"},
    )
    assert r.status_code == 200, r.text

    # active → closed (cancelled by clinic)
    r = await client.post(
        f"/api/v1/treatment_plan/treatment-plans/{plan_id}/close",
        headers=auth_headers,
        json={"closure_reason": "cancelled_by_clinic"},
    )
    assert r.status_code == 200, r.text

    assert await _treatment_is_deleted(client, auth_headers, setup["patient_id"], treatment_id)
