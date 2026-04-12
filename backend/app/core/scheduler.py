"""APScheduler configuration for background jobs.

Provides a singleton scheduler for running periodic tasks like
appointment reminders.
"""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.config import settings

logger = logging.getLogger(__name__)

# Singleton scheduler instance
scheduler: AsyncIOScheduler | None = None


def get_scheduler() -> AsyncIOScheduler:
    """Get the scheduler instance, creating it if needed."""
    global scheduler
    if scheduler is None:
        scheduler = AsyncIOScheduler()
    return scheduler


def init_scheduler() -> None:
    """Initialize and start the scheduler.

    Registers all periodic jobs and starts the scheduler.
    Should be called during application startup.
    """
    global scheduler

    # Don't run scheduler in test mode
    if settings.TESTING:
        logger.info("Skipping scheduler initialization in test mode")
        return

    from app.modules.notifications.tasks import process_appointment_reminders

    scheduler = get_scheduler()

    # Check if job already exists (in case of hot reload)
    existing_job = scheduler.get_job("appointment_reminders")
    if existing_job:
        logger.info("Scheduler job 'appointment_reminders' already exists, skipping registration")
    else:
        # Run appointment reminders every 5 minutes
        scheduler.add_job(
            process_appointment_reminders,
            IntervalTrigger(minutes=5),
            id="appointment_reminders",
            name="Process appointment reminders",
            replace_existing=True,
        )
        logger.info("Registered appointment reminders job (every 5 minutes)")

    if not scheduler.running:
        scheduler.start()
        logger.info("Scheduler started")


def shutdown_scheduler() -> None:
    """Shutdown the scheduler gracefully.

    Should be called during application shutdown.
    """
    global scheduler
    if scheduler and scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler shutdown complete")
