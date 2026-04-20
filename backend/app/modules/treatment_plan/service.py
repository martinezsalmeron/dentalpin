"""Treatment plan module service layer."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.events import event_bus
from app.modules.odontogram.models import Treatment
from app.modules.patients.models import Patient

from .models import PlannedTreatmentItem, TreatmentMedia, TreatmentPlan

logger = logging.getLogger(__name__)


def _treatment_loader() -> selectinload:
    """Eager-load the Treatment (with teeth + catalog_item)."""
    return selectinload(PlannedTreatmentItem.treatment).selectinload(Treatment.teeth)


class PlanLockedError(ValueError):
    """Raised when a mutation is attempted on a plan locked by an active budget."""


def _is_plan_locked(plan: TreatmentPlan) -> bool:
    """A plan is locked once it has a non-cancelled budget attached.

    Rationale: generating/sending/accepting a budget turns the plan into a
    contract with the patient. Any structural change would silently invalidate
    that contract, so mutations must go through the explicit unlock flow
    (which cancels the budget).
    """
    if not plan.budget_id or plan.budget is None:
        return False
    return plan.budget.status != "cancelled"


class TreatmentPlanService:
    """Service for treatment plan operations."""

    # -------------------------------------------------------------------------
    # Plan Number Generation
    # -------------------------------------------------------------------------

    @staticmethod
    async def generate_plan_number(db: AsyncSession, clinic_id: UUID) -> str:
        """Generate a unique plan number for the clinic."""
        year = datetime.now(UTC).year

        # Count existing plans for this year
        result = await db.execute(
            select(func.count(TreatmentPlan.id)).where(
                TreatmentPlan.clinic_id == clinic_id,
                TreatmentPlan.plan_number.like(f"PLAN-{year}-%"),
            )
        )
        count = result.scalar_one()

        return f"PLAN-{year}-{count + 1:04d}"

    # -------------------------------------------------------------------------
    # CRUD Operations
    # -------------------------------------------------------------------------

    @staticmethod
    async def list(
        db: AsyncSession,
        clinic_id: UUID,
        page: int = 1,
        page_size: int = 20,
        patient_id: UUID | None = None,
        status: str | list[str] | None = None,
    ) -> tuple[list[TreatmentPlan], int]:
        """List treatment plans with pagination and filters."""
        page_size = min(max(page_size, 1), 100)
        page = max(page, 1)
        offset = (page - 1) * page_size

        # Base query - exclude deleted
        base_where = [
            TreatmentPlan.clinic_id == clinic_id,
            TreatmentPlan.deleted_at.is_(None),
        ]

        if patient_id:
            base_where.append(TreatmentPlan.patient_id == patient_id)

        if status:
            statuses = [status] if isinstance(status, str) else list(status)
            if len(statuses) == 1:
                base_where.append(TreatmentPlan.status == statuses[0])
            else:
                base_where.append(TreatmentPlan.status.in_(statuses))

        # Count
        count_result = await db.execute(select(func.count(TreatmentPlan.id)).where(*base_where))
        total = count_result.scalar_one()

        # Query with relationships
        query = (
            select(TreatmentPlan)
            .where(*base_where)
            .options(
                selectinload(TreatmentPlan.patient),
                selectinload(TreatmentPlan.budget),
                selectinload(TreatmentPlan.items)
                .selectinload(PlannedTreatmentItem.treatment)
                .selectinload(Treatment.teeth),
                selectinload(TreatmentPlan.items)
                .selectinload(PlannedTreatmentItem.treatment)
                .selectinload(Treatment.catalog_item),
            )
            .order_by(TreatmentPlan.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await db.execute(query)
        items = list(result.scalars().all())

        return items, total

    @staticmethod
    async def get(
        db: AsyncSession,
        clinic_id: UUID,
        plan_id: UUID,
    ) -> TreatmentPlan | None:
        """Get a single treatment plan with all relationships."""
        result = await db.execute(
            select(TreatmentPlan)
            .where(
                TreatmentPlan.id == plan_id,
                TreatmentPlan.clinic_id == clinic_id,
                TreatmentPlan.deleted_at.is_(None),
            )
            .options(
                selectinload(TreatmentPlan.patient),
                selectinload(TreatmentPlan.budget),
                selectinload(TreatmentPlan.items)
                .selectinload(PlannedTreatmentItem.treatment)
                .selectinload(Treatment.teeth),
                selectinload(TreatmentPlan.items)
                .selectinload(PlannedTreatmentItem.treatment)
                .selectinload(Treatment.catalog_item),
                selectinload(TreatmentPlan.items).selectinload(PlannedTreatmentItem.media),
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create(
        db: AsyncSession,
        clinic_id: UUID,
        user_id: UUID,
        data: dict,
    ) -> TreatmentPlan:
        """Create a new treatment plan."""
        # Validate patient exists in clinic
        patient_id = data.get("patient_id")
        patient = await db.get(Patient, patient_id)
        if not patient or patient.clinic_id != clinic_id:
            raise ValueError("Invalid patient")

        plan_number = await TreatmentPlanService.generate_plan_number(db, clinic_id)

        plan = TreatmentPlan(
            clinic_id=clinic_id,
            patient_id=patient_id,
            plan_number=plan_number,
            title=data.get("title"),
            assigned_professional_id=data.get("assigned_professional_id"),
            diagnosis_notes=data.get("diagnosis_notes"),
            internal_notes=data.get("internal_notes"),
            created_by=user_id,
        )
        db.add(plan)
        await db.flush()

        # Load patient relationship for response serialization
        await db.refresh(plan, ["patient"])

        # Publish event
        event_bus.publish(
            "treatment_plan.created",
            {
                "plan_id": str(plan.id),
                "patient_id": str(plan.patient_id),
                "clinic_id": str(clinic_id),
                "created_by": str(user_id),
            },
        )

        return plan

    @staticmethod
    async def update(
        db: AsyncSession,
        clinic_id: UUID,
        plan_id: UUID,
        data: dict,
    ) -> TreatmentPlan | None:
        """Update a treatment plan."""
        plan = await TreatmentPlanService.get(db, clinic_id, plan_id)
        if not plan:
            return None

        for key, value in data.items():
            if value is not None and hasattr(plan, key):
                setattr(plan, key, value)

        return plan

    @staticmethod
    async def update_status(
        db: AsyncSession,
        clinic_id: UUID,
        plan_id: UUID,
        new_status: str,
        user_id: UUID,
    ) -> TreatmentPlan | None:
        """Update treatment plan status with validation."""
        plan = await TreatmentPlanService.get(db, clinic_id, plan_id)
        if not plan:
            return None

        old_status = plan.status
        if old_status == new_status:
            return plan

        # Validate status transitions
        valid_transitions = {
            "draft": ["active", "cancelled"],
            "active": ["completed", "cancelled"],
            "completed": ["archived"],
            "cancelled": ["draft"],  # Can reopen
            "archived": [],  # Terminal state
        }

        if new_status not in valid_transitions.get(old_status, []):
            raise ValueError(f"Invalid status transition from {old_status} to {new_status}")

        # Cannot activate plan without items
        if new_status == "active" and not plan.items:
            raise ValueError("Cannot activate plan without treatments")

        plan.status = new_status

        # Terminal transitions drop the plan's hold on its planned Treatments — clean
        # up any that become orphaned so the odontogram reflects reality.
        if new_status in ("cancelled", "archived"):
            await TreatmentPlanService._cleanup_orphan_planned_treatments(
                db, clinic_id, plan, user_id
            )

        # Publish event
        event_bus.publish(
            "treatment_plan.status_changed",
            {
                "plan_id": str(plan.id),
                "old_status": old_status,
                "new_status": new_status,
                "clinic_id": str(clinic_id),
            },
        )

        return plan

    @staticmethod
    async def delete(
        db: AsyncSession,
        clinic_id: UUID,
        plan_id: UUID,
        user_id: UUID,
    ) -> bool:
        """Soft delete (archive) a treatment plan.

        Also runs orphan cleanup: planned Treatments that only lived inside this
        plan are soft-deleted so they disappear from the odontogram. `performed`
        Treatments are always preserved as clinical history.
        """
        plan = await TreatmentPlanService.get(db, clinic_id, plan_id)
        if not plan:
            return False

        await TreatmentPlanService._cleanup_orphan_planned_treatments(db, clinic_id, plan, user_id)
        plan.deleted_at = datetime.now(UTC)
        return True

    @staticmethod
    async def _cleanup_orphan_planned_treatments(
        db: AsyncSession,
        clinic_id: UUID,
        plan: TreatmentPlan,
        user_id: UUID,
    ) -> None:
        """Soft-delete Treatments that become orphaned when `plan` goes terminal.

        For every Treatment referenced by this plan's items, check whether any
        *other* non-terminal plan still references it. If not, and the Treatment
        is still `planned` (never performed), soft-delete it so the odontogram
        stops showing it. Performed Treatments are left alone (clinical history).
        """
        from app.modules.odontogram.service import TreatmentService

        treatment_ids = {item.treatment_id for item in plan.items if item.treatment_id}
        if not treatment_ids:
            return

        for treatment_id in treatment_ids:
            # Count references from OTHER plans that are still "live" (non-terminal,
            # non-deleted). We exclude this plan explicitly — its items stay in DB
            # as history but no longer count as a live reference.
            result = await db.execute(
                select(func.count(PlannedTreatmentItem.id))
                .join(
                    TreatmentPlan,
                    TreatmentPlan.id == PlannedTreatmentItem.treatment_plan_id,
                )
                .where(
                    PlannedTreatmentItem.treatment_id == treatment_id,
                    PlannedTreatmentItem.clinic_id == clinic_id,
                    PlannedTreatmentItem.treatment_plan_id != plan.id,
                    TreatmentPlan.deleted_at.is_(None),
                    TreatmentPlan.status.notin_(("archived", "cancelled")),
                )
            )
            if (result.scalar_one() or 0) > 0:
                continue

            treatment = await db.get(Treatment, treatment_id)
            if treatment and treatment.deleted_at is None and treatment.status == "planned":
                await TreatmentService.delete(db, clinic_id, treatment_id, user_id)

    # -------------------------------------------------------------------------
    # Item Operations
    # -------------------------------------------------------------------------

    @staticmethod
    async def add_item(
        db: AsyncSession,
        clinic_id: UUID,
        plan_id: UUID,
        data: dict,
    ) -> PlannedTreatmentItem:
        """Add a Treatment to the plan as a new item."""
        plan = await TreatmentPlanService.get(db, clinic_id, plan_id)
        if not plan:
            raise ValueError("Treatment plan not found")

        if plan.status not in ("draft", "active"):
            raise ValueError("Cannot add items to a completed/cancelled plan")

        if _is_plan_locked(plan):
            raise PlanLockedError("Plan is locked by an active budget")

        treatment_id = data.get("treatment_id")
        if treatment_id is None:
            raise ValueError("treatment_id is required")

        # Validate the Treatment exists for this clinic/patient.
        treatment = await db.get(Treatment, treatment_id)
        if (
            not treatment
            or treatment.clinic_id != clinic_id
            or treatment.patient_id != plan.patient_id
            or treatment.deleted_at is not None
        ):
            raise ValueError("Invalid treatment for this plan")

        sequence_order = data.get("sequence_order")
        if sequence_order is None:
            result = await db.execute(
                select(func.max(PlannedTreatmentItem.sequence_order)).where(
                    PlannedTreatmentItem.treatment_plan_id == plan_id
                )
            )
            max_order = result.scalar_one() or 0
            sequence_order = max_order + 1

        item = PlannedTreatmentItem(
            clinic_id=clinic_id,
            treatment_plan_id=plan_id,
            treatment_id=treatment_id,
            sequence_order=sequence_order,
            notes=data.get("notes"),
        )
        db.add(item)
        await db.flush()

        # Re-fetch with eager-loaded treatment.teeth / .catalog_item for the response.
        reloaded = await db.execute(
            select(PlannedTreatmentItem)
            .options(
                selectinload(PlannedTreatmentItem.treatment).selectinload(Treatment.teeth),
                selectinload(PlannedTreatmentItem.treatment).selectinload(Treatment.catalog_item),
                selectinload(PlannedTreatmentItem.media),
            )
            .where(PlannedTreatmentItem.id == item.id)
        )
        item = reloaded.scalar_one()

        event_bus.publish(
            "treatment_plan.treatment_added",
            {
                "plan_id": str(plan_id),
                "item_id": str(item.id),
                "treatment_id": str(treatment_id),
                "clinic_id": str(clinic_id),
                "patient_id": str(plan.patient_id),
            },
        )

        return item

    @staticmethod
    async def update_item(
        db: AsyncSession,
        clinic_id: UUID,
        plan_id: UUID,
        item_id: UUID,
        data: dict,
    ) -> PlannedTreatmentItem | None:
        """Update scheduling metadata on a planned treatment item."""
        plan = await TreatmentPlanService.get(db, clinic_id, plan_id)
        if not plan:
            return None
        if _is_plan_locked(plan):
            raise PlanLockedError("Plan is locked by an active budget")

        result = await db.execute(
            select(PlannedTreatmentItem)
            .where(
                PlannedTreatmentItem.id == item_id,
                PlannedTreatmentItem.treatment_plan_id == plan_id,
                PlannedTreatmentItem.clinic_id == clinic_id,
            )
            .options(
                _treatment_loader(),
                selectinload(PlannedTreatmentItem.media),
            )
        )
        item = result.scalar_one_or_none()
        if not item:
            return None

        for key, value in data.items():
            if value is not None and hasattr(item, key):
                setattr(item, key, value)

        return item

    @staticmethod
    async def reorder_items(
        db: AsyncSession,
        clinic_id: UUID,
        plan_id: UUID,
        item_ids: list[UUID],
    ) -> list[PlannedTreatmentItem] | None:
        """Set `sequence_order` of items to match the position in `item_ids`.

        Validates that `item_ids` covers exactly the plan's items (no missing, no
        extras). Returns the reordered items or None if the plan does not exist.
        Raises ValueError on validation failure.
        """
        # Load plan to confirm ownership (with budget for lock check).
        plan_q = await db.execute(
            select(TreatmentPlan)
            .where(
                TreatmentPlan.id == plan_id,
                TreatmentPlan.clinic_id == clinic_id,
                TreatmentPlan.deleted_at.is_(None),
            )
            .options(selectinload(TreatmentPlan.budget))
        )
        plan = plan_q.scalar_one_or_none()
        if not plan:
            return None
        if _is_plan_locked(plan):
            raise PlanLockedError("Plan is locked by an active budget")

        # Load current items.
        items_q = await db.execute(
            select(PlannedTreatmentItem).where(
                PlannedTreatmentItem.treatment_plan_id == plan_id,
                PlannedTreatmentItem.clinic_id == clinic_id,
            )
        )
        current = {i.id: i for i in items_q.scalars().all()}

        # Validate set equality — no missing or extra IDs.
        requested = list(item_ids)
        if len(requested) != len(set(requested)):
            raise ValueError("Duplicate item ids not allowed")
        if set(requested) != set(current.keys()):
            raise ValueError("item_ids must cover exactly the plan's current items")

        # Apply new order.
        for index, item_id in enumerate(requested):
            current[item_id].sequence_order = index

        await db.flush()

        event_bus.publish(
            "treatment_plan.items_reordered",
            {
                "clinic_id": str(clinic_id),
                "plan_id": str(plan_id),
                "item_ids": [str(i) for i in requested],
            },
        )

        return [current[i] for i in requested]

    @staticmethod
    async def remove_item(
        db: AsyncSession,
        clinic_id: UUID,
        plan_id: UUID,
        item_id: UUID,
        user_id: UUID,
    ) -> bool:
        """Remove an item from the plan.

        Orphan rule: if the removed item was the last active PlannedTreatmentItem
        referencing its Treatment and that Treatment is still `planned`, soft-delete
        the Treatment so the odontogram reflects the removal. `performed` Treatments
        are kept (clinical history).
        """
        plan = await TreatmentPlanService.get(db, clinic_id, plan_id)
        if not plan:
            return False
        if _is_plan_locked(plan):
            raise PlanLockedError("Plan is locked by an active budget")

        result = await db.execute(
            select(PlannedTreatmentItem).where(
                PlannedTreatmentItem.id == item_id,
                PlannedTreatmentItem.treatment_plan_id == plan_id,
                PlannedTreatmentItem.clinic_id == clinic_id,
            )
        )
        item = result.scalar_one_or_none()
        if not item:
            return False

        treatment_id = item.treatment_id
        await db.delete(item)
        await db.flush()

        # Orphan check — any other active item still referencing the Treatment?
        other_refs = await db.execute(
            select(func.count(PlannedTreatmentItem.id)).where(
                PlannedTreatmentItem.treatment_id == treatment_id,
                PlannedTreatmentItem.clinic_id == clinic_id,
            )
        )
        remaining = other_refs.scalar_one() or 0
        if remaining == 0:
            treatment = await db.get(Treatment, treatment_id)
            if treatment and treatment.deleted_at is None and treatment.status == "planned":
                from app.modules.odontogram.service import TreatmentService

                await TreatmentService.delete(db, clinic_id, treatment_id, user_id)

        event_bus.publish(
            "treatment_plan.treatment_removed",
            {
                "plan_id": str(plan_id),
                "item_id": str(item_id),
                "treatment_id": str(treatment_id),
                "clinic_id": str(clinic_id),
            },
        )

        return True

    @staticmethod
    async def complete_item(
        db: AsyncSession,
        clinic_id: UUID,
        plan_id: UUID,
        item_id: UUID,
        user_id: UUID,
        completed_without_appointment: bool = True,
        notes: str | None = None,
    ) -> PlannedTreatmentItem | None:
        """Mark a plan item as completed and perform the underlying Treatment."""
        result = await db.execute(
            select(PlannedTreatmentItem)
            .where(
                PlannedTreatmentItem.id == item_id,
                PlannedTreatmentItem.treatment_plan_id == plan_id,
                PlannedTreatmentItem.clinic_id == clinic_id,
            )
            .options(
                _treatment_loader(),
                selectinload(PlannedTreatmentItem.media),
            )
        )
        item = result.scalar_one_or_none()
        if not item:
            return None

        if item.status == "completed":
            return item

        item.status = "completed"
        item.completed_at = datetime.now(UTC)
        item.completed_by = user_id
        item.completed_without_appointment = completed_without_appointment
        if notes:
            item.notes = notes

        # Propagate to the Treatment so the odontogram reflects performed state.
        from app.modules.odontogram.service import TreatmentService

        await TreatmentService.perform(
            db=db,
            clinic_id=clinic_id,
            treatment_id=item.treatment_id,
            user_id=user_id,
            notes=notes,
        )

        event_bus.publish(
            "treatment_plan.treatment_completed",
            {
                "plan_id": str(plan_id),
                "item_id": str(item_id),
                "treatment_id": str(item.treatment_id),
                "clinic_id": str(clinic_id),
                "completed_by": str(user_id),
            },
        )

        await TreatmentPlanService._check_and_complete_plan(db, clinic_id, plan_id)
        return item

    @staticmethod
    async def _check_and_complete_plan(
        db: AsyncSession,
        clinic_id: UUID,
        plan_id: UUID,
    ) -> None:
        """Check if all items completed and auto-complete the plan if so."""
        plan = await TreatmentPlanService.get(db, clinic_id, plan_id)
        if not plan or plan.status != "active":
            return

        # Check if any non-completed items remain
        has_pending = any(item.status != "completed" for item in plan.items)
        if has_pending:
            return

        # All items completed - auto-complete the plan
        old_status = plan.status
        plan.status = "completed"

        event_bus.publish(
            "treatment_plan.status_changed",
            {
                "plan_id": str(plan.id),
                "old_status": old_status,
                "new_status": "completed",
                "clinic_id": str(clinic_id),
            },
        )

        logger.info(
            "Auto-completed treatment plan %s (all items completed)",
            plan.id,
        )

    # -------------------------------------------------------------------------
    # Budget Integration
    # -------------------------------------------------------------------------

    @staticmethod
    async def link_budget(
        db: AsyncSession,
        clinic_id: UUID,
        plan_id: UUID,
        budget_id: UUID,
    ) -> TreatmentPlan | None:
        """Link an existing budget to the plan."""
        from app.modules.budget.models import Budget

        plan = await TreatmentPlanService.get(db, clinic_id, plan_id)
        if not plan:
            return None

        # Verify budget exists and belongs to same clinic/patient
        budget = await db.get(Budget, budget_id)
        if not budget or budget.clinic_id != clinic_id:
            raise ValueError("Invalid budget")

        if budget.patient_id != plan.patient_id:
            raise ValueError("Budget belongs to different patient")

        plan.budget_id = budget_id

        return plan

    @staticmethod
    async def unlock(
        db: AsyncSession,
        clinic_id: UUID,
        plan_id: UUID,
        user_id: UUID,
    ) -> TreatmentPlan | None:
        """Unlock a plan by cancelling its linked budget.

        Used when the clinician needs to modify a plan that already has a
        budget issued to the patient. The budget transitions to `cancelled`
        (preserving history for traceability) and the plan becomes mutable
        again. A new budget can be generated afterwards.
        """
        from app.modules.budget.models import Budget
        from app.modules.budget.workflow import BudgetWorkflowError, BudgetWorkflowService

        plan = await TreatmentPlanService.get(db, clinic_id, plan_id)
        if not plan:
            return None

        if not plan.budget_id:
            raise ValueError("Plan has no budget to unlock")

        budget = await db.get(Budget, plan.budget_id)
        if not budget or budget.clinic_id != clinic_id:
            raise ValueError("Linked budget not found")

        if budget.status == "cancelled":
            return plan

        try:
            await BudgetWorkflowService.cancel_budget(
                db, budget, user_id, reason="Plan unlocked for modification"
            )
        except BudgetWorkflowError as e:
            raise ValueError(str(e)) from e

        event_bus.publish(
            "treatment_plan.unlocked",
            {
                "plan_id": str(plan_id),
                "budget_id": str(budget.id),
                "clinic_id": str(clinic_id),
                "user_id": str(user_id),
            },
        )

        return plan

    @staticmethod
    async def request_budget_sync(
        db: AsyncSession,
        clinic_id: UUID,
        plan_id: UUID,
    ) -> bool:
        """Request budget module to sync items."""
        plan = await TreatmentPlanService.get(db, clinic_id, plan_id)
        if not plan or not plan.budget_id:
            return False

        event_bus.publish(
            "treatment_plan.budget_sync_requested",
            {
                "plan_id": str(plan_id),
                "budget_id": str(plan.budget_id),
                "clinic_id": str(clinic_id),
            },
        )

        return True

    # -------------------------------------------------------------------------
    # Media Operations
    # -------------------------------------------------------------------------

    @staticmethod
    async def add_media(
        db: AsyncSession,
        clinic_id: UUID,
        item_id: UUID,
        data: dict,
    ) -> TreatmentMedia:
        """Add media to a treatment item."""
        # Verify item exists
        result = await db.execute(
            select(PlannedTreatmentItem).where(
                PlannedTreatmentItem.id == item_id,
                PlannedTreatmentItem.clinic_id == clinic_id,
            )
        )
        item = result.scalar_one_or_none()
        if not item:
            raise ValueError("Treatment item not found")

        media = TreatmentMedia(
            clinic_id=clinic_id,
            planned_treatment_item_id=item_id,
            document_id=data["document_id"],
            media_type=data["media_type"],
            display_order=data.get("display_order", 0),
            notes=data.get("notes"),
        )
        db.add(media)
        await db.flush()

        return media

    @staticmethod
    async def remove_media(
        db: AsyncSession,
        clinic_id: UUID,
        item_id: UUID,
        media_id: UUID,
    ) -> bool:
        """Remove media from a treatment item."""
        result = await db.execute(
            select(TreatmentMedia).where(
                TreatmentMedia.id == media_id,
                TreatmentMedia.planned_treatment_item_id == item_id,
                TreatmentMedia.clinic_id == clinic_id,
            )
        )
        media = result.scalar_one_or_none()
        if not media:
            return False

        await db.delete(media)
        return True
