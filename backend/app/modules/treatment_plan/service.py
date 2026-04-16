"""Treatment plan module service layer."""

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.events import event_bus
from app.modules.clinical.models import Patient

from .models import PlannedTreatmentItem, TreatmentMedia, TreatmentPlan

logger = logging.getLogger(__name__)


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
        count_result = await db.execute(
            select(func.count(TreatmentPlan.id)).where(*base_where)
        )
        total = count_result.scalar_one()

        # Query with relationships
        query = (
            select(TreatmentPlan)
            .where(*base_where)
            .options(
                selectinload(TreatmentPlan.patient),
                selectinload(TreatmentPlan.budget),
                selectinload(TreatmentPlan.items).selectinload(
                    PlannedTreatmentItem.catalog_item
                ),
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
                selectinload(TreatmentPlan.items).selectinload(
                    PlannedTreatmentItem.tooth_treatment
                ),
                selectinload(TreatmentPlan.items).selectinload(
                    PlannedTreatmentItem.catalog_item
                ),
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
        """Add a treatment item to the plan."""
        plan = await TreatmentPlanService.get(db, clinic_id, plan_id)
        if not plan:
            raise ValueError("Treatment plan not found")

        if plan.status not in ("draft", "active"):
            raise ValueError("Cannot add items to a completed/cancelled plan")

        tooth_treatment_id = data.get("tooth_treatment_id")
        catalog_item_id = data.get("catalog_item_id")
        is_global = data.get("is_global", False)

        # Determine sequence order
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
            tooth_treatment_id=tooth_treatment_id,
            catalog_item_id=catalog_item_id,
            is_global=is_global,
            sequence_order=sequence_order,
            notes=data.get("notes"),
        )
        db.add(item)
        await db.flush()

        # Eagerly load relationships for response serialization
        await db.refresh(item, attribute_names=["tooth_treatment", "catalog_item", "media"])

        # Publish event for other modules
        event_bus.publish(
            "treatment_plan.treatment_added",
            {
                "plan_id": str(plan_id),
                "item_id": str(item.id),
                "tooth_treatment_id": str(tooth_treatment_id) if tooth_treatment_id else None,
                "catalog_item_id": str(catalog_item_id) if catalog_item_id else None,
                "is_global": is_global,
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
        """Update a planned treatment item."""
        result = await db.execute(
            select(PlannedTreatmentItem)
            .where(
                PlannedTreatmentItem.id == item_id,
                PlannedTreatmentItem.treatment_plan_id == plan_id,
                PlannedTreatmentItem.clinic_id == clinic_id,
            )
            .options(
                selectinload(PlannedTreatmentItem.tooth_treatment),
                selectinload(PlannedTreatmentItem.catalog_item),
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

        tooth_treatment_id = item.tooth_treatment_id

        await db.delete(item)

        # Publish event
        event_bus.publish(
            "treatment_plan.treatment_removed",
            {
                "plan_id": str(plan_id),
                "item_id": str(item_id),
                "tooth_treatment_id": str(tooth_treatment_id) if tooth_treatment_id else None,
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
        """Mark an item as completed."""
        result = await db.execute(
            select(PlannedTreatmentItem)
            .where(
                PlannedTreatmentItem.id == item_id,
                PlannedTreatmentItem.treatment_plan_id == plan_id,
                PlannedTreatmentItem.clinic_id == clinic_id,
            )
            .options(
                selectinload(PlannedTreatmentItem.tooth_treatment),
                selectinload(PlannedTreatmentItem.catalog_item),
                selectinload(PlannedTreatmentItem.media),
            )
        )
        item = result.scalar_one_or_none()
        if not item:
            return None

        if item.status == "completed":
            return item  # Already completed

        item.status = "completed"
        item.completed_at = datetime.now(UTC)
        item.completed_by = user_id
        item.completed_without_appointment = completed_without_appointment
        if notes:
            item.notes = notes

        # Publish event for odontogram to update ToothTreatment status
        event_bus.publish(
            "treatment_plan.treatment_completed",
            {
                "plan_id": str(plan_id),
                "item_id": str(item_id),
                "tooth_treatment_id": str(item.tooth_treatment_id)
                if item.tooth_treatment_id
                else None,
                "clinic_id": str(clinic_id),
                "completed_by": str(user_id),
            },
        )

        return item

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
