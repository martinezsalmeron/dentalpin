"""Budget module - dental treatment quotes management."""

import logging
from decimal import Decimal
from typing import Any
from uuid import UUID

from fastapi import APIRouter
from sqlalchemy import select

from app.core.events.types import EventType
from app.core.plugins import BaseModule
from app.database import async_session_maker

from .models import Budget, BudgetAccessLog, BudgetHistory, BudgetItem, BudgetSignature
from .public_router import public_router
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
        "depends": ["patients", "catalog", "odontogram"],
        "installable": True,
        "auto_install": True,
        "removable": False,
        "role_permissions": {
            "admin": ["*"],
            "dentist": ["*"],
            "hygienist": ["read"],
            "assistant": ["read", "write", "accept_in_clinic"],
            "receptionist": [
                "read",
                "write",
                "renegotiate",
                "accept_in_clinic",
            ],
        },
        "frontend": {
            "layer_path": "frontend",
            "navigation": [
                {
                    "label": "nav.budgets",
                    "icon": "i-lucide-file-text",
                    "to": "/budgets",
                    "permission": "budget.read",
                    "order": 40,
                },
            ],
        },
    }

    def get_models(self) -> list:
        return [Budget, BudgetItem, BudgetSignature, BudgetHistory, BudgetAccessLog]

    def get_router(self) -> APIRouter:
        # Compose authenticated + public sub-routers under one mount.
        # Public endpoints sit under ``/public/budgets/...`` and are
        # not gated by the clinic context dependency (see ADR 0006).
        combined = APIRouter()
        combined.include_router(router)
        combined.include_router(public_router)
        return combined

    def get_permissions(self) -> list[str]:
        return [
            "read",  # View budgets
            "write",  # Create/update budgets
            "admin",  # Delete budgets, manage settings
            # Workflow extensions split out for fine-grained RBAC.
            "renegotiate",  # Cancel a sent budget to renegotiate
            "accept_in_clinic",  # Capture in-clinic acceptance
        ]

    def get_event_handlers(self) -> dict[str, Any]:
        from .service import BudgetService

        return {
            EventType.ODONTOGRAM_TREATMENT_PERFORMED: BudgetService.on_treatment_performed,
            EventType.TREATMENT_PLAN_TREATMENT_ADDED: self._on_treatment_added_to_plan,
            EventType.TREATMENT_PLAN_TREATMENT_REMOVED: self._on_treatment_removed_from_plan,
            EventType.TREATMENT_PLAN_BUDGET_SYNC_REQUESTED: self._on_sync_requested,
        }

    def get_tools(self) -> list:
        return []

    async def _on_treatment_added_to_plan(self, data: dict[str, Any]) -> None:
        """Create BudgetItem when a treatment is added to a plan.

        Snapshot-only: the publisher (treatment_plan) sends a denormalized
        payload with ``budget_id``, ``catalog_item_id``, ``tooth_number``,
        ``surfaces`` and ``unit_price`` so this handler does not import
        models from modules outside ``budget``'s ``manifest.depends``.
        See ADR 0003.
        """
        from .service import BudgetItemService, BudgetService

        plan_id = data.get("plan_id")
        treatment_id_raw = data.get("treatment_id")
        clinic_id = data.get("clinic_id")
        budget_id_raw = data.get("budget_id")
        catalog_item_id_raw = data.get("catalog_item_id")
        tooth_number = data.get("tooth_number")
        surfaces = data.get("surfaces")
        unit_price_raw = data.get("unit_price")

        if not plan_id or not clinic_id or not treatment_id_raw:
            return
        if not budget_id_raw or not catalog_item_id_raw:
            # Plan has no budget yet, or treatment without catalog ref —
            # nothing to mirror.
            return

        async with async_session_maker() as db:
            try:
                budget = await db.get(Budget, UUID(budget_id_raw))
                if not budget or budget.status != "draft":
                    return

                await BudgetItemService.create_item(
                    db,
                    UUID(clinic_id),
                    UUID(budget_id_raw),
                    {
                        "catalog_item_id": UUID(catalog_item_id_raw),
                        "quantity": 1,
                        "treatment_id": UUID(treatment_id_raw),
                        "tooth_number": tooth_number,
                        "surfaces": surfaces,
                        "unit_price": (
                            Decimal(unit_price_raw) if unit_price_raw is not None else None
                        ),
                    },
                )

                await BudgetService._recalculate_totals(db, budget)
                await db.commit()

                logger.info("Added budget item for plan %s", plan_id)

            except Exception as e:
                logger.error("Error adding budget item from plan: %s", e, exc_info=True)
                await db.rollback()

    async def _on_treatment_removed_from_plan(self, data: dict[str, Any]) -> None:
        """Remove BudgetItem when a treatment is removed from a plan.

        Snapshot-only: the publisher includes ``budget_id`` so this
        handler does not need to read ``TreatmentPlan`` from another
        module (ADR 0003).
        """
        from .service import BudgetService

        plan_id = data.get("plan_id")
        treatment_id_raw = data.get("treatment_id")
        clinic_id = data.get("clinic_id")
        budget_id_raw = data.get("budget_id")

        if not plan_id or not clinic_id or not treatment_id_raw or not budget_id_raw:
            return

        async with async_session_maker() as db:
            try:
                budget = await db.get(Budget, UUID(budget_id_raw))
                if not budget or budget.status != "draft":
                    return

                item_result = await db.execute(
                    select(BudgetItem).where(
                        BudgetItem.budget_id == UUID(budget_id_raw),
                        BudgetItem.treatment_id == UUID(treatment_id_raw),
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

        Snapshot-only: the publisher includes ``items`` (a list of
        denormalized item snapshots). This handler reconciles the
        budget without reading treatment_plan / odontogram models
        (ADR 0003).
        """
        from .service import BudgetItemService, BudgetService

        plan_id = data.get("plan_id")
        budget_id_raw = data.get("budget_id")
        clinic_id = data.get("clinic_id")
        items_payload = data.get("items") or []

        if not plan_id or not budget_id_raw or not clinic_id:
            return

        async with async_session_maker() as db:
            try:
                budget = await db.get(Budget, UUID(budget_id_raw))
                if not budget or budget.status != "draft":
                    logger.warning("Cannot sync non-draft budget %s", budget_id_raw)
                    return

                existing_result = await db.execute(
                    select(BudgetItem).where(
                        BudgetItem.budget_id == UUID(budget_id_raw),
                        BudgetItem.treatment_id.isnot(None),
                    )
                )
                existing_treatment_ids = {
                    item.treatment_id for item in existing_result.scalars().all()
                }

                for snap in items_payload:
                    treatment_id_raw = snap.get("treatment_id")
                    catalog_item_id_raw = snap.get("catalog_item_id")
                    if not treatment_id_raw or not catalog_item_id_raw:
                        continue
                    treatment_uuid = UUID(treatment_id_raw)
                    if treatment_uuid in existing_treatment_ids:
                        continue
                    unit_price_raw = snap.get("unit_price")
                    await BudgetItemService.create_item(
                        db,
                        UUID(clinic_id),
                        UUID(budget_id_raw),
                        {
                            "catalog_item_id": UUID(catalog_item_id_raw),
                            "quantity": 1,
                            "treatment_id": treatment_uuid,
                            "tooth_number": snap.get("tooth_number"),
                            "surfaces": snap.get("surfaces"),
                            "unit_price": (
                                Decimal(unit_price_raw) if unit_price_raw is not None else None
                            ),
                        },
                    )

                await BudgetService._recalculate_totals(db, budget)
                await db.commit()

                logger.info("Synced plan %s with budget %s", plan_id, budget_id_raw)

            except Exception as e:
                logger.error("Error syncing plan with budget: %s", e, exc_info=True)
                await db.rollback()
