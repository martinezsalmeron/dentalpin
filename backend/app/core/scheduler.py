"""APScheduler configuration for background jobs.

Provides a singleton scheduler for running periodic tasks like
appointment reminders, budget expiry checks, etc.
"""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
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

    # Plan/budget workflow cron jobs (docs/workflows/plan-budget-flow-tech-plan.md §6).
    from app.modules.budget.tasks import (
        expire_budgets,
        purge_budget_access_logs,
        send_budget_reminders,
    )
    from app.modules.treatment_plan.tasks import auto_close_expired_plans

    _budget_jobs = [
        ("expire_budgets", expire_budgets, CronTrigger(hour=2, minute=0),
         "Mark draft/sent budgets past valid_until as expired (daily 02:00)"),
        ("send_budget_reminders", send_budget_reminders, CronTrigger(hour=9, minute=0),
         "Email patients about pending budgets at 7d/14d milestones (daily 09:00)"),
        ("auto_close_expired_plans", auto_close_expired_plans, CronTrigger(hour=3, minute=0),
         "Close pending plans whose budgets have been expired > N days (daily 03:00)"),
        ("purge_budget_access_logs", purge_budget_access_logs, CronTrigger(hour=4, minute=0),
         "Drop budget_access_logs older than 90 days (daily 04:00)"),
    ]
    for job_id, fn, trigger, name in _budget_jobs:
        if scheduler.get_job(job_id):
            logger.info("Scheduler job '%s' already exists, skipping", job_id)
            continue
        scheduler.add_job(
            fn,
            trigger,
            id=job_id,
            name=name,
            max_instances=1,
            replace_existing=True,
        )
        logger.info("Registered cron job '%s'", job_id)

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
