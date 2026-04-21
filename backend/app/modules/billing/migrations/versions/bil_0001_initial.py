"""v2 squash — billing initial.

Initial schema for the `billing` module.

Revision ID: bil_0001
Revises:
Create Date: 2026-04-21

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = 'bil_0001'
down_revision: str | None = 'pt_0001'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table('invoice_series',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('clinic_id', sa.UUID(), nullable=False),
    sa.Column('prefix', sa.String(length=20), nullable=False),
    sa.Column('series_type', sa.String(length=20), nullable=False),
    sa.Column('description', sa.String(length=200), nullable=True),
    sa.Column('current_number', sa.Integer(), nullable=False),
    sa.Column('reset_yearly', sa.Boolean(), nullable=False),
    sa.Column('last_reset_year', sa.Integer(), nullable=True),
    sa.Column('is_default', sa.Boolean(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['clinic_id'], ['clinics.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('clinic_id', 'prefix', name='uq_invoice_series_clinic_prefix')
    )
    op.create_index('idx_invoice_series_clinic', 'invoice_series', ['clinic_id'], unique=False)
    op.create_index('idx_invoice_series_clinic_type', 'invoice_series', ['clinic_id', 'series_type'], unique=False)
    op.create_index(op.f('ix_invoice_series_clinic_id'), 'invoice_series', ['clinic_id'], unique=False)


    op.create_table('invoice_series_history',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('clinic_id', sa.UUID(), nullable=False),
    sa.Column('series_id', sa.UUID(), nullable=False),
    sa.Column('action', sa.String(length=50), nullable=False),
    sa.Column('changed_by', sa.UUID(), nullable=False),
    sa.Column('changed_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('previous_state', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('new_state', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['changed_by'], ['users.id'], ),
    sa.ForeignKeyConstraint(['clinic_id'], ['clinics.id'], ),
    sa.ForeignKeyConstraint(['series_id'], ['invoice_series.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_invoice_series_history_changed_at', 'invoice_series_history', ['changed_at'], unique=False)
    op.create_index('idx_invoice_series_history_clinic', 'invoice_series_history', ['clinic_id'], unique=False)
    op.create_index('idx_invoice_series_history_series', 'invoice_series_history', ['series_id'], unique=False)
    op.create_index(op.f('ix_invoice_series_history_clinic_id'), 'invoice_series_history', ['clinic_id'], unique=False)
    op.create_index(op.f('ix_invoice_series_history_series_id'), 'invoice_series_history', ['series_id'], unique=False)


    op.create_table('invoices',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('clinic_id', sa.UUID(), nullable=False),
    sa.Column('patient_id', sa.UUID(), nullable=False),
    sa.Column('invoice_number', sa.String(length=50), nullable=True),
    sa.Column('series_id', sa.UUID(), nullable=True),
    sa.Column('sequential_number', sa.Integer(), nullable=True),
    sa.Column('budget_id', sa.UUID(), nullable=True),
    sa.Column('credit_note_for_id', sa.UUID(), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('issue_date', sa.Date(), nullable=True),
    sa.Column('due_date', sa.Date(), nullable=True),
    sa.Column('payment_term_days', sa.Integer(), nullable=False),
    sa.Column('billing_name', sa.String(length=200), nullable=True),
    sa.Column('billing_tax_id', sa.String(length=50), nullable=True),
    sa.Column('billing_address', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('billing_email', sa.String(length=255), nullable=True),
    sa.Column('subtotal', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('total_discount', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('total_tax', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('total', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('total_paid', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('balance_due', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('currency', sa.String(length=3), nullable=False),
    sa.Column('internal_notes', sa.Text(), nullable=True),
    sa.Column('public_notes', sa.Text(), nullable=True),
    sa.Column('compliance_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('document_hash', sa.String(length=64), nullable=True),
    sa.Column('previous_hash', sa.String(length=64), nullable=True),
    sa.Column('created_by', sa.UUID(), nullable=False),
    sa.Column('issued_by', sa.UUID(), nullable=True),
    sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['budget_id'], ['budgets.id'], ),
    sa.ForeignKeyConstraint(['clinic_id'], ['clinics.id'], ),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
    sa.ForeignKeyConstraint(['credit_note_for_id'], ['invoices.id'], ),
    sa.ForeignKeyConstraint(['issued_by'], ['users.id'], ),
    sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ),
    sa.ForeignKeyConstraint(['series_id'], ['invoice_series.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_invoices_budget', 'invoices', ['budget_id'], unique=False)
    op.create_index('idx_invoices_clinic', 'invoices', ['clinic_id'], unique=False)
    op.create_index('idx_invoices_clinic_due_date', 'invoices', ['clinic_id', 'due_date'], unique=False)
    op.create_index('idx_invoices_clinic_issue_date', 'invoices', ['clinic_id', 'issue_date'], unique=False)
    op.create_index('idx_invoices_clinic_patient', 'invoices', ['clinic_id', 'patient_id'], unique=False)
    op.create_index('idx_invoices_clinic_status', 'invoices', ['clinic_id', 'status'], unique=False)
    op.create_index('idx_invoices_credit_note_for', 'invoices', ['credit_note_for_id'], unique=False)
    op.create_index('idx_invoices_series', 'invoices', ['series_id'], unique=False)
    op.create_index(op.f('ix_invoices_budget_id'), 'invoices', ['budget_id'], unique=False)
    op.create_index(op.f('ix_invoices_clinic_id'), 'invoices', ['clinic_id'], unique=False)
    op.create_index(op.f('ix_invoices_credit_note_for_id'), 'invoices', ['credit_note_for_id'], unique=False)
    op.create_index(op.f('ix_invoices_patient_id'), 'invoices', ['patient_id'], unique=False)
    op.create_index(op.f('ix_invoices_series_id'), 'invoices', ['series_id'], unique=False)


    op.create_table('invoice_history',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('clinic_id', sa.UUID(), nullable=False),
    sa.Column('invoice_id', sa.UUID(), nullable=False),
    sa.Column('action', sa.String(length=50), nullable=False),
    sa.Column('changed_by', sa.UUID(), nullable=False),
    sa.Column('changed_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('previous_state', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('new_state', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['changed_by'], ['users.id'], ),
    sa.ForeignKeyConstraint(['clinic_id'], ['clinics.id'], ),
    sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_invoice_history_changed_at', 'invoice_history', ['changed_at'], unique=False)
    op.create_index('idx_invoice_history_clinic', 'invoice_history', ['clinic_id'], unique=False)
    op.create_index('idx_invoice_history_invoice', 'invoice_history', ['invoice_id'], unique=False)
    op.create_index(op.f('ix_invoice_history_clinic_id'), 'invoice_history', ['clinic_id'], unique=False)
    op.create_index(op.f('ix_invoice_history_invoice_id'), 'invoice_history', ['invoice_id'], unique=False)


    op.create_table('payments',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('clinic_id', sa.UUID(), nullable=False),
    sa.Column('invoice_id', sa.UUID(), nullable=False),
    sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('payment_method', sa.String(length=30), nullable=False),
    sa.Column('payment_date', sa.Date(), nullable=False),
    sa.Column('reference', sa.String(length=100), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('recorded_by', sa.UUID(), nullable=False),
    sa.Column('is_voided', sa.Boolean(), nullable=False),
    sa.Column('voided_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('voided_by', sa.UUID(), nullable=True),
    sa.Column('void_reason', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['clinic_id'], ['clinics.id'], ),
    sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['recorded_by'], ['users.id'], ),
    sa.ForeignKeyConstraint(['voided_by'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_payments_clinic', 'payments', ['clinic_id'], unique=False)
    op.create_index('idx_payments_clinic_date', 'payments', ['clinic_id', 'payment_date'], unique=False)
    op.create_index('idx_payments_clinic_method', 'payments', ['clinic_id', 'payment_method'], unique=False)
    op.create_index('idx_payments_invoice', 'payments', ['invoice_id'], unique=False)
    op.create_index(op.f('ix_payments_clinic_id'), 'payments', ['clinic_id'], unique=False)
    op.create_index(op.f('ix_payments_invoice_id'), 'payments', ['invoice_id'], unique=False)


    op.create_table('invoice_items',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('clinic_id', sa.UUID(), nullable=False),
    sa.Column('invoice_id', sa.UUID(), nullable=False),
    sa.Column('budget_item_id', sa.UUID(), nullable=True),
    sa.Column('catalog_item_id', sa.UUID(), nullable=True),
    sa.Column('description', sa.String(length=500), nullable=False),
    sa.Column('internal_code', sa.String(length=50), nullable=True),
    sa.Column('unit_price', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('quantity', sa.Integer(), nullable=False),
    sa.Column('discount_type', sa.String(length=20), nullable=True),
    sa.Column('discount_value', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('vat_type_id', sa.UUID(), nullable=True),
    sa.Column('vat_rate', sa.Float(), nullable=False),
    sa.Column('vat_exempt_reason', sa.String(length=200), nullable=True),
    sa.Column('line_subtotal', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('line_discount', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('line_tax', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('line_total', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('tooth_number', sa.Integer(), nullable=True),
    sa.Column('surfaces', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('display_order', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['budget_item_id'], ['budget_items.id'], ),
    sa.ForeignKeyConstraint(['catalog_item_id'], ['treatment_catalog_items.id'], ),
    sa.ForeignKeyConstraint(['clinic_id'], ['clinics.id'], ),
    sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['vat_type_id'], ['vat_types.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_invoice_items_budget_item', 'invoice_items', ['budget_item_id'], unique=False)
    op.create_index('idx_invoice_items_catalog_item', 'invoice_items', ['catalog_item_id'], unique=False)
    op.create_index('idx_invoice_items_invoice', 'invoice_items', ['invoice_id'], unique=False)
    op.create_index(op.f('ix_invoice_items_budget_item_id'), 'invoice_items', ['budget_item_id'], unique=False)
    op.create_index(op.f('ix_invoice_items_catalog_item_id'), 'invoice_items', ['catalog_item_id'], unique=False)
    op.create_index(op.f('ix_invoice_items_clinic_id'), 'invoice_items', ['clinic_id'], unique=False)
    op.create_index(op.f('ix_invoice_items_invoice_id'), 'invoice_items', ['invoice_id'], unique=False)
    op.create_index(op.f('ix_invoice_items_vat_type_id'), 'invoice_items', ['vat_type_id'], unique=False)


def downgrade() -> None:
    op.drop_table('invoice_items')
    op.drop_table('payments')
    op.drop_table('invoice_history')
    op.drop_table('invoices')
    op.drop_table('invoice_series_history')
    op.drop_table('invoice_series')
