"""VerifactuHook gates and auto-regenerate for billing-party edits."""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.models import Clinic, ClinicMembership, User
from app.modules.billing.models import Invoice, InvoiceItem
from app.modules.patients.models import Patient
from app.modules.verifactu.hook import VerifactuHook
from app.modules.verifactu.models import VerifactuRecord, VerifactuSettings


async def _setup(db: AsyncSession) -> tuple[Clinic, User, Patient, Invoice, VerifactuRecord]:
    clinic = Clinic(
        id=uuid4(),
        name="Clinic",
        legal_name="Clínica Demo S.L.",
        tax_id="A28000000",
        settings={"country": "ES"},
    )
    db.add(clinic)
    user = User(
        id=uuid4(),
        email=f"u-{uuid4()}@x.test",
        password_hash="x",
        first_name="A",
        last_name="B",
        is_active=True,
    )
    db.add(user)
    db.add(
        ClinicMembership(
            id=uuid4(), user_id=user.id, clinic_id=clinic.id, role="admin"
        )
    )
    patient = Patient(id=uuid4(), clinic_id=clinic.id, first_name="P", last_name="X")
    db.add(patient)
    db.add(
        VerifactuSettings(
            id=uuid4(),
            clinic_id=clinic.id,
            enabled=True,
            environment="test",
            numero_instalacion=str(uuid4()),
            producer_nif="B98765431",
            producer_name="DentalPin Producer",
            producer_id_sistema="DP",
            producer_version="0.1.0",
            declaracion_responsable_signed_at=datetime.now(UTC),
            declaracion_responsable_signed_by=user.id,
        )
    )
    invoice = Invoice(
        id=uuid4(),
        clinic_id=clinic.id,
        patient_id=patient.id,
        invoice_number="FAC-2026-0001",
        sequential_number=1,
        status="issued",
        issue_date=date.today(),
        billing_name="Cliente",
        billing_tax_id="B12345678",  # bad NIF — will be the cause of rejection
        subtotal=Decimal("100"),
        total=Decimal("100"),
        balance_due=Decimal("100"),
        created_by=user.id,
        issued_by=user.id,
    )
    db.add(invoice)
    await db.flush()
    db.add(
        InvoiceItem(
            id=uuid4(),
            clinic_id=clinic.id,
            invoice_id=invoice.id,
            description="Servicio",
            unit_price=Decimal("100"),
            quantity=1,
            vat_rate=0.0,
            line_subtotal=Decimal("100"),
            line_tax=Decimal("0"),
            line_total=Decimal("100"),
            display_order=0,
        )
    )
    await db.flush()
    await db.refresh(invoice)

    hook = VerifactuHook()
    payload = await hook.on_invoice_issued(invoice, db)
    record = await db.get(VerifactuRecord, payload["ES"]["record_id"])
    assert record is not None
    return clinic, user, patient, invoice, record


@pytest.mark.asyncio
async def test_can_edit_billing_party_blocked_when_accepted(
    db_session: AsyncSession,
) -> None:
    _, _, _, invoice, record = await _setup(db_session)
    record.state = "accepted"
    await db_session.flush()

    hook = VerifactuHook()
    allowed, reason = await hook.can_edit_billing_party(invoice, db_session)
    assert allowed is False
    assert reason and "rectificativa" in reason.lower()


@pytest.mark.asyncio
async def test_can_edit_billing_party_allowed_when_rejected(
    db_session: AsyncSession,
) -> None:
    _, _, _, invoice, record = await _setup(db_session)
    record.state = "rejected"
    record.aeat_estado_registro = "Incorrecto"
    await db_session.flush()

    hook = VerifactuHook()
    allowed, reason = await hook.can_edit_billing_party(invoice, db_session)
    assert allowed is True
    assert reason is None


@pytest.mark.asyncio
async def test_regenerate_after_party_change_noop_when_no_record(
    db_session: AsyncSession,
) -> None:
    clinic = Clinic(
        id=uuid4(), name="X", legal_name="X", tax_id="A28000000", settings={"country": "ES"}
    )
    db_session.add(clinic)
    user = User(
        id=uuid4(),
        email=f"u-{uuid4()}@x.test",
        password_hash="x",
        first_name="A",
        last_name="B",
        is_active=True,
    )
    db_session.add(user)
    patient = Patient(id=uuid4(), clinic_id=clinic.id, first_name="P", last_name="X")
    db_session.add(patient)
    invoice = Invoice(
        id=uuid4(),
        clinic_id=clinic.id,
        patient_id=patient.id,
        invoice_number="FAC-2026-0001",
        status="draft",
        subtotal=Decimal("0"),
        total=Decimal("0"),
        balance_due=Decimal("0"),
        created_by=user.id,
    )
    db_session.add(invoice)
    await db_session.flush()

    hook = VerifactuHook()
    result = await hook.regenerate_after_party_change(invoice, db_session)
    assert result == {}
