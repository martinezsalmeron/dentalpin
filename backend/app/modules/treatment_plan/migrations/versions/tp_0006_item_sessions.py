"""Add planned_treatment_item_sessions for multi-session billing.

Each ``PlannedTreatmentItem`` now owns 1..N sessions. Backfills one
session per existing item (sequence=1, amount=treatments.price_snapshot,
status inherited) so the post-migration code paths can rely on every
item having at least one session.

Revision ID: tp_0006
Revises: tp_0005
Create Date: 2026-05-19

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "tp_0006"
down_revision: str | None = "tp_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "planned_treatment_item_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "plan_item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("planned_treatment_items.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("label", sa.String(length=120), nullable=True),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "completed_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("plan_item_id", "sequence", name="uq_plan_item_session_sequence"),
    )
    op.create_index(
        "idx_pti_session_plan_item",
        "planned_treatment_item_sessions",
        ["plan_item_id"],
    )
    op.create_index(
        "ix_pti_session_plan_item_status",
        "planned_treatment_item_sessions",
        ["plan_item_id", "status"],
    )

    # Backfill: one session per existing item, snapshotting treatment price.
    op.execute(
        """
        INSERT INTO planned_treatment_item_sessions (
            id, plan_item_id, sequence, label, amount, status,
            completed_at, completed_by, notes, created_at, updated_at
        )
        SELECT
            gen_random_uuid(),
            pti.id,
            1,
            NULL,
            COALESCE(t.price_snapshot, 0),
            pti.status,
            pti.completed_at,
            pti.completed_by,
            NULL,
            now(),
            now()
        FROM planned_treatment_items pti
        JOIN treatments t ON t.id = pti.treatment_id
        """
    )


def downgrade() -> None:
    op.drop_index(
        "ix_pti_session_plan_item_status",
        table_name="planned_treatment_item_sessions",
    )
    op.drop_index(
        "idx_pti_session_plan_item",
        table_name="planned_treatment_item_sessions",
    )
    op.drop_table("planned_treatment_item_sessions")
