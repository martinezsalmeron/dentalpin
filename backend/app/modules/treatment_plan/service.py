"""Treatment plan module service layer."""

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.events import event_bus
from app.modules.clinical.models import Patient
from app.modules.odontogram.models import Treatment

from .models import PlannedTreatmentItem, TreatmentMedia, TreatmentPlan

logger = logging.getLogger(__name__)


def _treatment_loader() -> selectinload:
    """Eager-load the Treatment (with teeth + catalog_item)."""
    return selectinload(PlannedTreatmentItem.treatment).selectinload(Treatment.teeth)


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
        status: str | None = None,
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
            base_where.append(TreatmentPlan.status == status)

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
    ) -> bool:
        """Soft delete (archive) a treatment plan."""
        plan = await TreatmentPlanService.get(db, clinic_id, plan_id)
        if not plan:
            return False

        plan.deleted_at = datetime.now(UTC)
        return True

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
    async def remove_item(
        db: AsyncSession,
        clinic_id: UUID,
        plan_id: UUID,
        item_id: UUID,
    ) -> bool:
        """Remove an item from the plan."""
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
