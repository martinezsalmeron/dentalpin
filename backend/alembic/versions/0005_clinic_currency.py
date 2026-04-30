"""core — add clinics.currency column.

Currency is a clinic-level concern (one clinic, one currency). Until
now it was either hard-coded as ``"EUR"`` on each Budget/Invoice/
catalog row or stored loosely under ``clinics.settings.currency``.

This migration promotes currency to a first-class typed column on
``clinics`` (ISO 4217, default ``EUR``), backfills from any pre-
existing JSONB key, and removes that key so there is no drift.

The redundant ``currency`` columns on Budget, Invoice, catalog and
the odontogram snapshot are dropped by per-module follow-up
migrations on each module's chain — every module owns the lifecycle
of its own table.

Revision ID: 0005
Revises: 0004
Create Date: 2026-04-30
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "clinics",
        sa.Column(
            "currency",
            sa.String(length=3),
            nullable=False,
            server_default="EUR",
        ),
    )
    # Backfill from the pre-existing JSONB key when it looks like a
    # valid ISO 4217 code (3 letters). Anything else stays as default.
    op.execute(
        """
        UPDATE clinics
        SET currency = upper(settings->>'currency')
        WHERE settings ? 'currency'
          AND settings->>'currency' ~ '^[A-Za-z]{3}$';
        """
    )
    # Remove the JSONB key — the typed column is now the source of truth.
    op.execute("UPDATE clinics SET settings = settings - 'currency';")


def downgrade() -> None:
    op.drop_column("clinics", "currency")
