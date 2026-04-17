"""Add treatment_group_id column to tooth_treatments.

Revision ID: q7r8s9t0u1v2
Revises: p6q7r8s9t0u1
Create Date: 2026-04-17

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "q7r8s9t0u1v2"
down_revision: str | None = "p6q7r8s9t0u1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "tooth_treatments",
        sa.Column("treatment_group_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index(
        "idx_tooth_treatments_group",
        "tooth_treatments",
        ["treatment_group_id"],
    )


def downgrade() -> None:
    op.drop_index("idx_tooth_treatments_group", table_name="tooth_treatments")
    op.drop_column("tooth_treatments", "treatment_group_id")
