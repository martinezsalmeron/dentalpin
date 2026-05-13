"""payments module — initial schema.

Creates the payment-side tables that supersede the legacy
``billing.payments`` table. Allocations target ``budget`` or
``on_account``. The link to ``invoices`` is owned by billing in its
own ``invoice_payments`` table — payments does not depend on billing.

Revision ID: pay_0001
Revises: bud_0003
Create Date: 2026-05-13
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "pay_0001"
down_revision: str | None = "bud_0003"
branch_labels: str | Sequence[str] | None = ("payments",)
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "payments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("patient_id", sa.UUID(), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("method", sa.String(length=30), nullable=False),
        sa.Column("payment_date", sa.Date(), nullable=False),
        sa.Column("reference", sa.String(length=100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("recorded_by", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"]),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"]),
        sa.ForeignKeyConstraint(["recorded_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("amount > 0", name="ck_payments_amount_positive"),
    )
    op.create_index("idx_payments_clinic_patient", "payments", ["clinic_id", "patient_id"])
    op.create_index("idx_payments_clinic_date", "payments", ["clinic_id", "payment_date"])
    op.create_index("idx_payments_clinic_method", "payments", ["clinic_id", "method"])

    op.create_table(
        "payment_allocations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("payment_id", sa.UUID(), nullable=False),
        sa.Column("target_type", sa.String(length=20), nullable=False),
        sa.Column("budget_id", sa.UUID(), nullable=True),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("created_by", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"]),
        sa.ForeignKeyConstraint(["payment_id"], ["payments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["budget_id"], ["budgets.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("amount > 0", name="ck_alloc_amount_positive"),
        sa.CheckConstraint(
            "(target_type = 'budget' AND budget_id IS NOT NULL) "
            "OR (target_type = 'on_account' AND budget_id IS NULL)",
            name="ck_alloc_target_consistency",
        ),
    )
    op.create_index("idx_alloc_payment", "payment_allocations", ["payment_id"])
    op.create_index("idx_alloc_clinic_budget", "payment_allocations", ["clinic_id", "budget_id"])

    op.create_table(
        "refunds",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("payment_id", sa.UUID(), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("method", sa.String(length=30), nullable=False),
        sa.Column("reason_code", sa.String(length=30), nullable=False),
        sa.Column("reason_note", sa.Text(), nullable=True),
        sa.Column("refunded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("refunded_by", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"]),
        sa.ForeignKeyConstraint(["payment_id"], ["payments.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["refunded_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("amount > 0", name="ck_refund_amount_positive"),
    )
    op.create_index("idx_refund_payment", "refunds", ["payment_id"])
    op.create_index("idx_refund_clinic_date", "refunds", ["clinic_id", "refunded_at"])

    op.create_table(
        "patient_earned_entries",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("patient_id", sa.UUID(), nullable=False),
        sa.Column("treatment_id", sa.UUID(), nullable=False),
        sa.Column("catalog_item_id", sa.UUID(), nullable=True),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("performed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("professional_id", sa.UUID(), nullable=True),
        sa.Column("source_event", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"]),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("amount >= 0", name="ck_earned_amount_nonneg"),
        sa.UniqueConstraint("treatment_id", name="uq_earned_treatment"),
    )
    op.create_index(
        "idx_earned_clinic_patient", "patient_earned_entries", ["clinic_id", "patient_id"]
    )
    op.create_index(
        "idx_earned_clinic_performed", "patient_earned_entries", ["clinic_id", "performed_at"]
    )

    op.create_table(
        "payment_history",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("payment_id", sa.UUID(), nullable=False),
        sa.Column("action", sa.String(length=30), nullable=False),
        sa.Column("changed_by", sa.UUID(), nullable=False),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("previous_state", sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column("new_state", sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"]),
        sa.ForeignKeyConstraint(["payment_id"], ["payments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["changed_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_payment_history_payment", "payment_history", ["payment_id"])
    op.create_index(
        "idx_payment_history_clinic_changed", "payment_history", ["clinic_id", "changed_at"]
    )


def downgrade() -> None:
    op.drop_index("idx_payment_history_clinic_changed", table_name="payment_history")
    op.drop_index("idx_payment_history_payment", table_name="payment_history")
    op.drop_table("payment_history")

    op.drop_index("idx_earned_clinic_performed", table_name="patient_earned_entries")
    op.drop_index("idx_earned_clinic_patient", table_name="patient_earned_entries")
    op.drop_table("patient_earned_entries")

    op.drop_index("idx_refund_clinic_date", table_name="refunds")
    op.drop_index("idx_refund_payment", table_name="refunds")
    op.drop_table("refunds")

    op.drop_index("idx_alloc_clinic_budget", table_name="payment_allocations")
    op.drop_index("idx_alloc_payment", table_name="payment_allocations")
    op.drop_table("payment_allocations")

    op.drop_index("idx_payments_clinic_method", table_name="payments")
    op.drop_index("idx_payments_clinic_date", table_name="payments")
    op.drop_index("idx_payments_clinic_patient", table_name="payments")
    op.drop_table("payments")
