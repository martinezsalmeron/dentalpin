"""Add invoice series history table for audit logging.

Revision ID: m3n4o5p6q7r8
Revises: l2m3n4o5p6q7
Create Date: 2026-04-14

Tables created:
- invoice_series_history: Audit log for series configuration changes
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "m3n4o5p6q7r8"
down_revision: str | None = "l2m3n4o5p6q7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "invoice_series_history",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("series_id", sa.UUID(), nullable=False),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("changed_by", sa.UUID(), nullable=False),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("previous_state", postgresql.JSONB(), nullable=True),
        sa.Column("new_state", postgresql.JSONB(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"]),
        sa.ForeignKeyConstraint(["series_id"], ["invoice_series.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["changed_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_invoice_series_history_series",
        "invoice_series_history",
        ["series_id"],
    )
    op.create_index(
        "idx_invoice_series_history_clinic",
        "invoice_series_history",
        ["clinic_id"],
    )
    op.create_index(
        "idx_invoice_series_history_changed_at",
        "invoice_series_history",
        ["changed_at"],
    )


def downgrade() -> None:
    op.drop_index("idx_invoice_series_history_changed_at", "invoice_series_history")
    op.drop_index("idx_invoice_series_history_clinic", "invoice_series_history")
    op.drop_index("idx_invoice_series_history_series", "invoice_series_history")
    op.drop_table("invoice_series_history")
