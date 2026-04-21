"""v2 squash — patients initial.

Initial schema for the `patients` module.

Revision ID: pat_0001
Revises:
Create Date: 2026-04-21

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "pat_0001"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "patients",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("first_name", sa.String(length=100), nullable=False),
        sa.Column("last_name", sa.String(length=100), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("gender", sa.String(length=20), nullable=True),
        sa.Column("national_id", sa.String(length=50), nullable=True),
        sa.Column("national_id_type", sa.String(length=20), nullable=True),
        sa.Column("profession", sa.String(length=100), nullable=True),
        sa.Column("workplace", sa.String(length=200), nullable=True),
        sa.Column("preferred_language", sa.String(length=10), nullable=False),
        sa.Column("address", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("photo_url", sa.String(length=500), nullable=True),
        sa.Column("billing_name", sa.String(length=200), nullable=True),
        sa.Column("billing_tax_id", sa.String(length=50), nullable=True),
        sa.Column("billing_address", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("billing_email", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinics.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_patients_clinic_id"), "patients", ["clinic_id"], unique=False)


def downgrade() -> None:
    op.drop_table("patients")
