"""APScheduler integration for Verifactu background jobs + event handlers.

The scheduler is owned by the host app at :mod:`app.core.scheduler`.
We register our jobs from :func:`register_jobs`, called from the
module's startup hook.

Jobs:

* ``verifactu_submissions`` — every 60 s, drain pending records and
  submit to AEAT.
* ``verifactu_stuck_reaper`` — every 5 min, demote records left in
  ``state='sending'`` for >10 min (worker crash recovery).
* ``verifactu_cert_expiry`` — daily at 08:00, alert clinic admins
  whose certificate expires in ≤30 days.

Event handlers:

* ``verifactu.record.rejected`` → email clinic admins about an AEAT
  rejection (throttled to 1 alert per clinic per 30 min).
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select

from app.core.auth.models import Clinic, ClinicMembership, User
from app.core.email import email_service
from app.core.events import EventType, event_bus
from app.core.scheduler import get_scheduler
from app.database import async_session_maker

from .models import VerifactuSettings
from .services.submission_queue import process_all, reap_stuck_sending

logger = logging.getLogger(__name__)

JOB_ID_SUBMISSIONS = "verifactu_submissions"
JOB_ID_REAPER = "verifactu_stuck_reaper"
JOB_ID_CERT_CHECK = "verifactu_cert_expiry"

ALL_JOB_IDS = (JOB_ID_SUBMISSIONS, JOB_ID_REAPER, JOB_ID_CERT_CHECK)

REJECTED_ALERT_THROTTLE = timedelta(minutes=30)


async def process_verifactu_submissions() -> None:
    """Periodic job: drain Verifactu queue across every enabled clinic."""

    counts = await process_all(async_session_maker)
    if counts:
        logger.info("verifactu: processed %s", counts)


async def reap_stuck_records() -> None:
    """Periodic job: rescue records stuck in ``state='sending'``."""

    await reap_stuck_sending(async_session_maker)


async def daily_cert_check() -> None:
    """Daily job: alert clinic admins about certificates expiring soon."""

    from .services.cert_expiry import check_expiring_certs

    await check_expiring_certs(async_session_maker)


def register_jobs() -> None:
    """Idempotent registration; safe under uvicorn --reload."""

    scheduler = get_scheduler()

    if not scheduler.get_job(JOB_ID_SUBMISSIONS):
        scheduler.add_job(
            process_verifactu_submissions,
            IntervalTrigger(seconds=60),
            id=JOB_ID_SUBMISSIONS,
            name="Drain Verifactu submission queue",
            replace_existing=True,
        )

    if not scheduler.get_job(JOB_ID_REAPER):
        scheduler.add_job(
            reap_stuck_records,
            IntervalTrigger(minutes=5),
            id=JOB_ID_REAPER,
            name="Reap Verifactu records stuck in 'sending'",
            replace_existing=True,
        )

    if not scheduler.get_job(JOB_ID_CERT_CHECK):
        scheduler.add_job(
            daily_cert_check,
            CronTrigger(hour=8, minute=0),
            id=JOB_ID_CERT_CHECK,
            name="Check Verifactu certificates expiring soon",
            replace_existing=True,
        )


def unregister_jobs() -> None:
    """Remove every Verifactu job from the scheduler.

    Called from :meth:`VerifactuModule.uninstall` so the host scheduler
    doesn't keep firing into a module that no longer has the imports
    available.
    """

    scheduler = get_scheduler()
    for job_id in ALL_JOB_IDS:
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)


# ---------------------------------------------------------------------------
# Event handlers
# ---------------------------------------------------------------------------


async def _admins_for(db, clinic_id: UUID) -> list[User]:
    result = await db.execute(
        select(User)
        .join(ClinicMembership, ClinicMembership.user_id == User.id)
        .where(
            ClinicMembership.clinic_id == clinic_id,
            ClinicMembership.role == "admin",
            User.is_active.is_(True),
        )
    )
    return list(result.scalars())


async def _notify_rejected(payload: dict) -> None:
    """Email clinic admins about a rejected Verifactu record.

    Throttled per clinic to one email per
    :data:`REJECTED_ALERT_THROTTLE` (default 30 min). Otherwise a
    systemic issue (bad NIF, expired cert) processed in a single batch
    would email admins dozens of times in a row.
    """

    clinic_id_str = payload.get("clinic_id")
    if not clinic_id_str:
        return
    clinic_id = UUID(clinic_id_str)
    now = datetime.now(UTC)
    throttle_cutoff = now - REJECTED_ALERT_THROTTLE

    async with async_session_maker() as db:
        settings_q = await db.execute(
            select(VerifactuSettings)
            .where(VerifactuSettings.clinic_id == clinic_id)
            .with_for_update()
        )
        settings = settings_q.scalar_one_or_none()
        if (
            settings is not None
            and settings.last_rejected_alert_at is not None
            and settings.last_rejected_alert_at >= throttle_cutoff
        ):
            return

        clinic_q = await db.execute(select(Clinic).where(Clinic.id == clinic_id))
        clinic = clinic_q.scalar_one_or_none()
        if clinic is None:
            return

        admins = await _admins_for(db, clinic_id)
        if not admins:
            return

        ctx_base = {
            "clinic_name": clinic.name,
            "invoice_number": payload.get("serie_numero") or "",
            "codigo_error": payload.get("codigo_error"),
            "friendly_message": payload.get("friendly_message")
            or payload.get("descripcion_error")
            or "Sin detalle.",
            "suggested_cta": payload.get("suggested_cta"),
            "field": payload.get("field"),
            "queue_url": None,  # filled at deploy time via env if needed
        }

        for admin in admins:
            ctx = dict(ctx_base, admin_name=admin.full_name)
            try:
                await email_service.send_templated(
                    to_email=admin.email,
                    to_name=admin.full_name,
                    template_key="verifactu_record_rejected",
                    context=ctx,
                    subject="Factura rechazada por AEAT — acción requerida",
                    locale="es",
                    db=db,
                    clinic_id=clinic_id,
                )
            except Exception:  # noqa: BLE001 — one admin failing must not block others
                logger.exception(
                    "verifactu rejected-alert: failed for admin %s clinic %s",
                    admin.id,
                    clinic_id,
                )

        if settings is not None:
            settings.last_rejected_alert_at = now
            await db.commit()


def _on_rejected_event(payload: dict) -> None:
    """Bus adapter — forwards to the async handler."""
    import asyncio

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_notify_rejected(payload))
    except RuntimeError:
        asyncio.run(_notify_rejected(payload))


def register_event_handlers() -> None:
    """Idempotent — replaces previous subscription on re-register."""

    event_bus.unsubscribe(EventType.VERIFACTU_RECORD_REJECTED, _on_rejected_event)
    event_bus.subscribe(EventType.VERIFACTU_RECORD_REJECTED, _on_rejected_event)


def unregister_event_handlers() -> None:
    event_bus.unsubscribe(EventType.VERIFACTU_RECORD_REJECTED, _on_rejected_event)
