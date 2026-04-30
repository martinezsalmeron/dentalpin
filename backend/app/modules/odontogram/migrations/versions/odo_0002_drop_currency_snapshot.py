"""odontogram — drop treatments.currency_snapshot column.

Currency is now clinic-level (``clinics.currency``, core 0005). The
per-treatment snapshot existed to capture the catalog item's currency
at the time of creation in case it could differ from the clinic's —
that scenario no longer exists.

Revision ID: odo_0002
Revises: odo_0001
Create Date: 2026-04-30
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "odo_0002"
down_revision: str | None = "odo_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_column("treatments", "currency_snapshot")


def downgrade() -> None:
    op.add_column(
        "treatments",
        sa.Column("currency_snapshot", sa.String(length=3), nullable=True),
    )
