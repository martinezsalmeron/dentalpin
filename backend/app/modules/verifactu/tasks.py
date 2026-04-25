"""APScheduler integration for Verifactu submissions.

The scheduler is owned by the host app at :mod:`app.core.scheduler`.
We register our jobs from :func:`init_verifactu_scheduler`, called
from the module's startup hook.
"""

from __future__ import annotations

import logging

from apscheduler.triggers.interval import IntervalTrigger

from app.core.scheduler import get_scheduler
from app.database import async_session_maker

from .services.submission_queue import process_all

logger = logging.getLogger(__name__)

JOB_ID = "verifactu_submissions"


async def process_verifactu_submissions() -> None:
    """Periodic job: drain Verifactu queue across every enabled clinic."""

    counts = await process_all(async_session_maker)
    if counts:
        logger.info("verifactu: processed %s", counts)


def register_jobs() -> None:
    """Idempotent registration; safe under uvicorn --reload."""

    scheduler = get_scheduler()
    existing = scheduler.get_job(JOB_ID)
    if existing:
        return
    scheduler.add_job(
        process_verifactu_submissions,
        IntervalTrigger(seconds=60),
        id=JOB_ID,
        name="Drain Verifactu submission queue",
        replace_existing=True,
    )
