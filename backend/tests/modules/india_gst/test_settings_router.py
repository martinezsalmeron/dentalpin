"""Settings endpoint: GSTIN validation, permission boundary."""

from __future__ import annotations

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.models import Clinic


async def test_get_settings_creates_default_row(
    client: AsyncClient, auth_headers, india_gst_clinic: Clinic
):
    r = await client.get("/api/v1/india_gst/settings", headers=auth_headers)
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    assert data["registration_type"] == "regular"
    assert data["gstin"] is None


async def test_update_settings_accepts_valid_gstin(
    client: AsyncClient, auth_headers, india_gst_clinic: Clinic
):
    r = await client.put(
        "/api/v1/india_gst/settings",
        json={"gstin": "33ABCDE1234F1Z5", "clinic_state": "33"},
        headers=auth_headers,
    )
    assert r.status_code == 200, r.text
    assert r.json()["data"]["gstin"] == "33ABCDE1234F1Z5"
    assert r.json()["data"]["clinic_state_name"] == "Tamil Nadu"


async def test_update_settings_rejects_invalid_gstin(
    client: AsyncClient, auth_headers, india_gst_clinic: Clinic
):
    r = await client.put(
        "/api/v1/india_gst/settings", json={"gstin": "not-a-gstin"}, headers=auth_headers
    )
    assert r.status_code == 400


async def test_catalog_defaults_flags_missing_sac(
    client: AsyncClient, auth_headers, db_session: AsyncSession, india_gst_clinic: Clinic
):
    from app.modules.catalog.models import TreatmentCatalogItem, TreatmentCategory

    category = TreatmentCategory(
        clinic_id=india_gst_clinic.id, key="diagnostic", names={"en": "Diagnostic"}
    )
    db_session.add(category)
    await db_session.flush()
    item = TreatmentCatalogItem(
        clinic_id=india_gst_clinic.id,
        category_id=category.id,
        internal_code="XRAY-01",
        names={"en": "X-Ray"},
    )
    db_session.add(item)
    await db_session.commit()

    r = await client.get("/api/v1/india_gst/catalog-defaults", headers=auth_headers)
    assert r.status_code == 200, r.text
    missing_ids = [m["catalog_item_id"] for m in r.json()["data"]["missing"]]
    assert str(item.id) in missing_ids

    r = await client.put(
        f"/api/v1/india_gst/catalog-defaults/{item.id}",
        json={"sac_code": "999312"},
        headers=auth_headers,
    )
    assert r.status_code == 200, r.text

    r = await client.get("/api/v1/india_gst/catalog-defaults", headers=auth_headers)
    missing_ids = [m["catalog_item_id"] for m in r.json()["data"]["missing"]]
    assert str(item.id) not in missing_ids


async def _make_catalog_item(
    db_session: AsyncSession, clinic: Clinic, *, code: str, names: dict
) -> object:
    from app.modules.catalog.models import TreatmentCatalogItem, TreatmentCategory

    category = TreatmentCategory(clinic_id=clinic.id, key=f"cat-{code}", names={"en": "Cat"})
    db_session.add(category)
    await db_session.flush()
    item = TreatmentCatalogItem(
        clinic_id=clinic.id,
        category_id=category.id,
        internal_code=code,
        names=names,
    )
    db_session.add(item)
    await db_session.commit()
    return item


async def test_missing_sac_ships_all_translations_and_english_fallback(
    client: AsyncClient, auth_headers, db_session: AsyncSession, india_gst_clinic: Clinic
):
    """The client localises, not the server.

    Regression: ``name`` used to be resolved Spanish-first, so an
    English- or Tamil-speaking user saw Spanish treatment names on the
    India GST settings page.
    """
    item = await _make_catalog_item(
        db_session,
        india_gst_clinic,
        code="CROWN-01",
        names={"en": "Crown", "es": "Corona", "ta": "கிரீடம்"},
    )

    r = await client.get("/api/v1/india_gst/catalog-defaults", headers=auth_headers)
    assert r.status_code == 200, r.text
    row = next(m for m in r.json()["data"]["missing"] if m["catalog_item_id"] == str(item.id))
    assert row["names"] == {"en": "Crown", "es": "Corona", "ta": "கிரீடம்"}
    assert row["name"] == "Crown"


async def test_autoconfigure_fills_missing_sac_without_touching_configured(
    client: AsyncClient, auth_headers, db_session: AsyncSession, india_gst_clinic: Clinic
):
    already = await _make_catalog_item(
        db_session, india_gst_clinic, code="PROPH-01", names={"en": "Cleaning"}
    )
    missing = await _make_catalog_item(
        db_session, india_gst_clinic, code="ENDO-01", names={"en": "Root canal"}
    )

    r = await client.put(
        f"/api/v1/india_gst/catalog-defaults/{already.id}",
        json={"sac_code": "999311"},
        headers=auth_headers,
    )
    assert r.status_code == 200, r.text

    r = await client.post("/api/v1/india_gst/catalog-defaults/autoconfigure", headers=auth_headers)
    assert r.status_code == 200, r.text
    assert r.json()["data"]["sac_code"] == "999312"
    assert r.json()["data"]["configured_count"] >= 1

    r = await client.get("/api/v1/india_gst/catalog-defaults", headers=auth_headers)
    data = r.json()["data"]
    assert data["missing"] == []
    by_item = {c["catalog_item_id"]: c["sac_code"] for c in data["configured"]}
    assert by_item[str(missing.id)] == "999312"
    # The accountant's explicit choice survives autoconfigure.
    assert by_item[str(already.id)] == "999311"

    # Idempotent: a second run has nothing left to do.
    r = await client.post("/api/v1/india_gst/catalog-defaults/autoconfigure", headers=auth_headers)
    assert r.json()["data"]["configured_count"] == 0
