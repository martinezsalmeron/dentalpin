"""Add catalog_item_id to tooth_treatments.

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2024-04-09

Links tooth treatments to catalog items for pricing and nomenclature.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: str | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add catalog_item_id column to tooth_treatments
    op.add_column(
        "tooth_treatments",
        sa.Column("catalog_item_id", sa.UUID(), nullable=True),
    )
    op.create_foreign_key(
        "fk_tooth_treatments_catalog_item",
        "tooth_treatments",
        "treatment_catalog_items",
        ["catalog_item_id"],
        ["id"],
    )
    op.create_index(
        "idx_tooth_treatments_catalog",
        "tooth_treatments",
        ["catalog_item_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_tooth_treatments_catalog", table_name="tooth_treatments")
    op.drop_constraint("fk_tooth_treatments_catalog_item", "tooth_treatments", type_="foreignkey")
    op.drop_column("tooth_treatments", "catalog_item_id")
