"""Payments module database models."""

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, TimestampMixin

if TYPE_CHECKING:
    from app.core.auth.models import Clinic, User
    from app.modules.budget.models import Budget
    from app.modules.patients.models import Patient


# Allowed payment methods (kept as plain list — schemas validate via Literal).
PAYMENT_METHODS = ["cash", "card", "bank_transfer", "direct_debit", "insurance", "other"]

# Allocation targets that don't require a foreign key (``on_account``)
# vs targets backed by another row (``budget``).
ALLOCATION_TARGET_TYPES = ["budget", "on_account"]

# Closed list of refund reason codes. UI shows localized labels; this is
# the storage form. ``other`` allows free-text reason_note for the long
# tail.
REFUND_REASON_CODES = [
    "duplicate",
    "overpaid",
    "treatment_cancelled",
    "dispute",
    "other",
]


class Payment(Base, TimestampMixin):
    """A patient cash-in event.

    The amount is gross. Reductions happen via ``Refund`` rows. A
    payment must be fully covered by ``PaymentAllocation`` rows whose
    amounts sum to ``Payment.amount`` (invariant enforced in the
    service layer).
    """

    __tablename__ = "payments"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id"), index=True)
    patient_id: Mapped[UUID] = mapped_column(ForeignKey("patients.id"), index=True)

    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3))  # snapshot of Clinic.currency
    method: Mapped[str] = mapped_column(String(30))
    payment_date: Mapped[date] = mapped_column(Date)
    reference: Mapped[str | None] = mapped_column(String(100), default=None)
    notes: Mapped[str | None] = mapped_column(Text, default=None)

    recorded_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))

    # Relationships
    clinic: Mapped["Clinic"] = relationship(foreign_keys=[clinic_id])
    patient: Mapped["Patient"] = relationship()
    recorder: Mapped["User"] = relationship(foreign_keys=[recorded_by])
    allocations: Mapped[list["PaymentAllocation"]] = relationship(
        back_populates="payment",
        cascade="all, delete-orphan",
        order_by="PaymentAllocation.created_at",
    )
    refunds: Mapped[list["Refund"]] = relationship(
        back_populates="payment",
        order_by="Refund.refunded_at.desc()",
    )

    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_payments_amount_positive"),
        Index("idx_payments_clinic_patient", "clinic_id", "patient_id"),
        Index("idx_payments_clinic_date", "clinic_id", "payment_date"),
        Index("idx_payments_clinic_method", "clinic_id", "method"),
    )


class PaymentAllocation(Base, TimestampMixin):
    """How a payment is distributed across targets.

    Targets in v1:
    - ``budget``    — line is bound to a specific accepted budget. Used
      for anticipos and partial cobros on treatments-in-progress.
    - ``on_account``— patient credit balance with no specific budget.
      Reassignable later when an invoice is issued.

    Allocations to a specific Invoice live in the billing module's
    ``invoice_payments`` table — that link sits on the billing side so
    payments does not have to depend on billing.
    """

    __tablename__ = "payment_allocations"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id"), index=True)
    payment_id: Mapped[UUID] = mapped_column(
        ForeignKey("payments.id", ondelete="CASCADE"), index=True
    )

    target_type: Mapped[str] = mapped_column(String(20))
    # FK to budgets is nullable — null when target_type == 'on_account'.
    # Stored as ``budget_id`` (not ``target_id``) so the database can
    # enforce referential integrity directly. The CHECK below couples
    # the two columns so callers can't silently corrupt state.
    budget_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("budgets.id", ondelete="RESTRICT"), nullable=True, default=None, index=True
    )

    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))

    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))

    # Relationships
    clinic: Mapped["Clinic"] = relationship(foreign_keys=[clinic_id])
    payment: Mapped["Payment"] = relationship(back_populates="allocations")
    budget: Mapped["Budget | None"] = relationship()
    creator: Mapped["User"] = relationship(foreign_keys=[created_by])

    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_alloc_amount_positive"),
        CheckConstraint(
            "(target_type = 'budget' AND budget_id IS NOT NULL) "
            "OR (target_type = 'on_account' AND budget_id IS NULL)",
            name="ck_alloc_target_consistency",
        ),
        Index("idx_alloc_payment", "payment_id"),
        Index("idx_alloc_clinic_budget", "clinic_id", "budget_id"),
    )

    @property
    def target_id(self) -> UUID | None:
        """Public accessor over the heterogeneous target reference."""
        if self.target_type == "budget":
            return self.budget_id
        return None


class Refund(Base, TimestampMixin):
    """Partial or full reversal of a payment.

    A full reversal is just ``Refund(amount=payment.amount)`` — there is
    no separate ``is_voided`` flag. ``Σ Refund.amount per payment`` must
    stay ``≤ Payment.amount`` (invariant enforced in the service).
    """

    __tablename__ = "refunds"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id"), index=True)
    payment_id: Mapped[UUID] = mapped_column(
        ForeignKey("payments.id", ondelete="RESTRICT"), index=True
    )

    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    method: Mapped[str] = mapped_column(String(30))  # may differ from original payment method
    reason_code: Mapped[str] = mapped_column(String(30))
    reason_note: Mapped[str | None] = mapped_column(Text, default=None)

    refunded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    refunded_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))

    # Relationships
    clinic: Mapped["Clinic"] = relationship(foreign_keys=[clinic_id])
    payment: Mapped["Payment"] = relationship(back_populates="refunds")
    refunder: Mapped["User"] = relationship(foreign_keys=[refunded_by])

    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_refund_amount_positive"),
        Index("idx_refund_payment", "payment_id"),
        Index("idx_refund_clinic_date", "clinic_id", "refunded_at"),
    )


class PatientEarnedEntry(Base, TimestampMixin):
    """Denormalized ledger of treatments performed on a patient.

    Populated by event handlers reacting to
    ``odontogram.treatment.performed`` and
    ``treatment_plan.treatment_completed``. The unique ``treatment_id``
    constraint makes the upsert idempotent regardless of which event
    fires first — the two paths converge on the same row.

    No FK to ``treatments`` or ``catalog_items`` — payments must not
    depend on those modules. Values are snapshots from the event
    payload.
    """

    __tablename__ = "patient_earned_entries"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id"), index=True)
    patient_id: Mapped[UUID] = mapped_column(ForeignKey("patients.id"), index=True)

    treatment_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True))  # no FK on purpose
    catalog_item_id: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), default=None)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    performed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    professional_id: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), default=None)
    source_event: Mapped[str] = mapped_column(String(50))

    clinic: Mapped["Clinic"] = relationship(foreign_keys=[clinic_id])
    patient: Mapped["Patient"] = relationship()

    __table_args__ = (
        CheckConstraint("amount >= 0", name="ck_earned_amount_nonneg"),
        UniqueConstraint("treatment_id", name="uq_earned_treatment"),
        Index("idx_earned_clinic_patient", "clinic_id", "patient_id"),
        Index("idx_earned_clinic_performed", "clinic_id", "performed_at"),
    )


class PaymentHistory(Base):
    """Audit log for payment lifecycle changes."""

    __tablename__ = "payment_history"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id"), index=True)
    payment_id: Mapped[UUID] = mapped_column(
        ForeignKey("payments.id", ondelete="CASCADE"), index=True
    )

    action: Mapped[str] = mapped_column(String(30))  # created|allocated|reallocated|refunded
    changed_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    previous_state: Mapped[dict | None] = mapped_column(JSONB, default=None)
    new_state: Mapped[dict | None] = mapped_column(JSONB, default=None)

    notes: Mapped[str | None] = mapped_column(Text, default=None)

    clinic: Mapped["Clinic"] = relationship()
    payment: Mapped["Payment"] = relationship()
    user: Mapped["User"] = relationship()

    __table_args__ = (
        Index("idx_payment_history_payment", "payment_id"),
        Index("idx_payment_history_clinic_changed", "clinic_id", "changed_at"),
    )
