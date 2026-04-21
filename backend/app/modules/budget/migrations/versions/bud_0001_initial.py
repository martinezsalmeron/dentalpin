"""v2 squash — budget initial.

Initial schema for the `budget` module.

Revision ID: bud_0001
Revises:
Create Date: 2026-04-21

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = 'bud_0001'
down_revision: str | None = 'odo_0001'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table('budgets',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('clinic_id', sa.UUID(), nullable=False),
    sa.Column('patient_id', sa.UUID(), nullable=False),
    sa.Column('budget_number', sa.String(length=50), nullable=False),
    sa.Column('version', sa.Integer(), nullable=False),
    sa.Column('parent_budget_id', sa.UUID(), nullable=True),
    sa.Column('status', sa.String(length=30), nullable=False),
    sa.Column('valid_from', sa.Date(), nullable=False),
    sa.Column('valid_until', sa.Date(), nullable=True),
    sa.Column('created_by', sa.UUID(), nullable=False),
    sa.Column('assigned_professional_id', sa.UUID(), nullable=True),
    sa.Column('global_discount_type', sa.String(length=20), nullable=True),
    sa.Column('global_discount_value', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('subtotal', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('total_discount', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('total_tax', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('total', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('currency', sa.String(length=3), nullable=False),
    sa.Column('internal_notes', sa.Text(), nullable=True),
    sa.Column('patient_notes', sa.Text(), nullable=True),
    sa.Column('insurance_estimate', sa.Numeric(precision=12, scale=2), nullable=True),
    sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['assigned_professional_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['clinic_id'], ['clinics.id'], ),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
    sa.ForeignKeyConstraint(['parent_budget_id'], ['budgets.id'], ),
    sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('clinic_id', 'budget_number', 'version', name='uq_budget_clinic_number_version')
    )
    op.create_index('idx_budgets_clinic', 'budgets', ['clinic_id'], unique=False)
    op.create_index('idx_budgets_clinic_patient', 'budgets', ['clinic_id', 'patient_id'], unique=False)
    op.create_index('idx_budgets_clinic_status', 'budgets', ['clinic_id', 'status'], unique=False)
    op.create_index('idx_budgets_parent', 'budgets', ['parent_budget_id'], unique=False)
    op.create_index('idx_budgets_valid_until', 'budgets', ['valid_until'], unique=False)
    op.create_index(op.f('ix_budgets_clinic_id'), 'budgets', ['clinic_id'], unique=False)
    op.create_index(op.f('ix_budgets_parent_budget_id'), 'budgets', ['parent_budget_id'], unique=False)
    op.create_index(op.f('ix_budgets_patient_id'), 'budgets', ['patient_id'], unique=False)


    op.create_table('budget_history',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('clinic_id', sa.UUID(), nullable=False),
    sa.Column('budget_id', sa.UUID(), nullable=False),
    sa.Column('action', sa.String(length=30), nullable=False),
    sa.Column('changed_by', sa.UUID(), nullable=False),
    sa.Column('changed_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('previous_state', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('new_state', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['budget_id'], ['budgets.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['changed_by'], ['users.id'], ),
    sa.ForeignKeyConstraint(['clinic_id'], ['clinics.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_budget_history_budget', 'budget_history', ['budget_id'], unique=False)
    op.create_index('idx_budget_history_changed_at', 'budget_history', ['changed_at'], unique=False)
    op.create_index('idx_budget_history_clinic', 'budget_history', ['clinic_id'], unique=False)
    op.create_index(op.f('ix_budget_history_budget_id'), 'budget_history', ['budget_id'], unique=False)
    op.create_index(op.f('ix_budget_history_clinic_id'), 'budget_history', ['clinic_id'], unique=False)


    op.create_table('budget_signatures',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('clinic_id', sa.UUID(), nullable=False),
    sa.Column('budget_id', sa.UUID(), nullable=False),
    sa.Column('signature_type', sa.String(length=30), nullable=False),
    sa.Column('signed_items', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('signed_by_name', sa.String(length=200), nullable=False),
    sa.Column('signed_by_email', sa.String(length=255), nullable=True),
    sa.Column('relationship_to_patient', sa.String(length=30), nullable=False),
    sa.Column('signature_method', sa.String(length=30), nullable=False),
    sa.Column('signature_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('ip_address', sa.String(length=45), nullable=True),
    sa.Column('user_agent', sa.Text(), nullable=True),
    sa.Column('signed_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('external_signature_id', sa.String(length=255), nullable=True),
    sa.Column('external_provider', sa.String(length=50), nullable=True),
    sa.Column('document_hash', sa.String(length=64), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['budget_id'], ['budgets.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['clinic_id'], ['clinics.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_budget_signatures_budget', 'budget_signatures', ['budget_id'], unique=False)
    op.create_index('idx_budget_signatures_clinic', 'budget_signatures', ['clinic_id'], unique=False)
    op.create_index(op.f('ix_budget_signatures_budget_id'), 'budget_signatures', ['budget_id'], unique=False)
    op.create_index(op.f('ix_budget_signatures_clinic_id'), 'budget_signatures', ['clinic_id'], unique=False)


    op.create_table('budget_items',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('clinic_id', sa.UUID(), nullable=False),
    sa.Column('budget_id', sa.UUID(), nullable=False),
    sa.Column('catalog_item_id', sa.UUID(), nullable=False),
    sa.Column('unit_price', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('quantity', sa.Integer(), nullable=False),
    sa.Column('discount_type', sa.String(length=20), nullable=True),
    sa.Column('discount_value', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('vat_type_id', sa.UUID(), nullable=True),
    sa.Column('vat_rate', sa.Float(), nullable=False),
    sa.Column('line_subtotal', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('line_discount', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('line_tax', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('line_total', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('tooth_number', sa.Integer(), nullable=True),
    sa.Column('surfaces', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('treatment_id', sa.UUID(), nullable=True),
    sa.Column('invoiced_quantity', sa.Integer(), nullable=False),
    sa.Column('display_order', sa.Integer(), nullable=False),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['budget_id'], ['budgets.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['catalog_item_id'], ['treatment_catalog_items.id'], ),
    sa.ForeignKeyConstraint(['clinic_id'], ['clinics.id'], ),
    sa.ForeignKeyConstraint(['treatment_id'], ['treatments.id'], ),
    sa.ForeignKeyConstraint(['vat_type_id'], ['vat_types.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_budget_items_budget', 'budget_items', ['budget_id'], unique=False)
    op.create_index('idx_budget_items_catalog', 'budget_items', ['catalog_item_id'], unique=False)
    op.create_index('idx_budget_items_tooth', 'budget_items', ['budget_id', 'tooth_number'], unique=False)
    op.create_index('idx_budget_items_treatment', 'budget_items', ['treatment_id'], unique=False)
    op.create_index(op.f('ix_budget_items_budget_id'), 'budget_items', ['budget_id'], unique=False)
    op.create_index(op.f('ix_budget_items_catalog_item_id'), 'budget_items', ['catalog_item_id'], unique=False)
    op.create_index(op.f('ix_budget_items_clinic_id'), 'budget_items', ['clinic_id'], unique=False)
    op.create_index(op.f('ix_budget_items_treatment_id'), 'budget_items', ['treatment_id'], unique=False)
    op.create_index(op.f('ix_budget_items_vat_type_id'), 'budget_items', ['vat_type_id'], unique=False)


def downgrade() -> None:
    op.drop_table('budget_items')
    op.drop_table('budget_signatures')
    op.drop_table('budget_history')
    op.drop_table('budgets')
