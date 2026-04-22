"""agenda — cabinet assignment deferral.

Clinics rarely know two weeks ahead which chair a patient will end up in.
This migration makes ``cabinet_id`` / ``cabinet`` nullable on
``appointments`` and introduces ``appointment_cabinet_events``, an
append-only audit trail of every (re)assignment. The denormalized
``cabinet_assigned_at`` / ``cabinet_assigned_by`` columns let the UI show
"assigned 4 min ago by Ana" without joining the event table on every card.

Backfill: for each existing appointment that already has a cabinet, we
record a synthetic initial event so the history isn't empty when the
feature lands.

Revision ID: ag_0003
Revises: ag_0002
Create Date: 2026-04-22

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "ag_0003"
down_revision: str | None = "ag_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "appointment_cabinet_events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("appointment_id", sa.UUID(), nullable=False),
        sa.Column("from_cabinet_id", sa.UUID(), nullable=True),
        sa.Column("to_cabinet_id", sa.UUID(), nullable=True),
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
        sa.ForeignKeyConstraint(["from_cabinet_id"], ["cabinets.id"]),
        sa.ForeignKeyConstraint(["to_cabinet_id"], ["cabinets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_appointment_cabinet_events_appointment_id"),
        "appointment_cabinet_events",
        ["appointment_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_appointment_cabinet_events_clinic_id"),
        "appointment_cabinet_events",
        ["clinic_id"],
        unique=False,
    )
    op.create_index(
        "ix_appointment_cabinet_events_appointment_changed_at",
        "appointment_cabinet_events",
        ["appointment_id", "changed_at"],
        unique=False,
    )

    op.add_column(
        "appointments",
        sa.Column("cabinet_assigned_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "appointments",
        sa.Column("cabinet_assigned_by", sa.UUID(), nullable=True),
    )
    op.create_foreign_key(
        "appointments_cabinet_assigned_by_fkey",
        "appointments",
        "users",
        ["cabinet_assigned_by"],
        ["id"],
    )

    # Drop the NOT NULL constraints on cabinet columns. Postgres keeps the
    # existing values; new rows can now insert NULL.
    op.alter_column("appointments", "cabinet_id", nullable=True)
    op.alter_column("appointments", "cabinet", nullable=True)

    # Backfill: every appointment that already has a cabinet gets a synthetic
    # initial event so analytics and the cabinet-history endpoint aren't
    # empty from day one.
    op.execute(
        """
        INSERT INTO appointment_cabinet_events
            (id, clinic_id, appointment_id, from_cabinet_id, to_cabinet_id,
             changed_at, changed_by, note, created_at)
        SELECT
            gen_random_uuid(), a.clinic_id, a.id, NULL, a.cabinet_id,
            a.created_at, NULL, NULL, a.created_at
        FROM appointments a
        WHERE a.cabinet_id IS NOT NULL
        """
    )
    op.execute(
        """
        UPDATE appointments
           SET cabinet_assigned_at = created_at
         WHERE cabinet_id IS NOT NULL
        """
    )


def downgrade() -> None:
    # Before re-enforcing NOT NULL we'd need a fallback cabinet; in practice
    # downgrade is only run on clean dev DBs. Fail fast if there's data to
    # migrate back.
    op.execute("UPDATE appointments SET cabinet_id = cabinet_id WHERE cabinet_id IS NULL")
    op.drop_constraint("appointments_cabinet_assigned_by_fkey", "appointments", type_="foreignkey")
    op.drop_column("appointments", "cabinet_assigned_by")
    op.drop_column("appointments", "cabinet_assigned_at")
    op.alter_column("appointments", "cabinet", nullable=False)
    op.alter_column("appointments", "cabinet_id", nullable=False)

    op.drop_index(
        "ix_appointment_cabinet_events_appointment_changed_at",
        table_name="appointment_cabinet_events",
    )
    op.drop_index(
        op.f("ix_appointment_cabinet_events_clinic_id"),
        table_name="appointment_cabinet_events",
    )
    op.drop_index(
        op.f("ix_appointment_cabinet_events_appointment_id"),
        table_name="appointment_cabinet_events",
    )
    op.drop_table("appointment_cabinet_events")
