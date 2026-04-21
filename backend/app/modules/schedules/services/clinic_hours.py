"""Clinic hours service — CRUD on weekly template + clinic overrides."""

from __future__ import annotations

from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.auth.models import Clinic

from ..models import ClinicOverride, ClinicWeeklySchedule, ScheduleShift


class ClinicHoursService:
    """CRUD for a clinic's weekly schedule + date-range overrides."""

    DEFAULT_TIMEZONE = "Europe/Madrid"

    @staticmethod
    async def get_clinic_timezone(db: AsyncSession, clinic_id: UUID) -> str:
        """Return the clinic's configured timezone.

        Reads the first-class ``clinics.timezone`` column — the single
        source of truth shared by every time-aware module. Guarded
        against invalid values (database hand-edits) by falling back to
        the default and logging a warning instead of 500-ing the whole
        availability endpoint.
        """
        import logging
        from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

        result = await db.execute(select(Clinic.timezone).where(Clinic.id == clinic_id))
        tz = result.scalar_one_or_none() or ClinicHoursService.DEFAULT_TIMEZONE
        try:
            ZoneInfo(tz)
        except ZoneInfoNotFoundError:
            logging.getLogger(__name__).warning(
                "Invalid timezone %r on clinic %s; falling back to %s",
                tz,
                clinic_id,
                ClinicHoursService.DEFAULT_TIMEZONE,
            )
            return ClinicHoursService.DEFAULT_TIMEZONE
        return str(tz)

    @staticmethod
    async def get_or_create_weekly(db: AsyncSession, clinic_id: UUID) -> ClinicWeeklySchedule:
        """Fetch the clinic's weekly schedule or create a 24/7 default.

        Clinics that existed before the schedules module was installed
        got their 24/7 seed via the Alembic data migration. Clinics
        created afterwards (e.g. via `seed-demo.sh` or a fresh signup
        flow) land here on first read and get the same default, so the
        calendar never starts fully blocked.
        """
        from datetime import time as _time

        result = await db.execute(
            select(ClinicWeeklySchedule)
            .options(selectinload(ClinicWeeklySchedule.shifts))
            .where(ClinicWeeklySchedule.clinic_id == clinic_id)
        )
        weekly = result.scalar_one_or_none()
        if weekly is not None:
            return weekly

        weekly = ClinicWeeklySchedule(clinic_id=clinic_id, is_active=True)
        db.add(weekly)
        await db.flush()
        for weekday in range(7):
            db.add(
                ScheduleShift(
                    clinic_weekly_id=weekly.id,
                    weekday=weekday,
                    start_time=_time(0, 0),
                    end_time=_time(23, 59),
                )
            )
        await db.flush()
        await db.refresh(weekly, ["shifts"])
        return weekly

    @staticmethod
    async def replace_weekly_shifts(
        db: AsyncSession,
        weekly: ClinicWeeklySchedule,
        days: list[dict[str, Any]],
    ) -> ClinicWeeklySchedule:
        """Replace shifts for the weekdays named in ``days``.

        Any weekday NOT listed in ``days`` keeps its existing shifts. To
        clear a weekday, pass it with an empty shifts list.
        """
        weekdays_touched = {d["weekday"] for d in days}
        for shift in list(weekly.shifts):
            if shift.weekday in weekdays_touched:
                await db.delete(shift)
        await db.flush()

        for day in days:
            for s in day["shifts"]:
                db.add(
                    ScheduleShift(
                        clinic_weekly_id=weekly.id,
                        weekday=day["weekday"],
                        start_time=s["start_time"],
                        end_time=s["end_time"],
                    )
                )
        await db.flush()
        await db.refresh(weekly, ["shifts"])
        return weekly

    @staticmethod
    async def list_overrides(
        db: AsyncSession,
        clinic_id: UUID,
        start: date | None = None,
        end: date | None = None,
    ) -> list[ClinicOverride]:
        query = (
            select(ClinicOverride)
            .options(selectinload(ClinicOverride.shifts))
            .where(ClinicOverride.clinic_id == clinic_id)
        )
        if start is not None:
            query = query.where(ClinicOverride.end_date >= start)
        if end is not None:
            query = query.where(ClinicOverride.start_date <= end)
        query = query.order_by(ClinicOverride.start_date)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_override(
        db: AsyncSession, clinic_id: UUID, override_id: UUID
    ) -> ClinicOverride | None:
        result = await db.execute(
            select(ClinicOverride)
            .options(selectinload(ClinicOverride.shifts))
            .where(
                ClinicOverride.id == override_id,
                ClinicOverride.clinic_id == clinic_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create_override(
        db: AsyncSession, clinic_id: UUID, data: dict[str, Any]
    ) -> ClinicOverride:
        shifts = data.pop("shifts", []) or []
        override = ClinicOverride(clinic_id=clinic_id, **data)
        db.add(override)
        await db.flush()
        for s in shifts:
            db.add(
                ScheduleShift(
                    clinic_override_id=override.id,
                    shift_date=override.start_date,
                    start_time=s["start_time"],
                    end_time=s["end_time"],
                )
            )
        await db.flush()
        await db.refresh(override, ["shifts"])
        return override

    @staticmethod
    async def update_override(
        db: AsyncSession,
        override: ClinicOverride,
        data: dict[str, Any],
    ) -> ClinicOverride:
        shifts = data.pop("shifts", None)
        for key, value in data.items():
            setattr(override, key, value)
        await db.flush()

        if shifts is not None:
            for existing in list(override.shifts):
                await db.delete(existing)
            await db.flush()
            for s in shifts:
                db.add(
                    ScheduleShift(
                        clinic_override_id=override.id,
                        shift_date=override.start_date,
                        start_time=s["start_time"],
                        end_time=s["end_time"],
                    )
                )
            await db.flush()
            await db.refresh(override, ["shifts"])
        return override

    @staticmethod
    async def delete_override(db: AsyncSession, override: ClinicOverride) -> None:
        await db.delete(override)
        await db.flush()
