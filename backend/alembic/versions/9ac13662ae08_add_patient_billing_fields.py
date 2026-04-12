"""add_patient_billing_fields

Revision ID: 9ac13662ae08
Revises: h8i9j0k1l2m3
Create Date: 2026-04-12 08:48:10.865419

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '9ac13662ae08'
down_revision: Union[str, None] = 'h8i9j0k1l2m3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add billing fields to patients table
    op.add_column('patients', sa.Column('billing_name', sa.String(length=200), nullable=True))
    op.add_column('patients', sa.Column('billing_tax_id', sa.String(length=50), nullable=True))
    op.add_column('patients', sa.Column('billing_address', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('patients', sa.Column('billing_email', sa.String(length=255), nullable=True))


def downgrade() -> None:
    # Remove billing fields from patients table
    op.drop_column('patients', 'billing_email')
    op.drop_column('patients', 'billing_address')
    op.drop_column('patients', 'billing_tax_id')
    op.drop_column('patients', 'billing_name')
