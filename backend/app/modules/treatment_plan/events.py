"""Treatment plan module event handlers.

Listens to events from other modules and reacts accordingly.
"""

import logging
from typing import Any
from uuid import UUID

from sqlalchemy import select

from app.core.events import event_bus
from app.database import async_session_maker

from .models import PlannedTreatmentItem, TreatmentPlan

logger = logging.getLogger(__name__)


async def on_appointment_completed(data: dict[str, Any]) -> None:
    """Handle appointment completed event.

    When an appointment is completed, mark associated planned treatments as completed.
    """
    appointment_id = data.get("appointment_id")
    clinic_id = data.get("clinic_id")

    if not appointment_id or not clinic_id:
        logger.warning("on_appointment_completed: missing appointment_id or clinic_id")
        return

    async with async_session_maker() as db:
        try:
            # Import here to avoid circular imports
            from app.modules.clinical.models import AppointmentTreatment

            # Get completed treatments from the appointment
            result = await db.execute(
                select(AppointmentTreatment).where(
                    AppointmentTreatment.appointment_id == UUID(appointment_id),
                    AppointmentTreatment.completed_in_appointment == True,  # noqa: E712
                )
            )
            completed_treatments = result.scalars().all()

            for apt_treatment in completed_treatments:
                # Find planned item that references this treatment
                if apt_treatment.planned_treatment_item_id:
                    item_result = await db.execute(
                        select(PlannedTreatmentItem).where(
                            PlannedTreatmentItem.id == apt_treatment.planned_treatment_item_id,
                            PlannedTreatmentItem.clinic_id == UUID(clinic_id),
                        )
                    )
                    item = item_result.scalar_one_or_none()

                    if item and item.status != "completed":
                        item.status = "completed"
                        item.completed_without_appointment = False

                        # Publish completion event
                        event_bus.publish(
                            "treatment_plan.treatment_completed",
                            {
                                "plan_id": str(item.treatment_plan_id),
                                "item_id": str(item.id),
                                "tooth_treatment_id": str(item.tooth_treatment_id)
                                if item.tooth_treatment_id
                                else None,
                                "clinic_id": clinic_id,
                            },
                        )

            await db.commit()
            logger.info(
                f"Processed appointment completion for {len(completed_treatments)} treatments"
            )

        except Exception as e:
            logger.error(f"Error processing appointment completion: {e}", exc_info=True)
            await db.rollback()


async def on_budget_accepted(data: dict[str, Any]) -> None:
    """Handle budget accepted event.

    When a budget is accepted, activate the linked treatment plan if in draft.
    """
    budget_id = data.get("budget_id")
    clinic_id = data.get("clinic_id")

    if not budget_id or not clinic_id:
        logger.warning("on_budget_accepted: missing budget_id or clinic_id")
        return

    async with async_session_maker() as db:
        try:
            # Find plan linked to this budget
            result = await db.execute(
                select(TreatmentPlan).where(
                    TreatmentPlan.budget_id == UUID(budget_id),
                    TreatmentPlan.clinic_id == UUID(clinic_id),
                )
            )
            plan = result.scalar_one_or_none()

            if plan and plan.status == "draft":
                old_status = plan.status
                plan.status = "active"

                event_bus.publish(
                    "treatment_plan.status_changed",
                    {
                        "plan_id": str(plan.id),
                        "old_status": old_status,
                        "new_status": "active",
                        "clinic_id": clinic_id,
                        "triggered_by": "budget_accepted",
                    },
                )

                await db.commit()
                logger.info(f"Activated treatment plan {plan.id} after budget acceptance")

        except Exception as e:
            logger.error(f"Error processing budget acceptance: {e}", exc_info=True)
            await db.rollback()


async def on_treatment_performed(data: dict[str, Any]) -> None:
    """Handle treatment performed from odontogram.

    When a treatment is performed directly in the odontogram,
    mark the corresponding planned item as completed.
    """
    tooth_treatment_id = data.get("tooth_treatment_id")
    clinic_id = data.get("clinic_id")

    if not tooth_treatment_id or not clinic_id:
        logger.warning("on_treatment_performed: missing tooth_treatment_id or clinic_id")
        return

    async with async_session_maker() as db:
        try:
            # Find planned item referencing this tooth treatment
            result = await db.execute(
                select(PlannedTreatmentItem).where(
                    PlannedTreatmentItem.tooth_treatment_id == UUID(tooth_treatment_id),
                    PlannedTreatmentItem.clinic_id == UUID(clinic_id),
                    PlannedTreatmentItem.status == "pending",
                )
            )
            item = result.scalar_one_or_none()

            if item:
                item.status = "completed"
                item.completed_without_appointment = True

                event_bus.publish(
                    "treatment_plan.treatment_completed",
                    {
                        "plan_id": str(item.treatment_plan_id),
                        "item_id": str(item.id),
                        "tooth_treatment_id": tooth_treatment_id,
                        "clinic_id": clinic_id,
                        "triggered_by": "odontogram_performed",
                    },
                )

                await db.commit()
                logger.info(
                    f"Marked planned item {item.id} as completed from odontogram"
                )

        except Exception as e:
            logger.error(f"Error processing treatment performed: {e}", exc_info=True)
            await db.rollback()
