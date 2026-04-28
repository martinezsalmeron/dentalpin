"""Smoke tests for the clinical_notes module (issue #60).

Covers the four note_type pairings, the recent feed for the patient summary
tab, the type/owner matrix CHECK rejection and the per-treatment endpoint.
"""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.models import Clinic, ClinicMembership
from app.modules.odontogram.models import Treatment


async def _seed_clinic_and_patient(
    db_session: AsyncSession, client: AsyncClient, auth_headers: dict[str, str]
) -> dict:
    me = await client.get("/api/v1/auth/me", headers=auth_headers)
    user_id = me.json()["data"]["user"]["id"]

    clinic = Clinic(
        id=uuid4(),
        name="Notes Clinic",
        tax_id="B22222222",
        address={"street": "x", "city": "y"},
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
        json={"first_name": "Ana", "last_name": "García", "phone": "+34699111222"},
    )
    return {"clinic_id": str(clinic.id), "patient_id": patient_resp.json()["data"]["id"]}


async def _seed_treatment(db_session: AsyncSession, clinic_id, patient_id) -> str:
    """Seed a minimal Treatment row tied to a patient — represents a tooth
    finding diagnosed in the odontogram. Notes attach to its id."""
    treatment = Treatment(
        id=uuid4(),
        clinic_id=clinic_id,
        patient_id=patient_id,
        clinical_type="caries",
        scope="tooth",
        status="existing",
        recorded_at=datetime.now(UTC),
        source_module="odontogram",
    )
    db_session.add(treatment)
    await db_session.commit()
    return str(treatment.id)


@pytest.mark.asyncio
async def test_create_administrative_note(
    client: AsyncClient, auth_headers: dict[str, str], db_session: AsyncSession
):
    ctx = await _seed_clinic_and_patient(db_session, client, auth_headers)

    resp = await client.post(
        "/api/v1/clinical_notes/notes",
        headers=auth_headers,
        json={
            "note_type": "administrative",
            "owner_type": "patient",
            "owner_id": ctx["patient_id"],
            "body": "Patient called complaining of tooth pain",
        },
    )
    assert resp.status_code == 201, resp.text
    note = resp.json()["data"]
    assert note["note_type"] == "administrative"
    assert note["owner_type"] == "patient"
    assert note["tooth_number"] is None


@pytest.mark.asyncio
async def test_create_diagnosis_note_with_tooth(
    client: AsyncClient, auth_headers: dict[str, str], db_session: AsyncSession
):
    ctx = await _seed_clinic_and_patient(db_session, client, auth_headers)
    resp = await client.post(
        "/api/v1/clinical_notes/notes",
        headers=auth_headers,
        json={
            "note_type": "diagnosis",
            "owner_type": "patient",
            "owner_id": ctx["patient_id"],
            "tooth_number": 47,
            "body": "Deep caries on 47",
        },
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["data"]["tooth_number"] == 47


@pytest.mark.asyncio
async def test_create_treatment_note_attaches_to_treatment_id(
    client: AsyncClient, auth_headers: dict[str, str], db_session: AsyncSession
):
    ctx = await _seed_clinic_and_patient(db_session, client, auth_headers)
    treatment_id = await _seed_treatment(db_session, ctx["clinic_id"], ctx["patient_id"])

    resp = await client.post(
        "/api/v1/clinical_notes/notes",
        headers=auth_headers,
        json={
            "note_type": "treatment",
            "owner_type": "treatment",
            "owner_id": treatment_id,
            "body": "Filling was deep — may need endodontics",
        },
    )
    assert resp.status_code == 201, resp.text
    note = resp.json()["data"]
    assert note["owner_type"] == "treatment"
    assert note["owner_id"] == treatment_id

    # Same note shows up via the per-owner list and the patient recent feed.
    list_resp = await client.get(
        f"/api/v1/clinical_notes/notes?owner_type=treatment&owner_id={treatment_id}",
        headers=auth_headers,
    )
    assert list_resp.status_code == 200
    assert any(n["id"] == note["id"] for n in list_resp.json()["data"])

    recent = await client.get(
        f"/api/v1/clinical_notes/patients/{ctx['patient_id']}/recent",
        headers=auth_headers,
    )
    assert recent.status_code == 200
    bodies = [e["body"] for e in recent.json()["data"]]
    assert any("endodontics" in b for b in bodies)


@pytest.mark.asyncio
async def test_matrix_rejects_tooth_on_admin(
    client: AsyncClient, auth_headers: dict[str, str], db_session: AsyncSession
):
    ctx = await _seed_clinic_and_patient(db_session, client, auth_headers)
    resp = await client.post(
        "/api/v1/clinical_notes/notes",
        headers=auth_headers,
        json={
            "note_type": "administrative",
            "owner_type": "patient",
            "owner_id": ctx["patient_id"],
            "tooth_number": 47,
            "body": "should fail",
        },
    )
    # The schema-level validator catches the bad pairing as 422.
    assert resp.status_code == 422, resp.text


@pytest.mark.asyncio
async def test_matrix_rejects_diagnosis_on_treatment(
    client: AsyncClient, auth_headers: dict[str, str], db_session: AsyncSession
):
    ctx = await _seed_clinic_and_patient(db_session, client, auth_headers)
    treatment_id = await _seed_treatment(db_session, ctx["clinic_id"], ctx["patient_id"])
    resp = await client.post(
        "/api/v1/clinical_notes/notes",
        headers=auth_headers,
        json={
            "note_type": "diagnosis",
            "owner_type": "treatment",
            "owner_id": treatment_id,
            "body": "should fail",
        },
    )
    assert resp.status_code == 422, resp.text


@pytest.mark.asyncio
async def test_recent_feed_filters_by_type(
    client: AsyncClient, auth_headers: dict[str, str], db_session: AsyncSession
):
    ctx = await _seed_clinic_and_patient(db_session, client, auth_headers)

    # Two notes of different types
    await client.post(
        "/api/v1/clinical_notes/notes",
        headers=auth_headers,
        json={
            "note_type": "administrative",
            "owner_type": "patient",
            "owner_id": ctx["patient_id"],
            "body": "Admin",
        },
    )
    await client.post(
        "/api/v1/clinical_notes/notes",
        headers=auth_headers,
        json={
            "note_type": "diagnosis",
            "owner_type": "patient",
            "owner_id": ctx["patient_id"],
            "body": "Diag",
        },
    )

    only_admin = await client.get(
        f"/api/v1/clinical_notes/patients/{ctx['patient_id']}/recent?types=administrative",
        headers=auth_headers,
    )
    assert only_admin.status_code == 200
    rows = only_admin.json()["data"]
    assert all(r["note_type"] == "administrative" for r in rows)
    assert any(r["body"] == "Admin" for r in rows)
