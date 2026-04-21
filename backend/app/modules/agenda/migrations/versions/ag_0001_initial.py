"""v2 squash — agenda initial.

Initial schema for the `agenda` module.

Revision ID: ag_0001
Revises:
Create Date: 2026-04-21

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = 'ag_0001'
down_revision: str | None = 'med_0001'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table('cabinets',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('clinic_id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=50), nullable=False),
    sa.Column('color', sa.String(length=7), nullable=False),
    sa.Column('display_order', sa.Integer(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['clinic_id'], ['clinics.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_cabinets_clinic_id'), 'cabinets', ['clinic_id'], unique=False)
    op.create_index('uq_cabinet_clinic_name', 'cabinets', ['clinic_id', 'name'], unique=True)


    op.create_table('appointments',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('clinic_id', sa.UUID(), nullable=False),
    sa.Column('patient_id', sa.UUID(), nullable=True),
    sa.Column('professional_id', sa.UUID(), nullable=False),
    sa.Column('cabinet', sa.String(length=50), nullable=False),
    sa.Column('cabinet_id', sa.UUID(), nullable=False),
    sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
    sa.Column('end_time', sa.DateTime(timezone=True), nullable=False),
    sa.Column('treatment_type', sa.String(length=100), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('color', sa.String(length=7), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['cabinet_id'], ['cabinets.id'], ),
    sa.ForeignKeyConstraint(['clinic_id'], ['clinics.id'], ),
    sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ),
    sa.ForeignKeyConstraint(['professional_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_appointment_slot', 'appointments', ['clinic_id', 'cabinet_id', 'professional_id', 'start_time'], unique=True, postgresql_where=sa.text("status != 'cancelled'"))
    op.create_index(op.f('ix_appointments_cabinet_id'), 'appointments', ['cabinet_id'], unique=False)
    op.create_index(op.f('ix_appointments_clinic_id'), 'appointments', ['clinic_id'], unique=False)
    op.create_index(op.f('ix_appointments_start_time'), 'appointments', ['start_time'], unique=False)


    op.create_table('appointment_treatments',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('appointment_id', sa.UUID(), nullable=False),
    sa.Column('planned_treatment_item_id', sa.UUID(), nullable=False),
    sa.Column('catalog_item_id', sa.UUID(), nullable=True),
    sa.Column('display_order', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('completed_in_appointment', sa.Boolean(), nullable=False),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['appointment_id'], ['appointments.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['catalog_item_id'], ['treatment_catalog_items.id'], ondelete='SET NULL'),
    # planned_treatment_item_id → treatment_plan.planned_treatment_items
    # is added by the treatment_plan initial (`tp_0001`) to break the
    # circular module dependency — agenda and treatment_plan FK into
    # each other, so one side defers the constraint.
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_appointment_treatments_appointment_id'), 'appointment_treatments', ['appointment_id'], unique=False)
    op.create_index(op.f('ix_appointment_treatments_planned_treatment_item_id'), 'appointment_treatments', ['planned_treatment_item_id'], unique=False)


def downgrade() -> None:
    op.drop_table('appointment_treatments')
    op.drop_table('appointments')
    op.drop_table('cabinets')
