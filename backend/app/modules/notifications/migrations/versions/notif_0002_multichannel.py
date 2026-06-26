"""notifications: generalize email-only → multi-channel gateway.

Renames ``email_templates`` → ``notification_templates`` and ``email_logs``
→ ``communication_messages`` (data preserved, ``channel`` backfilled to
``'email'``), adds the outbox/retry lifecycle, per-channel WhatsApp opt-in on
preferences, and the generic ``clinic_channel_settings`` table.

Revision ID: notif_0002
Revises: notif_0001
Create Date: 2026-06-26

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "notif_0002"
down_revision: str | None = "notif_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ---- email_templates -> notification_templates -------------------------
    op.rename_table("email_templates", "notification_templates")
    op.add_column(
        "notification_templates",
        sa.Column("channel", sa.String(length=20), nullable=False, server_default="email"),
    )
    op.add_column(
        "notification_templates",
        sa.Column("provider_template_name", sa.String(length=200), nullable=True),
    )
    op.add_column(
        "notification_templates",
        sa.Column("provider_template_status", sa.String(length=20), nullable=True),
    )
    # WhatsApp rows have no subject/body — relax the email NOT NULLs.
    op.alter_column("notification_templates", "subject", nullable=True)
    op.alter_column("notification_templates", "body_html", nullable=True)
    op.alter_column("notification_templates", "channel", server_default=None)

    op.drop_constraint(
        "uq_email_template_clinic_key_locale", "notification_templates", type_="unique"
    )
    op.create_unique_constraint(
        "uq_notification_template_clinic_key_locale_channel",
        "notification_templates",
        ["clinic_id", "template_key", "locale", "channel"],
    )
    op.execute("ALTER INDEX idx_email_templates_clinic RENAME TO idx_notification_templates_clinic")
    op.execute("ALTER INDEX idx_email_templates_key RENAME TO idx_notification_templates_key")
    op.execute(
        "ALTER INDEX ix_email_templates_clinic_id RENAME TO ix_notification_templates_clinic_id"
    )
    op.execute(
        "ALTER INDEX ix_email_templates_template_key "
        "RENAME TO ix_notification_templates_template_key"
    )
    op.create_index(
        op.f("ix_notification_templates_channel"),
        "notification_templates",
        ["channel"],
        unique=False,
    )

    # ---- email_logs -> communication_messages (outbox + audit) -------------
    op.rename_table("email_logs", "communication_messages")
    op.alter_column("communication_messages", "recipient_email", new_column_name="to_address")
    op.add_column(
        "communication_messages",
        sa.Column("channel", sa.String(length=20), nullable=False, server_default="email"),
    )
    op.add_column(
        "communication_messages",
        sa.Column("message_kind", sa.String(length=20), nullable=False, server_default="template"),
    )
    op.add_column(
        "communication_messages",
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "communication_messages",
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="5"),
    )
    op.add_column(
        "communication_messages",
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "communication_messages",
        sa.Column("dedup_key", sa.String(length=200), nullable=True),
    )
    op.add_column(
        "communication_messages",
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "communication_messages",
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "communication_messages",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    # provider/subject are unknown while a row is still queued.
    op.alter_column("communication_messages", "provider", nullable=True)
    op.alter_column("communication_messages", "subject", nullable=True)
    # drop the temporary server defaults — the model fills these in Python.
    for col in ("channel", "message_kind", "attempts", "max_attempts", "updated_at"):
        op.alter_column("communication_messages", col, server_default=None)

    op.execute("ALTER INDEX idx_email_logs_clinic RENAME TO idx_communication_messages_clinic")
    op.execute(
        "ALTER INDEX idx_email_logs_created_at RENAME TO idx_communication_messages_created_at"
    )
    op.execute("ALTER INDEX idx_email_logs_patient RENAME TO idx_communication_messages_patient")
    op.execute("ALTER INDEX idx_email_logs_status RENAME TO idx_communication_messages_status")
    op.execute("ALTER INDEX idx_email_logs_template RENAME TO idx_communication_messages_template")
    op.execute("ALTER INDEX ix_email_logs_clinic_id RENAME TO ix_communication_messages_clinic_id")
    op.execute(
        "ALTER INDEX ix_email_logs_patient_id RENAME TO ix_communication_messages_patient_id"
    )
    op.execute("ALTER INDEX ix_email_logs_status RENAME TO ix_communication_messages_status")
    op.execute(
        "ALTER INDEX ix_email_logs_triggered_by_user_id "
        "RENAME TO ix_communication_messages_triggered_by_user_id"
    )
    op.create_index(
        "idx_communication_messages_dispatch",
        "communication_messages",
        ["status", "next_attempt_at"],
        unique=False,
    )
    op.create_index(
        "uq_communication_messages_dedup",
        "communication_messages",
        ["clinic_id", "dedup_key"],
        unique=True,
        postgresql_where=sa.text("dedup_key IS NOT NULL"),
    )

    # ---- notification_preferences: per-channel WhatsApp opt-in -------------
    op.add_column(
        "notification_preferences",
        sa.Column("whatsapp_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "notification_preferences",
        sa.Column("whatsapp_opt_in_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "notification_preferences",
        sa.Column("last_inbound_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.alter_column("notification_preferences", "whatsapp_enabled", server_default=None)

    # ---- clinic_channel_settings (new, generic, no secrets) ----------------
    op.create_table(
        "clinic_channel_settings",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("channel", sa.String(length=20), nullable=False),
        sa.Column("adapter_name", sa.String(length=50), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False),
        sa.Column("is_verified", sa.Boolean(), nullable=False),
        sa.Column("config", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "clinic_id", "channel", name="uq_clinic_channel_settings_clinic_channel"
        ),
    )
    op.create_index(
        "idx_clinic_channel_settings_clinic", "clinic_channel_settings", ["clinic_id"], unique=False
    )
    op.create_index(
        op.f("ix_clinic_channel_settings_clinic_id"),
        "clinic_channel_settings",
        ["clinic_id"],
        unique=False,
    )

    # clinic_notification_settings: no backfill — the gateway treats a missing
    # per-type "channels" key as ["email"] at read time (no brittle JSONB migration).


def downgrade() -> None:
    op.drop_index("ix_clinic_channel_settings_clinic_id", table_name="clinic_channel_settings")
    op.drop_index("idx_clinic_channel_settings_clinic", table_name="clinic_channel_settings")
    op.drop_table("clinic_channel_settings")

    op.drop_column("notification_preferences", "last_inbound_at")
    op.drop_column("notification_preferences", "whatsapp_opt_in_at")
    op.drop_column("notification_preferences", "whatsapp_enabled")

    # communication_messages -> email_logs
    op.drop_index("uq_communication_messages_dedup", table_name="communication_messages")
    op.drop_index("idx_communication_messages_dispatch", table_name="communication_messages")
    op.execute(
        "ALTER INDEX ix_communication_messages_triggered_by_user_id "
        "RENAME TO ix_email_logs_triggered_by_user_id"
    )
    op.execute("ALTER INDEX ix_communication_messages_status RENAME TO ix_email_logs_status")
    op.execute(
        "ALTER INDEX ix_communication_messages_patient_id RENAME TO ix_email_logs_patient_id"
    )
    op.execute("ALTER INDEX ix_communication_messages_clinic_id RENAME TO ix_email_logs_clinic_id")
    op.execute("ALTER INDEX idx_communication_messages_template RENAME TO idx_email_logs_template")
    op.execute("ALTER INDEX idx_communication_messages_status RENAME TO idx_email_logs_status")
    op.execute("ALTER INDEX idx_communication_messages_patient RENAME TO idx_email_logs_patient")
    op.execute(
        "ALTER INDEX idx_communication_messages_created_at RENAME TO idx_email_logs_created_at"
    )
    op.execute("ALTER INDEX idx_communication_messages_clinic RENAME TO idx_email_logs_clinic")
    op.alter_column("communication_messages", "subject", nullable=False)
    op.alter_column("communication_messages", "provider", nullable=False)
    for col in (
        "updated_at",
        "read_at",
        "delivered_at",
        "dedup_key",
        "next_attempt_at",
        "max_attempts",
        "attempts",
        "message_kind",
        "channel",
    ):
        op.drop_column("communication_messages", col)
    op.alter_column("communication_messages", "to_address", new_column_name="recipient_email")
    op.rename_table("communication_messages", "email_logs")

    # notification_templates -> email_templates
    op.drop_index("ix_notification_templates_channel", table_name="notification_templates")
    op.drop_constraint(
        "uq_notification_template_clinic_key_locale_channel",
        "notification_templates",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_email_template_clinic_key_locale",
        "notification_templates",
        ["clinic_id", "template_key", "locale"],
    )
    op.execute(
        "ALTER INDEX ix_notification_templates_template_key "
        "RENAME TO ix_email_templates_template_key"
    )
    op.execute(
        "ALTER INDEX ix_notification_templates_clinic_id RENAME TO ix_email_templates_clinic_id"
    )
    op.execute("ALTER INDEX idx_notification_templates_key RENAME TO idx_email_templates_key")
    op.execute("ALTER INDEX idx_notification_templates_clinic RENAME TO idx_email_templates_clinic")
    op.alter_column("notification_templates", "body_html", nullable=False)
    op.alter_column("notification_templates", "subject", nullable=False)
    op.drop_column("notification_templates", "provider_template_status")
    op.drop_column("notification_templates", "provider_template_name")
    op.drop_column("notification_templates", "channel")
    op.rename_table("notification_templates", "email_templates")
