"""add_legal_guardian_field

Revision ID: n4o5p6q7r8s9
Revises: m3n4o5p6q7r8
Create Date: 2026-04-14 18:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "n4o5p6q7r8s9"
down_revision: str | None = "m3n4o5p6q7r8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add legal_guardian JSONB column to patients
    op.add_column("patients", sa.Column("legal_guardian", postgresql.JSONB(), nullable=True))


def downgrade() -> None:
    op.drop_column("patients", "legal_guardian")
