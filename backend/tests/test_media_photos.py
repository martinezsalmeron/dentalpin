"""Tests for the photo-aware media endpoints (issue #55)."""

from __future__ import annotations

import io
from uuid import uuid4

import pytest
from httpx import AsyncClient
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.models import Clinic, ClinicMembership
from app.modules.patients.models import Patient


def _png_bytes(size: tuple[int, int] = (512, 512)) -> bytes:
    """Render a tiny solid-color PNG so Pillow can decode + thumbnail it."""
    buf = io.BytesIO()
    Image.new("RGB", size, color=(255, 0, 0)).save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
async def photo_setup(
    db_session: AsyncSession, auth_headers: dict[str, str], client: AsyncClient
) -> dict:
    me = await client.get("/api/v1/auth/me", headers=auth_headers)
    user_id = me.json()["data"]["user"]["id"]

    clinic = Clinic(
        id=uuid4(),
        name="Photo Clinic",
        tax_id="B11111111",
        address={"street": "Foto St"},
        settings={"slot_duration_min": 15},
    )
    db_session.add(clinic)
    await db_session.flush()

    db_session.add(ClinicMembership(id=uuid4(), user_id=user_id, clinic_id=clinic.id, role="admin"))
    patient = Patient(
        id=uuid4(),
        clinic_id=clinic.id,
        first_name="Photo",
        last_name="Tester",
        phone="+34666112233",
    )
    db_session.add(patient)
    await db_session.commit()
    return {"clinic_id": str(clinic.id), "patient_id": str(patient.id)}


async def _upload_photo(
    client: AsyncClient,
    auth_headers: dict[str, str],
    patient_id: str,
    *,
    title: str = "intraoral",
    media_kind: str = "photo",
    media_category: str = "intraoral",
    media_subtype: str = "frontal",
) -> dict:
    response = await client.post(
        f"/api/v1/media/patients/{patient_id}/photos",
        headers=auth_headers,
        files={"file": (f"{title}.png", _png_bytes(), "image/png")},
        data={
            "title": title,
            "media_kind": media_kind,
            "media_category": media_category,
            "media_subtype": media_subtype,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]


@pytest.mark.asyncio
async def test_upload_photo_classifies_and_returns_thumb_url(
    client: AsyncClient, auth_headers: dict[str, str], photo_setup: dict
) -> None:
    photo = await _upload_photo(client, auth_headers, photo_setup["patient_id"])
    assert photo["media_kind"] == "photo"
    assert photo["media_category"] == "intraoral"
    assert photo["media_subtype"] == "frontal"
    # URLs are present for thumbnailable images
    assert photo["thumb_url"], photo
    assert photo["medium_url"]
    assert photo["full_url"]


@pytest.mark.asyncio
async def test_invalid_subtype_rejected(
    client: AsyncClient, auth_headers: dict[str, str], photo_setup: dict
) -> None:
    response = await client.post(
        f"/api/v1/media/patients/{photo_setup['patient_id']}/photos",
        headers=auth_headers,
        files={"file": ("bad.png", _png_bytes(), "image/png")},
        data={
            "title": "bad",
            "media_kind": "photo",
            "media_category": "intraoral",
            "media_subtype": "panoramic",  # belongs to xray, not intraoral
        },
    )
    assert response.status_code == 400
    body = response.json()
    assert "Invalid media_subtype" in body.get("detail", body.get("message", ""))


@pytest.mark.asyncio
async def test_xray_kind_requires_xray_category(
    client: AsyncClient, auth_headers: dict[str, str], photo_setup: dict
) -> None:
    response = await client.post(
        f"/api/v1/media/patients/{photo_setup['patient_id']}/photos",
        headers=auth_headers,
        files={"file": ("rx.png", _png_bytes(), "image/png")},
        data={
            "title": "rx",
            "media_kind": "xray",
            "media_category": "intraoral",  # invalid combo
            "media_subtype": "panoramic",
        },
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_gallery_filters_by_category(
    client: AsyncClient, auth_headers: dict[str, str], photo_setup: dict
) -> None:
    patient_id = photo_setup["patient_id"]
    await _upload_photo(
        client,
        auth_headers,
        patient_id,
        title="intra",
        media_category="intraoral",
        media_subtype="frontal",
    )
    await _upload_photo(
        client,
        auth_headers,
        patient_id,
        title="extra",
        media_category="extraoral",
        media_subtype="smile",
    )

    listed = await client.get(
        f"/api/v1/media/patients/{patient_id}/photos?media_category=intraoral",
        headers=auth_headers,
    )
    assert listed.status_code == 200
    body = listed.json()
    assert body["total"] == 1
    assert body["data"][0]["media_category"] == "intraoral"


@pytest.mark.asyncio
async def test_pair_documents_same_patient(
    client: AsyncClient, auth_headers: dict[str, str], photo_setup: dict
) -> None:
    patient_id = photo_setup["patient_id"]
    a = await _upload_photo(
        client,
        auth_headers,
        patient_id,
        title="before",
        media_category="clinical",
        media_subtype="before",
    )
    b = await _upload_photo(
        client,
        auth_headers,
        patient_id,
        title="after",
        media_category="clinical",
        media_subtype="after",
    )

    response = await client.post(
        f"/api/v1/media/documents/{a['id']}/pair/{b['id']}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    paired = response.json()["data"]
    assert paired["paired_document_id"] == b["id"]


@pytest.mark.asyncio
async def test_pair_rejects_cross_patient(
    db_session: AsyncSession,
    client: AsyncClient,
    auth_headers: dict[str, str],
    photo_setup: dict,
) -> None:
    patient_id = photo_setup["patient_id"]
    a = await _upload_photo(client, auth_headers, patient_id, title="a")

    other_patient = Patient(
        id=uuid4(),
        clinic_id=photo_setup["clinic_id"],
        first_name="Other",
        last_name="Patient",
    )
    db_session.add(other_patient)
    await db_session.commit()

    b = await _upload_photo(
        client,
        auth_headers,
        str(other_patient.id),
        title="b",
    )

    response = await client.post(
        f"/api/v1/media/documents/{a['id']}/pair/{b['id']}",
        headers=auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_unpair_clears_both_sides(
    client: AsyncClient, auth_headers: dict[str, str], photo_setup: dict
) -> None:
    patient_id = photo_setup["patient_id"]
    a = await _upload_photo(client, auth_headers, patient_id, title="a")
    b = await _upload_photo(client, auth_headers, patient_id, title="b")

    await client.post(f"/api/v1/media/documents/{a['id']}/pair/{b['id']}", headers=auth_headers)
    response = await client.delete(f"/api/v1/media/documents/{a['id']}/pair", headers=auth_headers)
    assert response.status_code == 200

    fetched_b = await client.get(f"/api/v1/media/documents/{b['id']}", headers=auth_headers)
    assert fetched_b.json()["data"]["paired_document_id"] is None


@pytest.mark.asyncio
async def test_patch_photo_metadata(
    client: AsyncClient, auth_headers: dict[str, str], photo_setup: dict
) -> None:
    photo = await _upload_photo(
        client,
        auth_headers,
        photo_setup["patient_id"],
        media_category="clinical",
        media_subtype="reference",
    )
    response = await client.patch(
        f"/api/v1/media/documents/{photo['id']}/photo-metadata",
        headers=auth_headers,
        json={"media_subtype": "before", "tags": ["composite", "tooth-26"]},
    )
    assert response.status_code == 200
    updated = response.json()["data"]
    assert updated["media_subtype"] == "before"
    assert updated["tags"] == ["composite", "tooth-26"]
