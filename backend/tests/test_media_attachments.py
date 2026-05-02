"""Tests for the polymorphic attachment registry + endpoints (issue #55)."""

from __future__ import annotations

import io
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.models import Clinic, ClinicMembership
from app.modules.media.attachment_registry import OwnerSpec, attachment_registry
from app.modules.patients.models import Patient


def _png_bytes() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (32, 32), color=(0, 128, 0)).save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
async def attach_setup(
    db_session: AsyncSession, auth_headers: dict[str, str], client: AsyncClient
) -> dict:
    me = await client.get("/api/v1/auth/me", headers=auth_headers)
    user_id = me.json()["data"]["user"]["id"]

    clinic = Clinic(
        id=uuid4(),
        name="Attach Clinic",
        tax_id="B22222222",
        address={"street": "Adj St"},
        settings={"slot_duration_min": 15},
    )
    db_session.add(clinic)
    await db_session.flush()
    db_session.add(ClinicMembership(id=uuid4(), user_id=user_id, clinic_id=clinic.id, role="admin"))
    patient = Patient(
        id=uuid4(),
        clinic_id=clinic.id,
        first_name="Attach",
        last_name="Tester",
    )
    db_session.add(patient)
    await db_session.commit()

    upload = await client.post(
        f"/api/v1/media/patients/{patient.id}/photos",
        headers=auth_headers,
        files={"file": ("p.png", _png_bytes(), "image/png")},
        data={
            "title": "p",
            "media_kind": "photo",
            "media_category": "intraoral",
            "media_subtype": "frontal",
        },
    )
    assert upload.status_code == 201
    document_id = upload.json()["data"]["id"]
    return {
        "clinic_id": str(clinic.id),
        "patient_id": str(patient.id),
        "document_id": document_id,
    }


@pytest.mark.asyncio
async def test_link_to_known_owner_resolves_patient(
    client: AsyncClient, auth_headers: dict[str, str], attach_setup: dict
) -> None:
    """Linking with owner_type='patient' (registered by clinical_notes) works."""
    response = await client.post(
        "/api/v1/media/attachments",
        headers=auth_headers,
        json={
            "document_id": attach_setup["document_id"],
            "owner_type": "patient",
            "owner_id": attach_setup["patient_id"],
        },
    )
    assert response.status_code == 201, response.text
    body = response.json()["data"]
    assert body["owner_type"] == "patient"
    assert body["document_id"] == attach_setup["document_id"]


@pytest.mark.asyncio
async def test_link_unknown_owner_type_400(
    client: AsyncClient, auth_headers: dict[str, str], attach_setup: dict
) -> None:
    response = await client.post(
        "/api/v1/media/attachments",
        headers=auth_headers,
        json={
            "document_id": attach_setup["document_id"],
            "owner_type": "totally_made_up",
            "owner_id": str(uuid4()),
        },
    )
    assert response.status_code == 400
    body = response.json()
    assert "Unknown owner_type" in body.get("detail", body.get("message", ""))


@pytest.mark.asyncio
async def test_link_cross_patient_owner_422(
    db_session: AsyncSession,
    client: AsyncClient,
    auth_headers: dict[str, str],
    attach_setup: dict,
) -> None:
    """Linking a doc to a different patient's owner row is rejected."""
    other_patient = Patient(
        id=uuid4(),
        clinic_id=attach_setup["clinic_id"],
        first_name="Other",
        last_name="Tester",
    )
    db_session.add(other_patient)
    await db_session.commit()

    response = await client.post(
        "/api/v1/media/attachments",
        headers=auth_headers,
        json={
            "document_id": attach_setup["document_id"],
            "owner_type": "patient",
            "owner_id": str(other_patient.id),
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_by_owner_returns_decorated_response(
    client: AsyncClient, auth_headers: dict[str, str], attach_setup: dict
) -> None:
    await client.post(
        "/api/v1/media/attachments",
        headers=auth_headers,
        json={
            "document_id": attach_setup["document_id"],
            "owner_type": "patient",
            "owner_id": attach_setup["patient_id"],
        },
    )
    response = await client.get(
        f"/api/v1/media/attachments?owner_type=patient&owner_id={attach_setup['patient_id']}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    rows = response.json()["data"]
    assert len(rows) == 1
    assert rows[0]["document"]["id"] == attach_setup["document_id"]
    assert rows[0]["thumb_url"]


@pytest.mark.asyncio
async def test_unlink_attachment(
    client: AsyncClient, auth_headers: dict[str, str], attach_setup: dict
) -> None:
    created = await client.post(
        "/api/v1/media/attachments",
        headers=auth_headers,
        json={
            "document_id": attach_setup["document_id"],
            "owner_type": "patient",
            "owner_id": attach_setup["patient_id"],
        },
    )
    attachment_id = created.json()["data"]["id"]

    response = await client.delete(
        f"/api/v1/media/attachments/{attachment_id}", headers=auth_headers
    )
    assert response.status_code == 204


def test_registry_register_is_idempotent() -> None:
    """Registering the same owner_type twice keeps a single resolver mapping."""

    async def _fake_resolver(_db, _clinic_id, _owner_id):  # pragma: no cover - dummy
        return None

    spec = OwnerSpec(owner_type="__test_owner_type__", resolver=_fake_resolver)
    attachment_registry.register(spec)
    attachment_registry.register(spec)  # second call must not raise
    assert attachment_registry.has("__test_owner_type__")


@pytest.mark.asyncio
async def test_registry_resolves_clinical_note_owner(
    db_session: AsyncSession, attach_setup: dict
) -> None:
    """A clinical_note owner_type resolves to the underlying patient."""
    from app.modules.clinical_notes.models import (
        NOTE_OWNER_PATIENT,
        NOTE_TYPE_DIAGNOSIS,
        ClinicalNote,
    )

    note = ClinicalNote(
        clinic_id=UUID(attach_setup["clinic_id"]),
        note_type=NOTE_TYPE_DIAGNOSIS,
        owner_type=NOTE_OWNER_PATIENT,
        owner_id=UUID(attach_setup["patient_id"]),
        body="caries on 26",
        author_id=(
            await db_session.execute(  # pick any user
                __import__("sqlalchemy").text("SELECT id FROM users LIMIT 1")
            )
        ).scalar(),
    )
    db_session.add(note)
    await db_session.commit()

    resolved = await attachment_registry.resolve_patient_id(
        db_session,
        UUID(attach_setup["clinic_id"]),
        "clinical_note",
        note.id,
    )
    assert resolved is not None
    assert str(resolved) == attach_setup["patient_id"]
