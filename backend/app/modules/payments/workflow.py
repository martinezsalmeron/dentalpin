"""Transactional payment workflows.

Service-level invariants:
- ``Σ allocation.amount == payment.amount``
- ``Σ refund.amount ≤ payment.amount``
- Allocations to ``target_type='budget'`` must reference a budget in
  the same ``clinic_id``.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import EventType, event_bus
from app.modules.budget.models import Budget

from .models import Payment, PaymentAllocation, PaymentHistory, Refund


class PaymentWorkflowError(ValueError):
    """Raised when a payment workflow precondition fails (400/422)."""


def _now() -> datetime:
    return datetime.now(UTC)


async def _validate_allocations_for_clinic(
    db: AsyncSession,
    clinic_id: UUID,
    allocations: list[dict],
) -> None:
    """Confirm every budget target exists and belongs to ``clinic_id``."""
    budget_ids = {
        a["target_id"]
        for a in allocations
        if a["target_type"] == "budget" and a.get("target_id") is not None
    }
    if not budget_ids:
        return

    result = await db.execute(
        select(Budget.id, Budget.clinic_id, Budget.status).where(Budget.id.in_(budget_ids))
    )
    rows = {row.id: row for row in result.all()}

    for bid in budget_ids:
        row = rows.get(bid)
        if row is None:
            raise PaymentWorkflowError(f"Budget {bid} not found")
        if row.clinic_id != clinic_id:
            raise PaymentWorkflowError(f"Budget {bid} belongs to another clinic")


def _allocations_sum(allocations: list[dict]) -> Decimal:
    return sum((Decimal(str(a["amount"])) for a in allocations), Decimal("0"))


def _publish_allocated(
    *,
    clinic_id: UUID,
    payment_id: UUID,
    allocation: PaymentAllocation,
    previous_target_type: str | None = None,
    previous_target_id: UUID | None = None,
) -> None:
    event_bus.publish(
        EventType.PAYMENT_ALLOCATED,
        {
            "clinic_id": str(clinic_id),
            "payment_id": str(payment_id),
            "allocation_id": str(allocation.id),
            "target_type": allocation.target_type,
            "target_id": str(allocation.budget_id) if allocation.budget_id else None,
            "amount": str(allocation.amount),
            "previous_target_type": previous_target_type,
            "previous_target_id": str(previous_target_id) if previous_target_id else None,
            "occurred_at": _now().isoformat(),
        },
    )


async def record_payment(
    db: AsyncSession,
    *,
    clinic_id: UUID,
    currency: str,
    patient_id: UUID,
    amount: Decimal,
    method: str,
    payment_date,
    recorded_by: UUID,
    allocations: list[dict],
    reference: str | None = None,
    notes: str | None = None,
) -> Payment:
    """Create a Payment with its allocations transactionally.

    Each item of ``allocations`` is ``{target_type, target_id?, amount}``.
    """
    if not allocations:
        raise PaymentWorkflowError("At least one allocation required")
    allocated_total = _allocations_sum(allocations)
    if allocated_total != amount:
        raise PaymentWorkflowError(
            f"Allocations sum {allocated_total} does not match payment amount {amount}"
        )

    await _validate_allocations_for_clinic(db, clinic_id, allocations)

    payment = Payment(
        clinic_id=clinic_id,
        patient_id=patient_id,
        amount=amount,
        currency=currency,
        method=method,
        payment_date=payment_date,
        reference=reference,
        notes=notes,
        recorded_by=recorded_by,
    )
    db.add(payment)
    await db.flush()  # need payment.id for allocations

    created_allocations: list[PaymentAllocation] = []
    for spec in allocations:
        alloc = PaymentAllocation(
            clinic_id=clinic_id,
            payment_id=payment.id,
            target_type=spec["target_type"],
            budget_id=spec.get("target_id") if spec["target_type"] == "budget" else None,
            amount=Decimal(str(spec["amount"])),
            created_by=recorded_by,
        )
        db.add(alloc)
        created_allocations.append(alloc)

    db.add(
        PaymentHistory(
            clinic_id=clinic_id,
            payment_id=payment.id,
            action="created",
            changed_by=recorded_by,
            changed_at=_now(),
            previous_state=None,
            new_state={
                "amount": str(amount),
                "method": method,
                "allocations": [
                    {
                        "target_type": spec["target_type"],
                        "target_id": str(spec["target_id"]) if spec.get("target_id") else None,
                        "amount": str(spec["amount"]),
                    }
                    for spec in allocations
                ],
            },
        )
    )

    await db.flush()

    event_bus.publish(
        EventType.PAYMENT_RECORDED,
        {
            "clinic_id": str(clinic_id),
            "payment_id": str(payment.id),
            "patient_id": str(patient_id),
            "amount": str(amount),
            "currency": currency,
            "method": method,
            "payment_date": payment_date.isoformat(),
            "occurred_at": _now().isoformat(),
        },
    )
    for alloc in created_allocations:
        _publish_allocated(clinic_id=clinic_id, payment_id=payment.id, allocation=alloc)

    return payment


async def reallocate_payment(
    db: AsyncSession,
    *,
    clinic_id: UUID,
    payment: Payment,
    new_allocations: list[dict],
    changed_by: UUID,
) -> Payment:
    """Replace a payment's allocations atomically.

    New allocations must sum to ``payment.amount``. Previous allocation
    rows are deleted; new rows are created. One ``payment.allocated``
    event per new row carries the previous target so subscribers can
    reconcile budget/on_account/invoice balances.
    """
    if not new_allocations:
        raise PaymentWorkflowError("At least one allocation required")
    if _allocations_sum(new_allocations) != payment.amount:
        raise PaymentWorkflowError("New allocations must sum to payment.amount")

    await _validate_allocations_for_clinic(db, clinic_id, new_allocations)

    previous_state = [
        {
            "id": str(a.id),
            "target_type": a.target_type,
            "target_id": str(a.budget_id) if a.budget_id else None,
            "amount": str(a.amount),
        }
        for a in payment.allocations
    ]

    # Cascade delete via ORM (also removes references in-memory).
    for old in list(payment.allocations):
        await db.delete(old)
    await db.flush()

    created_allocations: list[PaymentAllocation] = []
    for spec in new_allocations:
        alloc = PaymentAllocation(
            clinic_id=clinic_id,
            payment_id=payment.id,
            target_type=spec["target_type"],
            budget_id=spec.get("target_id") if spec["target_type"] == "budget" else None,
            amount=Decimal(str(spec["amount"])),
            created_by=changed_by,
        )
        db.add(alloc)
        created_allocations.append(alloc)

    db.add(
        PaymentHistory(
            clinic_id=clinic_id,
            payment_id=payment.id,
            action="reallocated",
            changed_by=changed_by,
            changed_at=_now(),
            previous_state={"allocations": previous_state},
            new_state={
                "allocations": [
                    {
                        "target_type": spec["target_type"],
                        "target_id": str(spec["target_id"]) if spec.get("target_id") else None,
                        "amount": str(spec["amount"]),
                    }
                    for spec in new_allocations
                ]
            },
        )
    )

    await db.flush()

    for alloc in created_allocations:
        _publish_allocated(clinic_id=clinic_id, payment_id=payment.id, allocation=alloc)

    return payment


async def refund_payment(
    db: AsyncSession,
    *,
    clinic_id: UUID,
    payment: Payment,
    amount: Decimal,
    method: str,
    reason_code: str,
    reason_note: str | None,
    refunded_by: UUID,
) -> Refund:
    """Create a Refund row, enforcing the per-payment cap."""
    if amount <= 0:
        raise PaymentWorkflowError("Refund amount must be > 0")

    result = await db.execute(
        select(func.coalesce(func.sum(Refund.amount), Decimal("0"))).where(
            Refund.payment_id == payment.id
        )
    )
    already_refunded: Decimal = result.scalar_one()
    if already_refunded + amount > payment.amount:
        raise PaymentWorkflowError(
            f"Refund {amount} exceeds remaining cap "
            f"{payment.amount - already_refunded} for payment {payment.id}"
        )

    now = _now()
    refund = Refund(
        clinic_id=clinic_id,
        payment_id=payment.id,
        amount=amount,
        method=method,
        reason_code=reason_code,
        reason_note=reason_note,
        refunded_at=now,
        refunded_by=refunded_by,
    )
    db.add(refund)

    db.add(
        PaymentHistory(
            clinic_id=clinic_id,
            payment_id=payment.id,
            action="refunded",
            changed_by=refunded_by,
            changed_at=now,
            previous_state={"refunded_total": str(already_refunded)},
            new_state={
                "refunded_total": str(already_refunded + amount),
                "refund_amount": str(amount),
                "reason_code": reason_code,
            },
        )
    )

    await db.flush()

    event_bus.publish(
        EventType.PAYMENT_REFUNDED,
        {
            "clinic_id": str(clinic_id),
            "payment_id": str(payment.id),
            "refund_id": str(refund.id),
            "amount": str(amount),
            "reason_code": reason_code,
            "occurred_at": now.isoformat(),
        },
    )

    return refund


__all__ = [
    "PaymentWorkflowError",
    "record_payment",
    "reallocate_payment",
    "refund_payment",
]
