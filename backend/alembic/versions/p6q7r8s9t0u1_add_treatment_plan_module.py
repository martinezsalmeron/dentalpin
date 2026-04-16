"""Add treatment plan module tables and extend existing models.

Revision ID: p6q7r8s9t0u1
Revises: o5p6q7r8s9t0
Create Date: 2026-04-15

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "p6q7r8s9t0u1"
down_revision: str | None = "o5p6q7r8s9t0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # -------------------------------------------------------------------------
    # 1. Create treatment_plans table
    # -------------------------------------------------------------------------
    op.create_table(
        "treatment_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "clinic_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clinics.id"),
            nullable=False,
        ),
        sa.Column(
            "patient_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("patients.id"),
            nullable=False,
        ),
        sa.Column("plan_number", sa.String(50), nullable=False),
        sa.Column("title", sa.String(200), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column(
            "budget_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("budgets.id"),
            nullable=True,
            unique=True,
        ),
        sa.Column(
            "assigned_professional_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("diagnosis_notes", sa.Text, nullable=True),
        sa.Column("internal_notes", sa.Text, nullable=True),
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
        sa.UniqueConstraint("clinic_id", "plan_number", name="uq_treatment_plan_number"),
    )

    # Create indexes for treatment_plans
    op.create_index(
        "idx_treatment_plans_clinic",
        "treatment_plans",
        ["clinic_id"],
    )
    op.create_index(
        "idx_treatment_plans_patient",
        "treatment_plans",
        ["patient_id"],
    )
    op.create_index(
        "idx_treatment_plans_status",
        "treatment_plans",
        ["clinic_id", "status"],
    )
    op.create_index(
        "idx_treatment_plans_budget",
        "treatment_plans",
        ["budget_id"],
    )

    # -------------------------------------------------------------------------
    # 2. Create planned_treatment_items table
    # -------------------------------------------------------------------------
    op.create_table(
        "planned_treatment_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "clinic_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clinics.id"),
            nullable=False,
        ),
        sa.Column(
            "treatment_plan_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("treatment_plans.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "tooth_treatment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tooth_treatments.id"),
            nullable=True,
        ),
        sa.Column(
            "catalog_item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("treatment_catalog_items.id"),
            nullable=True,
        ),
        sa.Column("is_global", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("sequence_order", sa.Integer, nullable=False, server_default="0"),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column(
            "completed_without_appointment",
            sa.Boolean,
            nullable=False,
            server_default="false",
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "completed_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
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
    )

    # Create indexes for planned_treatment_items
    op.create_index(
        "idx_planned_items_clinic",
        "planned_treatment_items",
        ["clinic_id"],
    )
    op.create_index(
        "idx_planned_items_plan",
        "planned_treatment_items",
        ["treatment_plan_id"],
    )
    op.create_index(
        "idx_planned_items_tooth",
        "planned_treatment_items",
        ["tooth_treatment_id"],
    )
    op.create_index(
        "idx_planned_items_status",
        "planned_treatment_items",
        ["treatment_plan_id", "status"],
    )

    # -------------------------------------------------------------------------
    # 3. Create treatment_media table
    # -------------------------------------------------------------------------
    op.create_table(
        "treatment_media",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "clinic_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clinics.id"),
            nullable=False,
        ),
        sa.Column(
            "planned_treatment_item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("planned_treatment_items.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("media_type", sa.String(20), nullable=False),
        sa.Column("display_order", sa.Integer, nullable=False, server_default="0"),
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
    )

    # Create indexes for treatment_media
    op.create_index(
        "idx_treatment_media_clinic",
        "treatment_media",
        ["clinic_id"],
    )
    op.create_index(
        "idx_treatment_media_item",
        "treatment_media",
        ["planned_treatment_item_id"],
    )
    op.create_index(
        "idx_treatment_media_document",
        "treatment_media",
        ["document_id"],
    )

    # -------------------------------------------------------------------------
    # 4. Extend appointment_treatments table
    # -------------------------------------------------------------------------
    op.add_column(
        "appointment_treatments",
        sa.Column(
            "planned_treatment_item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("planned_treatment_items.id"),
            nullable=True,
        ),
    )
    op.add_column(
        "appointment_treatments",
        sa.Column(
            "completed_in_appointment",
            sa.Boolean,
            nullable=False,
            server_default="false",
        ),
    )
    op.add_column(
        "appointment_treatments",
        sa.Column("notes", sa.Text, nullable=True),
    )
    op.create_index(
        "idx_appointment_treatments_planned_item",
        "appointment_treatments",
        ["planned_treatment_item_id"],
    )

    # -------------------------------------------------------------------------
    # 5. Extend treatment_catalog_items table
    # -------------------------------------------------------------------------
    op.add_column(
        "treatment_catalog_items",
        sa.Column(
            "billing_mode",
            sa.String(20),
            nullable=False,
            server_default="on_completion",
        ),
    )


def downgrade() -> None:
    # Remove billing_mode from treatment_catalog_items
    op.drop_column("treatment_catalog_items", "billing_mode")

    # Remove columns from appointment_treatments
    op.drop_index(
        "idx_appointment_treatments_planned_item", table_name="appointment_treatments"
    )
    op.drop_column("appointment_treatments", "notes")
    op.drop_column("appointment_treatments", "completed_in_appointment")
    op.drop_column("appointment_treatments", "planned_treatment_item_id")

    # Drop treatment_media
    op.drop_index("idx_treatment_media_document", table_name="treatment_media")
    op.drop_index("idx_treatment_media_item", table_name="treatment_media")
    op.drop_index("idx_treatment_media_clinic", table_name="treatment_media")
    op.drop_table("treatment_media")

    # Drop planned_treatment_items
    op.drop_index("idx_planned_items_status", table_name="planned_treatment_items")
    op.drop_index("idx_planned_items_tooth", table_name="planned_treatment_items")
    op.drop_index("idx_planned_items_plan", table_name="planned_treatment_items")
    op.drop_index("idx_planned_items_clinic", table_name="planned_treatment_items")
    op.drop_table("planned_treatment_items")

    # Drop treatment_plans
    op.drop_index("idx_treatment_plans_budget", table_name="treatment_plans")
    op.drop_index("idx_treatment_plans_status", table_name="treatment_plans")
    op.drop_index("idx_treatment_plans_patient", table_name="treatment_plans")
    op.drop_index("idx_treatment_plans_clinic", table_name="treatment_plans")
    op.drop_table("treatment_plans")
