"""schedules module — initial schema + 24/7 default seed.

Revision ID: sch_0001
Revises: notif_0001
Create Date: 2026-04-21
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "sch_0001"
down_revision: str | None = "notif_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "clinic_weekly_schedules",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("clinic_id", name="uq_clinic_weekly_schedule_clinic"),
    )
    op.create_index(
        op.f("ix_clinic_weekly_schedules_clinic_id"),
        "clinic_weekly_schedules",
        ["clinic_id"],
    )

    op.create_table(
        "clinic_overrides",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("kind", sa.String(length=20), nullable=False),
        sa.Column("reason", sa.String(length=200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("end_date >= start_date", name="ck_clinic_override_date_order"),
        sa.CheckConstraint("kind IN ('closed', 'custom_hours')", name="ck_clinic_override_kind"),
    )
    op.create_index(op.f("ix_clinic_overrides_clinic_id"), "clinic_overrides", ["clinic_id"])
    op.create_index(
        "ix_clinic_overrides_clinic_range",
        "clinic_overrides",
        ["clinic_id", "start_date", "end_date"],
    )

    op.create_table(
        "professional_weekly_schedules",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("clinic_id", "user_id", name="uq_professional_weekly_schedule_user"),
    )
    op.create_index(
        op.f("ix_professional_weekly_schedules_clinic_id"),
        "professional_weekly_schedules",
        ["clinic_id"],
    )
    op.create_index(
        op.f("ix_professional_weekly_schedules_user_id"),
        "professional_weekly_schedules",
        ["user_id"],
    )

    op.create_table(
        "professional_overrides",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("kind", sa.String(length=20), nullable=False),
        sa.Column("reason", sa.String(length=200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("end_date >= start_date", name="ck_professional_override_date_order"),
        sa.CheckConstraint(
            "kind IN ('unavailable', 'custom_hours')",
            name="ck_professional_override_kind",
        ),
    )
    op.create_index(
        op.f("ix_professional_overrides_clinic_id"),
        "professional_overrides",
        ["clinic_id"],
    )
    op.create_index(
        op.f("ix_professional_overrides_user_id"),
        "professional_overrides",
        ["user_id"],
    )
    op.create_index(
        "ix_professional_overrides_clinic_user_range",
        "professional_overrides",
        ["clinic_id", "user_id", "start_date", "end_date"],
    )

    op.create_table(
        "schedule_shifts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clinic_weekly_id", sa.UUID(), nullable=True),
        sa.Column("clinic_override_id", sa.UUID(), nullable=True),
        sa.Column("professional_weekly_id", sa.UUID(), nullable=True),
        sa.Column("professional_override_id", sa.UUID(), nullable=True),
        sa.Column("weekday", sa.SmallInteger(), nullable=True),
        sa.Column("shift_date", sa.Date(), nullable=True),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.ForeignKeyConstraint(
            ["clinic_weekly_id"], ["clinic_weekly_schedules.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["clinic_override_id"], ["clinic_overrides.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["professional_weekly_id"],
            ["professional_weekly_schedules.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["professional_override_id"],
            ["professional_overrides.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "(CASE WHEN clinic_weekly_id IS NOT NULL THEN 1 ELSE 0 END) + "
            "(CASE WHEN clinic_override_id IS NOT NULL THEN 1 ELSE 0 END) + "
            "(CASE WHEN professional_weekly_id IS NOT NULL THEN 1 ELSE 0 END) + "
            "(CASE WHEN professional_override_id IS NOT NULL THEN 1 ELSE 0 END) = 1",
            name="ck_schedule_shift_exactly_one_parent",
        ),
        sa.CheckConstraint(
            "(weekday IS NOT NULL AND shift_date IS NULL) OR "
            "(weekday IS NULL AND shift_date IS NOT NULL)",
            name="ck_schedule_shift_weekday_xor_date",
        ),
        sa.CheckConstraint(
            "weekday IS NULL OR (weekday >= 0 AND weekday <= 6)",
            name="ck_schedule_shift_weekday_range",
        ),
        sa.CheckConstraint("end_time > start_time", name="ck_schedule_shift_time_order"),
    )
    op.create_index(
        "ix_schedule_shifts_clinic_weekly",
        "schedule_shifts",
        ["clinic_weekly_id", "weekday"],
    )
    op.create_index(
        "ix_schedule_shifts_clinic_override",
        "schedule_shifts",
        ["clinic_override_id", "shift_date"],
    )
    op.create_index(
        "ix_schedule_shifts_professional_weekly",
        "schedule_shifts",
        ["professional_weekly_id", "weekday"],
    )
    op.create_index(
        "ix_schedule_shifts_professional_override",
        "schedule_shifts",
        ["professional_override_id", "shift_date"],
    )

    # Seed a 24/7 default template for every existing clinic so calendar
    # callers get sane "always open" behaviour until an admin edits it.
    # Uses SQL-side generation so the data migration is self-contained
    # (no Python ORM call within migrations).
    op.execute(
        """
        INSERT INTO clinic_weekly_schedules (id, clinic_id, is_active, created_at, updated_at)
        SELECT gen_random_uuid(), c.id, TRUE, NOW(), NOW()
        FROM clinics c
        WHERE NOT EXISTS (
            SELECT 1 FROM clinic_weekly_schedules cws WHERE cws.clinic_id = c.id
        );
        """
    )
    op.execute(
        """
        INSERT INTO schedule_shifts
            (id, clinic_weekly_id, weekday, start_time, end_time)
        SELECT gen_random_uuid(), cws.id, d.wd, TIME '00:00', TIME '23:59'
        FROM clinic_weekly_schedules cws
        CROSS JOIN (
            SELECT generate_series(0, 6)::smallint AS wd
        ) d
        WHERE NOT EXISTS (
            SELECT 1 FROM schedule_shifts s
            WHERE s.clinic_weekly_id = cws.id AND s.weekday = d.wd
        );
        """
    )


def downgrade() -> None:
    op.drop_index("ix_schedule_shifts_professional_override", table_name="schedule_shifts")
    op.drop_index("ix_schedule_shifts_professional_weekly", table_name="schedule_shifts")
    op.drop_index("ix_schedule_shifts_clinic_override", table_name="schedule_shifts")
    op.drop_index("ix_schedule_shifts_clinic_weekly", table_name="schedule_shifts")
    op.drop_table("schedule_shifts")

    op.drop_index(
        "ix_professional_overrides_clinic_user_range", table_name="professional_overrides"
    )
    op.drop_index(op.f("ix_professional_overrides_user_id"), table_name="professional_overrides")
    op.drop_index(op.f("ix_professional_overrides_clinic_id"), table_name="professional_overrides")
    op.drop_table("professional_overrides")

    op.drop_index(
        op.f("ix_professional_weekly_schedules_user_id"),
        table_name="professional_weekly_schedules",
    )
    op.drop_index(
        op.f("ix_professional_weekly_schedules_clinic_id"),
        table_name="professional_weekly_schedules",
    )
    op.drop_table("professional_weekly_schedules")

    op.drop_index("ix_clinic_overrides_clinic_range", table_name="clinic_overrides")
    op.drop_index(op.f("ix_clinic_overrides_clinic_id"), table_name="clinic_overrides")
    op.drop_table("clinic_overrides")

    op.drop_index(
        op.f("ix_clinic_weekly_schedules_clinic_id"),
        table_name="clinic_weekly_schedules",
    )
    op.drop_table("clinic_weekly_schedules")
