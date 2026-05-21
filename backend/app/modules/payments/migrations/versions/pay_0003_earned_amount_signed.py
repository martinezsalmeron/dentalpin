"""payments — let earned amount go negative.

Gesdén records ``Nota Económica`` adjustments (refunds, corrections,
discounts after invoicing) as ``TtosMed`` rows with negative
``Importe``. The migration importer needs to land them somewhere so
the patient ledger reflects the source's reality; ``PatientEarnedEntry``
is the natural home because it already feeds ``LedgerService.total_earned``
via ``SUM``. The old ``amount >= 0`` check was a single-direction
invariant the event-driven path imposed; relaxing it for the whole
table costs nothing in normal flow (the publishers still emit
positive amounts) and lets the migration import the full picture.

Revision ID: pay_0003
Revises: pay_0002
Create Date: 2026-05-21
"""

from collections.abc import Sequence

from alembic import op

revision: str = "pay_0003"
down_revision: str | None = "pay_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint(
        "ck_earned_amount_nonneg",
        "patient_earned_entries",
        type_="check",
    )


def downgrade() -> None:
    op.create_check_constraint(
        "ck_earned_amount_nonneg",
        "patient_earned_entries",
        "amount >= 0",
    )
