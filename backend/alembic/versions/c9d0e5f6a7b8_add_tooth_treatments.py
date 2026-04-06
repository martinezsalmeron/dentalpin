"""Add tooth treatments table and positional fields

Revision ID: c9d0e5f6a7b8
Revises: b8c9d4e5f6a7
Create Date: 2026-04-06 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c9d0e5f6a7b8"
down_revision: str | None = "b8c9d4e5f6a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add positional fields to tooth_records
    op.add_column(
        "tooth_records",
        sa.Column("is_displaced", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "tooth_records",
        sa.Column("is_rotated", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "tooth_records",
        sa.Column("displacement_notes", sa.Text(), nullable=True),
    )

    # Create tooth_treatments table
    op.create_table(
        "tooth_treatments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("patient_id", sa.UUID(), nullable=False),
        sa.Column("tooth_record_id", sa.UUID(), nullable=False),
        sa.Column("tooth_number", sa.Integer(), nullable=False),
        sa.Column("treatment_type", sa.String(length=30), nullable=False),
        sa.Column("treatment_category", sa.String(length=20), nullable=False),
        sa.Column("surfaces", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="performed"),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("performed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("performed_by", sa.UUID(), nullable=True),
        sa.Column("budget_item_id", sa.UUID(), nullable=True),
        sa.Column("source_module", sa.String(length=30), nullable=False, server_default="odontogram"),
        sa.Column("notes", sa.Text(), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["tooth_record_id"],
            ["tooth_records.id"],
        ),
        sa.ForeignKeyConstraint(
            ["performed_by"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_tooth_treatments_clinic_id"),
        "tooth_treatments",
        ["clinic_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_tooth_treatments_patient_id"),
        "tooth_treatments",
        ["patient_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_tooth_treatments_tooth_record_id"),
        "tooth_treatments",
        ["tooth_record_id"],
        unique=False,
    )
    op.create_index(
        "idx_tooth_treatments_patient",
        "tooth_treatments",
        ["patient_id"],
        unique=False,
    )
    op.create_index(
        "idx_tooth_treatments_tooth_record",
        "tooth_treatments",
        ["tooth_record_id"],
        unique=False,
    )
    op.create_index(
        "idx_tooth_treatments_status",
        "tooth_treatments",
        ["patient_id", "status"],
        unique=False,
    )
    op.create_index(
        "idx_tooth_treatments_budget",
        "tooth_treatments",
        ["budget_item_id"],
        unique=False,
    )


def downgrade() -> None:
    # Drop tooth_treatments table and indexes
    op.drop_index("idx_tooth_treatments_budget", table_name="tooth_treatments")
    op.drop_index("idx_tooth_treatments_status", table_name="tooth_treatments")
    op.drop_index("idx_tooth_treatments_tooth_record", table_name="tooth_treatments")
    op.drop_index("idx_tooth_treatments_patient", table_name="tooth_treatments")
    op.drop_index(op.f("ix_tooth_treatments_tooth_record_id"), table_name="tooth_treatments")
    op.drop_index(op.f("ix_tooth_treatments_patient_id"), table_name="tooth_treatments")
    op.drop_index(op.f("ix_tooth_treatments_clinic_id"), table_name="tooth_treatments")
    op.drop_table("tooth_treatments")

    # Remove positional fields from tooth_records
    op.drop_column("tooth_records", "displacement_notes")
    op.drop_column("tooth_records", "is_rotated")
    op.drop_column("tooth_records", "is_displaced")
