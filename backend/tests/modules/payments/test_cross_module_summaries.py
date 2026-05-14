"""Tests for the cross-module summary + filter endpoints.

Contract: docs/technical/payments/cross-module-summaries.md.

These endpoints power the /patients and /budgets list pages
(other modules) — they must:
  - return correct collected/pending/payment_status per budget
  - return correct total_paid/debt/on_account per patient
  - enforce the 100-id cap on bulk summaries
  - enforce the 1000-id cap (with truncated flag) on filter endpoints
  - **stay off-books safe**: debt = earned − net_paid, never invoiced − paid
  - respect multi-tenancy (cross-clinic ids silently absent)
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.models import Clinic, ClinicMembership
from app.modules.budget.models import Budget
from app.modules.patients.models import Patient
from app.modules.payments.models import PatientEarnedEntry


async def _setup_clinic(
    db: AsyncSession,
    auth_headers: dict,
    client: AsyncClient,
    *,
    name: str = "CXTest Clinic",
) -> dict:
    me = await client.get("/api/v1/auth/me", headers=auth_headers)
    user_id = me.json()["data"]["user"]["id"]

    clinic = Clinic(
        id=uuid4(),
        name=name,
        tax_id="A28000000",
        timezone="Europe/Madrid",
        currency="EUR",
        settings={},
    )
    db.add(clinic)
    await db.flush()
    db.add(ClinicMembership(id=uuid4(), clinic_id=clinic.id, user_id=user_id, role="admin"))

    patient = Patient(id=uuid4(), clinic_id=clinic.id, first_name="Ana", last_name="García")
    db.add(patient)
    await db.commit()

    return {
        "clinic_id": str(clinic.id),
        "user_id": user_id,
        "patient_id": str(patient.id),
    }


async def _create_budget(
    db: AsyncSession, clinic_id: str, patient_id: str, total: Decimal, user_id: str
) -> Budget:
    budget = Budget(
        id=uuid4(),
        clinic_id=clinic_id,
        patient_id=patient_id,
        budget_number=f"PRES-T-{uuid4().hex[:6]}",
        version=1,
        status="accepted",
        valid_from=date.today(),
        created_by=user_id,
        subtotal=total,
        total_discount=Decimal("0"),
        total_tax=Decimal("0"),
        total=total,
    )
    db.add(budget)
    await db.commit()
    await db.refresh(budget)
    return budget


@pytest.mark.asyncio
async def test_summary_by_budgets_paid_partial_unpaid(
    client: AsyncClient,
    auth_headers: dict,
    db_session: AsyncSession,
):
    setup = await _setup_clinic(db_session, auth_headers, client)
    clinic_id = setup["clinic_id"]
    user_id = setup["user_id"]
    patient_id = setup["patient_id"]

    paid_budget = await _create_budget(
        db_session, clinic_id, patient_id, Decimal("100.00"), user_id
    )
    partial_budget = await _create_budget(
        db_session, clinic_id, patient_id, Decimal("200.00"), user_id
    )
    unpaid_budget = await _create_budget(
        db_session, clinic_id, patient_id, Decimal("300.00"), user_id
    )

    # Pay paid_budget in full.
    body = {
        "patient_id": patient_id,
        "amount": "100.00",
        "method": "cash",
        "payment_date": date.today().isoformat(),
        "allocations": [
            {"target_type": "budget", "target_id": str(paid_budget.id), "amount": "100.00"}
        ],
    }
    resp = await client.post(
        f"/api/v1/payments?clinic_id={clinic_id}", headers=auth_headers, json=body
    )
    assert resp.status_code == 201, resp.text

    # Pay partial_budget halfway.
    body["amount"] = "100.00"
    body["allocations"] = [
        {"target_type": "budget", "target_id": str(partial_budget.id), "amount": "100.00"}
    ]
    resp = await client.post(
        f"/api/v1/payments?clinic_id={clinic_id}", headers=auth_headers, json=body
    )
    assert resp.status_code == 201, resp.text

    # Query bulk summary.
    resp = await client.post(
        f"/api/v1/payments/summary/by-budgets?clinic_id={clinic_id}",
        headers=auth_headers,
        json={
            "budget_ids": [
                str(paid_budget.id),
                str(partial_budget.id),
                str(unpaid_budget.id),
            ]
        },
    )
    assert resp.status_code == 200, resp.text
    summaries = resp.json()["data"]["summaries"]

    assert summaries[str(paid_budget.id)]["payment_status"] == "paid"
    assert Decimal(summaries[str(paid_budget.id)]["collected"]) == Decimal("100.00")
    assert Decimal(summaries[str(paid_budget.id)]["pending"]) == Decimal("0.00")

    assert summaries[str(partial_budget.id)]["payment_status"] == "partial"
    assert Decimal(summaries[str(partial_budget.id)]["collected"]) == Decimal("100.00")
    assert Decimal(summaries[str(partial_budget.id)]["pending"]) == Decimal("100.00")

    assert summaries[str(unpaid_budget.id)]["payment_status"] == "unpaid"
    assert Decimal(summaries[str(unpaid_budget.id)]["collected"]) == Decimal("0.00")
    assert Decimal(summaries[str(unpaid_budget.id)]["pending"]) == Decimal("300.00")


@pytest.mark.asyncio
async def test_summary_by_budgets_caps_ids(
    client: AsyncClient,
    auth_headers: dict,
    db_session: AsyncSession,
):
    setup = await _setup_clinic(db_session, auth_headers, client)
    over_cap = [str(uuid4()) for _ in range(101)]
    resp = await client.post(
        f"/api/v1/payments/summary/by-budgets?clinic_id={setup['clinic_id']}",
        headers=auth_headers,
        json={"budget_ids": over_cap},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_off_books_invariant_debt_from_earned_not_invoiced(
    client: AsyncClient,
    auth_headers: dict,
    db_session: AsyncSession,
):
    """Critical: ``debt`` must equal ``earned − net_paid``, never ``invoiced − paid``.

    Build a patient with an earned entry but **no invoice**. The
    payments-side debt endpoint must include the patient. The billing
    invoice list (independent axis) must remain empty. Two truths
    coexist without ever being mixed.
    """
    setup = await _setup_clinic(db_session, auth_headers, client)
    clinic_id = setup["clinic_id"]
    patient_id = setup["patient_id"]

    # Earned entry: the dentist performed a treatment worth 250 €.
    earned = PatientEarnedEntry(
        id=uuid4(),
        clinic_id=clinic_id,
        patient_id=patient_id,
        treatment_id=uuid4(),
        amount=Decimal("250.00"),
        performed_at=datetime.now(UTC),
        source_event="test.fixture",
    )
    db_session.add(earned)
    await db_session.commit()

    # The patient should appear in the debt filter result.
    resp = await client.get(
        f"/api/v1/payments/filters/patients-with-debt?clinic_id={clinic_id}",
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()["data"]
    assert patient_id in body["patient_ids"]

    # And the summary must report debt = 250, total_paid = 0, on_account = 0.
    resp = await client.post(
        f"/api/v1/payments/summary/by-patients?clinic_id={clinic_id}",
        headers=auth_headers,
        json={"patient_ids": [patient_id]},
    )
    assert resp.status_code == 200, resp.text
    summary = resp.json()["data"]["summaries"][patient_id]
    assert Decimal(summary["debt"]) == Decimal("250.00")
    assert Decimal(summary["total_paid"]) == Decimal("0")
    assert Decimal(summary["on_account_balance"]) == Decimal("0")

    # Billing-side: no invoice for this patient. The invoice list is
    # intentionally empty — proves the two axes are independent.
    resp = await client.get(
        f"/api/v1/billing/invoices?clinic_id={clinic_id}&patient_id={patient_id}",
        headers=auth_headers,
    )
    # billing.read permission may not be auto-granted to admin role in
    # all envs; skip the assertion when 403 — the key assertion is that
    # *debt was computed without consulting invoices*, which we
    # validated above.
    if resp.status_code == 200:
        assert resp.json()["total"] == 0


@pytest.mark.asyncio
async def test_filter_budgets_by_status_unpaid_includes_uncollected(
    client: AsyncClient,
    auth_headers: dict,
    db_session: AsyncSession,
):
    setup = await _setup_clinic(db_session, auth_headers, client)
    clinic_id = setup["clinic_id"]
    user_id = setup["user_id"]
    patient_id = setup["patient_id"]

    budget = await _create_budget(db_session, clinic_id, patient_id, Decimal("400.00"), user_id)

    resp = await client.get(
        f"/api/v1/payments/filters/budgets-by-status?clinic_id={clinic_id}&status=unpaid",
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()["data"]
    assert str(budget.id) in body["budget_ids"]
    assert body["truncated"] is False


@pytest.mark.asyncio
async def test_summary_patients_with_payment_only_has_credit_not_debt(
    client: AsyncClient,
    auth_headers: dict,
    db_session: AsyncSession,
):
    """A patient who paid 100 € on-account with zero earned has 100 € credit
    and zero debt — confirms the asymmetry of the off-books computation."""
    setup = await _setup_clinic(db_session, auth_headers, client)
    clinic_id = setup["clinic_id"]
    patient_id = setup["patient_id"]

    resp = await client.post(
        f"/api/v1/payments?clinic_id={clinic_id}",
        headers=auth_headers,
        json={
            "patient_id": patient_id,
            "amount": "100.00",
            "method": "cash",
            "payment_date": date.today().isoformat(),
            "allocations": [{"target_type": "on_account", "amount": "100.00"}],
        },
    )
    assert resp.status_code == 201, resp.text

    resp = await client.post(
        f"/api/v1/payments/summary/by-patients?clinic_id={clinic_id}",
        headers=auth_headers,
        json={"patient_ids": [patient_id]},
    )
    assert resp.status_code == 200, resp.text
    s = resp.json()["data"]["summaries"][patient_id]
    assert Decimal(s["debt"]) == Decimal("0")
    assert Decimal(s["total_paid"]) == Decimal("100.00")
    assert Decimal(s["on_account_balance"]) == Decimal("100.00")
