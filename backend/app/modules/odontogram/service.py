"""Business logic service for odontogram module."""

from datetime import UTC, date, datetime
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.events import event_bus
from app.core.events.types import EventType

from .constants import ToothCondition, TreatmentStatus, get_tooth_type, get_treatment_category
from .models import OdontogramHistory, ToothRecord, ToothTreatment


class OdontogramEventType:
    """Event types for odontogram module."""

    SURFACE_UPDATED = "odontogram.surface.updated"
    TOOTH_UPDATED = "odontogram.tooth.updated"
    CONDITION_CHANGED = "odontogram.condition.changed"


class OdontogramService:
    """Service for odontogram operations."""

    @staticmethod
    def _default_surfaces() -> dict[str, str]:
        """Return default healthy surfaces."""
        return {
            "M": ToothCondition.HEALTHY.value,
            "D": ToothCondition.HEALTHY.value,
            "O": ToothCondition.HEALTHY.value,
            "V": ToothCondition.HEALTHY.value,
            "L": ToothCondition.HEALTHY.value,
        }

    @staticmethod
    async def get_patient_odontogram(
        db: AsyncSession,
        clinic_id: UUID,
        patient_id: UUID,
    ) -> list[ToothRecord]:
        """Get all tooth records for a patient."""
        result = await db.execute(
            select(ToothRecord)
            .where(
                ToothRecord.clinic_id == clinic_id,
                ToothRecord.patient_id == patient_id,
            )
            .order_by(ToothRecord.tooth_number)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_tooth_record(
        db: AsyncSession,
        clinic_id: UUID,
        patient_id: UUID,
        tooth_number: int,
    ) -> ToothRecord | None:
        """Get a specific tooth record."""
        result = await db.execute(
            select(ToothRecord).where(
                ToothRecord.clinic_id == clinic_id,
                ToothRecord.patient_id == patient_id,
                ToothRecord.tooth_number == tooth_number,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create_or_update_tooth(
        db: AsyncSession,
        clinic_id: UUID,
        patient_id: UUID,
        tooth_number: int,
        user_id: UUID,
        general_condition: str | None = None,
        surface_updates: list[dict] | None = None,
        notes: str | None = None,
        is_displaced: bool | None = None,
        is_rotated: bool | None = None,
        displacement_notes: str | None = None,
    ) -> ToothRecord:
        """Create or update a tooth record with history tracking."""
        # Get existing record or create new
        existing = await OdontogramService.get_tooth_record(db, clinic_id, patient_id, tooth_number)

        tooth_type = get_tooth_type(tooth_number)
        now = datetime.now(UTC)

        if existing:
            # Update existing record
            record = existing
            old_general = record.general_condition

            # Update general condition if provided
            if general_condition is not None and general_condition != old_general:
                record.general_condition = general_condition

                # Log history
                history = OdontogramHistory(
                    clinic_id=clinic_id,
                    patient_id=patient_id,
                    tooth_number=tooth_number,
                    change_type="general_condition",
                    surface=None,
                    old_condition=old_general,
                    new_condition=general_condition,
                    changed_by=user_id,
                    changed_at=now,
                )
                db.add(history)

                # Publish event
                event_bus.publish(
                    OdontogramEventType.CONDITION_CHANGED,
                    {
                        "clinic_id": str(clinic_id),
                        "patient_id": str(patient_id),
                        "tooth_number": tooth_number,
                        "surface": None,
                        "old_condition": old_general,
                        "new_condition": general_condition,
                        "changed_by": str(user_id),
                    },
                )

            # Update surfaces if provided
            if surface_updates:
                current_surfaces = dict(record.surfaces)
                for update in surface_updates:
                    surface = update["surface"]
                    new_condition = update["condition"]
                    old_condition = current_surfaces.get(surface, ToothCondition.HEALTHY.value)

                    if new_condition != old_condition:
                        current_surfaces[surface] = new_condition

                        # Log history
                        history = OdontogramHistory(
                            clinic_id=clinic_id,
                            patient_id=patient_id,
                            tooth_number=tooth_number,
                            change_type="surface_update",
                            surface=surface,
                            old_condition=old_condition,
                            new_condition=new_condition,
                            changed_by=user_id,
                            changed_at=now,
                        )
                        db.add(history)

                        # Publish event
                        event_bus.publish(
                            OdontogramEventType.SURFACE_UPDATED,
                            {
                                "clinic_id": str(clinic_id),
                                "patient_id": str(patient_id),
                                "tooth_number": tooth_number,
                                "surface": surface,
                                "old_condition": old_condition,
                                "new_condition": new_condition,
                                "changed_by": str(user_id),
                            },
                        )

                record.surfaces = current_surfaces

            # Update notes if provided
            if notes is not None and notes != record.notes:
                record.notes = notes

                # Log history
                history = OdontogramHistory(
                    clinic_id=clinic_id,
                    patient_id=patient_id,
                    tooth_number=tooth_number,
                    change_type="note",
                    surface=None,
                    old_condition=None,
                    new_condition=None,
                    notes=notes,
                    changed_by=user_id,
                    changed_at=now,
                )
                db.add(history)

            # Update positional fields if provided
            if is_displaced is not None:
                record.is_displaced = is_displaced
            if is_rotated is not None:
                record.is_rotated = is_rotated
            if displacement_notes is not None:
                record.displacement_notes = displacement_notes

        else:
            # Create new record
            default_surfaces = OdontogramService._default_surfaces()

            # Apply surface updates if provided
            if surface_updates:
                for update in surface_updates:
                    default_surfaces[update["surface"]] = update["condition"]

            record = ToothRecord(
                clinic_id=clinic_id,
                patient_id=patient_id,
                tooth_number=tooth_number,
                tooth_type=tooth_type.value,
                general_condition=general_condition or ToothCondition.HEALTHY.value,
                surfaces=default_surfaces,
                notes=notes,
                is_displaced=is_displaced or False,
                is_rotated=is_rotated or False,
                displacement_notes=displacement_notes,
            )
            db.add(record)

            # Log creation in history
            history = OdontogramHistory(
                clinic_id=clinic_id,
                patient_id=patient_id,
                tooth_number=tooth_number,
                change_type="created",
                surface=None,
                old_condition=None,
                new_condition=general_condition or ToothCondition.HEALTHY.value,
                changed_by=user_id,
                changed_at=now,
            )
            db.add(history)

            # Publish event
            event_bus.publish(
                OdontogramEventType.TOOTH_UPDATED,
                {
                    "clinic_id": str(clinic_id),
                    "patient_id": str(patient_id),
                    "tooth_number": tooth_number,
                    "changed_by": str(user_id),
                },
            )

        await db.flush()
        await db.refresh(record)
        return record

    @staticmethod
    async def bulk_update_teeth(
        db: AsyncSession,
        clinic_id: UUID,
        patient_id: UUID,
        user_id: UUID,
        updates: list[dict],
    ) -> list[ToothRecord]:
        """Bulk update multiple teeth."""
        results = []
        for update in updates:
            record = await OdontogramService.create_or_update_tooth(
                db=db,
                clinic_id=clinic_id,
                patient_id=patient_id,
                tooth_number=update["tooth_number"],
                user_id=user_id,
                general_condition=update.get("general_condition"),
                surface_updates=update.get("surface_updates"),
                notes=update.get("notes"),
            )
            results.append(record)
        return results

    @staticmethod
    async def get_tooth_history(
        db: AsyncSession,
        clinic_id: UUID,
        patient_id: UUID,
        tooth_number: int,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[OdontogramHistory], int]:
        """Get history for a specific tooth."""
        offset = (page - 1) * page_size

        # Count query
        count_result = await db.execute(
            select(OdontogramHistory).where(
                OdontogramHistory.clinic_id == clinic_id,
                OdontogramHistory.patient_id == patient_id,
                OdontogramHistory.tooth_number == tooth_number,
            )
        )
        total = len(count_result.scalars().all())

        # Data query with pagination
        result = await db.execute(
            select(OdontogramHistory)
            .options(selectinload(OdontogramHistory.user))
            .where(
                OdontogramHistory.clinic_id == clinic_id,
                OdontogramHistory.patient_id == patient_id,
                OdontogramHistory.tooth_number == tooth_number,
            )
            .order_by(OdontogramHistory.changed_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        history = list(result.scalars().all())

        return history, total

    @staticmethod
    async def get_patient_history(
        db: AsyncSession,
        clinic_id: UUID,
        patient_id: UUID,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[OdontogramHistory], int]:
        """Get full odontogram history for a patient."""
        offset = (page - 1) * page_size

        # Count query
        count_result = await db.execute(
            select(OdontogramHistory).where(
                OdontogramHistory.clinic_id == clinic_id,
                OdontogramHistory.patient_id == patient_id,
            )
        )
        total = len(count_result.scalars().all())

        # Data query with pagination
        result = await db.execute(
            select(OdontogramHistory)
            .options(selectinload(OdontogramHistory.user))
            .where(
                OdontogramHistory.clinic_id == clinic_id,
                OdontogramHistory.patient_id == patient_id,
            )
            .order_by(OdontogramHistory.changed_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        history = list(result.scalars().all())

        return history, total

    @staticmethod
    async def get_tooth_with_treatments(
        db: AsyncSession,
        clinic_id: UUID,
        patient_id: UUID,
        tooth_number: int,
    ) -> ToothRecord | None:
        """Get a tooth record with all its treatments eagerly loaded."""
        result = await db.execute(
            select(ToothRecord)
            .options(selectinload(ToothRecord.treatments).selectinload(ToothTreatment.performer))
            .where(
                ToothRecord.clinic_id == clinic_id,
                ToothRecord.patient_id == patient_id,
                ToothRecord.tooth_number == tooth_number,
            )
        )
        return result.scalar_one_or_none()

    # ========================================================================
    # Timeline Methods
    # ========================================================================

    @staticmethod
    async def get_timeline_dates(
        db: AsyncSession,
        clinic_id: UUID,
        patient_id: UUID,
    ) -> list[dict]:
        """Get distinct dates when odontogram was modified.

        Returns dates from both OdontogramHistory (tooth changes) and
        ToothTreatment (treatments added/recorded).
        """
        # Get dates from OdontogramHistory
        history_dates = await db.execute(
            select(
                func.date(OdontogramHistory.changed_at).label("change_date"),
                func.count().label("count"),
            )
            .where(
                OdontogramHistory.clinic_id == clinic_id,
                OdontogramHistory.patient_id == patient_id,
            )
            .group_by(func.date(OdontogramHistory.changed_at))
        )
        history_results = {row.change_date: row.count for row in history_dates.all()}

        # Get dates from ToothTreatment (recorded_at)
        treatment_dates = await db.execute(
            select(
                func.date(ToothTreatment.recorded_at).label("recorded_date"),
                func.count().label("count"),
            )
            .where(
                ToothTreatment.clinic_id == clinic_id,
                ToothTreatment.patient_id == patient_id,
            )
            .group_by(func.date(ToothTreatment.recorded_at))
        )
        treatment_results = {row.recorded_date: row.count for row in treatment_dates.all()}

        # Combine dates and counts
        all_dates: dict[date, int] = {}
        for d, count in history_results.items():
            all_dates[d] = all_dates.get(d, 0) + count
        for d, count in treatment_results.items():
            all_dates[d] = all_dates.get(d, 0) + count

        # Sort by date and format
        sorted_dates = sorted(all_dates.items(), key=lambda x: x[0])
        return [
            {"date": d.isoformat(), "change_count": count}
            for d, count in sorted_dates
        ]

    @staticmethod
    async def get_odontogram_at_date(
        db: AsyncSession,
        clinic_id: UUID,
        patient_id: UUID,
        target_date: date,
    ) -> dict:
        """Reconstruct odontogram state at a specific date.

        Algorithm:
        1. Get all OdontogramHistory entries with changed_at <= target_date
        2. Get all ToothTreatment with recorded_at <= target_date AND
           (deleted_at IS NULL OR deleted_at > target_date)
        3. Build tooth states by replaying history chronologically
        4. Return reconstructed teeth and treatments
        """
        # Convert date to datetime at end of day for inclusive comparison
        target_datetime = datetime.combine(target_date, datetime.max.time())
        target_datetime = target_datetime.replace(tzinfo=UTC)

        # Get history up to target date, ordered chronologically
        history_result = await db.execute(
            select(OdontogramHistory)
            .where(
                OdontogramHistory.clinic_id == clinic_id,
                OdontogramHistory.patient_id == patient_id,
                OdontogramHistory.changed_at <= target_datetime,
            )
            .order_by(OdontogramHistory.changed_at.asc())
        )
        history_entries = list(history_result.scalars().all())

        # Get treatments that existed at target date
        # Include: recorded_at <= target AND (deleted_at is NULL OR deleted_at > target)
        treatment_result = await db.execute(
            select(ToothTreatment)
            .options(selectinload(ToothTreatment.performer))
            .where(
                ToothTreatment.clinic_id == clinic_id,
                ToothTreatment.patient_id == patient_id,
                ToothTreatment.recorded_at <= target_datetime,
                or_(
                    ToothTreatment.deleted_at.is_(None),
                    ToothTreatment.deleted_at > target_datetime,
                ),
            )
        )
        treatments = list(treatment_result.scalars().all())

        # Reconstruct tooth states by replaying history
        teeth_state: dict[int, dict] = {}

        for entry in history_entries:
            tooth_num = entry.tooth_number

            if tooth_num not in teeth_state:
                # Initialize tooth with default state
                teeth_state[tooth_num] = {
                    "tooth_number": tooth_num,
                    "tooth_type": "permanent" if tooth_num < 50 else "deciduous",
                    "general_condition": ToothCondition.HEALTHY.value,
                    "surfaces": {
                        "M": ToothCondition.HEALTHY.value,
                        "D": ToothCondition.HEALTHY.value,
                        "O": ToothCondition.HEALTHY.value,
                        "V": ToothCondition.HEALTHY.value,
                        "L": ToothCondition.HEALTHY.value,
                    },
                    "notes": None,
                    "is_displaced": False,
                    "is_rotated": False,
                }

            tooth = teeth_state[tooth_num]

            # Apply change based on type
            if entry.change_type == "created" and entry.new_condition:
                tooth["general_condition"] = entry.new_condition
            elif entry.change_type == "general_condition" and entry.new_condition:
                tooth["general_condition"] = entry.new_condition
            elif entry.change_type == "surface_update" and entry.surface and entry.new_condition:
                tooth["surfaces"][entry.surface] = entry.new_condition
            elif entry.change_type == "note" and entry.notes:
                tooth["notes"] = entry.notes

        # Convert to list of tooth records
        reconstructed_teeth = list(teeth_state.values())

        # Format treatments for response
        formatted_treatments = []
        for t in treatments:
            formatted_treatments.append({
                "id": t.id,
                "tooth_record_id": t.tooth_record_id,
                "tooth_number": t.tooth_number,
                "treatment_type": t.treatment_type,
                "treatment_category": t.treatment_category,
                "surfaces": t.surfaces,
                "status": t.status,
                "recorded_at": t.recorded_at,
                "performed_at": t.performed_at,
                "performed_by": t.performed_by,
                "performed_by_name": (
                    f"{t.performer.first_name} {t.performer.last_name}"
                    if t.performer else None
                ),
                "budget_item_id": t.budget_item_id,
                "source_module": t.source_module,
                "notes": t.notes,
                "created_at": t.created_at,
                "updated_at": t.updated_at,
            })

        return {
            "teeth": reconstructed_teeth,
            "treatments": formatted_treatments,
        }


class TreatmentService:
    """Service for tooth treatment operations."""

    @staticmethod
    async def create_treatment(
        db: AsyncSession,
        clinic_id: UUID,
        patient_id: UUID,
        tooth_number: int,
        user_id: UUID,
        treatment_type: str,
        status: str = TreatmentStatus.EXISTING.value,
        surfaces: list[str] | None = None,
        notes: str | None = None,
        budget_item_id: UUID | None = None,
        source_module: str = "odontogram",
    ) -> ToothTreatment:
        """Create a new treatment for a tooth."""
        now = datetime.now(UTC)

        # Get or create tooth record
        tooth_record = await OdontogramService.get_tooth_record(
            db, clinic_id, patient_id, tooth_number
        )
        if not tooth_record:
            tooth_record = await OdontogramService.create_or_update_tooth(
                db, clinic_id, patient_id, tooth_number, user_id
            )

        # Determine treatment category
        treatment_category = get_treatment_category(treatment_type).value

        # Create treatment
        treatment = ToothTreatment(
            clinic_id=clinic_id,
            patient_id=patient_id,
            tooth_record_id=tooth_record.id,
            tooth_number=tooth_number,
            treatment_type=treatment_type,
            treatment_category=treatment_category,
            surfaces=surfaces,
            status=status,
            recorded_at=now,
            performed_at=now if status == TreatmentStatus.EXISTING.value else None,
            performed_by=user_id if status == TreatmentStatus.EXISTING.value else None,
            budget_item_id=budget_item_id,
            source_module=source_module,
            notes=notes,
        )
        db.add(treatment)
        await db.flush()
        await db.refresh(treatment)

        # Publish event
        event_bus.publish(
            EventType.ODONTOGRAM_TREATMENT_ADDED,
            {
                "clinic_id": str(clinic_id),
                "patient_id": str(patient_id),
                "treatment_id": str(treatment.id),
                "tooth_number": tooth_number,
                "treatment_type": treatment_type,
                "status": status,
                "budget_item_id": str(budget_item_id) if budget_item_id else None,
                "source_module": source_module,
                "created_by": str(user_id),
                "created_at": now.isoformat(),
            },
        )

        return treatment

    @staticmethod
    async def get_treatment(
        db: AsyncSession,
        clinic_id: UUID,
        treatment_id: UUID,
        include_deleted: bool = False,
    ) -> ToothTreatment | None:
        """Get a treatment by ID.

        Args:
            include_deleted: If True, include soft-deleted treatments. Default False.
        """
        conditions = [
            ToothTreatment.clinic_id == clinic_id,
            ToothTreatment.id == treatment_id,
        ]
        # Filter out soft-deleted treatments unless explicitly requested
        if not include_deleted:
            conditions.append(ToothTreatment.deleted_at.is_(None))

        result = await db.execute(
            select(ToothTreatment)
            .options(selectinload(ToothTreatment.performer))
            .where(*conditions)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_patient_treatments(
        db: AsyncSession,
        clinic_id: UUID,
        patient_id: UUID,
        status: str | None = None,
        treatment_type: str | None = None,
        tooth_number: int | None = None,
        page: int = 1,
        page_size: int = 50,
        include_deleted: bool = False,
    ) -> tuple[list[ToothTreatment], int]:
        """List treatments for a patient with optional filters.

        Args:
            include_deleted: If True, include soft-deleted treatments. Default False.
        """
        offset = (page - 1) * page_size

        # Build base query
        conditions = [
            ToothTreatment.clinic_id == clinic_id,
            ToothTreatment.patient_id == patient_id,
        ]
        # Filter out soft-deleted treatments unless explicitly requested
        if not include_deleted:
            conditions.append(ToothTreatment.deleted_at.is_(None))

        if status:
            conditions.append(ToothTreatment.status == status)
        if treatment_type:
            conditions.append(ToothTreatment.treatment_type == treatment_type)
        if tooth_number:
            conditions.append(ToothTreatment.tooth_number == tooth_number)

        # Count query
        count_result = await db.execute(select(func.count(ToothTreatment.id)).where(*conditions))
        total = count_result.scalar() or 0

        # Data query with pagination
        result = await db.execute(
            select(ToothTreatment)
            .options(selectinload(ToothTreatment.performer))
            .where(*conditions)
            .order_by(ToothTreatment.recorded_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        treatments = list(result.scalars().all())

        return treatments, total

    @staticmethod
    async def update_treatment(
        db: AsyncSession,
        clinic_id: UUID,
        treatment_id: UUID,
        user_id: UUID,
        status: str | None = None,
        surfaces: list[str] | None = None,
        notes: str | None = None,
    ) -> ToothTreatment | None:
        """Update a treatment."""
        treatment = await TreatmentService.get_treatment(db, clinic_id, treatment_id)
        if not treatment:
            return None

        old_status = treatment.status
        now = datetime.now(UTC)

        if status is not None and status != old_status:
            treatment.status = status
            # If marking as existing, set performed_at and performed_by
            if status == TreatmentStatus.EXISTING.value:
                treatment.performed_at = now
                treatment.performed_by = user_id

            # Publish status change event
            event_bus.publish(
                EventType.ODONTOGRAM_TREATMENT_STATUS_CHANGED,
                {
                    "clinic_id": str(clinic_id),
                    "patient_id": str(treatment.patient_id),
                    "treatment_id": str(treatment_id),
                    "tooth_number": treatment.tooth_number,
                    "treatment_type": treatment.treatment_type,
                    "old_status": old_status,
                    "new_status": status,
                    "budget_item_id": str(treatment.budget_item_id)
                    if treatment.budget_item_id
                    else None,
                    "changed_by": str(user_id),
                },
            )

        if surfaces is not None:
            treatment.surfaces = surfaces
        if notes is not None:
            treatment.notes = notes

        await db.flush()
        await db.refresh(treatment)
        return treatment

    @staticmethod
    async def delete_treatment(
        db: AsyncSession,
        clinic_id: UUID,
        treatment_id: UUID,
        user_id: UUID,
    ) -> bool:
        """Soft delete a treatment (sets deleted_at timestamp).

        Following CLAUDE.md convention: use soft deletes for patient data.
        """
        treatment = await TreatmentService.get_treatment(db, clinic_id, treatment_id)
        if not treatment:
            return False

        # Store data for event before deletion
        event_data = {
            "clinic_id": str(clinic_id),
            "patient_id": str(treatment.patient_id),
            "treatment_id": str(treatment_id),
            "tooth_number": treatment.tooth_number,
            "treatment_type": treatment.treatment_type,
            "budget_item_id": str(treatment.budget_item_id) if treatment.budget_item_id else None,
            "deleted_by": str(user_id),
        }

        # Soft delete: set deleted_at timestamp instead of hard delete
        treatment.deleted_at = datetime.now(UTC)
        await db.flush()

        # Publish deletion event
        event_bus.publish(EventType.ODONTOGRAM_TREATMENT_DELETED, event_data)

        return True

    @staticmethod
    async def perform_treatment(
        db: AsyncSession,
        clinic_id: UUID,
        treatment_id: UUID,
        user_id: UUID,
        notes: str | None = None,
    ) -> ToothTreatment | None:
        """Mark a treatment as existing (performed).

        This is the key method for budget integration - emits a specific event
        that the budget module can listen to for updating budget item status.
        """
        treatment = await TreatmentService.get_treatment(db, clinic_id, treatment_id)
        if not treatment:
            return None

        old_status = treatment.status
        now = datetime.now(UTC)

        treatment.status = TreatmentStatus.EXISTING.value
        treatment.performed_at = now
        treatment.performed_by = user_id
        if notes:
            treatment.notes = notes

        await db.flush()
        await db.refresh(treatment)

        # Publish specific "performed" event for budget integration
        event_bus.publish(
            EventType.ODONTOGRAM_TREATMENT_PERFORMED,
            {
                "clinic_id": str(clinic_id),
                "patient_id": str(treatment.patient_id),
                "treatment_id": str(treatment_id),
                "tooth_number": treatment.tooth_number,
                "treatment_type": treatment.treatment_type,
                "budget_item_id": str(treatment.budget_item_id)
                if treatment.budget_item_id
                else None,
                "performed_by": str(user_id),
                "performed_at": now.isoformat(),
                "previous_status": old_status,
            },
        )

        return treatment
