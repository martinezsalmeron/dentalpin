"""Add documents table for media module.

Revision ID: o5p6q7r8s9t0
Revises: n4o5p6q7r8s9
Create Date: 2026-04-15

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "o5p6q7r8s9t0"
down_revision: str | None = "n4o5p6q7r8s9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "documents",
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
        sa.Column("document_type", sa.String(30), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("storage_path", sa.String(500), nullable=False, unique=True),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("file_size", sa.Integer, nullable=False),
        sa.Column("extra_data", postgresql.JSONB, nullable=True, server_default="{}"),
        sa.Column(
            "uploaded_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
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

    # Create indexes
    op.create_index(
        "idx_documents_clinic_patient",
        "documents",
        ["clinic_id", "patient_id"],
    )
    op.create_index(
        "idx_documents_type",
        "documents",
        ["clinic_id", "document_type"],
    )
    op.create_index(
        "idx_documents_clinic_id",
        "documents",
        ["clinic_id"],
    )
    op.create_index(
        "idx_documents_patient_id",
        "documents",
        ["patient_id"],
    )


def downgrade() -> None:
    op.drop_index("idx_documents_patient_id", table_name="documents")
    op.drop_index("idx_documents_clinic_id", table_name="documents")
    op.drop_index("idx_documents_type", table_name="documents")
    op.drop_index("idx_documents_clinic_patient", table_name="documents")
    op.drop_table("documents")
