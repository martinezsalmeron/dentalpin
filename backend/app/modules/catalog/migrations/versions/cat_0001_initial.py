"""v2 squash — catalog initial.

Initial schema for the `catalog` module.

Revision ID: cat_0001
Revises:
Create Date: 2026-04-21

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "cat_0001"
down_revision: str | None = "pat_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "treatment_categories",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("parent_id", sa.UUID(), nullable=True),
        sa.Column("key", sa.String(length=50), nullable=False),
        sa.Column("names", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("descriptions", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("icon", sa.String(length=50), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_system", sa.Boolean(), nullable=False),
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
    op.create_index(
        op.f("ix_treatment_categories_clinic_id"),
        "treatment_categories",
        ["clinic_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_treatment_categories_parent_id"),
        "treatment_categories",
        ["parent_id"],
        unique=False,
    )

    op.create_table(
        "vat_types",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("names", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("rate", sa.Float(), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_system", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinics.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_vat_types_clinic", "vat_types", ["clinic_id"], unique=False)
    op.create_index("idx_vat_types_default", "vat_types", ["clinic_id", "is_default"], unique=False)
    op.create_index(op.f("ix_vat_types_clinic_id"), "vat_types", ["clinic_id"], unique=False)

    op.create_table(
        "treatment_catalog_items",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("category_id", sa.UUID(), nullable=False),
        sa.Column("internal_code", sa.String(length=50), nullable=False),
        sa.Column("names", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("descriptions", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("default_price", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("cost_price", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("default_duration_minutes", sa.Integer(), nullable=True),
        sa.Column("requires_appointment", sa.Boolean(), nullable=False),
        sa.Column("vat_type_id", sa.UUID(), nullable=True),
        sa.Column("pricing_strategy", sa.String(length=20), nullable=False),
        sa.Column("pricing_config", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("surface_prices", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("treatment_scope", sa.String(length=20), nullable=False),
        sa.Column("is_diagnostic", sa.Boolean(), nullable=False),
        sa.Column("requires_surfaces", sa.Boolean(), nullable=False),
        sa.Column("billing_mode", sa.String(length=20), nullable=False),
        sa.Column("material_notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_system", sa.Boolean(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["treatment_categories.id"],
        ),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinics.id"],
        ),
        sa.ForeignKeyConstraint(
            ["vat_type_id"],
            ["vat_types.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("clinic_id", "internal_code", name="uq_catalog_item_clinic_code"),
    )
    op.create_index(
        "idx_catalog_items_active",
        "treatment_catalog_items",
        ["clinic_id", "is_active"],
        unique=False,
    )
    op.create_index(
        "idx_catalog_items_category", "treatment_catalog_items", ["category_id"], unique=False
    )
    op.create_index(
        "idx_catalog_items_clinic", "treatment_catalog_items", ["clinic_id"], unique=False
    )
    op.create_index(
        "idx_catalog_items_vat_type", "treatment_catalog_items", ["vat_type_id"], unique=False
    )
    op.create_index(
        op.f("ix_treatment_catalog_items_category_id"),
        "treatment_catalog_items",
        ["category_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_treatment_catalog_items_clinic_id"),
        "treatment_catalog_items",
        ["clinic_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_treatment_catalog_items_vat_type_id"),
        "treatment_catalog_items",
        ["vat_type_id"],
        unique=False,
    )

    op.create_table(
        "treatment_odontogram_mappings",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("catalog_item_id", sa.UUID(), nullable=False),
        sa.Column("odontogram_treatment_type", sa.String(length=30), nullable=False),
        sa.Column("visualization_rules", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("visualization_config", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("clinical_category", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["catalog_item_id"], ["treatment_catalog_items.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinics.id"],
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
    op.create_index(
        op.f("ix_treatment_odontogram_mappings_clinic_id"),
        "treatment_odontogram_mappings",
        ["clinic_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("treatment_odontogram_mappings")
    op.drop_table("treatment_catalog_items")
    op.drop_table("vat_types")
    op.drop_table("treatment_categories")
