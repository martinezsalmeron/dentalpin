"""catalog — drop currency column.

Currency is now clinic-level (``clinics.currency``, core 0005). All
catalog items in a clinic price in the clinic's currency; storing it
per item was leftover from a multi-currency design that is out of
scope.

Revision ID: cat_0002
Revises: cat_0001
Create Date: 2026-04-30
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "cat_0002"
down_revision: str | None = "cat_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_column("treatment_catalog_items", "currency")


def downgrade() -> None:
    op.add_column(
        "treatment_catalog_items",
        sa.Column(
            "currency",
            sa.String(length=3),
            nullable=False,
            server_default="EUR",
        ),
    )
