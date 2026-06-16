"""Copilot event handlers — proactive nudges (ADR 0014 §Deferred).

Each handler follows the module convention: ``async def on_*(data: dict)``
that opens its own ``async_session_maker`` session. Copilot keeps
``depends = []`` — it only *subscribes* to other modules' events through
the bus (ADR 0003), never imports them.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, time, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import text

from app.database import async_session_maker

from .service import NudgeService

logger = logging.getLogger(__name__)


async def _end_of_local_day(db, clinic_id: UUID, now_utc: datetime) -> datetime:
    """The next local midnight for the clinic, as a UTC instant (same-day TTL)."""
    name = await db.scalar(text("SELECT timezone FROM clinics WHERE id = :id"), {"id": clinic_id})
    try:
        tz = ZoneInfo(name) if name else ZoneInfo("UTC")
    except (ZoneInfoNotFoundError, ValueError):
        tz = ZoneInfo("UTC")
    local = now_utc.astimezone(tz)
    next_midnight = datetime.combine(local.date() + timedelta(days=1), time.min, tzinfo=tz)
    return next_midnight.astimezone(UTC)


async def on_appointment_cancelled(data: dict) -> None:
    """A cancellation frees a slot — nudge staff to fill it from recalls."""
    appointment_id = data.get("appointment_id")
    clinic_id = data.get("clinic_id")
    if not appointment_id or not clinic_id:
        return
    async with async_session_maker() as db:
        try:
            cid = UUID(str(clinic_id))
            now_utc = datetime.now(UTC)
            await NudgeService.create(
                db,
                clinic_id=cid,
                kind="appointment_cancelled",
                dedupe_key=f"appointment_cancelled:{appointment_id}",
                # Acting on it means looking at recalls to fill the gap.
                required_permission="recalls.read",
                payload={
                    "appointment_id": str(appointment_id),
                    "patient_id": data.get("patient_id"),
                    "start_time": data.get("start_time"),
                    "professional_id": data.get("professional_id"),
                },
                expires_at=await _end_of_local_day(db, cid, now_utc),
            )
            await db.commit()
        except Exception as exc:  # never break the publisher
            logger.error("copilot nudge (cancellation) failed: %s", exc, exc_info=True)
            await db.rollback()
