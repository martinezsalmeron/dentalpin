"""IndiaGstModule.uninstall() blocking guard — direct unit test.

Complements ``test_uninstall_roundtrip.py`` (which exercises the real
Alembic branch-scoped downgrade) with a fast, DB-only check of the
*business* guard: uninstall must refuse once GST data exists for any
non-draft invoice, not just once an e-invoice reaches ``generated``.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.billing.models import Invoice, InvoiceItem
from app.modules.india_gst import IndiaGstModule
from app.modules.india_gst.models import IndiaGstInvoiceItem, IndiaGstSettings
from app.modules.patients.models import Patient


@dataclass
class _FakeLogger:
    def info(self, *_args, **_kwargs):
        pass


@dataclass
class _FakeCtx:
    db: AsyncSession
    logger: _FakeLogger


async def _issued_invoice_with_gst_row(
    db_session: AsyncSession, clinic_id, patient_id, user_id
) -> None:
    invoice = Invoice(
        id=uuid4(),
        clinic_id=clinic_id,
        patient_id=patient_id,
        status="issued",
        billing_name="Test Patient",
        created_by=user_id,
    )
    db_session.add(invoice)
    await db_session.flush()
    item = InvoiceItem(
        id=uuid4(),
        clinic_id=clinic_id,
        invoice_id=invoice.id,
        description="Crown",
        unit_price="1000.00",
        quantity=1,
    )
    db_session.add(item)
    await db_session.flush()
    db_session.add(
        IndiaGstInvoiceItem(
            clinic_id=clinic_id,
            invoice_item_id=item.id,
            tax_type="intra",
            cgst_amount="90.00",
            sgst_amount="90.00",
        )
    )
    await db_session.commit()


async def test_uninstall_blocked_when_issued_invoice_has_gst_data(
    client, auth_headers, db_session: AsyncSession, india_gst_settings: IndiaGstSettings
):
    user_id = (await client.get("/api/v1/auth/me", headers=auth_headers)).json()["data"]["user"][
        "id"
    ]
    patient = Patient(
        id=uuid4(), clinic_id=india_gst_settings.clinic_id, first_name="A", last_name="B"
    )
    db_session.add(patient)
    await db_session.flush()
    await _issued_invoice_with_gst_row(
        db_session, india_gst_settings.clinic_id, patient.id, user_id
    )

    ctx = _FakeCtx(db=db_session, logger=_FakeLogger())
    module = IndiaGstModule()
    with pytest.raises(RuntimeError, match="issued invoices"):
        await module.uninstall(ctx)
    # Blocked uninstall must not have unregistered the hook.
    from app.modules.billing.hooks import BillingHookRegistry

    assert BillingHookRegistry.is_registered("IN")


async def test_uninstall_allowed_with_no_issued_gst_invoices(
    db_session: AsyncSession, india_gst_settings: IndiaGstSettings
):
    from app.modules.billing.hooks import BillingHookRegistry

    ctx = _FakeCtx(db=db_session, logger=_FakeLogger())
    module = IndiaGstModule()
    try:
        # No exception — settings-only clinics (no issued GST invoices
        # yet) must remain freely uninstallable.
        await module.uninstall(ctx)
        assert not BillingHookRegistry.is_registered("IN")
    finally:
        # Re-register so later tests in this session still see the hook
        # (module-load-time registration only happens once per process).
        from app.modules.india_gst.hook import IndiaGstHook

        BillingHookRegistry.register(IndiaGstHook())
