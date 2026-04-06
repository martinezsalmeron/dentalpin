"""add soft delete to treatments

Revision ID: d0e1f2a3b4c5
Revises: c9d0e5f6a7b8
Create Date: 2026-04-06

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d0e1f2a3b4c5"
down_revision: str | None = "c9d0e5f6a7b8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add deleted_at column for soft delete support
    op.add_column(
        "tooth_treatments", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True)
    )
    # Add index for filtering non-deleted treatments
    op.create_index(
        "idx_tooth_treatments_deleted_at",
        "tooth_treatments",
        ["deleted_at"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("idx_tooth_treatments_deleted_at", table_name="tooth_treatments")
    op.drop_column("tooth_treatments", "deleted_at")
