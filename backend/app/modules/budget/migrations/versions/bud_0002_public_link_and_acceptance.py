"""Public link metadata, acceptance/rejection details, access log.

Adds:

- Acceptance / rejection metadata on ``budgets``: ``accepted_via``,
  ``rejection_reason``, ``rejection_note``.
- Public link 2-factor auth fields on ``budgets``: ``public_token``
  (UUID, unique), ``viewed_at``, ``last_reminder_sent_at``,
  ``public_auth_method``, ``public_auth_secret_hash``,
  ``public_locked_at``.
- Plan snapshots on ``budgets``: ``plan_number_snapshot``,
  ``plan_status_snapshot``. Avoid cross-module imports from budget into
  treatment_plan (ADR 0003).
- New table ``budget_access_logs`` for verification audit + rate
  limiting + lockout (ADR 0006). 90-day retention is enforced by the
  ``purge_budget_access_logs`` cron.

App is not in production yet, so backfill is best-effort and not
defensive: existing accepted budgets are tagged ``accepted_via='manual'``
and all rows get ``public_auth_method='none'`` so that pre-existing
links keep working without verification (clinics opt-in).

Revision ID: bud_0002
Revises: bud_0001
Create Date: 2026-04-28

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "bud_0002"
down_revision: str | None = "bud_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Acceptance / rejection metadata
    op.add_column(
        "budgets",
        sa.Column("accepted_via", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "budgets",
        sa.Column("rejection_reason", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "budgets",
        sa.Column("rejection_note", sa.Text(), nullable=True),
    )

    # Public link 2-factor auth fields
    op.add_column(
        "budgets",
        sa.Column(
            "public_token",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.add_column(
        "budgets",
        sa.Column("viewed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "budgets",
        sa.Column(
            "last_reminder_sent_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "budgets",
        sa.Column("public_auth_method", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "budgets",
        sa.Column("public_auth_secret_hash", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "budgets",
        sa.Column("public_locked_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Plan snapshots (denormalized read-only mirrors)
    op.add_column(
        "budgets",
        sa.Column("plan_number_snapshot", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "budgets",
        sa.Column("plan_status_snapshot", sa.String(length=20), nullable=True),
    )

    # Backfill: every existing budget needs a public_token (unique)
    # and a public_auth_method (NOT NULL). Existing accepted ones are
    # tagged ``accepted_via='manual'``.
    op.execute(
        """
        CREATE EXTENSION IF NOT EXISTS pgcrypto
        """
    )
    op.execute(
        """
        UPDATE budgets
        SET public_token = gen_random_uuid()
        WHERE public_token IS NULL
        """
    )
    op.execute(
        """
        UPDATE budgets
        SET accepted_via = 'manual'
        WHERE status = 'accepted' AND accepted_via IS NULL
        """
    )
    op.execute(
        """
        UPDATE budgets
        SET public_auth_method = 'none'
        WHERE public_auth_method IS NULL
        """
    )

    op.alter_column("budgets", "public_token", nullable=False)
    op.alter_column("budgets", "public_auth_method", nullable=False)
    op.create_index(
        "idx_budgets_public_token",
        "budgets",
        ["public_token"],
        unique=True,
    )

    # Access log table
    op.create_table(
        "budget_access_logs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
        ),
        sa.Column(
            "budget_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("budgets.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "attempted_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("ip_hash", sa.String(length=64), nullable=False),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("method_attempted", sa.String(length=20), nullable=False),
    )
    op.create_index(
        "idx_budget_access_logs_budget_attempted",
        "budget_access_logs",
        ["budget_id", "attempted_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "idx_budget_access_logs_budget_attempted",
        table_name="budget_access_logs",
    )
    op.drop_table("budget_access_logs")

    op.drop_index("idx_budgets_public_token", table_name="budgets")

    op.drop_column("budgets", "plan_status_snapshot")
    op.drop_column("budgets", "plan_number_snapshot")
    op.drop_column("budgets", "public_locked_at")
    op.drop_column("budgets", "public_auth_secret_hash")
    op.drop_column("budgets", "public_auth_method")
    op.drop_column("budgets", "last_reminder_sent_at")
    op.drop_column("budgets", "viewed_at")
    op.drop_column("budgets", "public_token")
    op.drop_column("budgets", "rejection_note")
    op.drop_column("budgets", "rejection_reason")
    op.drop_column("budgets", "accepted_via")
