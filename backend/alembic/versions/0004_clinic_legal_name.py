"""core — add clinics.legal_name column.

Spanish AEAT compliance (verifactu) needs the clinic's legal name
("Razón social") which can differ from the commercial ``name``. Adding
it here keeps clinic identity centralised so every module reads from a
single source of truth instead of duplicating the field.

Revision ID: 0004
Revises: 0003
Create Date: 2026-04-25
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "clinics",
        sa.Column("legal_name", sa.String(length=200), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("clinics", "legal_name")
