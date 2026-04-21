"""PatientService — business logic for patient CRUD.

Moved from ``app.modules.clinical.service`` in Fase B.1 chunk 2.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import EventType, event_bus

from .models import Patient


class PatientService:
    """Service for patient CRUD."""

    @staticmethod
    async def get_recent_patients(
        db: AsyncSession,
        clinic_id: UUID,
        limit: int = 8,
    ) -> list[Patient]:
        """Patients ordered by last visit, falling back to newest created."""
        # Lazy import to avoid a circular path between
        # ``patients.service`` and ``agenda.models``.
        from app.modules.agenda.models import Appointment

        subquery = (
            select(
                Appointment.patient_id,
                func.max(Appointment.start_time).label("last_visit"),
            )
            .where(
                Appointment.clinic_id == clinic_id,
                Appointment.patient_id.isnot(None),
            )
            .group_by(Appointment.patient_id)
            .subquery()
        )

        query = (
            select(Patient)
            .outerjoin(subquery, Patient.id == subquery.c.patient_id)
            .where(
                Patient.clinic_id == clinic_id,
                Patient.status != "archived",
            )
            .order_by(
                subquery.c.last_visit.desc().nulls_last(),
                Patient.created_at.desc(),
            )
            .limit(limit)
        )

        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def list_patients(
        db: AsyncSession,
        clinic_id: UUID,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Patient], int]:
        """List patients with optional search + pagination."""
        page_size = min(max(page_size, 1), 100)
        page = max(page, 1)
        offset = (page - 1) * page_size

        query = select(Patient).where(
            Patient.clinic_id == clinic_id,
            Patient.status != "archived",
        )

        if search:
            like = f"%{search}%"
            query = query.where(
                or_(
                    Patient.first_name.ilike(like),
                    Patient.last_name.ilike(like),
                    Patient.phone.ilike(like),
                )
            )

        total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0

        query = query.order_by(Patient.last_name, Patient.first_name)
        query = query.offset(offset).limit(page_size)
        result = await db.execute(query)
        return list(result.scalars().all()), total

    @staticmethod
    async def get_patient(db: AsyncSession, clinic_id: UUID, patient_id: UUID) -> Patient | None:
        result = await db.execute(
            select(Patient).where(
                Patient.id == patient_id,
                Patient.clinic_id == clinic_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create_patient(db: AsyncSession, clinic_id: UUID, data: dict) -> Patient:
        patient = Patient(clinic_id=clinic_id, **data)
        db.add(patient)
        await db.flush()

        event_bus.publish(
            EventType.PATIENT_CREATED,
            {"patient_id": str(patient.id), "clinic_id": str(clinic_id)},
        )
        return patient

    @staticmethod
    async def update_patient(db: AsyncSession, patient: Patient, data: dict) -> Patient:
        """Update an existing patient.

        ``data`` should come from ``model_dump(exclude_unset=True)`` so
        unspecified fields are preserved and explicit ``None`` clears.
        """
        for key, value in data.items():
            setattr(patient, key, value)

        await db.flush()

        event_bus.publish(
            EventType.PATIENT_UPDATED,
            {"patient_id": str(patient.id), "changes": list(data.keys())},
        )
        return patient

    @staticmethod
    async def archive_patient(db: AsyncSession, patient: Patient) -> Patient:
        patient.status = "archived"
        await db.flush()

        event_bus.publish(
            EventType.PATIENT_ARCHIVED,
            {"patient_id": str(patient.id)},
        )
        return patient
