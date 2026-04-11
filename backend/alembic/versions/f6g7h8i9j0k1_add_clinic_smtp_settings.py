"""Add clinic SMTP settings table.

Revision ID: f6g7h8i9j0k1
Revises: e5f6a7b8c9d0
Create Date: 2024-04-12

Tables created:
- clinic_smtp_settings: Per-clinic SMTP configuration
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f6g7h8i9j0k1"
down_revision: str | None = "e5f6a7b8c9d0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create clinic_smtp_settings table
    op.create_table(
        "clinic_smtp_settings",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        # Provider selection
        sa.Column("provider", sa.String(length=20), nullable=False, server_default="'smtp'"),
        # SMTP Configuration
        sa.Column("host", sa.String(length=255), nullable=True),
        sa.Column("port", sa.Integer(), nullable=False, server_default="587"),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("password_encrypted", sa.Text(), nullable=True),
        sa.Column("use_tls", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("use_ssl", sa.Boolean(), nullable=False, server_default="false"),
        # Sender defaults
        sa.Column("from_email", sa.String(length=255), nullable=True),
        sa.Column("from_name", sa.String(length=255), nullable=True),
        # Status
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        # Constraints
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("clinic_id", name="uq_clinic_smtp_settings_clinic"),
    )
    op.create_index(
        "idx_clinic_smtp_settings_clinic",
        "clinic_smtp_settings",
        ["clinic_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_clinic_smtp_settings_clinic", table_name="clinic_smtp_settings")
    op.drop_table("clinic_smtp_settings")
