"""Odontogram module - dental charting and tooth condition tracking."""

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter
from sqlalchemy import select

from app.core.events.types import EventType
from app.core.plugins import BaseModule
from app.database import async_session_maker

from .models import OdontogramHistory, ToothRecord, ToothTreatment
from .router import router

logger = logging.getLogger(__name__)


class OdontogramModule(BaseModule):
    """Odontogram module providing dental charting functionality."""

    @property
    def name(self) -> str:
        return "odontogram"

    @property
    def version(self) -> str:
        return "0.2.0"

    @property
    def dependencies(self) -> list[str]:
        return ["clinical"]  # Depends on clinical for Patient model

    def get_models(self) -> list:
        return [ToothRecord, OdontogramHistory, ToothTreatment]

    def get_router(self) -> APIRouter:
        return router

    def get_permissions(self) -> list[str]:
        return [
            "read",
            "write",
            "treatments.read",
            "treatments.write",
        ]

    def get_event_handlers(self) -> dict[str, Any]:
        return {
            EventType.TREATMENT_PLAN_TREATMENT_COMPLETED: self._on_plan_treatment_completed,
        }

    async def _on_plan_treatment_completed(self, data: dict[str, Any]) -> None:
        """Update ToothTreatment status when completed in treatment plan.

        Changes status from 'planned' to 'existing' and records completion.
        """
        tooth_treatment_id = data.get("tooth_treatment_id")
        clinic_id = data.get("clinic_id")
        completed_by = data.get("completed_by")

        if not tooth_treatment_id or not clinic_id:
            return

        async with async_session_maker() as db:
            try:
                result = await db.execute(
                    select(ToothTreatment).where(
                        ToothTreatment.id == UUID(tooth_treatment_id),
                        ToothTreatment.clinic_id == UUID(clinic_id),
                    )
                )
                treatment = result.scalar_one_or_none()

                if treatment and treatment.status == "planned":
                    treatment.status = "existing"
                    treatment.performed_at = datetime.now(UTC)
                    if completed_by:
                        treatment.performed_by = UUID(completed_by)

                    await db.commit()
                    logger.info(f"Updated ToothTreatment {tooth_treatment_id} status to existing")

            except Exception as e:
                logger.error(f"Error updating tooth treatment status: {e}", exc_info=True)
                await db.rollback()
