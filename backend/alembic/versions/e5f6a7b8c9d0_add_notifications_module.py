"""Add notifications module tables.

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2024-04-12

Tables created:
- email_templates: Customizable email templates per clinic
- notification_preferences: Patient/user notification preferences
- clinic_notification_settings: Clinic-level notification configuration
- email_logs: Audit log for sent emails
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e5f6a7b8c9d0"
down_revision: str | None = "d4e5f6a7b8c9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create email_templates table
    op.create_table(
        "email_templates",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=True),  # NULL = system template
        # Template identification
        sa.Column("template_key", sa.String(length=100), nullable=False),
        sa.Column("locale", sa.String(length=5), nullable=False, server_default="'es'"),
        # Content
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("body_html", sa.Text(), nullable=False),
        sa.Column("body_text", sa.Text(), nullable=True),
        # Metadata
        sa.Column("variables", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("description", sa.String(length=500), nullable=True),
        # Flags
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        # Constraints
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "clinic_id", "template_key", "locale", name="uq_email_template_clinic_key_locale"
        ),
    )
    op.create_index("idx_email_templates_clinic", "email_templates", ["clinic_id"], unique=False)
    op.create_index("idx_email_templates_key", "email_templates", ["template_key"], unique=False)

    # Create notification_preferences table
    op.create_table(
        "notification_preferences",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        # Subject - either patient or user
        sa.Column("patient_id", sa.UUID(), nullable=True),
        sa.Column("user_id", sa.UUID(), nullable=True),
        # Global email toggle
        sa.Column("email_enabled", sa.Boolean(), nullable=False, server_default="true"),
        # Per-type preferences
        sa.Column("preferences", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        # Language preference
        sa.Column("preferred_locale", sa.String(length=5), nullable=False, server_default="'es'"),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        # Constraints
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"]),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "clinic_id", "patient_id", name="uq_notification_pref_clinic_patient"
        ),
        sa.UniqueConstraint("clinic_id", "user_id", name="uq_notification_pref_clinic_user"),
    )
    op.create_index(
        "idx_notification_preferences_clinic",
        "notification_preferences",
        ["clinic_id"],
        unique=False,
    )
    op.create_index(
        "idx_notification_preferences_patient",
        "notification_preferences",
        ["patient_id"],
        unique=False,
    )
    op.create_index(
        "idx_notification_preferences_user", "notification_preferences", ["user_id"], unique=False
    )

    # Create clinic_notification_settings table
    op.create_table(
        "clinic_notification_settings",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        # Per-notification-type settings
        sa.Column("settings", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        # Constraints
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("clinic_id", name="uq_clinic_notification_settings_clinic"),
    )
    op.create_index(
        "idx_clinic_notification_settings_clinic",
        "clinic_notification_settings",
        ["clinic_id"],
        unique=False,
    )

    # Create email_logs table
    op.create_table(
        "email_logs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        # Recipient info
        sa.Column("recipient_email", sa.String(length=255), nullable=False),
        sa.Column("patient_id", sa.UUID(), nullable=True),
        # Template info
        sa.Column("template_key", sa.String(length=100), nullable=False),
        sa.Column("subject", sa.String(length=255), nullable=False),
        # Status
        sa.Column("status", sa.String(length=20), nullable=False),
        # Provider info
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("provider_message_id", sa.String(length=255), nullable=True),
        # Error tracking
        sa.Column("error_message", sa.Text(), nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        # Event tracking
        sa.Column("triggered_by_event", sa.String(length=100), nullable=True),
        sa.Column("triggered_by_user_id", sa.UUID(), nullable=True),
        # Context data
        sa.Column("context_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        # Constraints
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"]),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"]),
        sa.ForeignKeyConstraint(["triggered_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_email_logs_clinic", "email_logs", ["clinic_id"], unique=False)
    op.create_index("idx_email_logs_status", "email_logs", ["status"], unique=False)
    op.create_index("idx_email_logs_created_at", "email_logs", ["created_at"], unique=False)
    op.create_index("idx_email_logs_patient", "email_logs", ["patient_id"], unique=False)
    op.create_index("idx_email_logs_template", "email_logs", ["template_key"], unique=False)


def downgrade() -> None:
    # Drop email_logs
    op.drop_index("idx_email_logs_template", table_name="email_logs")
    op.drop_index("idx_email_logs_patient", table_name="email_logs")
    op.drop_index("idx_email_logs_created_at", table_name="email_logs")
    op.drop_index("idx_email_logs_status", table_name="email_logs")
    op.drop_index("idx_email_logs_clinic", table_name="email_logs")
    op.drop_table("email_logs")

    # Drop clinic_notification_settings
    op.drop_index(
        "idx_clinic_notification_settings_clinic", table_name="clinic_notification_settings"
    )
    op.drop_table("clinic_notification_settings")

    # Drop notification_preferences
    op.drop_index("idx_notification_preferences_user", table_name="notification_preferences")
    op.drop_index("idx_notification_preferences_patient", table_name="notification_preferences")
    op.drop_index("idx_notification_preferences_clinic", table_name="notification_preferences")
    op.drop_table("notification_preferences")

    # Drop email_templates
    op.drop_index("idx_email_templates_key", table_name="email_templates")
    op.drop_index("idx_email_templates_clinic", table_name="email_templates")
    op.drop_table("email_templates")
