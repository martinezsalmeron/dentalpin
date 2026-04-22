"""agenda — appointment status lifecycle.

Adds the ``appointment_status_events`` audit trail, a denormalized
``current_status_since`` column on ``appointments`` and a CHECK constraint
limiting ``appointments.status`` to the canonical set.

Backfill:
- ``appointments.current_status_since`` <- ``updated_at``.
- One synthetic event per appointment: ``(from=NULL, to=status,
  changed_at=created_at, changed_by=NULL)``. When ``status`` differs from
  ``'scheduled'`` we also insert a second event at ``updated_at`` so the
  history at least captures *that* the transition happened even though the
  actor and intermediate steps are unknown for legacy rows.

Revision ID: ag_0002
Revises: 0003
Create Date: 2026-04-22

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "ag_0002"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


STATUSES = (
    "scheduled",
    "confirmed",
    "checked_in",
    "in_treatment",
    "completed",
    "cancelled",
    "no_show",
)


def upgrade() -> None:
    op.create_table(
        "appointment_status_events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("appointment_id", sa.UUID(), nullable=False),
        sa.Column("from_status", sa.String(length=20), nullable=True),
        sa.Column("to_status", sa.String(length=20), nullable=False),
        sa.Column(
            "changed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("changed_by", sa.UUID(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["appointment_id"], ["appointments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"]),
        sa.ForeignKeyConstraint(["changed_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_appointment_status_events_appointment_id"),
        "appointment_status_events",
        ["appointment_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_appointment_status_events_clinic_id"),
        "appointment_status_events",
        ["clinic_id"],
        unique=False,
    )
    op.create_index(
        "ix_appointment_status_events_appointment_changed_at",
        "appointment_status_events",
        ["appointment_id", "changed_at"],
        unique=False,
    )

    op.add_column(
        "appointments",
        sa.Column(
            "current_status_since",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # Align current_status_since with the last known mutation before adding
    # the constraint / backfill so the history we insert matches the row.
    op.execute("UPDATE appointments SET current_status_since = updated_at")

    # Drop any rows that somehow fell out of the canonical set before
    # enforcing the constraint (defensive; no-op on clean installs).
    values = ", ".join(f"'{s}'" for s in STATUSES)
    op.execute(f"UPDATE appointments SET status = 'scheduled' WHERE status NOT IN ({values})")
    op.create_check_constraint(
        "ck_appointment_status_valid",
        "appointments",
        f"status IN ({values})",
    )

    # Seed the synthetic initial event for every existing appointment.
    op.execute(
        """
        INSERT INTO appointment_status_events
            (id, clinic_id, appointment_id, from_status, to_status,
             changed_at, changed_by, note, created_at)
        SELECT
            gen_random_uuid(), a.clinic_id, a.id, NULL, 'scheduled',
            a.created_at, NULL, NULL, a.created_at
        FROM appointments a
        """
    )
    # And a second event for anything that already moved past 'scheduled'.
    op.execute(
        """
        INSERT INTO appointment_status_events
            (id, clinic_id, appointment_id, from_status, to_status,
             changed_at, changed_by, note, created_at)
        SELECT
            gen_random_uuid(), a.clinic_id, a.id, 'scheduled', a.status,
            a.updated_at, NULL, NULL, a.updated_at
        FROM appointments a
        WHERE a.status <> 'scheduled'
        """
    )


def downgrade() -> None:
    op.drop_constraint("ck_appointment_status_valid", "appointments", type_="check")
    op.drop_column("appointments", "current_status_since")
    op.drop_index(
        "ix_appointment_status_events_appointment_changed_at",
        table_name="appointment_status_events",
    )
    op.drop_index(
        op.f("ix_appointment_status_events_clinic_id"),
        table_name="appointment_status_events",
    )
    op.drop_index(
        op.f("ix_appointment_status_events_appointment_id"),
        table_name="appointment_status_events",
    )
    op.drop_table("appointment_status_events")
