"""add_patient_extended_fields_and_timeline

Revision ID: l2m3n4o5p6q7
Revises: k1l2m3n4o5p6
Create Date: 2026-04-13 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "l2m3n4o5p6q7"
down_revision: str | None = "k1l2m3n4o5p6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add extended demographics to patients
    op.add_column("patients", sa.Column("gender", sa.String(20), nullable=True))
    op.add_column("patients", sa.Column("national_id", sa.String(50), nullable=True))
    op.add_column("patients", sa.Column("national_id_type", sa.String(20), nullable=True))
    op.add_column("patients", sa.Column("profession", sa.String(100), nullable=True))
    op.add_column("patients", sa.Column("workplace", sa.String(200), nullable=True))
    op.add_column(
        "patients",
        sa.Column("preferred_language", sa.String(10), server_default="es", nullable=False),
    )
    op.add_column("patients", sa.Column("address", postgresql.JSONB(), nullable=True))
    op.add_column("patients", sa.Column("photo_url", sa.String(500), nullable=True))
    op.add_column("patients", sa.Column("emergency_contact", postgresql.JSONB(), nullable=True))
    op.add_column(
        "patients",
        sa.Column("medical_history", postgresql.JSONB(), server_default="{}", nullable=True),
    )

    # Create patient_timeline table
    op.create_table(
        "patient_timeline",
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
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("event_category", sa.String(30), nullable=False),
        sa.Column("source_table", sa.String(50), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("event_data", postgresql.JSONB(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
    )

    # Indexes for efficient timeline queries
    op.create_index("idx_timeline_patient_date", "patient_timeline", ["patient_id", "occurred_at"])
    op.create_index("idx_timeline_clinic_patient", "patient_timeline", ["clinic_id", "patient_id"])
    op.create_index("ix_patient_timeline_clinic_id", "patient_timeline", ["clinic_id"])
    op.create_index("ix_patient_timeline_patient_id", "patient_timeline", ["patient_id"])
    op.create_index("ix_patient_timeline_occurred_at", "patient_timeline", ["occurred_at"])


def downgrade() -> None:
    # Drop timeline table
    op.drop_table("patient_timeline")

    # Remove extended demographics from patients
    op.drop_column("patients", "medical_history")
    op.drop_column("patients", "emergency_contact")
    op.drop_column("patients", "photo_url")
    op.drop_column("patients", "address")
    op.drop_column("patients", "preferred_language")
    op.drop_column("patients", "workplace")
    op.drop_column("patients", "profession")
    op.drop_column("patients", "national_id_type")
    op.drop_column("patients", "national_id")
    op.drop_column("patients", "gender")
