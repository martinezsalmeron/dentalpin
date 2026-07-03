"""Fiscal uniqueness backstop for issued invoices (bil_0005, issue #93).

Duplicate invoice numbers / duplicate per-series sequentials must be
rejected at the DB level; drafts (NULL identifiers) must still be free to
coexist.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.models import Clinic, User
from app.modules.billing.models import Invoice, InvoiceSeries
from app.modules.patients.models import Patient


async def _make_series(db: AsyncSession, clinic: Clinic):
    series = InvoiceSeries(
        id=uuid4(),
        clinic_id=clinic.id,
        prefix="FAC",
        series_type="invoice",
    )
    db.add(series)
    await db.flush()
    return series.id


@pytest_asyncio.fixture
async def test_user_id(test_clinic: Clinic, db_session: AsyncSession):
    """ID of the single user created by the ``auth_headers`` fixture
    (pulled in transitively via ``test_clinic``)."""
    user = (await db_session.execute(select(User))).scalars().first()
    return user.id


def _issued_invoice(
    clinic: Clinic,
    patient: Patient,
    user_id,
    *,
    number: str | None,
    series_id=None,
    sequential: int | None = None,
) -> Invoice:
    return Invoice(
        id=uuid4(),
        clinic_id=clinic.id,
        patient_id=patient.id,
        invoice_number=number,
        series_id=series_id,
        sequential_number=sequential,
        status="draft" if number is None else "issued",
        issue_date=None if number is None else date.today(),
        billing_name="X",
        billing_tax_id="A28000000",
        subtotal=Decimal("100"),
        total=Decimal("100"),
        created_by=user_id,
        issued_by=None if number is None else user_id,
    )


@pytest.mark.asyncio
async def test_duplicate_invoice_number_rejected(
    test_clinic: Clinic,
    test_patient: Patient,
    test_user_id,
    db_session: AsyncSession,
) -> None:
    db_session.add(_issued_invoice(test_clinic, test_patient, test_user_id, number="FAC-2026-0001"))
    await db_session.flush()

    db_session.add(_issued_invoice(test_clinic, test_patient, test_user_id, number="FAC-2026-0001"))
    with pytest.raises(IntegrityError):
        await db_session.flush()


@pytest.mark.asyncio
async def test_duplicate_series_sequential_rejected(
    test_clinic: Clinic,
    test_patient: Patient,
    test_user_id,
    db_session: AsyncSession,
) -> None:
    series_id = await _make_series(db_session, test_clinic)
    db_session.add(
        _issued_invoice(
            test_clinic,
            test_patient,
            test_user_id,
            number="FAC-2026-0100",
            series_id=series_id,
            sequential=100,
        )
    )
    await db_session.flush()

    # Same series + sequential but a different rendered number must still
    # be rejected — the sequential is the gap-control fiscal invariant.
    db_session.add(
        _issued_invoice(
            test_clinic,
            test_patient,
            test_user_id,
            number="FAC-2026-9999",
            series_id=series_id,
            sequential=100,
        )
    )
    with pytest.raises(IntegrityError):
        await db_session.flush()


@pytest.mark.asyncio
async def test_multiple_drafts_coexist(
    test_clinic: Clinic,
    test_patient: Patient,
    test_user_id,
    db_session: AsyncSession,
) -> None:
    # Drafts carry NULL number/series/sequential — the partial index must
    # not treat two NULL rows as a collision.
    db_session.add(_issued_invoice(test_clinic, test_patient, test_user_id, number=None))
    db_session.add(_issued_invoice(test_clinic, test_patient, test_user_id, number=None))
    await db_session.flush()  # no IntegrityError
