"""End-to-end tests for clinical notes + polymorphic attachments."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID, uuid4

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
from app.modules.media.models import Document

# ---------------------------------------------------------------------------
# Setup helpers
# ---------------------------------------------------------------------------


async def _bootstrap(
    db_session: AsyncSession, client: AsyncClient, auth_headers: dict[str, str]
) -> dict:
    me = await client.get("/api/v1/auth/me", headers=auth_headers)
    user_id = me.json()["data"]["user"]["id"]

    clinic = Clinic(
        id=uuid4(),
        name="Notes Clinic",
        tax_id="B12398765",
        address={"street": "Test", "city": "Madrid"},
        settings={"slot_duration_min": 15},
    )
    db_session.add(clinic)
    await db_session.flush()
    db_session.add(
        ClinicMembership(id=uuid4(), user_id=user_id, clinic_id=clinic.id, role="dentist")
    )
    await db_session.commit()

    pat = await client.post(
        "/api/v1/patients",
        headers=auth_headers,
        json={"first_name": "Ana", "last_name": "Gómez", "phone": "+34666111222"},
    )
    patient_id = pat.json()["data"]["id"]

    return {"clinic_id": str(clinic.id), "user_id": user_id, "patient_id": patient_id}


async def _seed_catalog(db_session: AsyncSession, clinic_id: str) -> str:
    vat = VatType(clinic_id=clinic_id, names={"es": "Exento"}, rate=0.0, is_default=True)
    db_session.add(vat)
    await db_session.flush()
    cat = TreatmentCategory(
        clinic_id=clinic_id, key="endo", names={"es": "Endodoncia"}, is_system=True
    )
    db_session.add(cat)
    await db_session.flush()
    item = TreatmentCatalogItem(
        clinic_id=clinic_id,
        category_id=cat.id,
        internal_code="NOTE-ENDO",
        names={"es": "Endodoncia"},
        default_price=Decimal("200.00"),
        pricing_strategy="flat",
        treatment_scope="tooth",
        vat_type_id=vat.id,
    )
    db_session.add(item)
    await db_session.flush()
    db_session.add(
        TreatmentOdontogramMapping(
            clinic_id=clinic_id,
            catalog_item_id=item.id,
            odontogram_treatment_type="endodontics",
            clinical_category="endodoncia",
            visualization_rules=[],
            visualization_config={},
        )
    )
    await db_session.commit()
    return str(item.id)


@pytest.fixture
async def ctx(db_session: AsyncSession, client: AsyncClient, auth_headers: dict[str, str]) -> dict:
    c = await _bootstrap(db_session, client, auth_headers)
    c["catalog_item_id"] = await _seed_catalog(db_session, c["clinic_id"])
    return c


async def _create_plan_with_item(
    client: AsyncClient, auth_headers: dict, ctx: dict
) -> tuple[str, str]:
    plan = await client.post(
        "/api/v1/treatment_plan/treatment-plans",
        headers=auth_headers,
        json={"patient_id": ctx["patient_id"], "title": "Plan de endodoncia"},
    )
    assert plan.status_code == 201, plan.text
    plan_id = plan.json()["data"]["id"]

    tr = await client.post(
        f"/api/v1/odontogram/patients/{ctx['patient_id']}/treatments",
        headers=auth_headers,
        json={
            "catalog_item_id": ctx["catalog_item_id"],
            "tooth_numbers": [16],
            "status": "planned",
        },
    )
    assert tr.status_code == 201, tr.text
    add = await client.post(
        f"/api/v1/treatment_plan/treatment-plans/{plan_id}/items",
        headers=auth_headers,
        json={"treatment_id": tr.json()["data"]["id"]},
    )
    assert add.status_code == 201, add.text
    return plan_id, add.json()["data"]["id"]


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_plan_note_and_list(
    client: AsyncClient, auth_headers: dict, ctx: dict
) -> None:
    plan_id, _ = await _create_plan_with_item(client, auth_headers, ctx)

    resp = await client.post(
        "/api/v1/treatment_plan/notes",
        headers=auth_headers,
        json={
            "owner_type": "plan",
            "owner_id": plan_id,
            "body": "<p>Diagnóstico preliminar: pulpitis irreversible 16.</p>",
        },
    )
    assert resp.status_code == 201, resp.text
    note_id = resp.json()["data"]["id"]

    listing = await client.get(
        f"/api/v1/treatment_plan/notes?owner_type=plan&owner_id={plan_id}",
        headers=auth_headers,
    )
    assert listing.status_code == 200
    ids = [n["id"] for n in listing.json()["data"]]
    assert note_id in ids


@pytest.mark.asyncio
async def test_create_item_note_and_soft_delete(
    client: AsyncClient, auth_headers: dict, ctx: dict
) -> None:
    _, item_id = await _create_plan_with_item(client, auth_headers, ctx)

    create = await client.post(
        "/api/v1/treatment_plan/notes",
        headers=auth_headers,
        json={
            "owner_type": "plan_item",
            "owner_id": item_id,
            "body": "<p>Anestesia: articaina 1:100k</p>",
        },
    )
    note_id = create.json()["data"]["id"]

    delete = await client.delete(f"/api/v1/treatment_plan/notes/{note_id}", headers=auth_headers)
    assert delete.status_code == 204

    listing = await client.get(
        f"/api/v1/treatment_plan/notes?owner_type=plan_item&owner_id={item_id}",
        headers=auth_headers,
    )
    assert all(n["id"] != note_id for n in listing.json()["data"])


@pytest.mark.asyncio
async def test_update_note_body(client: AsyncClient, auth_headers: dict, ctx: dict) -> None:
    plan_id, _ = await _create_plan_with_item(client, auth_headers, ctx)

    create = await client.post(
        "/api/v1/treatment_plan/notes",
        headers=auth_headers,
        json={"owner_type": "plan", "owner_id": plan_id, "body": "<p>v1</p>"},
    )
    note_id = create.json()["data"]["id"]
    patch = await client.patch(
        f"/api/v1/treatment_plan/notes/{note_id}",
        headers=auth_headers,
        json={"body": "<p>v2</p>"},
    )
    assert patch.status_code == 200
    assert patch.json()["data"]["body"] == "<p>v2</p>"


@pytest.mark.asyncio
async def test_rejects_unsupported_owner_type(
    client: AsyncClient, auth_headers: dict, ctx: dict
) -> None:
    resp = await client.post(
        "/api/v1/treatment_plan/notes",
        headers=auth_headers,
        json={
            "owner_type": "appointment_treatment",
            "owner_id": str(uuid4()),
            "body": "<p>x</p>",
        },
    )
    # Pydantic pattern validation on owner_type rejects anything outside {plan, plan_item}
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Attachments
# ---------------------------------------------------------------------------


async def _seed_document(
    db_session: AsyncSession, clinic_id: str, patient_id: str, user_id: str
) -> Document:
    doc = Document(
        id=uuid4(),
        clinic_id=UUID(clinic_id),
        patient_id=UUID(patient_id),
        document_type="report",
        title="RX 16",
        original_filename="rx16.png",
        storage_path=f"/docs/{uuid4()}.png",
        mime_type="image/png",
        file_size=1024,
        uploaded_by=UUID(user_id),
    )
    db_session.add(doc)
    await db_session.commit()
    return doc


@pytest.mark.asyncio
async def test_attach_document_to_plan_note(
    db_session: AsyncSession,
    client: AsyncClient,
    auth_headers: dict,
    ctx: dict,
) -> None:
    plan_id, _ = await _create_plan_with_item(client, auth_headers, ctx)
    doc = await _seed_document(db_session, ctx["clinic_id"], ctx["patient_id"], ctx["user_id"])

    create_note = await client.post(
        "/api/v1/treatment_plan/notes",
        headers=auth_headers,
        json={
            "owner_type": "plan",
            "owner_id": plan_id,
            "body": "<p>con RX</p>",
            "attachment_document_ids": [str(doc.id)],
        },
    )
    assert create_note.status_code == 201, create_note.text
    note = create_note.json()["data"]
    assert len(note["attachments"]) == 1
    assert note["attachments"][0]["document_id"] == str(doc.id)


@pytest.mark.asyncio
async def test_attach_document_patient_mismatch_rejected(
    db_session: AsyncSession,
    client: AsyncClient,
    auth_headers: dict,
    ctx: dict,
) -> None:
    plan_id, _ = await _create_plan_with_item(client, auth_headers, ctx)

    # Seed a document belonging to a *different* patient in the same clinic.
    other_patient = await client.post(
        "/api/v1/patients",
        headers=auth_headers,
        json={"first_name": "Otro", "last_name": "Paciente", "phone": "+34111000111"},
    )
    other_patient_id = other_patient.json()["data"]["id"]
    doc = await _seed_document(db_session, ctx["clinic_id"], other_patient_id, ctx["user_id"])

    resp = await client.post(
        "/api/v1/treatment_plan/notes",
        headers=auth_headers,
        json={
            "owner_type": "plan",
            "owner_id": plan_id,
            "body": "<p>mismatch</p>",
            "attachment_document_ids": [str(doc.id)],
        },
    )
    assert resp.status_code == 400, resp.text


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_note_templates_endpoint(client: AsyncClient, auth_headers: dict, ctx: dict) -> None:
    resp = await client.get(
        "/api/v1/treatment_plan/note-templates?category=endodontics",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    ids = [t["id"] for t in resp.json()["data"]]
    assert "endo_single_visit" in ids


# ---------------------------------------------------------------------------
# complete_item integration
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_complete_item_with_note_creates_timeline_note(
    client: AsyncClient, auth_headers: dict, ctx: dict
) -> None:
    plan_id, item_id = await _create_plan_with_item(client, auth_headers, ctx)

    resp = await client.patch(
        f"/api/v1/treatment_plan/treatment-plans/{plan_id}/items/{item_id}/complete",
        headers=auth_headers,
        json={
            "completed_without_appointment": True,
            "note_body": "<p>Endodoncia completada en una sesión.</p>",
        },
    )
    assert resp.status_code == 200, resp.text

    notes = await client.get(
        f"/api/v1/treatment_plan/notes?owner_type=plan_item&owner_id={item_id}",
        headers=auth_headers,
    )
    bodies = [n["body"] for n in notes.json()["data"]]
    assert any("Endodoncia completada" in b for b in bodies)


@pytest.mark.asyncio
async def test_complete_item_without_note_emits_skip_event(
    client: AsyncClient, auth_headers: dict, ctx: dict
) -> None:
    from app.core.events import event_bus
    from app.core.events.types import EventType

    seen: list[dict] = []

    def _capture(data: dict) -> None:
        seen.append(data)

    event_bus.subscribe(EventType.TREATMENT_PLAN_ITEM_COMPLETED_WITHOUT_NOTE, _capture)

    plan_id, item_id = await _create_plan_with_item(client, auth_headers, ctx)

    resp = await client.patch(
        f"/api/v1/treatment_plan/treatment-plans/{plan_id}/items/{item_id}/complete",
        headers=auth_headers,
        json={"completed_without_appointment": True},
    )
    assert resp.status_code == 200

    assert any(d.get("plan_item_id") == item_id for d in seen), "skip event not emitted"


# ---------------------------------------------------------------------------
# Merged feed
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_merged_clinical_notes_feed(
    client: AsyncClient, auth_headers: dict, ctx: dict
) -> None:
    plan_id, item_id = await _create_plan_with_item(client, auth_headers, ctx)

    await client.post(
        "/api/v1/treatment_plan/notes",
        headers=auth_headers,
        json={"owner_type": "plan", "owner_id": plan_id, "body": "<p>plan note</p>"},
    )
    await client.post(
        "/api/v1/treatment_plan/notes",
        headers=auth_headers,
        json={
            "owner_type": "plan_item",
            "owner_id": item_id,
            "body": "<p>item note</p>",
        },
    )

    resp = await client.get(
        f"/api/v1/treatment_plan/treatment-plans/{plan_id}/clinical-notes",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    sources = {e["source"] for e in resp.json()["data"]}
    assert {"plan", "plan_item"}.issubset(sources)


# ---------------------------------------------------------------------------
# Cross-clinic isolation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cross_clinic_note_listing_isolated(
    db_session: AsyncSession,
    client: AsyncClient,
    auth_headers: dict,
    ctx: dict,
) -> None:
    plan_id, _ = await _create_plan_with_item(client, auth_headers, ctx)
    await client.post(
        "/api/v1/treatment_plan/notes",
        headers=auth_headers,
        json={"owner_type": "plan", "owner_id": plan_id, "body": "<p>mine</p>"},
    )

    # Second user in a brand-new clinic; cannot see notes from first clinic's plan.
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "other@example.com",
            "password": "OtherPass1234",
            "first_name": "Other",
            "last_name": "User",
        },
    )
    other_token = reg.json()["access_token"]
    me_other = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {other_token}"}
    )
    other_user_id = me_other.json()["data"]["user"]["id"]

    other_clinic = Clinic(
        id=uuid4(),
        name="Other Clinic",
        tax_id="B99999999",
        address={"street": "x", "city": "y"},
        settings={"slot_duration_min": 15},
    )
    db_session.add(other_clinic)
    await db_session.flush()
    db_session.add(
        ClinicMembership(
            id=uuid4(),
            user_id=other_user_id,
            clinic_id=other_clinic.id,
            role="dentist",
        )
    )
    await db_session.commit()

    other_headers = {"Authorization": f"Bearer {other_token}"}
    listing = await client.get(
        f"/api/v1/treatment_plan/notes?owner_type=plan&owner_id={plan_id}",
        headers=other_headers,
    )
    # Other clinic can't resolve this plan → 400 owner-not-found
    assert listing.status_code in (400, 404)
