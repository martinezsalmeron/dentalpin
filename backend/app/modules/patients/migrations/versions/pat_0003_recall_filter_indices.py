"""patients: indices for recall / outreach filters.

Recalls and search list endpoints filter heavily on
``(clinic_id, status)`` (active vs archived patients) and
``(clinic_id, do_not_contact)`` (operational opt-out). Without these
indices the planner falls back to a clinic-wide scan once a clinic
crosses a few thousand patients.

The ``do_not_contact`` index is partial — outreach lists always look
for the ``false`` half, and the ``true`` half is small (review bucket
only), so we don't pay for indexing it.

Revision ID: pat_0003
Revises: pat_0002
Create Date: 2026-05-18

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "pat_0003"
down_revision: str | None = "pat_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ix_patients_clinic_status",
        "patients",
        ["clinic_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_patients_clinic_do_not_contact_active",
        "patients",
        ["clinic_id"],
        unique=False,
        postgresql_where=sa.text("do_not_contact = false"),
    )


def downgrade() -> None:
    op.drop_index("ix_patients_clinic_do_not_contact_active", table_name="patients")
    op.drop_index("ix_patients_clinic_status", table_name="patients")
