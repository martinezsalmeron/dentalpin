"""whatsapp_kapso: initial schema.

Tables (own Alembic branch ``whatsapp_kapso`` per ADR 0002, so uninstall is
branch-scoped and drops only these):
    - ``whatsapp_kapso_settings`` — per-clinic Kapso credentials + number.
    - ``whatsapp_kapso_templates`` — cached Meta templates for the picker.

Revision ID: wak_0001
Revises:
Create Date: 2026-06-26
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "wak_0001"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = ("whatsapp_kapso",)
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "whatsapp_kapso_settings",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("api_key_encrypted", sa.Text(), nullable=False),
        sa.Column("phone_number_id", sa.String(length=64), nullable=False),
        sa.Column("business_account_id", sa.String(length=64), nullable=True),
        sa.Column("webhook_secret_encrypted", sa.Text(), nullable=False),
        sa.Column("display_phone_number", sa.String(length=32), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_verified", sa.Boolean(), nullable=False),
        sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_template_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_whatsapp_kapso_settings_clinic", "whatsapp_kapso_settings", ["clinic_id"], unique=False
    )
    op.create_index(
        "idx_whatsapp_kapso_settings_phone_number_id",
        "whatsapp_kapso_settings",
        ["phone_number_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_whatsapp_kapso_settings_clinic_id"),
        "whatsapp_kapso_settings",
        ["clinic_id"],
        unique=True,
    )
    op.create_index(
        op.f("ix_whatsapp_kapso_settings_phone_number_id"),
        "whatsapp_kapso_settings",
        ["phone_number_id"],
        unique=False,
    )

    op.create_table(
        "whatsapp_kapso_templates",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("language", sa.String(length=10), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=True),
        sa.Column("synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("clinic_id", "name", "language", name="uq_whatsapp_kapso_template"),
    )
    op.create_index(
        "idx_whatsapp_kapso_templates_clinic",
        "whatsapp_kapso_templates",
        ["clinic_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_whatsapp_kapso_templates_clinic_id"),
        "whatsapp_kapso_templates",
        ["clinic_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("whatsapp_kapso_templates")
    op.drop_table("whatsapp_kapso_settings")
