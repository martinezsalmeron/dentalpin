"""billing — add invoice_payments link table.

Issue #53. The new ``payments`` module owns the ``payments`` table on
its own branch. Billing keeps the link to invoices in its own
``invoice_payments`` table, which FKs ``payments.id``.

``Invoice.total_paid`` and ``Invoice.balance_due`` were removed from
the schema in the same release (handled inline in bil_0001 — the
columns were never created in a fresh DB). Computation now lives in
``BillingService.compute_paid_summary``.

Revision ID: bil_0004
Revises: bil_0003
Create Date: 2026-05-13
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "bil_0004"
down_revision: str | None = "bil_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = ("pay_0001",)


def upgrade() -> None:
    op.create_table(
        "invoice_payments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("invoice_id", sa.UUID(), nullable=False),
        sa.Column("payment_id", sa.UUID(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("created_by", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"]),
        sa.ForeignKeyConstraint(["invoice_id"], ["invoices.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["payment_id"], ["payments.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("amount > 0", name="ck_invpay_amount_positive"),
    )
    op.create_index("idx_invpay_clinic_invoice", "invoice_payments", ["clinic_id", "invoice_id"])
    op.create_index("idx_invpay_payment", "invoice_payments", ["payment_id"])


def downgrade() -> None:
    op.drop_index("idx_invpay_payment", table_name="invoice_payments")
    op.drop_index("idx_invpay_clinic_invoice", table_name="invoice_payments")
    op.drop_table("invoice_payments")
