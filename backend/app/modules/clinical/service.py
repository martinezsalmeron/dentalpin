"""Business logic service for clinical module."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.auth.models import ClinicMembership
from app.core.events import EventType, event_bus
from app.modules.odontogram.models import Treatment
from app.modules.patients.models import Patient

# Re-export PatientService so legacy callers keep resolving. The
# implementation now lives in ``app.modules.patients.service``.
from app.modules.patients.service import PatientService  # noqa: F401
from app.modules.treatment_plan.models import PlannedTreatmentItem

from .models import Appointment, AppointmentTreatment, PatientTimeline
from .schemas import TimelineEntry


class AppointmentService:
    """Service for appointment operations."""

    @staticmethod
    async def list_appointments(
        db: AsyncSession,
        clinic_id: UUID,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        cabinet: str | None = None,
        professional_id: UUID | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 100,
    ) -> tuple[list[Appointment], int]:
        """List appointments with filters."""
        page_size = min(max(page_size, 1), 500)
        page = max(page, 1)
        offset = (page - 1) * page_size

        query = (
            select(Appointment)
            .options(
                selectinload(Appointment.patient),
                selectinload(Appointment.professional),
                selectinload(Appointment.treatments).options(
                    selectinload(AppointmentTreatment.planned_item).options(
                        selectinload(PlannedTreatmentItem.treatment).options(
                            selectinload(Treatment.teeth),
                            selectinload(Treatment.catalog_item),
                        ),
                        selectinload(PlannedTreatmentItem.treatment_plan),
                    ),
                    selectinload(AppointmentTreatment.catalog_item),
                ),
            )
            .where(Appointment.clinic_id == clinic_id)
        )

        if start_date:
            query = query.where(Appointment.start_time >= start_date)
        if end_date:
            query = query.where(Appointment.start_time <= end_date)
        if cabinet:
            query = query.where(Appointment.cabinet == cabinet)
        if professional_id:
            query = query.where(Appointment.professional_id == professional_id)
        if status:
            query = query.where(Appointment.status == status)

        # Count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_query)).scalar() or 0

        # Paginate
        query = query.order_by(Appointment.start_time)
        query = query.offset(offset).limit(page_size)
        result = await db.execute(query)
        appointments = result.scalars().all()

        return list(appointments), total

    @staticmethod
    async def get_appointment(
        db: AsyncSession,
        clinic_id: UUID,
        appointment_id: UUID,
    ) -> Appointment | None:
        """Get an appointment by ID."""
        result = await db.execute(
            select(Appointment)
            .options(
                selectinload(Appointment.patient),
                selectinload(Appointment.professional),
                selectinload(Appointment.treatments).options(
                    selectinload(AppointmentTreatment.planned_item).options(
                        selectinload(PlannedTreatmentItem.treatment).options(
                            selectinload(Treatment.teeth),
                            selectinload(Treatment.catalog_item),
                        ),
                        selectinload(PlannedTreatmentItem.treatment_plan),
                    ),
                    selectinload(AppointmentTreatment.catalog_item),
                ),
            )
            .where(
                Appointment.id == appointment_id,
                Appointment.clinic_id == clinic_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def validate_patient_access(
        db: AsyncSession,
        clinic_id: UUID,
        patient_id: UUID,
    ) -> bool:
        """Check if patient exists and belongs to clinic."""
        result = await db.execute(
            select(Patient.id).where(
                Patient.id == patient_id,
                Patient.clinic_id == clinic_id,
                Patient.status != "archived",
            )
        )
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def validate_professional_access(
        db: AsyncSession,
        clinic_id: UUID,
        professional_id: UUID,
    ) -> bool:
        """Check if professional exists, belongs to clinic, and has valid role."""
        result = await db.execute(
            select(ClinicMembership.id).where(
                ClinicMembership.user_id == professional_id,
                ClinicMembership.clinic_id == clinic_id,
                ClinicMembership.role.in_(["dentist", "hygienist"]),
            )
        )
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def validate_planned_items(
        db: AsyncSession,
        clinic_id: UUID,
        patient_id: UUID,
        planned_item_ids: list[UUID],
    ) -> None:
        """Validate planned treatment items for appointment.

        Checks:
        - Each item exists and belongs to the clinic
        - Each item belongs to the specified patient (via treatment plan)
        - Each item has status "pending"
        - Parent treatment plan is "active" or "draft"

        Raises ValueError with details if validation fails.
        """
        if not planned_item_ids:
            return

        # Fetch all items with their treatment plans in one query
        result = await db.execute(
            select(PlannedTreatmentItem)
            .options(selectinload(PlannedTreatmentItem.treatment_plan))
            .where(PlannedTreatmentItem.id.in_(planned_item_ids))
        )
        items = {item.id: item for item in result.scalars().all()}

        errors = []
        for item_id in planned_item_ids:
            item = items.get(item_id)

            if not item:
                errors.append(f"Treatment item {item_id} not found")
                continue

            if item.clinic_id != clinic_id:
                errors.append(f"Treatment item {item_id} not found")
                continue

            plan = item.treatment_plan
            if not plan or plan.patient_id != patient_id:
                errors.append(f"Treatment item {item_id} does not belong to patient")
                continue

            if plan.status not in ("active", "draft"):
                errors.append(f"Treatment item {item_id} belongs to {plan.status} plan")
                continue

            if item.status != "pending":
                errors.append(f"Treatment item {item_id} is already {item.status}")

        if errors:
            raise ValueError("; ".join(errors))

    @staticmethod
    async def create_appointment(
        db: AsyncSession,
        clinic_id: UUID,
        data: dict,
    ) -> Appointment:
        """Create an appointment. Raises IntegrityError on conflict."""
        # Extract planned_item_ids before creating appointment
        planned_item_ids = data.pop("planned_item_ids", None)

        # Validate planned items belong to patient and are in valid state
        if planned_item_ids and data.get("patient_id"):
            await AppointmentService.validate_planned_items(
                db, clinic_id, data["patient_id"], planned_item_ids
            )

        appointment = Appointment(clinic_id=clinic_id, **data)
        db.add(appointment)

        try:
            await db.flush()
        except IntegrityError:
            await db.rollback()
            raise

        # Add treatments from planned items
        if planned_item_ids:
            for order, planned_item_id in enumerate(planned_item_ids):
                # Resolve catalog_item_id from the referenced Treatment.
                planned_item = await db.get(PlannedTreatmentItem, planned_item_id)
                catalog_item_id = None
                if planned_item:
                    await db.refresh(planned_item, ["treatment"])
                    if planned_item.treatment:
                        catalog_item_id = planned_item.treatment.catalog_item_id

                treatment = AppointmentTreatment(
                    appointment_id=appointment.id,
                    planned_treatment_item_id=planned_item_id,
                    catalog_item_id=catalog_item_id,
                    display_order=order,
                )
                db.add(treatment)
            await db.flush()

        event_bus.publish(
            EventType.APPOINTMENT_SCHEDULED,
            {
                "appointment_id": str(appointment.id),
                "patient_id": str(appointment.patient_id) if appointment.patient_id else None,
                "professional_id": str(appointment.professional_id),
                "start_time": appointment.start_time.isoformat(),
            },
        )

        await db.refresh(appointment, ["patient", "professional", "treatments"])
        for treatment in appointment.treatments:
            await db.refresh(treatment, ["planned_item", "catalog_item"])
            if treatment.planned_item:
                await db.refresh(treatment.planned_item, ["treatment", "treatment_plan"])
                if treatment.planned_item.treatment:
                    await db.refresh(treatment.planned_item.treatment, ["teeth", "catalog_item"])

        return appointment

    @staticmethod
    async def update_appointment(
        db: AsyncSession,
        appointment: Appointment,
        data: dict,
    ) -> Appointment:
        """Update an appointment."""
        old_status = appointment.status

        # Extract planned_item_ids before updating other fields
        planned_item_ids = data.pop("planned_item_ids", None)

        # Validate planned items if provided
        if planned_item_ids:
            # Use patient_id from data if changing, otherwise from existing appointment
            patient_id = data.get("patient_id") or appointment.patient_id
            if patient_id:
                await AppointmentService.validate_planned_items(
                    db, appointment.clinic_id, patient_id, planned_item_ids
                )

        for key, value in data.items():
            if value is not None:
                setattr(appointment, key, value)

        try:
            await db.flush()
        except IntegrityError:
            await db.rollback()
            raise

        # Update treatments if provided
        if planned_item_ids is not None:
            # Remove existing treatments
            for existing in list(appointment.treatments):
                await db.delete(existing)
            await db.flush()

            # Add new treatments from planned items
            for order, planned_item_id in enumerate(planned_item_ids):
                planned_item = await db.get(PlannedTreatmentItem, planned_item_id)
                catalog_item_id = None
                if planned_item:
                    await db.refresh(planned_item, ["treatment"])
                    if planned_item.treatment:
                        catalog_item_id = planned_item.treatment.catalog_item_id

                treatment = AppointmentTreatment(
                    appointment_id=appointment.id,
                    planned_treatment_item_id=planned_item_id,
                    catalog_item_id=catalog_item_id,
                    display_order=order,
                )
                db.add(treatment)
            await db.flush()

            # Refresh treatments with nested relationships
            await db.refresh(appointment, ["treatments"])
            for treatment in appointment.treatments:
                await db.refresh(treatment, ["planned_item", "catalog_item"])
                if treatment.planned_item:
                    await db.refresh(treatment.planned_item, ["treatment", "treatment_plan"])
                    if treatment.planned_item.treatment:
                        await db.refresh(
                            treatment.planned_item.treatment, ["teeth", "catalog_item"]
                        )

        # Publish appropriate event based on status change
        new_status = appointment.status
        if old_status != new_status:
            if new_status == "completed":
                event_bus.publish(
                    EventType.APPOINTMENT_COMPLETED,
                    {"appointment_id": str(appointment.id)},
                )
            elif new_status == "cancelled":
                event_bus.publish(
                    EventType.APPOINTMENT_CANCELLED,
                    {"appointment_id": str(appointment.id)},
                )
            elif new_status == "no_show":
                event_bus.publish(
                    EventType.APPOINTMENT_NO_SHOW,
                    {"appointment_id": str(appointment.id)},
                )
        else:
            event_bus.publish(
                EventType.APPOINTMENT_UPDATED,
                {"appointment_id": str(appointment.id)},
            )

        return appointment

    @staticmethod
    async def cancel_appointment(
        db: AsyncSession,
        appointment: Appointment,
    ) -> Appointment:
        """Cancel an appointment."""
        appointment.status = "cancelled"
        await db.flush()

        event_bus.publish(
            EventType.APPOINTMENT_CANCELLED,
            {"appointment_id": str(appointment.id)},
        )

        return appointment


class TimelineService:
    """Service for patient timeline operations."""

    @staticmethod
    async def get_timeline(
        db: AsyncSession,
        clinic_id: UUID,
        patient_id: UUID,
        category: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[TimelineEntry], int]:
        """Get timeline entries for a patient with optional category filter."""
        page_size = min(max(page_size, 1), 100)
        page = max(page, 1)
        offset = (page - 1) * page_size

        query = select(PatientTimeline).where(
            PatientTimeline.clinic_id == clinic_id,
            PatientTimeline.patient_id == patient_id,
        )

        if category:
            query = query.where(PatientTimeline.event_category == category)

        # Count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_query)).scalar() or 0

        # Paginate (most recent first)
        query = query.order_by(PatientTimeline.occurred_at.desc())
        query = query.offset(offset).limit(page_size)
        result = await db.execute(query)
        entries = result.scalars().all()

        return [TimelineEntry.model_validate(e) for e in entries], total

    @staticmethod
    async def add_entry(
        db: AsyncSession,
        clinic_id: UUID,
        patient_id: UUID,
        event_type: str,
        event_category: str,
        source_table: str,
        source_id: UUID,
        title: str,
        description: str | None = None,
        event_data: dict | None = None,
        occurred_at: datetime | None = None,
        created_by: UUID | None = None,
    ) -> PatientTimeline:
        """Add a timeline entry."""
        entry = PatientTimeline(
            clinic_id=clinic_id,
            patient_id=patient_id,
            event_type=event_type,
            event_category=event_category,
            source_table=source_table,
            source_id=source_id,
            title=title,
            description=description,
            event_data=event_data,
            occurred_at=occurred_at or datetime.utcnow(),
            created_by=created_by,
        )
        db.add(entry)
        await db.flush()
        return entry
