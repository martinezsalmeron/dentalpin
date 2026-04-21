"""v2 squash — odontogram initial.

Initial schema for the `odontogram` module.

Revision ID: odo_0001
Revises:
Create Date: 2026-04-21

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "odo_0001"
down_revision: str | None = "cat_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "odontogram_history",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("patient_id", sa.UUID(), nullable=False),
        sa.Column("tooth_number", sa.Integer(), nullable=False),
        sa.Column("change_type", sa.String(length=30), nullable=False),
        sa.Column("surface", sa.String(length=1), nullable=True),
        sa.Column("old_condition", sa.String(length=30), nullable=True),
        sa.Column("new_condition", sa.String(length=30), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("changed_by", sa.UUID(), nullable=False),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["changed_by"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinics.id"],
        ),
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["patients.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_odontogram_history_patient", "odontogram_history", ["patient_id"], unique=False
    )
    op.create_index(
        "idx_odontogram_history_tooth",
        "odontogram_history",
        ["patient_id", "tooth_number"],
        unique=False,
    )
    op.create_index(
        op.f("ix_odontogram_history_clinic_id"), "odontogram_history", ["clinic_id"], unique=False
    )
    op.create_index(
        op.f("ix_odontogram_history_patient_id"), "odontogram_history", ["patient_id"], unique=False
    )

    op.create_table(
        "tooth_records",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("patient_id", sa.UUID(), nullable=False),
        sa.Column("tooth_number", sa.Integer(), nullable=False),
        sa.Column("tooth_type", sa.String(length=20), nullable=False),
        sa.Column("general_condition", sa.String(length=30), nullable=False),
        sa.Column("surfaces", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_displaced", sa.Boolean(), nullable=False),
        sa.Column("is_rotated", sa.Boolean(), nullable=False),
        sa.Column("displacement_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinics.id"],
        ),
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["patients.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("patient_id", "tooth_number", name="uq_patient_tooth"),
    )
    op.create_index(
        "idx_tooth_records_clinic_patient",
        "tooth_records",
        ["clinic_id", "patient_id"],
        unique=False,
    )
    op.create_index("idx_tooth_records_patient", "tooth_records", ["patient_id"], unique=False)
    op.create_index(
        op.f("ix_tooth_records_clinic_id"), "tooth_records", ["clinic_id"], unique=False
    )
    op.create_index(
        op.f("ix_tooth_records_patient_id"), "tooth_records", ["patient_id"], unique=False
    )

    op.create_table(
        "treatments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("patient_id", sa.UUID(), nullable=False),
        sa.Column("clinical_type", sa.String(length=30), nullable=False),
        sa.Column("scope", sa.String(length=20), nullable=False),
        sa.Column("arch", sa.String(length=10), nullable=True),
        sa.Column("catalog_item_id", sa.UUID(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("performed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("performed_by", sa.UUID(), nullable=True),
        sa.Column("price_snapshot", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("currency_snapshot", sa.String(length=3), nullable=True),
        sa.Column("duration_snapshot", sa.Integer(), nullable=True),
        sa.Column("vat_rate_snapshot", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("budget_item_id", sa.UUID(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("source_module", sa.String(length=30), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "(scope = 'global_arch' AND arch IS NOT NULL) OR (scope <> 'global_arch' AND arch IS NULL)",
            name="ck_treatments_arch_matches_scope",
        ),
        sa.CheckConstraint(
            "arch IS NULL OR arch IN ('upper', 'lower')", name="ck_treatments_arch_value"
        ),
        sa.CheckConstraint(
            "scope IN ('tooth', 'multi_tooth', 'global_mouth', 'global_arch')",
            name="ck_treatments_scope",
        ),
        sa.ForeignKeyConstraint(
            ["catalog_item_id"],
            ["treatment_catalog_items.id"],
        ),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinics.id"],
        ),
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["patients.id"],
        ),
        sa.ForeignKeyConstraint(
            ["performed_by"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_treatments_budget", "treatments", ["budget_item_id"], unique=False)
    op.create_index("idx_treatments_catalog", "treatments", ["catalog_item_id"], unique=False)
    op.create_index("idx_treatments_patient", "treatments", ["patient_id"], unique=False)
    op.create_index("idx_treatments_status", "treatments", ["patient_id", "status"], unique=False)
    op.create_index(
        op.f("ix_treatments_catalog_item_id"), "treatments", ["catalog_item_id"], unique=False
    )
    op.create_index(op.f("ix_treatments_clinic_id"), "treatments", ["clinic_id"], unique=False)
    op.create_index(op.f("ix_treatments_patient_id"), "treatments", ["patient_id"], unique=False)

    op.create_table(
        "treatment_teeth",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("treatment_id", sa.UUID(), nullable=False),
        sa.Column("tooth_record_id", sa.UUID(), nullable=False),
        sa.Column("tooth_number", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=True),
        sa.Column("surfaces", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["tooth_record_id"],
            ["tooth_records.id"],
        ),
        sa.ForeignKeyConstraint(["treatment_id"], ["treatments.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("treatment_id", "tooth_number", name="uq_treatment_tooth"),
    )
    op.create_index(
        "idx_treatment_teeth_tooth_record", "treatment_teeth", ["tooth_record_id"], unique=False
    )
    op.create_index(
        "idx_treatment_teeth_treatment", "treatment_teeth", ["treatment_id"], unique=False
    )
    op.create_index(
        op.f("ix_treatment_teeth_tooth_record_id"),
        "treatment_teeth",
        ["tooth_record_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_treatment_teeth_treatment_id"), "treatment_teeth", ["treatment_id"], unique=False
    )


def downgrade() -> None:
    op.drop_table("treatment_teeth")
    op.drop_table("treatments")
    op.drop_table("tooth_records")
    op.drop_table("odontogram_history")
