"""copilot module — proactive nudges (ADR 0014 §Deferred).

Event-driven contextual suggestions surfaced in the drawer. Deduped per
clinic on ``dedupe_key``; same-day TTL via ``expires_at``.

Revision ID: cop_0004
Revises: cop_0003
Create Date: 2026-06-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "cop_0004"
down_revision: str | None = "cop_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "copilot_nudges",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "clinic_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clinics.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("kind", sa.String(length=50), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("required_permission", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("dedupe_key", sa.String(length=200), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("clinic_id", "dedupe_key", name="uq_copilot_nudge_dedupe"),
    )
    op.create_index("ix_copilot_nudges_clinic_id", "copilot_nudges", ["clinic_id"])


def downgrade() -> None:
    op.drop_index("ix_copilot_nudges_clinic_id", table_name="copilot_nudges")
    op.drop_table("copilot_nudges")
