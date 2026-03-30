"""Business logic service for clinical module."""
from datetime import datetime
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.events import EventType, event_bus

from .models import Appointment, Patient


class PatientService:
    """Service for patient operations."""

    @staticmethod
    async def list_patients(
        db: AsyncSession,
        clinic_id: UUID,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Patient], int]:
        """List patients with optional search and pagination."""
        page_size = min(max(page_size, 1), 100)  # Clamp to 1-100
        page = max(page, 1)
        offset = (page - 1) * page_size

        # Base query
        query = select(Patient).where(
            Patient.clinic_id == clinic_id,
            Patient.status != "archived",
        )

        # Add search filter
        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    Patient.first_name.ilike(search_term),
                    Patient.last_name.ilike(search_term),
                    Patient.phone.ilike(search_term),
                )
            )

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_query)).scalar() or 0

        # Get paginated results
        query = query.order_by(Patient.last_name, Patient.first_name)
        query = query.offset(offset).limit(page_size)
        result = await db.execute(query)
        patients = result.scalars().all()

        return list(patients), total

    @staticmethod
    async def get_patient(
        db: AsyncSession,
        clinic_id: UUID,
        patient_id: UUID,
    ) -> Patient | None:
        """Get a patient by ID within a clinic."""
        result = await db.execute(
            select(Patient).where(
                Patient.id == patient_id,
                Patient.clinic_id == clinic_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create_patient(
        db: AsyncSession,
        clinic_id: UUID,
        data: dict,
    ) -> Patient:
        """Create a new patient."""
        patient = Patient(clinic_id=clinic_id, **data)
        db.add(patient)
        await db.flush()

        # Publish event
        event_bus.publish(
            EventType.PATIENT_CREATED,
            {"patient_id": str(patient.id), "clinic_id": str(clinic_id)},
        )

        return patient

    @staticmethod
    async def update_patient(
        db: AsyncSession,
        patient: Patient,
        data: dict,
    ) -> Patient:
        """Update an existing patient."""
        for key, value in data.items():
            if value is not None:
                setattr(patient, key, value)

        await db.flush()

        # Publish event
        event_bus.publish(
            EventType.PATIENT_UPDATED,
            {"patient_id": str(patient.id), "changes": list(data.keys())},
        )

        return patient

    @staticmethod
    async def archive_patient(
        db: AsyncSession,
        patient: Patient,
    ) -> Patient:
        """Soft delete a patient by setting status to archived."""
        patient.status = "archived"
        await db.flush()

        event_bus.publish(
            EventType.PATIENT_ARCHIVED,
            {"patient_id": str(patient.id)},
        )

        return patient


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
            .options(selectinload(Appointment.patient))
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
            .options(selectinload(Appointment.patient))
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
    async def create_appointment(
        db: AsyncSession,
        clinic_id: UUID,
        data: dict,
    ) -> Appointment:
        """Create an appointment. Raises IntegrityError on conflict."""
        appointment = Appointment(clinic_id=clinic_id, **data)
        db.add(appointment)

        try:
            await db.flush()
        except IntegrityError:
            await db.rollback()
            raise

        event_bus.publish(
            EventType.APPOINTMENT_SCHEDULED,
            {
                "appointment_id": str(appointment.id),
                "patient_id": str(appointment.patient_id) if appointment.patient_id else None,
                "professional_id": str(appointment.professional_id),
                "start_time": appointment.start_time.isoformat(),
            },
        )

        # Refresh to load relationships
        await db.refresh(appointment, ["patient"])

        return appointment

    @staticmethod
    async def update_appointment(
        db: AsyncSession,
        appointment: Appointment,
        data: dict,
    ) -> Appointment:
        """Update an appointment."""
        old_status = appointment.status

        for key, value in data.items():
            if value is not None:
                setattr(appointment, key, value)

        try:
            await db.flush()
        except IntegrityError:
            await db.rollback()
            raise

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
