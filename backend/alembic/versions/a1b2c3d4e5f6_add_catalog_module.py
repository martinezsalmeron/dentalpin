"""Add catalog module tables.

Revision ID: a1b2c3d4e5f6
Revises: f2a3b4c5d6e7
Create Date: 2024-04-09

Tables created:
- treatment_categories: Hierarchical treatment categories
- treatment_catalog_items: Treatment catalog with pricing and VAT
- treatment_odontogram_mappings: Bridge to odontogram visualization
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "f2a3b4c5d6e7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create treatment_categories table
    op.create_table(
        "treatment_categories",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("parent_id", sa.UUID(), nullable=True),
        sa.Column("key", sa.String(length=50), nullable=False),
        sa.Column(
            "names", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"
        ),
        sa.Column("descriptions", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("icon", sa.String(length=50), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinics.id"],
        ),
        sa.ForeignKeyConstraint(
            ["parent_id"],
            ["treatment_categories.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("clinic_id", "key", name="uq_category_clinic_key"),
    )
    op.create_index(
        "idx_treatment_categories_clinic", "treatment_categories", ["clinic_id"], unique=False
    )
    op.create_index(
        "idx_treatment_categories_parent", "treatment_categories", ["parent_id"], unique=False
    )

    # Create treatment_catalog_items table
    op.create_table(
        "treatment_catalog_items",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("category_id", sa.UUID(), nullable=False),
        sa.Column("internal_code", sa.String(length=50), nullable=False),
        sa.Column(
            "names", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"
        ),
        sa.Column("descriptions", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        # Pricing
        sa.Column("default_price", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("cost_price", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="EUR"),
        # Scheduling
        sa.Column("default_duration_minutes", sa.Integer(), nullable=True),
        sa.Column("requires_appointment", sa.Boolean(), nullable=False, server_default="true"),
        # Tax
        sa.Column("vat_type", sa.String(length=20), nullable=False, server_default="'exempt'"),
        sa.Column("vat_rate", sa.Float(), nullable=False, server_default="0.0"),
        # Treatment characteristics
        sa.Column(
            "treatment_scope", sa.String(length=20), nullable=False, server_default="'whole_tooth'"
        ),
        sa.Column("is_diagnostic", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("requires_surfaces", sa.Boolean(), nullable=False, server_default="false"),
        # Material
        sa.Column("material_notes", sa.Text(), nullable=True),
        # Status
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinics.id"],
        ),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["treatment_categories.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("clinic_id", "internal_code", name="uq_catalog_item_clinic_code"),
    )
    op.create_index(
        "idx_catalog_items_clinic", "treatment_catalog_items", ["clinic_id"], unique=False
    )
    op.create_index(
        "idx_catalog_items_category", "treatment_catalog_items", ["category_id"], unique=False
    )
    op.create_index(
        "idx_catalog_items_active",
        "treatment_catalog_items",
        ["clinic_id", "is_active"],
        unique=False,
    )

    # Create treatment_odontogram_mappings table
    op.create_table(
        "treatment_odontogram_mappings",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("catalog_item_id", sa.UUID(), nullable=False),
        sa.Column("odontogram_treatment_type", sa.String(length=30), nullable=False),
        sa.Column(
            "visualization_rules",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "visualization_config",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("clinical_category", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinics.id"],
        ),
        sa.ForeignKeyConstraint(
            ["catalog_item_id"],
            ["treatment_catalog_items.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("catalog_item_id"),
    )
    op.create_index(
        "idx_odontogram_mapping_clinic",
        "treatment_odontogram_mappings",
        ["clinic_id"],
        unique=False,
    )
    op.create_index(
        "idx_odontogram_mapping_type",
        "treatment_odontogram_mappings",
        ["odontogram_treatment_type"],
        unique=False,
    )


def downgrade() -> None:
    # Drop treatment_odontogram_mappings
    op.drop_index("idx_odontogram_mapping_type", table_name="treatment_odontogram_mappings")
    op.drop_index("idx_odontogram_mapping_clinic", table_name="treatment_odontogram_mappings")
    op.drop_table("treatment_odontogram_mappings")

    # Drop treatment_catalog_items
    op.drop_index("idx_catalog_items_active", table_name="treatment_catalog_items")
    op.drop_index("idx_catalog_items_category", table_name="treatment_catalog_items")
    op.drop_index("idx_catalog_items_clinic", table_name="treatment_catalog_items")
    op.drop_table("treatment_catalog_items")

    # Drop treatment_categories
    op.drop_index("idx_treatment_categories_parent", table_name="treatment_categories")
    op.drop_index("idx_treatment_categories_clinic", table_name="treatment_categories")
    op.drop_table("treatment_categories")
