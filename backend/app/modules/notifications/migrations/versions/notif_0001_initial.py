"""v2 squash — notifications initial.

Initial schema for the `notifications` module.

Revision ID: notif_0001
Revises:
Create Date: 2026-04-21

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = 'notif_0001'
down_revision: str | None = 'bil_0001'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table('clinic_notification_settings',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('clinic_id', sa.UUID(), nullable=False),
    sa.Column('settings', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['clinic_id'], ['clinics.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_clinic_notification_settings_clinic', 'clinic_notification_settings', ['clinic_id'], unique=False)
    op.create_index(op.f('ix_clinic_notification_settings_clinic_id'), 'clinic_notification_settings', ['clinic_id'], unique=True)


    op.create_table('clinic_smtp_settings',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('clinic_id', sa.UUID(), nullable=False),
    sa.Column('provider', sa.String(length=20), nullable=False),
    sa.Column('host', sa.String(length=255), nullable=True),
    sa.Column('port', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=255), nullable=True),
    sa.Column('password_encrypted', sa.Text(), nullable=True),
    sa.Column('use_tls', sa.Boolean(), nullable=False),
    sa.Column('use_ssl', sa.Boolean(), nullable=False),
    sa.Column('from_email', sa.String(length=255), nullable=True),
    sa.Column('from_name', sa.String(length=255), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('is_verified', sa.Boolean(), nullable=False),
    sa.Column('last_verified_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['clinic_id'], ['clinics.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_clinic_smtp_settings_clinic', 'clinic_smtp_settings', ['clinic_id'], unique=False)
    op.create_index(op.f('ix_clinic_smtp_settings_clinic_id'), 'clinic_smtp_settings', ['clinic_id'], unique=True)


    op.create_table('email_templates',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('clinic_id', sa.UUID(), nullable=True),
    sa.Column('template_key', sa.String(length=100), nullable=False),
    sa.Column('locale', sa.String(length=5), nullable=False),
    sa.Column('subject', sa.String(length=255), nullable=False),
    sa.Column('body_html', sa.Text(), nullable=False),
    sa.Column('body_text', sa.Text(), nullable=True),
    sa.Column('variables', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('description', sa.String(length=500), nullable=True),
    sa.Column('is_system', sa.Boolean(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['clinic_id'], ['clinics.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('clinic_id', 'template_key', 'locale', name='uq_email_template_clinic_key_locale')
    )
    op.create_index('idx_email_templates_clinic', 'email_templates', ['clinic_id'], unique=False)
    op.create_index('idx_email_templates_key', 'email_templates', ['template_key'], unique=False)
    op.create_index(op.f('ix_email_templates_clinic_id'), 'email_templates', ['clinic_id'], unique=False)
    op.create_index(op.f('ix_email_templates_template_key'), 'email_templates', ['template_key'], unique=False)


    op.create_table('email_logs',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('clinic_id', sa.UUID(), nullable=False),
    sa.Column('recipient_email', sa.String(length=255), nullable=False),
    sa.Column('patient_id', sa.UUID(), nullable=True),
    sa.Column('template_key', sa.String(length=100), nullable=False),
    sa.Column('subject', sa.String(length=255), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('provider', sa.String(length=50), nullable=False),
    sa.Column('provider_message_id', sa.String(length=255), nullable=True),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('triggered_by_event', sa.String(length=100), nullable=True),
    sa.Column('triggered_by_user_id', sa.UUID(), nullable=True),
    sa.Column('context_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.ForeignKeyConstraint(['clinic_id'], ['clinics.id'], ),
    sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ),
    sa.ForeignKeyConstraint(['triggered_by_user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_email_logs_clinic', 'email_logs', ['clinic_id'], unique=False)
    op.create_index('idx_email_logs_created_at', 'email_logs', ['created_at'], unique=False)
    op.create_index('idx_email_logs_patient', 'email_logs', ['patient_id'], unique=False)
    op.create_index('idx_email_logs_status', 'email_logs', ['status'], unique=False)
    op.create_index('idx_email_logs_template', 'email_logs', ['template_key'], unique=False)
    op.create_index(op.f('ix_email_logs_clinic_id'), 'email_logs', ['clinic_id'], unique=False)
    op.create_index(op.f('ix_email_logs_patient_id'), 'email_logs', ['patient_id'], unique=False)
    op.create_index(op.f('ix_email_logs_status'), 'email_logs', ['status'], unique=False)
    op.create_index(op.f('ix_email_logs_triggered_by_user_id'), 'email_logs', ['triggered_by_user_id'], unique=False)


    op.create_table('notification_preferences',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('clinic_id', sa.UUID(), nullable=False),
    sa.Column('patient_id', sa.UUID(), nullable=True),
    sa.Column('user_id', sa.UUID(), nullable=True),
    sa.Column('email_enabled', sa.Boolean(), nullable=False),
    sa.Column('preferences', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('preferred_locale', sa.String(length=5), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['clinic_id'], ['clinics.id'], ),
    sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('clinic_id', 'patient_id', name='uq_notification_pref_clinic_patient'),
    sa.UniqueConstraint('clinic_id', 'user_id', name='uq_notification_pref_clinic_user')
    )
    op.create_index('idx_notification_preferences_clinic', 'notification_preferences', ['clinic_id'], unique=False)
    op.create_index('idx_notification_preferences_patient', 'notification_preferences', ['patient_id'], unique=False)
    op.create_index('idx_notification_preferences_user', 'notification_preferences', ['user_id'], unique=False)
    op.create_index(op.f('ix_notification_preferences_clinic_id'), 'notification_preferences', ['clinic_id'], unique=False)
    op.create_index(op.f('ix_notification_preferences_patient_id'), 'notification_preferences', ['patient_id'], unique=False)
    op.create_index(op.f('ix_notification_preferences_user_id'), 'notification_preferences', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_table('notification_preferences')
    op.drop_table('email_logs')
    op.drop_table('email_templates')
    op.drop_table('clinic_smtp_settings')
    op.drop_table('clinic_notification_settings')
