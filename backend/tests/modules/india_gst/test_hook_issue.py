"""Integration tests for IndiaGstHook via the real billing issue endpoint."""

from __future__ import annotations

from uuid import UUID

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.catalog.models import TreatmentCatalogItem, TreatmentCategory, VatType
from app.modules.india_gst.models import IndiaGstInvoiceItem, IndiaGstSettings
from app.modules.patients.models import Patient


async def _make_catalog_item(db_session: AsyncSession, clinic_id, *, rate: float) -> tuple:
    vat = VatType(clinic_id=clinic_id, names={"en": f"GST {rate}%"}, rate=rate)
    category = TreatmentCategory(
        clinic_id=clinic_id, key="restorative", names={"en": "Restorative"}
    )
    db_session.add_all([vat, category])
    await db_session.flush()
    item = TreatmentCatalogItem(
        clinic_id=clinic_id,
        category_id=category.id,
        internal_code="CROWN-01",
        names={"en": "Crown"},
        default_price="1000.00",
        vat_type_id=vat.id,
    )
    db_session.add(item)
    await db_session.commit()
    return vat, item


async def _create_and_add_item(
    client: AsyncClient, auth_headers, patient_id, vat_id, catalog_item_id
) -> tuple[str, str]:
    r = await client.post(
        "/api/v1/billing/invoices", json={"patient_id": str(patient_id)}, headers=auth_headers
    )
    assert r.status_code == 201, r.text
    invoice_id = r.json()["data"]["id"]

    r = await client.post(
        f"/api/v1/billing/invoices/{invoice_id}/items",
        json={
            "description": "Crown",
            "catalog_item_id": str(catalog_item_id),
            "unit_price": "1000.00",
            "quantity": 1,
            "vat_type_id": str(vat_id),
        },
        headers=auth_headers,
    )
    assert r.status_code == 201, r.text
    item_id = r.json()["data"]["id"]
    return invoice_id, item_id


async def test_intra_state_issue_produces_cgst_sgst_rows(
    client: AsyncClient,
    auth_headers,
    db_session: AsyncSession,
    india_gst_settings: IndiaGstSettings,
    test_patient: Patient,
):
    vat, item = await _make_catalog_item(db_session, india_gst_settings.clinic_id, rate=18.0)
    invoice_id, item_id = await _create_and_add_item(
        client, auth_headers, test_patient.id, vat.id, item.id
    )

    r = await client.put(
        f"/api/v1/india_gst/invoices/{invoice_id}",
        json={"place_of_supply": "33"},  # same as clinic_state (Tamil Nadu) -> intra
        headers=auth_headers,
    )
    assert r.status_code == 200, r.text

    r = await client.post(
        f"/api/v1/billing/invoices/{invoice_id}/issue", json={}, headers=auth_headers
    )
    assert r.status_code == 200, r.text
    cd = r.json()["data"]["compliance_data"]["IN"]
    assert cd["tax_type"] == "intra"
    assert cd["cgst_total"] == "90.00"
    assert cd["sgst_total"] == "90.00"
    assert cd["einvoice_state"] == "not_required"
    assert cd["gst_document_number"]

    rows = await db_session.execute(
        select(IndiaGstInvoiceItem).where(IndiaGstInvoiceItem.invoice_item_id == UUID(item_id))
    )
    row = rows.scalar_one()
    assert row.tax_type == "intra"
    assert row.cgst_amount == row.sgst_amount


async def test_inter_state_issue_produces_igst_only(
    client: AsyncClient,
    auth_headers,
    db_session: AsyncSession,
    india_gst_settings: IndiaGstSettings,
    test_patient: Patient,
):
    vat, item = await _make_catalog_item(db_session, india_gst_settings.clinic_id, rate=18.0)
    invoice_id, _ = await _create_and_add_item(
        client, auth_headers, test_patient.id, vat.id, item.id
    )

    await client.put(
        f"/api/v1/india_gst/invoices/{invoice_id}",
        json={"place_of_supply": "29"},  # Karnataka, differs from clinic_state 33 -> inter
        headers=auth_headers,
    )

    r = await client.post(
        f"/api/v1/billing/invoices/{invoice_id}/issue", json={}, headers=auth_headers
    )
    assert r.status_code == 200, r.text
    cd = r.json()["data"]["compliance_data"]["IN"]
    assert cd["tax_type"] == "inter"
    assert cd["igst_total"] == "180.00"
    assert cd["cgst_total"] == "0.00"
    assert cd["sgst_total"] == "0.00"


async def test_missing_place_of_supply_blocks_issue(
    client: AsyncClient,
    auth_headers,
    db_session: AsyncSession,
    india_gst_settings: IndiaGstSettings,
    test_patient: Patient,
):
    vat, item = await _make_catalog_item(db_session, india_gst_settings.clinic_id, rate=18.0)
    invoice_id, _ = await _create_and_add_item(
        client, auth_headers, test_patient.id, vat.id, item.id
    )

    r = await client.post(
        f"/api/v1/billing/invoices/{invoice_id}/issue", json={}, headers=auth_headers
    )
    assert r.status_code == 400
    assert "place of supply" in r.json()["message"].lower()


async def test_non_regular_registration_issues_with_no_gst_rows(
    client: AsyncClient,
    auth_headers,
    db_session: AsyncSession,
    india_gst_settings: IndiaGstSettings,
    test_patient: Patient,
):
    india_gst_settings.registration_type = "unregistered"
    db_session.add(india_gst_settings)
    await db_session.commit()

    vat, item = await _make_catalog_item(db_session, india_gst_settings.clinic_id, rate=18.0)
    invoice_id, item_id = await _create_and_add_item(
        client, auth_headers, test_patient.id, vat.id, item.id
    )

    r = await client.post(
        f"/api/v1/billing/invoices/{invoice_id}/issue", json={}, headers=auth_headers
    )
    assert r.status_code == 200, r.text
    assert not (r.json()["data"].get("compliance_data") or {}).get("IN")

    rows = await db_session.execute(
        select(IndiaGstInvoiceItem).where(IndiaGstInvoiceItem.invoice_item_id == UUID(item_id))
    )
    assert rows.scalar_one_or_none() is None


async def test_re_issuing_hook_path_does_not_duplicate_rows(
    client: AsyncClient,
    auth_headers,
    db_session: AsyncSession,
    india_gst_settings: IndiaGstSettings,
    test_patient: Patient,
):
    """Calling the hook's ``on_invoice_issued`` twice against the same
    invoice_item_id must upsert, never insert a second row."""
    from app.modules.billing.models import Invoice
    from app.modules.india_gst.hook import IndiaGstHook

    vat, item = await _make_catalog_item(db_session, india_gst_settings.clinic_id, rate=18.0)
    invoice_id, item_id = await _create_and_add_item(
        client, auth_headers, test_patient.id, vat.id, item.id
    )
    await client.put(
        f"/api/v1/india_gst/invoices/{invoice_id}",
        json={"place_of_supply": "33"},
        headers=auth_headers,
    )
    r = await client.post(
        f"/api/v1/billing/invoices/{invoice_id}/issue", json={}, headers=auth_headers
    )
    assert r.status_code == 200, r.text

    invoice_q = await db_session.execute(
        select(Invoice).where(Invoice.id == UUID(invoice_id)).options(selectinload(Invoice.items))
    )
    invoice = invoice_q.scalar_one()
    hook = IndiaGstHook()
    await hook.on_invoice_issued(invoice, db_session)
    await db_session.commit()

    rows = await db_session.execute(
        select(IndiaGstInvoiceItem).where(IndiaGstInvoiceItem.invoice_item_id == UUID(item_id))
    )
    assert len(rows.scalars().all()) == 1
