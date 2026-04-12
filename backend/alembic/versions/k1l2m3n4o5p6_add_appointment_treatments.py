"""add_appointment_treatments

Revision ID: k1l2m3n4o5p6
Revises: i9j0k1l2m3n4
Create Date: 2026-04-12 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "k1l2m3n4o5p6"
down_revision: str | None = "j0k1l2m3n4o5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create appointment_treatments junction table
    op.create_table(
        "appointment_treatments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "appointment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("appointments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "catalog_item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("treatment_catalog_items.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("display_order", sa.Integer(), default=0, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # Index for efficient lookups
    op.create_index(
        "ix_appointment_treatments_appointment_id",
        "appointment_treatments",
        ["appointment_id"],
    )

    # Unique constraint to prevent duplicate treatments per appointment
    op.create_unique_constraint(
        "uq_appointment_treatment",
        "appointment_treatments",
        ["appointment_id", "catalog_item_id"],
    )


def downgrade() -> None:
    op.drop_table("appointment_treatments")
