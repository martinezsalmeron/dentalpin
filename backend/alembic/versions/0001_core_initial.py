"""v2 squash — core initial.

Core schema: users, clinics, memberships, module registry + external-id table.

Revision ID: 0001
Revises:
Create Date: 2026-04-21

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = '0001'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table('clinics',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('tax_id', sa.String(length=20), nullable=False),
    sa.Column('address', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('phone', sa.String(length=20), nullable=True),
    sa.Column('email', sa.String(length=255), nullable=True),
    sa.Column('settings', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )


    op.create_table('users',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('password_hash', sa.String(length=255), nullable=False),
    sa.Column('first_name', sa.String(length=100), nullable=False),
    sa.Column('last_name', sa.String(length=100), nullable=False),
    sa.Column('professional_id', sa.String(length=50), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('token_version', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)


    op.create_table('clinic_memberships',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('clinic_id', sa.UUID(), nullable=False),
    sa.Column('role', sa.String(length=20), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['clinic_id'], ['clinics.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_clinic_memberships_clinic_id'), 'clinic_memberships', ['clinic_id'], unique=False)
    op.create_index(op.f('ix_clinic_memberships_user_id'), 'clinic_memberships', ['user_id'], unique=False)


    op.create_table('core_module',
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('version', sa.String(length=50), nullable=False),
    sa.Column('state', sa.String(length=30), nullable=False),
    sa.Column('category', sa.String(length=20), nullable=False),
    sa.Column('removable', sa.Boolean(), nullable=False),
    sa.Column('auto_install', sa.Boolean(), nullable=False),
    sa.Column('installed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('last_state_change', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('base_revision', sa.String(length=64), nullable=True),
    sa.Column('applied_revision', sa.String(length=64), nullable=True),
    sa.Column('manifest_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('error_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('name')
    )


    op.create_table('core_module_operation_log',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('module_name', sa.String(length=100), nullable=False),
    sa.Column('operation', sa.String(length=30), nullable=False),
    sa.Column('step', sa.String(length=30), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['module_name'], ['core_module.name'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_core_module_operation_log_created', 'core_module_operation_log', ['created_at'], unique=False)
    op.create_index('ix_core_module_operation_log_module', 'core_module_operation_log', ['module_name'], unique=False)


    op.create_table('core_external_id',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('module_name', sa.String(length=100), nullable=False),
    sa.Column('xml_id', sa.String(length=255), nullable=False),
    sa.Column('table_name', sa.String(length=100), nullable=False),
    sa.Column('record_id', sa.UUID(), nullable=False),
    sa.Column('noupdate', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('module_name', 'xml_id', name='uq_core_external_id_module_xml')
    )
    op.create_index('ix_core_external_id_module', 'core_external_id', ['module_name'], unique=False)
    op.create_index('ix_core_external_id_table_record', 'core_external_id', ['table_name', 'record_id'], unique=False)


def downgrade() -> None:
    op.drop_table('core_external_id')
    op.drop_table('core_module_operation_log')
    op.drop_table('core_module')
    op.drop_table('clinic_memberships')
    op.drop_table('users')
    op.drop_table('clinics')
