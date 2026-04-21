"""Schedules models — clinic + professional weekly templates + overrides + shifts.

Normalized: no JSONB for shifts. One row per shift period, hanging off
one of four parent tables via nullable FKs with a CHECK constraint that
guarantees exactly one parent is set. The polymorphic-via-check-constraint
pattern keeps availability resolution in a single join path while
preserving referential integrity.
"""

from __future__ import annotations

from datetime import date, time
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    Time,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, TimestampMixin

if TYPE_CHECKING:
    from app.core.auth.models import Clinic, User


class ClinicWeeklySchedule(Base, TimestampMixin):
    """Weekly template for a clinic. One per clinic."""

    __tablename__ = "clinic_weekly_schedules"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    clinic_id: Mapped[UUID] = mapped_column(
        ForeignKey("clinics.id", ondelete="CASCADE"), index=True, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    clinic: Mapped[Clinic] = relationship()
    shifts: Mapped[list[ScheduleShift]] = relationship(
        back_populates="clinic_weekly",
        cascade="all, delete-orphan",
        foreign_keys="ScheduleShift.clinic_weekly_id",
    )

    __table_args__ = (UniqueConstraint("clinic_id", name="uq_clinic_weekly_schedule_clinic"),)


class ClinicOverride(Base, TimestampMixin):
    """Clinic-wide override for a date range (holidays, reduced hours)."""

    __tablename__ = "clinic_overrides"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    clinic_id: Mapped[UUID] = mapped_column(
        ForeignKey("clinics.id", ondelete="CASCADE"), index=True, nullable=False
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(200))

    clinic: Mapped[Clinic] = relationship()
    shifts: Mapped[list[ScheduleShift]] = relationship(
        back_populates="clinic_override",
        cascade="all, delete-orphan",
        foreign_keys="ScheduleShift.clinic_override_id",
    )

    __table_args__ = (
        CheckConstraint("end_date >= start_date", name="ck_clinic_override_date_order"),
        CheckConstraint("kind IN ('closed', 'custom_hours')", name="ck_clinic_override_kind"),
        Index(
            "ix_clinic_overrides_clinic_range",
            "clinic_id",
            "start_date",
            "end_date",
        ),
    )


class ProfessionalWeeklySchedule(Base, TimestampMixin):
    """Weekly template for a professional (dentist/hygienist) in a clinic."""

    __tablename__ = "professional_weekly_schedules"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    clinic_id: Mapped[UUID] = mapped_column(
        ForeignKey("clinics.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    clinic: Mapped[Clinic] = relationship()
    user: Mapped[User] = relationship()
    shifts: Mapped[list[ScheduleShift]] = relationship(
        back_populates="professional_weekly",
        cascade="all, delete-orphan",
        foreign_keys="ScheduleShift.professional_weekly_id",
    )

    __table_args__ = (
        UniqueConstraint("clinic_id", "user_id", name="uq_professional_weekly_schedule_user"),
    )


class ProfessionalOverride(Base, TimestampMixin):
    """Per-professional override for a date range (vacation, sick, training)."""

    __tablename__ = "professional_overrides"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    clinic_id: Mapped[UUID] = mapped_column(
        ForeignKey("clinics.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(200))

    clinic: Mapped[Clinic] = relationship()
    user: Mapped[User] = relationship()
    shifts: Mapped[list[ScheduleShift]] = relationship(
        back_populates="professional_override",
        cascade="all, delete-orphan",
        foreign_keys="ScheduleShift.professional_override_id",
    )

    __table_args__ = (
        CheckConstraint("end_date >= start_date", name="ck_professional_override_date_order"),
        CheckConstraint(
            "kind IN ('unavailable', 'custom_hours')",
            name="ck_professional_override_kind",
        ),
        Index(
            "ix_professional_overrides_clinic_user_range",
            "clinic_id",
            "user_id",
            "start_date",
            "end_date",
        ),
    )


class ScheduleShift(Base):
    """Single shift row belonging to exactly one parent schedule/override.

    Four nullable FKs plus a CHECK constraint for exactly-one-parent.
    ``weekday`` applies when parent is a weekly template (Mon=0..Sun=6);
    ``shift_date`` applies when parent is an override of kind
    ``custom_hours``. The XOR check enforces that invariant.
    """

    __tablename__ = "schedule_shifts"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    clinic_weekly_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("clinic_weekly_schedules.id", ondelete="CASCADE")
    )
    clinic_override_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("clinic_overrides.id", ondelete="CASCADE")
    )
    professional_weekly_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("professional_weekly_schedules.id", ondelete="CASCADE")
    )
    professional_override_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("professional_overrides.id", ondelete="CASCADE")
    )
    weekday: Mapped[int | None] = mapped_column(SmallInteger)
    shift_date: Mapped[date | None] = mapped_column(Date)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)

    clinic_weekly: Mapped[ClinicWeeklySchedule | None] = relationship(
        back_populates="shifts", foreign_keys=[clinic_weekly_id]
    )
    clinic_override: Mapped[ClinicOverride | None] = relationship(
        back_populates="shifts", foreign_keys=[clinic_override_id]
    )
    professional_weekly: Mapped[ProfessionalWeeklySchedule | None] = relationship(
        back_populates="shifts", foreign_keys=[professional_weekly_id]
    )
    professional_override: Mapped[ProfessionalOverride | None] = relationship(
        back_populates="shifts", foreign_keys=[professional_override_id]
    )

    __table_args__ = (
        CheckConstraint(
            "(CASE WHEN clinic_weekly_id IS NOT NULL THEN 1 ELSE 0 END) + "
            "(CASE WHEN clinic_override_id IS NOT NULL THEN 1 ELSE 0 END) + "
            "(CASE WHEN professional_weekly_id IS NOT NULL THEN 1 ELSE 0 END) + "
            "(CASE WHEN professional_override_id IS NOT NULL THEN 1 ELSE 0 END) = 1",
            name="ck_schedule_shift_exactly_one_parent",
        ),
        CheckConstraint(
            "(weekday IS NOT NULL AND shift_date IS NULL) OR "
            "(weekday IS NULL AND shift_date IS NOT NULL)",
            name="ck_schedule_shift_weekday_xor_date",
        ),
        CheckConstraint(
            "weekday IS NULL OR (weekday >= 0 AND weekday <= 6)",
            name="ck_schedule_shift_weekday_range",
        ),
        CheckConstraint("end_time > start_time", name="ck_schedule_shift_time_order"),
        Index(
            "ix_schedule_shifts_clinic_weekly",
            "clinic_weekly_id",
            "weekday",
        ),
        Index(
            "ix_schedule_shifts_clinic_override",
            "clinic_override_id",
            "shift_date",
        ),
        Index(
            "ix_schedule_shifts_professional_weekly",
            "professional_weekly_id",
            "weekday",
        ),
        Index(
            "ix_schedule_shifts_professional_override",
            "professional_override_id",
            "shift_date",
        ),
    )
