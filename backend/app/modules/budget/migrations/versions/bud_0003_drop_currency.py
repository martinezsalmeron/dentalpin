"""budget — drop currency column.

Currency is now clinic-level (``clinics.currency``, core 0005). A
clinic operates in a single currency, so the per-budget snapshot is
redundant. Renderers read ``clinic.currency`` at PDF/email time.

The app is not in production, so we drop the column outright instead
of carrying a deprecated NOT-NULL field forever.

Revision ID: bud_0003
Revises: bud_0002
Create Date: 2026-04-30
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "bud_0003"
down_revision: str | None = "bud_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_column("budgets", "currency")


def downgrade() -> None:
    op.add_column(
        "budgets",
        sa.Column(
            "currency",
            sa.String(length=3),
            nullable=False,
            server_default="EUR",
        ),
    )
