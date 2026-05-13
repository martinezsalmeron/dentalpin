"""Event handlers consumed by the payments module.

Both handlers upsert a single ``PatientEarnedEntry`` per
``treatment_id``. The unique index on ``treatment_id`` makes the
operation idempotent regardless of which publisher fires first or
whether both fire for the same treatment.
"""

from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.database import async_session_maker

from .models import PatientEarnedEntry

logger = logging.getLogger(__name__)


def _parse_uuid(value: Any) -> UUID | None:
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    try:
        return UUID(str(value))
    except (ValueError, TypeError):
        return None


def _parse_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def _parse_amount(value: Any) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except Exception:
        return None


async def _upsert_earned_entry(data: dict[str, Any], source_event: str) -> None:
    clinic_id = _parse_uuid(data.get("clinic_id"))
    patient_id = _parse_uuid(data.get("patient_id"))
    treatment_id = _parse_uuid(data.get("treatment_id"))
    performed_at = _parse_datetime(data.get("performed_at"))
    amount = _parse_amount(data.get("unit_price") or data.get("price_snapshot"))

    if not (clinic_id and patient_id and treatment_id and performed_at):
        logger.debug(
            "%s: missing required fields, skipping earned upsert (data=%s)",
            source_event,
            data,
        )
        return
    if amount is None:
        # Publisher didn't carry a price. Without it the earned ledger
        # cannot reflect this treatment. Logged so missing publisher
        # extensions surface during integration.
        logger.info(
            "%s: no unit_price/price_snapshot in payload, skipping (treatment_id=%s)",
            source_event,
            treatment_id,
        )
        return

    catalog_item_id = _parse_uuid(data.get("catalog_item_id"))
    professional_id = _parse_uuid(data.get("performed_by") or data.get("professional_id"))

    async with async_session_maker() as db:
        try:
            stmt = (
                pg_insert(PatientEarnedEntry)
                .values(
                    clinic_id=clinic_id,
                    patient_id=patient_id,
                    treatment_id=treatment_id,
                    catalog_item_id=catalog_item_id,
                    amount=amount,
                    performed_at=performed_at,
                    professional_id=professional_id,
                    source_event=source_event,
                )
                .on_conflict_do_nothing(constraint="uq_earned_treatment")
            )
            await db.execute(stmt)
            await db.commit()
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Failed to upsert PatientEarnedEntry: %s", exc, exc_info=True)
            await db.rollback()


async def on_treatment_performed(data: dict[str, Any]) -> None:
    """Handler for ``odontogram.treatment.performed``."""
    await _upsert_earned_entry(data, source_event="odontogram.treatment.performed")


async def on_plan_item_completed(data: dict[str, Any]) -> None:
    """Handler for ``treatment_plan.treatment_completed``.

    Convergent with ``on_treatment_performed`` via the unique
    ``treatment_id`` constraint — only the first event materializes a
    row, the rest are no-ops.
    """
    await _upsert_earned_entry(data, source_event="treatment_plan.treatment_completed")
