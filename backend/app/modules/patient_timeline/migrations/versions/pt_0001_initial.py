"""v2 squash — patient_timeline initial.

Initial schema for the `patient_timeline` module.

Revision ID: pt_0001
Revises:
Create Date: 2026-04-21

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "pt_0001"
down_revision: str | None = "pc_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "patient_timeline",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("patient_id", sa.UUID(), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("event_category", sa.String(length=30), nullable=False),
        sa.Column("source_table", sa.String(length=50), nullable=False),
        sa.Column("source_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("event_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinics.id"],
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["patients.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_timeline_clinic_patient", "patient_timeline", ["clinic_id", "patient_id"], unique=False
    )
    op.create_index(
        "idx_timeline_patient_date", "patient_timeline", ["patient_id", "occurred_at"], unique=False
    )
    op.create_index(
        op.f("ix_patient_timeline_clinic_id"), "patient_timeline", ["clinic_id"], unique=False
    )
    op.create_index(
        op.f("ix_patient_timeline_occurred_at"), "patient_timeline", ["occurred_at"], unique=False
    )
    op.create_index(
        op.f("ix_patient_timeline_patient_id"), "patient_timeline", ["patient_id"], unique=False
    )


def downgrade() -> None:
    op.drop_table("patient_timeline")
