"""Credit-note GST reversal — sign-safety and FY-scoped CN numbering."""

from __future__ import annotations

import uuid

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.billing.models import InvoiceItem
from app.modules.catalog.models import TreatmentCatalogItem, TreatmentCategory, VatType
from app.modules.india_gst.models import IndiaGstInvoiceItem, IndiaGstSettings
from app.modules.patients.models import Patient


async def _issue_intra_state_invoice(
    client: AsyncClient, auth_headers, db_session: AsyncSession, clinic_id, patient_id
) -> str:
    vat = VatType(clinic_id=clinic_id, names={"en": "GST 18%"}, rate=18.0)
    category = TreatmentCategory(
        clinic_id=clinic_id, key="restorative", names={"en": "Restorative"}
    )
    db_session.add_all([vat, category])
    await db_session.flush()
    item = TreatmentCatalogItem(
        clinic_id=clinic_id,
        category_id=category.id,
        internal_code="RCT-01",
        names={"en": "Root canal"},
        default_price="9000.00",
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
            "description": "Root canal",
            "catalog_item_id": str(item.id),
            "unit_price": "9000.00",
            "quantity": 1,
            "vat_type_id": str(vat.id),
        },
        headers=auth_headers,
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
    return invoice_id


async def test_credit_note_reverses_cgst_sgst_with_correct_sign(
    client: AsyncClient,
    auth_headers,
    db_session: AsyncSession,
    india_gst_settings: IndiaGstSettings,
    test_patient: Patient,
):
    invoice_id = await _issue_intra_state_invoice(
        client, auth_headers, db_session, india_gst_settings.clinic_id, test_patient.id
    )

    r = await client.post(
        f"/api/v1/billing/invoices/{invoice_id}/credit-note",
        json={"reason": "Treatment cancelled"},
        headers=auth_headers,
    )
    assert r.status_code == 201, r.text
    credit_note_id = r.json()["data"]["id"]

    r = await client.post(
        f"/api/v1/billing/invoices/{credit_note_id}/issue", json={}, headers=auth_headers
    )
    assert r.status_code == 200, r.text
    cd = r.json()["data"]["compliance_data"]["IN"]
    assert cd["cgst_total"] == "-810.00"
    assert cd["sgst_total"] == "-810.00"
    assert cd["gst_document_number"].startswith("CN/FY")

    # Per-line reconciliation: the persisted split must still sum
    # exactly to the credit note's own (already-negative) line_tax.
    rows = await db_session.execute(
        select(IndiaGstInvoiceItem, InvoiceItem.line_tax)
        .join(InvoiceItem, InvoiceItem.id == IndiaGstInvoiceItem.invoice_item_id)
        .where(InvoiceItem.invoice_id == uuid.UUID(credit_note_id))
    )
    for gst_row, line_tax in rows.all():
        assert gst_row.cgst_amount + gst_row.sgst_amount == line_tax
        assert line_tax < 0


async def test_credit_note_links_original_reference(
    client: AsyncClient,
    auth_headers,
    db_session: AsyncSession,
    india_gst_settings: IndiaGstSettings,
    test_patient: Patient,
):
    invoice_id = await _issue_intra_state_invoice(
        client, auth_headers, db_session, india_gst_settings.clinic_id, test_patient.id
    )
    r = await client.get(f"/api/v1/billing/invoices/{invoice_id}", headers=auth_headers)
    original_number = r.json()["data"]["compliance_data"]["IN"]["gst_document_number"]

    r = await client.post(
        f"/api/v1/billing/invoices/{invoice_id}/credit-note",
        json={"reason": "Refund"},
        headers=auth_headers,
    )
    credit_note_id = r.json()["data"]["id"]
    r = await client.post(
        f"/api/v1/billing/invoices/{credit_note_id}/issue", json={}, headers=auth_headers
    )
    cd = r.json()["data"]["compliance_data"]["IN"]
    assert cd["original_reference"] == original_number
