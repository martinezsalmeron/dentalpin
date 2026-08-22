"""GST reconciliation report: totals reconcile against persisted splits."""

from __future__ import annotations

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalog.models import TreatmentCatalogItem, TreatmentCategory, VatType
from app.modules.india_gst.models import IndiaGstSettings
from app.modules.patients.models import Patient


async def _issue_invoice(
    client: AsyncClient,
    auth_headers,
    db_session: AsyncSession,
    clinic_id,
    patient_id,
    *,
    place_of_supply: str,
) -> str:
    vat = VatType(clinic_id=clinic_id, names={"en": "GST 18%"}, rate=18.0)
    category = TreatmentCategory(
        clinic_id=clinic_id,
        key=f"restorative-{place_of_supply}",
        names={"en": "Restorative"},
    )
    db_session.add_all([vat, category])
    await db_session.flush()
    item = TreatmentCatalogItem(
        clinic_id=clinic_id,
        category_id=category.id,
        internal_code=f"CROWN-{place_of_supply}",
        names={"en": "Crown"},
        default_price="1000.00",
        vat_type_id=vat.id,
    )
    db_session.add(item)
    await db_session.commit()

    r = await client.post(
        "/api/v1/billing/invoices", json={"patient_id": str(patient_id)}, headers=auth_headers
    )
    invoice_id = r.json()["data"]["id"]
    await client.post(
        f"/api/v1/billing/invoices/{invoice_id}/items",
        json={
            "description": "Crown",
            "catalog_item_id": str(item.id),
            "unit_price": "1000.00",
            "quantity": 1,
            "vat_type_id": str(vat.id),
        },
        headers=auth_headers,
    )
    await client.put(
        f"/api/v1/india_gst/invoices/{invoice_id}",
        json={"place_of_supply": place_of_supply},
        headers=auth_headers,
    )
    r = await client.post(
        f"/api/v1/billing/invoices/{invoice_id}/issue", json={}, headers=auth_headers
    )
    assert r.status_code == 200, r.text
    return invoice_id


async def test_summary_totals_reconcile_intra_and_inter(
    client: AsyncClient,
    auth_headers,
    db_session: AsyncSession,
    india_gst_settings: IndiaGstSettings,
    test_patient: Patient,
):
    await _issue_invoice(
        client,
        auth_headers,
        db_session,
        india_gst_settings.clinic_id,
        test_patient.id,
        place_of_supply="33",
    )
    await _issue_invoice(
        client,
        auth_headers,
        db_session,
        india_gst_settings.clinic_id,
        test_patient.id,
        place_of_supply="29",
    )

    r = await client.get("/api/v1/india_gst/reports/summary", headers=auth_headers)
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    assert data["cgst_total"] == "90.00"
    assert data["sgst_total"] == "90.00"
    assert data["igst_total"] == "180.00"
    assert data["invoice_count"] == 2
    assert data["credit_note_count"] == 0

    r = await client.get("/api/v1/india_gst/reports/transactions", headers=auth_headers)
    assert len(r.json()["data"]) == 2

    r = await client.get("/api/v1/india_gst/reports/export", headers=auth_headers)
    assert r.status_code == 200
    assert b"gst_document_number" in r.content
