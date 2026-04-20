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

    manifest = {
        "name": "budget",
        "version": "0.1.0",
        "summary": "Dental treatment quotes, versioning, signatures.",
        "author": "DentalPin Core Team",
        "license": "BSL-1.1",
        "category": "official",
        "depends": ["clinical", "catalog"],
        "installable": True,
        "auto_install": True,
        "removable": False,
        "role_permissions": {
            "admin": ["*"],
            "dentist": ["*"],
            "hygienist": ["read"],
            "assistant": ["read", "write"],
            "receptionist": ["read", "write"],
        },
    }

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

        Only creates item if the budget is in draft status. Reads the Treatment
        to resolve catalog_item_id and primary tooth (when a single-tooth treatment).
        """
        from .service import BudgetItemService

        plan_id = data.get("plan_id")
        treatment_id = data.get("treatment_id")
        clinic_id = data.get("clinic_id")

        if not plan_id or not clinic_id or not treatment_id:
            return

        async with async_session_maker() as db:
            try:
                from app.modules.odontogram.models import Treatment
                from app.modules.treatment_plan.models import TreatmentPlan

                result = await db.execute(
                    select(TreatmentPlan.budget_id).where(
                        TreatmentPlan.id == UUID(plan_id),
                        TreatmentPlan.clinic_id == UUID(clinic_id),
                    )
                )
                budget_id = result.scalar_one_or_none()
                if not budget_id:
                    return

                budget = await db.get(Budget, budget_id)
                if not budget or budget.status != "draft":
                    return

                from sqlalchemy.orm import selectinload

                t_result = await db.execute(
                    select(Treatment)
                    .options(selectinload(Treatment.teeth))
                    .where(
                        Treatment.id == UUID(treatment_id),
                        Treatment.clinic_id == UUID(clinic_id),
                    )
                )
                treatment = t_result.scalar_one_or_none()
                if not treatment or treatment.catalog_item_id is None:
                    return

                primary_tooth = treatment.teeth[0].tooth_number if treatment.teeth else None
                primary_surfaces = treatment.teeth[0].surfaces if treatment.teeth else None

                await BudgetItemService.create_item(
                    db,
                    UUID(clinic_id),
                    budget_id,
                    {
                        "catalog_item_id": treatment.catalog_item_id,
                        "quantity": 1,
                        "treatment_id": treatment.id,
                        "tooth_number": primary_tooth,
                        "surfaces": primary_surfaces,
                        "unit_price": treatment.price_snapshot,
                    },
                )

                from .service import BudgetService

                await BudgetService._recalculate_totals(db, budget)
                await db.commit()

                logger.info("Added budget item for plan %s", plan_id)

            except Exception as e:
                logger.error("Error adding budget item from plan: %s", e, exc_info=True)
                await db.rollback()

    async def _on_treatment_removed_from_plan(self, data: dict[str, Any]) -> None:
        """Remove BudgetItem when a treatment is removed from a plan.

        Only removes item if the budget is in draft status.
        """
        from .service import BudgetService

        plan_id = data.get("plan_id")
        treatment_id = data.get("treatment_id")
        clinic_id = data.get("clinic_id")

        if not plan_id or not clinic_id or not treatment_id:
            return

        async with async_session_maker() as db:
            try:
                from app.modules.treatment_plan.models import TreatmentPlan

                result = await db.execute(
                    select(TreatmentPlan.budget_id).where(
                        TreatmentPlan.id == UUID(plan_id),
                        TreatmentPlan.clinic_id == UUID(clinic_id),
                    )
                )
                budget_id = result.scalar_one_or_none()
                if not budget_id:
                    return

                budget = await db.get(Budget, budget_id)
                if not budget or budget.status != "draft":
                    return

                item_result = await db.execute(
                    select(BudgetItem).where(
                        BudgetItem.budget_id == budget_id,
                        BudgetItem.treatment_id == UUID(treatment_id),
                    )
                )
                item = item_result.scalar_one_or_none()
                if item:
                    await db.delete(item)
                    await BudgetService._recalculate_totals(db, budget)
                    await db.commit()
                    logger.info("Removed budget item for plan %s", plan_id)

            except Exception as e:
                logger.error("Error removing budget item from plan: %s", e, exc_info=True)
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

                from sqlalchemy.orm import selectinload

                from app.modules.odontogram.models import Treatment
                from app.modules.treatment_plan.models import PlannedTreatmentItem

                plan_items_result = await db.execute(
                    select(PlannedTreatmentItem)
                    .options(
                        selectinload(PlannedTreatmentItem.treatment).selectinload(Treatment.teeth)
                    )
                    .where(
                        PlannedTreatmentItem.treatment_plan_id == UUID(plan_id),
                        PlannedTreatmentItem.clinic_id == UUID(clinic_id),
                    )
                )
                plan_items = list(plan_items_result.scalars().all())

                existing_result = await db.execute(
                    select(BudgetItem).where(
                        BudgetItem.budget_id == UUID(budget_id),
                        BudgetItem.treatment_id.isnot(None),
                    )
                )
                existing_items = {
                    item.treatment_id: item for item in existing_result.scalars().all()
                }

                for plan_item in plan_items:
                    treatment = plan_item.treatment
                    if not treatment or not treatment.catalog_item_id:
                        continue
                    if treatment.id in existing_items:
                        continue
                    primary_tooth = treatment.teeth[0].tooth_number if treatment.teeth else None
                    primary_surfaces = treatment.teeth[0].surfaces if treatment.teeth else None
                    await BudgetItemService.create_item(
                        db,
                        UUID(clinic_id),
                        UUID(budget_id),
                        {
                            "catalog_item_id": treatment.catalog_item_id,
                            "quantity": 1,
                            "treatment_id": treatment.id,
                            "tooth_number": primary_tooth,
                            "surfaces": primary_surfaces,
                            "unit_price": treatment.price_snapshot,
                        },
                    )

                await BudgetService._recalculate_totals(db, budget)
                await db.commit()

                logger.info("Synced plan %s with budget %s", plan_id, budget_id)

            except Exception as e:
                logger.error("Error syncing plan with budget: %s", e, exc_info=True)
                await db.rollback()
