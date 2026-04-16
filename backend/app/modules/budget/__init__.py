"""Budget module - dental treatment quotes management."""

import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter
from sqlalchemy import select

from app.core.events.types import EventType
from app.core.plugins import BaseModule
from app.database import async_session_maker

from .models import Budget, BudgetHistory, BudgetItem, BudgetSignature
from .router import router

logger = logging.getLogger(__name__)


class BudgetModule(BaseModule):
    """Budget module providing dental treatment quotes management.

    Features:
    - Budget creation with items from treatment catalog
    - Versioning and duplication
    - Partial acceptance with digital signatures
    - PDF generation
    - Integration with odontogram treatments
    - Synchronization with treatment plans
    """

    @property
    def name(self) -> str:
        return "budget"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def dependencies(self) -> list[str]:
        return ["clinical", "catalog"]  # Requires patients and catalog

    def get_models(self) -> list:
        return [Budget, BudgetItem, BudgetSignature, BudgetHistory]

    def get_router(self) -> APIRouter:
        return router

    def get_permissions(self) -> list[str]:
        return [
            "read",  # View budgets
            "write",  # Create/update budgets
            "admin",  # Delete budgets, manage settings
        ]

    def get_event_handlers(self) -> dict[str, Any]:
        from .service import BudgetService

        return {
            EventType.ODONTOGRAM_TREATMENT_PERFORMED: BudgetService.on_treatment_performed,
            EventType.TREATMENT_PLAN_TREATMENT_ADDED: self._on_treatment_added_to_plan,
            EventType.TREATMENT_PLAN_TREATMENT_REMOVED: self._on_treatment_removed_from_plan,
            EventType.TREATMENT_PLAN_BUDGET_SYNC_REQUESTED: self._on_sync_requested,
        }

    async def _on_treatment_added_to_plan(self, data: dict[str, Any]) -> None:
        """Create BudgetItem when a treatment is added to a plan.

        Only creates item if the budget is in draft status.
        """
        from .service import BudgetItemService

        plan_id = data.get("plan_id")
        catalog_item_id = data.get("catalog_item_id")
        clinic_id = data.get("clinic_id")
        tooth_treatment_id = data.get("tooth_treatment_id")

        if not plan_id or not clinic_id:
            return

        async with async_session_maker() as db:
            try:
                # Import here to avoid circular imports
                from app.modules.treatment_plan.models import TreatmentPlan

                # Find budget linked to plan
                result = await db.execute(
                    select(TreatmentPlan.budget_id).where(
                        TreatmentPlan.id == UUID(plan_id),
                        TreatmentPlan.clinic_id == UUID(clinic_id),
                    )
                )
                budget_id = result.scalar_one_or_none()

                if not budget_id:
                    return  # No budget linked

                # Check budget status
                budget = await db.get(Budget, budget_id)
                if not budget or budget.status != "draft":
                    return  # Only modify draft budgets

                if not catalog_item_id:
                    return  # Need catalog item to create budget item

                # Create budget item
                await BudgetItemService.create_item(
                    db,
                    UUID(clinic_id),
                    budget_id,
                    {
                        "catalog_item_id": UUID(catalog_item_id),
                        "quantity": 1,
                        "tooth_treatment_id": UUID(tooth_treatment_id)
                        if tooth_treatment_id
                        else None,
                    },
                )

                # Recalculate budget totals
                from .service import BudgetService

                await BudgetService._recalculate_totals(db, budget)
                await db.commit()

                logger.info(f"Added budget item for plan {plan_id}")

            except Exception as e:
                logger.error(f"Error adding budget item from plan: {e}", exc_info=True)
                await db.rollback()

    async def _on_treatment_removed_from_plan(self, data: dict[str, Any]) -> None:
        """Remove BudgetItem when a treatment is removed from a plan.

        Only removes item if the budget is in draft status.
        """
        from .service import BudgetService

        plan_id = data.get("plan_id")
        tooth_treatment_id = data.get("tooth_treatment_id")
        clinic_id = data.get("clinic_id")

        if not plan_id or not clinic_id:
            return

        async with async_session_maker() as db:
            try:
                from app.modules.treatment_plan.models import TreatmentPlan

                # Find budget linked to plan
                result = await db.execute(
                    select(TreatmentPlan.budget_id).where(
                        TreatmentPlan.id == UUID(plan_id),
                        TreatmentPlan.clinic_id == UUID(clinic_id),
                    )
                )
                budget_id = result.scalar_one_or_none()

                if not budget_id:
                    return

                # Check budget status
                budget = await db.get(Budget, budget_id)
                if not budget or budget.status != "draft":
                    return

                if not tooth_treatment_id:
                    return

                # Find and remove budget item
                item_result = await db.execute(
                    select(BudgetItem).where(
                        BudgetItem.budget_id == budget_id,
                        BudgetItem.tooth_treatment_id == UUID(tooth_treatment_id),
                    )
                )
                item = item_result.scalar_one_or_none()

                if item:
                    await db.delete(item)
                    await BudgetService._recalculate_totals(db, budget)
                    await db.commit()
                    logger.info(f"Removed budget item for plan {plan_id}")

            except Exception as e:
                logger.error(f"Error removing budget item from plan: {e}", exc_info=True)
                await db.rollback()

    async def _on_sync_requested(self, data: dict[str, Any]) -> None:
        """Synchronize all plan items with the budget.

        Only syncs if the budget is in draft status.
        """
        from .service import BudgetItemService, BudgetService

        plan_id = data.get("plan_id")
        budget_id = data.get("budget_id")
        clinic_id = data.get("clinic_id")

        if not plan_id or not budget_id or not clinic_id:
            return

        async with async_session_maker() as db:
            try:
                # Check budget status
                budget = await db.get(Budget, UUID(budget_id))
                if not budget or budget.status != "draft":
                    logger.warning(f"Cannot sync non-draft budget {budget_id}")
                    return

                # Get plan items
                from app.modules.treatment_plan.models import PlannedTreatmentItem

                plan_items_result = await db.execute(
                    select(PlannedTreatmentItem).where(
                        PlannedTreatmentItem.treatment_plan_id == UUID(plan_id),
                        PlannedTreatmentItem.clinic_id == UUID(clinic_id),
                    )
                )
                plan_items = list(plan_items_result.scalars().all())

                # Get existing budget items with tooth_treatment_id
                existing_result = await db.execute(
                    select(BudgetItem).where(
                        BudgetItem.budget_id == UUID(budget_id),
                        BudgetItem.tooth_treatment_id.isnot(None),
                    )
                )
                existing_items = {
                    item.tooth_treatment_id: item
                    for item in existing_result.scalars().all()
                }

                # Sync items
                for plan_item in plan_items:
                    if plan_item.tooth_treatment_id and plan_item.catalog_item_id:
                        if plan_item.tooth_treatment_id not in existing_items:
                            # Add missing item
                            await BudgetItemService.create_item(
                                db,
                                UUID(clinic_id),
                                UUID(budget_id),
                                {
                                    "catalog_item_id": plan_item.catalog_item_id,
                                    "quantity": 1,
                                    "tooth_treatment_id": plan_item.tooth_treatment_id,
                                },
                            )

                # Recalculate totals
                await BudgetService._recalculate_totals(db, budget)
                await db.commit()

                logger.info(f"Synced plan {plan_id} with budget {budget_id}")

            except Exception as e:
                logger.error(f"Error syncing plan with budget: {e}", exc_info=True)
                await db.rollback()
