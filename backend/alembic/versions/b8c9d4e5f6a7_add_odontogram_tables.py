"""Add odontogram tables

Revision ID: b8c9d4e5f6a7
Revises: 74c032298f5f
Create Date: 2026-04-06 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b8c9d4e5f6a7"
down_revision: str | None = "74c032298f5f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create tooth_records table
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
    op.create_index(op.f("ix_tooth_records_clinic_id"), "tooth_records", ["clinic_id"], unique=False)
    op.create_index(op.f("ix_tooth_records_patient_id"), "tooth_records", ["patient_id"], unique=False)
    op.create_index(
        "idx_tooth_records_patient", "tooth_records", ["patient_id"], unique=False
    )
    op.create_index(
        "idx_tooth_records_clinic_patient",
        "tooth_records",
        ["clinic_id", "patient_id"],
        unique=False,
    )

    # Create odontogram_history table
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
            ["clinic_id"],
            ["clinics.id"],
        ),
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["patients.id"],
        ),
        sa.ForeignKeyConstraint(
            ["changed_by"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_odontogram_history_clinic_id"),
        "odontogram_history",
        ["clinic_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_odontogram_history_patient_id"),
        "odontogram_history",
        ["patient_id"],
        unique=False,
    )
    op.create_index(
        "idx_odontogram_history_patient",
        "odontogram_history",
        ["patient_id"],
        unique=False,
    )
    op.create_index(
        "idx_odontogram_history_tooth",
        "odontogram_history",
        ["patient_id", "tooth_number"],
        unique=False,
    )


def downgrade() -> None:
    # Drop odontogram_history
    op.drop_index("idx_odontogram_history_tooth", table_name="odontogram_history")
    op.drop_index("idx_odontogram_history_patient", table_name="odontogram_history")
    op.drop_index(op.f("ix_odontogram_history_patient_id"), table_name="odontogram_history")
    op.drop_index(op.f("ix_odontogram_history_clinic_id"), table_name="odontogram_history")
    op.drop_table("odontogram_history")

    # Drop tooth_records
    op.drop_index("idx_tooth_records_clinic_patient", table_name="tooth_records")
    op.drop_index("idx_tooth_records_patient", table_name="tooth_records")
    op.drop_index(op.f("ix_tooth_records_patient_id"), table_name="tooth_records")
    op.drop_index(op.f("ix_tooth_records_clinic_id"), table_name="tooth_records")
    op.drop_table("tooth_records")
