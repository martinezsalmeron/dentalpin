"""Budget background tasks (APScheduler entry points).

These functions are called by ``app.core.scheduler``. Each opens its
own session and commits explicitly. They are idempotent — re-running
without state change is a no-op.
"""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime, timedelta
from uuid import UUID

from sqlalchemy import select, text

from app.database import async_session_maker

from .models import Budget
from .workflow import BudgetWorkflowService

logger = logging.getLogger(__name__)


async def expire_budgets() -> None:
    """Mark every draft/sent budget past ``valid_until`` as ``expired``.

    Wraps ``BudgetWorkflowService.check_expired_budgets`` per clinic.
    """
    async with async_session_maker() as db:
        clinic_rows = (
            await db.execute(text("SELECT id FROM clinics WHERE deleted_at IS NULL"))
        ).all()
        clinic_ids = [row.id for row in clinic_rows]

    for clinic_id in clinic_ids:
        async with async_session_maker() as db:
            try:
                await BudgetWorkflowService.check_expired_budgets(db, clinic_id)
                await db.commit()
            except Exception as exc:
                logger.error("expire_budgets failed for clinic %s: %s", clinic_id, exc, exc_info=True)
                await db.rollback()


async def send_budget_reminders() -> None:
    """Send 7-day / 14-day reminders for sent budgets without response.

    Honours the per-clinic toggle ``budget_reminders_enabled`` (default
    off). The function only emits the ``budget.reminder_sent`` event;
    the notifications module subscribes and renders the email.
    """
    today = date.today()
    async with async_session_maker() as db:
        clinic_rows = (
            await db.execute(text("SELECT id, settings FROM clinics WHERE deleted_at IS NULL"))
        ).all()

    for clinic_row in clinic_rows:
        settings_json = clinic_row.settings or {}
        if not settings_json.get("budget_reminders_enabled"):
            continue
        clinic_id: UUID = clinic_row.id

        async with async_session_maker() as db:
            try:
                seven_ago = today - timedelta(days=7)
                fourteen_ago = today - timedelta(days=14)
                # Fetch sent budgets created up to 14 days ago without a
                # reminder in the last 5 days. We cap the rolling
                # cooldown at 5 days so neither the 7d nor the 14d
                # milestone double-fires within the same cycle.
                cutoff_no_reminder = datetime.combine(
                    today - timedelta(days=5),
                    datetime.min.time(),
                    tzinfo=UTC,
                )
                rows = (
                    await db.execute(
                        select(Budget).where(
                            Budget.clinic_id == clinic_id,
                            Budget.status == "sent",
                            Budget.deleted_at.is_(None),
                            Budget.valid_from <= seven_ago,
                            (
                                Budget.last_reminder_sent_at.is_(None)
                                | (Budget.last_reminder_sent_at <= cutoff_no_reminder)
                            ),
                        )
                    )
                ).scalars().all()

                for budget in rows:
                    days_since_send = (today - budget.valid_from).days
                    if days_since_send >= 14:
                        milestone = 14
                    elif days_since_send >= 7:
                        milestone = 7
                    else:
                        continue
                    await BudgetWorkflowService.send_reminder(
                        db, budget, milestone_days=milestone
                    )
                await db.commit()
            except Exception as exc:
                logger.error(
                    "send_budget_reminders failed for clinic %s: %s",
                    clinic_id,
                    exc,
                    exc_info=True,
                )
                await db.rollback()


async def purge_budget_access_logs() -> None:
    """Drop ``budget_access_logs`` rows older than 90 days.

    Retention policy from ADR 0006. Single bulk DELETE per run.
    """
    cutoff = datetime.now(UTC) - timedelta(days=90)
    async with async_session_maker() as db:
        try:
            result = await db.execute(
                text(
                    "DELETE FROM budget_access_logs "
                    "WHERE attempted_at < :cutoff"
                ),
                {"cutoff": cutoff},
            )
            await db.commit()
            logger.info("purge_budget_access_logs: removed %s rows", result.rowcount or 0)
        except Exception as exc:
            logger.error("purge_budget_access_logs failed: %s", exc, exc_info=True)
            await db.rollback()
