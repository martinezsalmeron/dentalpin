"""patients: add do_not_contact flag.

Issue #62 (recalls). Receptionists need a way to mark a patient as
"do not contact" so they are excluded from the recalls call list and
any future automated outreach. Lives on the patient record because
it is operational identity (same level as ``status``), not a clinical
preference.

Revision ID: pat_0002
Revises: pat_0001
Create Date: 2026-05-01

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "pat_0002"
down_revision: str | None = "pat_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "patients",
        sa.Column(
            "do_not_contact",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    # Drop the server default so application code controls future inserts.
    op.alter_column("patients", "do_not_contact", server_default=None)


def downgrade() -> None:
    op.drop_column("patients", "do_not_contact")
