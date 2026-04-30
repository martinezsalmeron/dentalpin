"""Treatment plan background tasks (APScheduler entry points).

Lives in ``treatment_plan`` rather than ``budget`` because closing a
plan is a treatment_plan write — and treatment_plan declares budget
as a dependency, so reading ``budgets`` from here respects the module
contract (ADR 0003).
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import text

from app.database import async_session_maker

logger = logging.getLogger(__name__)

# Default plan auto-close window (days) after a budget has been
# expired. Mirrors ``DEFAULT_PLAN_AUTO_CLOSE_DAYS`` in the budget
# workflow but kept here too so the cron does not import it from
# budget (avoids tight coupling on a constant).
DEFAULT_PLAN_AUTO_CLOSE_DAYS = 30


async def auto_close_expired_plans() -> None:
    """Close ``pending`` plans whose linked budget has been ``expired``
    for more than the per-clinic threshold (default: 30 days).

    Idempotent — re-runs on a clinic with no eligible plans are no-ops.
    Errors per-plan are logged but do not poison the run.
    """
    today = date.today()
    async with async_session_maker() as db:
        clinic_rows = (
            await db.execute(text("SELECT id, settings FROM clinics WHERE deleted_at IS NULL"))
        ).all()

    from .service import TreatmentPlanService  # avoid circular at import-time

    for clinic_row in clinic_rows:
        settings_json = clinic_row.settings or {}
        threshold_days = int(
            settings_json.get("plan_auto_close_days_after_expiry", DEFAULT_PLAN_AUTO_CLOSE_DAYS)
        )
        cutoff = today - timedelta(days=threshold_days)
        clinic_id: UUID = clinic_row.id

        async with async_session_maker() as db:
            try:
                rows = (
                    await db.execute(
                        text(
                            "SELECT tp.id "
                            "FROM treatment_plans tp "
                            "JOIN budgets b ON b.id = tp.budget_id "
                            "WHERE tp.clinic_id = :clinic_id "
                            "  AND tp.deleted_at IS NULL "
                            "  AND tp.status = 'pending' "
                            "  AND b.status = 'expired' "
                            "  AND b.valid_until <= :cutoff"
                        ),
                        {"clinic_id": clinic_id, "cutoff": cutoff},
                    )
                ).all()

                if not rows:
                    continue

                for row in rows:
                    plan = await TreatmentPlanService.get(db, clinic_id, row.id)
                    if not plan:
                        continue
                    try:
                        await TreatmentPlanService.close(
                            db,
                            clinic_id,
                            plan.id,
                            plan.created_by,
                            closure_reason="expired",
                            closure_note=(f"Auto-closed {threshold_days}d after budget expiry"),
                        )
                    except ValueError as exc:
                        logger.info(
                            "auto_close_expired_plans skip plan %s: %s",
                            plan.id,
                            exc,
                        )
                await db.commit()
            except Exception as exc:
                logger.error(
                    "auto_close_expired_plans failed for clinic %s: %s",
                    clinic_id,
                    exc,
                    exc_info=True,
                )
                await db.rollback()
