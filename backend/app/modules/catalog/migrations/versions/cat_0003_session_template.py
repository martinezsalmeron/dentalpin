"""Add catalog_item_sessions for multi-session billing templates.

Lets clinics define named, priced steps for treatments billed in
stages (e.g. Crown: "Impressions" 200€ + "Placement" 600€). Treatment
plans snapshot this template when the catalog item is added to a plan.

Revision ID: cat_0003
Revises: cat_0002
Create Date: 2026-05-19

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "cat_0003"
down_revision: str | None = "cat_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "catalog_item_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "catalog_item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("treatment_catalog_items.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column(
            "labels",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("default_price", sa.Numeric(10, 2), nullable=False),
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
        sa.UniqueConstraint("catalog_item_id", "sequence", name="uq_catalog_session_item_sequence"),
    )
    op.create_index(
        "idx_catalog_sessions_item",
        "catalog_item_sessions",
        ["catalog_item_id"],
    )


def downgrade() -> None:
    op.drop_index("idx_catalog_sessions_item", table_name="catalog_item_sessions")
    op.drop_table("catalog_item_sessions")
