"""agenda: relax the unique slot index to active statuses only.

The original ``idx_appointment_slot`` partial unique index
(``ag_0001``) excluded only ``cancelled`` rows from the uniqueness
check, so a ``completed`` or ``no_show`` appointment kept reserving
its (clinic, cabinet, professional, start_time) tuple forever. This
made it impossible to assign a *new* checked-in appointment to a
cabinet whose slot had been used earlier by another now-finished
visit at the same nominal hour — a 409 the operator can't recover
from without DB surgery.

Terminal statuses (``cancelled``, ``completed``, ``no_show``) are
historical: they shouldn't compete for slot exclusivity. Only the
*active* statuses (``scheduled``, ``confirmed``, ``checked_in``,
``in_treatment``) need the guard.

Drops the old index and recreates it with a wider exclusion. Index
name kept the same so anything that asks Postgres about it by name
keeps working.

Revision ID: ag_0004
Revises: ag_0003
Create Date: 2026-05-01
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "ag_0004"
down_revision: str | None = "ag_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_index("idx_appointment_slot", table_name="appointments")
    op.create_index(
        "idx_appointment_slot",
        "appointments",
        ["clinic_id", "cabinet_id", "professional_id", "start_time"],
        unique=True,
        postgresql_where=sa.text("status NOT IN ('cancelled', 'completed', 'no_show')"),
    )


def downgrade() -> None:
    op.drop_index("idx_appointment_slot", table_name="appointments")
    op.create_index(
        "idx_appointment_slot",
        "appointments",
        ["clinic_id", "cabinet_id", "professional_id", "start_time"],
        unique=True,
        postgresql_where=sa.text("status != 'cancelled'"),
    )
