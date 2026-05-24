"""Widen clinical_notes.note_type to VARCHAR(40).

The two appointment-owner discriminators (``appointment_clinical``,
``appointment_administrative``) exceed the original VARCHAR(20) cap —
``appointment_administrative`` is 26 chars and was silently rejected by
PostgreSQL with ``StringDataRightTruncationError``. Bumping the column
to 40 keeps headroom for future owners without rewriting the CHECK
matrix.

Revision ID: cn_0004
Revises: cn_0003
Create Date: 2026-05-24

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "cn_0004"
down_revision: str | None = "cn_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "clinical_notes",
        "note_type",
        existing_type=sa.String(length=20),
        type_=sa.String(length=40),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "clinical_notes",
        "note_type",
        existing_type=sa.String(length=40),
        type_=sa.String(length=20),
        existing_nullable=False,
    )
