"""Add VAT types table and migrate treatment_catalog_items.

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2024-04-10

Tables created:
- vat_types: Centralized VAT type definitions per clinic

Changes to treatment_catalog_items:
- Add vat_type_id column (FK to vat_types)
- Keep old vat_type/vat_rate columns temporarily for data migration
"""

from collections.abc import Sequence
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6a7b8"
down_revision: str | None = "b2c3d4e5f6a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# Default VAT types to create for each clinic
DEFAULT_VAT_TYPES = [
    {
        "names": {"es": "Exento", "en": "Exempt"},
        "rate": 0.0,
        "is_default": True,
        "is_system": True,
    },
    {
        "names": {"es": "Reducido (10%)", "en": "Reduced (10%)"},
        "rate": 10.0,
        "is_default": False,
        "is_system": True,
    },
    {
        "names": {"es": "General (21%)", "en": "Standard (21%)"},
        "rate": 21.0,
        "is_default": False,
        "is_system": True,
    },
]


def upgrade() -> None:
    # Create vat_types table
    op.create_table(
        "vat_types",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column(
            "names", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"
        ),
        sa.Column("rate", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default="false"),
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

    # Add vat_type_id column to treatment_catalog_items (nullable for now)
    op.add_column(
        "treatment_catalog_items",
        sa.Column("vat_type_id", sa.UUID(), nullable=True),
    )
    op.create_foreign_key(
        "fk_catalog_items_vat_type",
        "treatment_catalog_items",
        "vat_types",
        ["vat_type_id"],
        ["id"],
    )
    op.create_index(
        "idx_catalog_items_vat_type",
        "treatment_catalog_items",
        ["vat_type_id"],
        unique=False,
    )

    # Make old columns nullable for transition
    op.alter_column(
        "treatment_catalog_items",
        "vat_type",
        existing_type=sa.String(length=20),
        nullable=True,
    )
    op.alter_column(
        "treatment_catalog_items",
        "vat_rate",
        existing_type=sa.Float(),
        nullable=True,
    )

    # Data migration: create default VAT types for each clinic and update catalog items
    connection = op.get_bind()

    # Get all clinics
    clinics = connection.execute(sa.text("SELECT id FROM clinics")).fetchall()

    for (clinic_id,) in clinics:
        # Create default VAT types for this clinic
        vat_type_map = {}  # Maps (vat_type_str, rate) -> vat_type_id

        for vat_config in DEFAULT_VAT_TYPES:
            vat_id = uuid4()
            connection.execute(
                sa.text("""
                    INSERT INTO vat_types (id, clinic_id, names, rate, is_default, is_active, is_system, created_at, updated_at)
                    VALUES (:id, :clinic_id, :names, :rate, :is_default, true, :is_system, NOW(), NOW())
                """),
                {
                    "id": str(vat_id),
                    "clinic_id": str(clinic_id),
                    "names": sa.type_coerce(vat_config["names"], postgresql.JSONB),
                    "rate": vat_config["rate"],
                    "is_default": vat_config["is_default"],
                    "is_system": vat_config["is_system"],
                },
            )

            # Build mapping for old vat_type strings to new vat_type_id
            if vat_config["rate"] == 0.0:
                vat_type_map["exempt"] = vat_id
            elif vat_config["rate"] == 10.0:
                vat_type_map["reduced"] = vat_id
            elif vat_config["rate"] == 21.0:
                vat_type_map["standard"] = vat_id

        # Update catalog items to use new vat_type_id
        for old_type, new_id in vat_type_map.items():
            connection.execute(
                sa.text("""
                    UPDATE treatment_catalog_items
                    SET vat_type_id = :vat_type_id
                    WHERE clinic_id = :clinic_id AND vat_type = :old_type
                """),
                {
                    "vat_type_id": str(new_id),
                    "clinic_id": str(clinic_id),
                    "old_type": old_type,
                },
            )

        # For any items without a vat_type, use the default (exempt)
        default_vat_id = vat_type_map.get("exempt")
        if default_vat_id:
            connection.execute(
                sa.text("""
                    UPDATE treatment_catalog_items
                    SET vat_type_id = :vat_type_id
                    WHERE clinic_id = :clinic_id AND vat_type_id IS NULL
                """),
                {
                    "vat_type_id": str(default_vat_id),
                    "clinic_id": str(clinic_id),
                },
            )


def downgrade() -> None:
    # Remove vat_type_id column from treatment_catalog_items
    op.drop_index("idx_catalog_items_vat_type", table_name="treatment_catalog_items")
    op.drop_constraint("fk_catalog_items_vat_type", "treatment_catalog_items", type_="foreignkey")
    op.drop_column("treatment_catalog_items", "vat_type_id")

    # Make old columns non-nullable again with defaults
    op.alter_column(
        "treatment_catalog_items",
        "vat_type",
        existing_type=sa.String(length=20),
        nullable=False,
        server_default="'exempt'",
    )
    op.alter_column(
        "treatment_catalog_items",
        "vat_rate",
        existing_type=sa.Float(),
        nullable=False,
        server_default="0.0",
    )

    # Drop vat_types table
    op.drop_index("idx_vat_types_default", table_name="vat_types")
    op.drop_index("idx_vat_types_clinic", table_name="vat_types")
    op.drop_table("vat_types")
