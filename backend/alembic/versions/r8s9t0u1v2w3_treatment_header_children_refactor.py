"""Refactor treatments to header + children model.

Replaces tooth_treatments with treatments + treatment_teeth. Simplifies
PlannedTreatmentItem to reference a single Treatment. Adds pricing_strategy and
pricing_config to catalog items; drops legacy vat_type/vat_rate string columns.

Revision ID: r8s9t0u1v2w3
Revises: q7r8s9t0u1v2
Create Date: 2026-04-17

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "r8s9t0u1v2w3"
down_revision: str | None = "q7r8s9t0u1v2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ------------------------------------------------------------------------
    # 1. Drop dependent FKs and tables from the old model.
    # ------------------------------------------------------------------------
    # budget_items references tooth_treatments; drop that column first.
    op.drop_index("idx_budget_items_tooth_treatment", table_name="budget_items")
    op.drop_column("budget_items", "tooth_treatment_id")

    # Drop FKs from dependent tables before dropping planned_treatment_items.
    op.drop_constraint(
        "treatment_media_planned_treatment_item_id_fkey",
        "treatment_media",
        type_="foreignkey",
    )
    op.drop_constraint(
        "appointment_treatments_planned_treatment_item_id_fkey",
        "appointment_treatments",
        type_="foreignkey",
    )

    op.drop_table("planned_treatment_items")
    op.drop_table("tooth_treatments")

    # ------------------------------------------------------------------------
    # 2. Catalog changes.
    # ------------------------------------------------------------------------
    op.add_column(
        "treatment_catalog_items",
        sa.Column("pricing_strategy", sa.String(20), nullable=False, server_default="flat"),
    )
    op.add_column(
        "treatment_catalog_items",
        sa.Column("pricing_config", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    # Drop legacy tax columns (vat_type_id stays).
    op.drop_column("treatment_catalog_items", "vat_type")
    op.drop_column("treatment_catalog_items", "vat_rate")

    # ------------------------------------------------------------------------
    # 3. Create new odontogram tables: treatments + treatment_teeth.
    # ------------------------------------------------------------------------
    op.create_table(
        "treatments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "clinic_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clinics.id"), nullable=False
        ),
        sa.Column(
            "patient_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("patients.id"),
            nullable=False,
        ),
        sa.Column("clinical_type", sa.String(30), nullable=False),
        sa.Column(
            "catalog_item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("treatment_catalog_items.id"),
            nullable=True,
        ),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("performed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "performed_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True
        ),
        sa.Column("price_snapshot", sa.Numeric(10, 2), nullable=True),
        sa.Column("currency_snapshot", sa.String(3), nullable=True),
        sa.Column("duration_snapshot", sa.Integer, nullable=True),
        sa.Column("vat_rate_snapshot", sa.Numeric(5, 2), nullable=True),
        sa.Column("budget_item_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("source_module", sa.String(30), nullable=False, server_default="odontogram"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("idx_treatments_patient", "treatments", ["patient_id"])
    op.create_index("idx_treatments_status", "treatments", ["patient_id", "status"])
    op.create_index("idx_treatments_catalog", "treatments", ["catalog_item_id"])
    op.create_index("idx_treatments_budget", "treatments", ["budget_item_id"])

    op.create_table(
        "treatment_teeth",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "treatment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("treatments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "tooth_record_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tooth_records.id"),
            nullable=False,
        ),
        sa.Column("tooth_number", sa.Integer, nullable=False),
        sa.Column("role", sa.String(20), nullable=True),
        sa.Column("surfaces", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("treatment_id", "tooth_number", name="uq_treatment_tooth"),
    )
    op.create_index("idx_treatment_teeth_treatment", "treatment_teeth", ["treatment_id"])
    op.create_index("idx_treatment_teeth_tooth_record", "treatment_teeth", ["tooth_record_id"])

    # ------------------------------------------------------------------------
    # 3b. Re-add the budget_items -> treatments link with the new target.
    # ------------------------------------------------------------------------
    op.add_column(
        "budget_items",
        sa.Column(
            "treatment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("treatments.id"),
            nullable=True,
        ),
    )
    op.create_index("idx_budget_items_treatment", "budget_items", ["treatment_id"])

    # ------------------------------------------------------------------------
    # 4. Recreate planned_treatment_items with new shape.
    # ------------------------------------------------------------------------
    op.create_table(
        "planned_treatment_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "clinic_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clinics.id"), nullable=False
        ),
        sa.Column(
            "treatment_plan_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("treatment_plans.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "treatment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("treatments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("sequence_order", sa.Integer, nullable=False, server_default="0"),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column(
            "completed_without_appointment", sa.Boolean, nullable=False, server_default=sa.false()
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "completed_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True
        ),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("treatment_id", name="uq_planned_item_treatment"),
    )
    op.create_index("idx_planned_items_plan", "planned_treatment_items", ["treatment_plan_id"])
    op.create_index("idx_planned_items_treatment", "planned_treatment_items", ["treatment_id"])
    op.create_index(
        "idx_planned_items_status", "planned_treatment_items", ["treatment_plan_id", "status"]
    )

    # Re-add FKs that we dropped before rebuilding planned_treatment_items.
    op.create_foreign_key(
        "treatment_media_planned_treatment_item_id_fkey",
        "treatment_media",
        "planned_treatment_items",
        ["planned_treatment_item_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "appointment_treatments_planned_treatment_item_id_fkey",
        "appointment_treatments",
        "planned_treatment_items",
        ["planned_treatment_item_id"],
        ["id"],
    )


def downgrade() -> None:
    # Downgrade is intentionally destructive (no data preservation).
    op.drop_index("idx_budget_items_treatment", table_name="budget_items")
    op.drop_column("budget_items", "treatment_id")

    op.drop_table("planned_treatment_items")
    op.drop_table("treatment_teeth")
    op.drop_table("treatments")

    op.add_column(
        "treatment_catalog_items",
        sa.Column("vat_rate", sa.Float, nullable=True),
    )
    op.add_column(
        "treatment_catalog_items",
        sa.Column("vat_type", sa.String(20), nullable=True),
    )
    op.drop_column("treatment_catalog_items", "pricing_config")
    op.drop_column("treatment_catalog_items", "pricing_strategy")

    # Rebuild old shape as an empty skeleton so the chain is reversible enough for dev.
    op.create_table(
        "tooth_treatments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("clinic_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
    )
    op.create_table(
        "planned_treatment_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("clinic_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("treatment_plan_id", postgresql.UUID(as_uuid=True), nullable=False),
    )
    op.add_column(
        "budget_items",
        sa.Column("tooth_treatment_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index("idx_budget_items_tooth_treatment", "budget_items", ["tooth_treatment_id"])
