"""E-invoice retry is honest: no provider exists in v1, so always 409."""

from __future__ import annotations

from uuid import uuid4

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.india_gst.models import IndiaGstEinvoiceSubmission, IndiaGstSettings


async def test_retry_returns_409_never_fabricates_success(
    client: AsyncClient,
    auth_headers,
    db_session: AsyncSession,
    india_gst_settings: IndiaGstSettings,
):
    from app.modules.billing.models import Invoice
    from app.modules.patients.models import Patient

    user_id = (await client.get("/api/v1/auth/me", headers=auth_headers)).json()["data"]["user"][
        "id"
    ]
    patient = Patient(
        id=uuid4(), clinic_id=india_gst_settings.clinic_id, first_name="A", last_name="B"
    )
    db_session.add(patient)
    await db_session.flush()
    invoice = Invoice(
        id=uuid4(),
        clinic_id=india_gst_settings.clinic_id,
        patient_id=patient.id,
        status="issued",
        billing_name="A B",
        created_by=user_id,
    )
    db_session.add(invoice)
    submission = IndiaGstEinvoiceSubmission(
        clinic_id=india_gst_settings.clinic_id, invoice_id=invoice.id, state="not_configured"
    )
    db_session.add(submission)
    await db_session.commit()

    r = await client.post(
        f"/api/v1/india_gst/invoices/{invoice.id}/einvoice/retry", headers=auth_headers
    )
    assert r.status_code == 409
    assert "provider" in r.json()["message"].lower()

    await db_session.refresh(submission)
    assert submission.state == "not_configured"
