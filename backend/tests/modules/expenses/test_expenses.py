"""expenses: happy-path CRUD + tenant isolation."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.models import Clinic
from app.modules.expenses.schemas import ExpenseCreate, ExpenseUpdate
from app.modules.expenses.service import ExpenseService


@pytest.mark.asyncio
async def test_create_list_update_delete_happy_path(db_session: AsyncSession, test_clinic: Clinic):
    expense = await ExpenseService.create_expense(
        db_session,
        test_clinic.id,
        ExpenseCreate(category="rent", amount=Decimal("1200.00"), expense_date=date(2026, 8, 1)),
        created_by=None,
    )
    assert expense.category == "rent"
    assert expense.amount == Decimal("1200.00")

    rows, total = await ExpenseService.list_expenses(db_session, test_clinic.id)
    assert total == 1
    assert rows[0].id == expense.id

    updated = await ExpenseService.update_expense(
        db_session, test_clinic.id, expense.id, ExpenseUpdate(amount=Decimal("1250.00"))
    )
    assert updated.amount == Decimal("1250.00")
    assert updated.category == "rent"  # unset fields untouched

    await ExpenseService.delete_expense(db_session, test_clinic.id, expense.id)

    rows, total = await ExpenseService.list_expenses(db_session, test_clinic.id)
    assert total == 0


@pytest.mark.asyncio
async def test_monthly_totals_by_category(db_session: AsyncSession, test_clinic: Clinic):
    await ExpenseService.create_expense(
        db_session,
        test_clinic.id,
        ExpenseCreate(category="rent", amount=Decimal("1000.00"), expense_date=date(2026, 8, 5)),
        created_by=None,
    )
    await ExpenseService.create_expense(
        db_session,
        test_clinic.id,
        ExpenseCreate(
            category="utilities", amount=Decimal("150.00"), expense_date=date(2026, 8, 10)
        ),
        created_by=None,
    )
    # Different month -- must not be included in the August total.
    await ExpenseService.create_expense(
        db_session,
        test_clinic.id,
        ExpenseCreate(category="rent", amount=Decimal("1000.00"), expense_date=date(2026, 9, 1)),
        created_by=None,
    )

    totals = await ExpenseService.monthly_totals_by_category(db_session, test_clinic.id, 2026, 8)
    by_category = {t.category: t.total for t in totals}
    assert by_category["rent"] == Decimal("1000.00")
    assert by_category["utilities"] == Decimal("150.00")


@pytest.mark.asyncio
async def test_expenses_are_clinic_scoped(db_session: AsyncSession, test_clinic: Clinic):
    other_clinic = Clinic(
        id=uuid4(), name="Other Clinic", tax_id="B22222222", address={}, settings={}
    )
    db_session.add(other_clinic)
    await db_session.commit()

    other_expense = await ExpenseService.create_expense(
        db_session,
        other_clinic.id,
        ExpenseCreate(
            category="salaries", amount=Decimal("5000.00"), expense_date=date(2026, 8, 1)
        ),
        created_by=None,
    )

    with pytest.raises(HTTPException) as exc_info:
        await ExpenseService.get_expense(db_session, test_clinic.id, other_expense.id)
    assert exc_info.value.status_code == 404

    rows, total = await ExpenseService.list_expenses(db_session, test_clinic.id)
    assert total == 0
    assert other_expense.id not in [r.id for r in rows]

    totals = await ExpenseService.monthly_totals_by_category(db_session, test_clinic.id, 2026, 8)
    assert totals == []
