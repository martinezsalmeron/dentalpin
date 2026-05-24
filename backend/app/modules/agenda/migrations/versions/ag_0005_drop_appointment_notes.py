"""Drop legacy ``appointments.notes`` (moved to clinical_notes).

Appointment notes are now polymorphic ``ClinicalNote`` rows with
``owner_type='appointment'`` (see ``cn_0003``). Pre-production app —
no data backfill, dev environments reset.

Revision ID: ag_0005
Revises: ag_0004
Create Date: 2026-05-24

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "ag_0005"
down_revision: str | None = "ag_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_column("appointments", "notes")


def downgrade() -> None:
    op.add_column(
        "appointments",
        sa.Column("notes", sa.Text(), nullable=True),
    )
