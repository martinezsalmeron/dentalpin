"""AppointmentService — business logic for scheduling.

Moved from ``app.modules.clinical.service`` in Fase B.2 chunk 1.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.auth.models import ClinicMembership
from app.core.events import EventType, event_bus
from app.modules.catalog.models import TreatmentCatalogItem  # noqa: F401
from app.modules.odontogram.models import Treatment
from app.modules.patients.models import Patient
from app.modules.treatment_plan.models import PlannedTreatmentItem

from .models import Appointment, AppointmentTreatment, Cabinet


class CabinetService:
    """CRUD for clinic cabinets."""

    @staticmethod
    async def list_cabinets(db: AsyncSession, clinic_id: UUID) -> list[Cabinet]:
        result = await db.execute(
            select(Cabinet)
            .where(Cabinet.clinic_id == clinic_id)
            .order_by(Cabinet.display_order, Cabinet.name)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_cabinet(db: AsyncSession, clinic_id: UUID, cabinet_id: UUID) -> Cabinet | None:
        result = await db.execute(
            select(Cabinet).where(Cabinet.id == cabinet_id, Cabinet.clinic_id == clinic_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_name(db: AsyncSession, clinic_id: UUID, name: str) -> Cabinet | None:
        result = await db.execute(
            select(Cabinet).where(Cabinet.clinic_id == clinic_id, Cabinet.name == name)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create_cabinet(db: AsyncSession, clinic_id: UUID, data: dict) -> Cabinet:
        if data.get("display_order") is None:
            # Append at the end.
            max_order = (
                await db.execute(
                    select(func.coalesce(func.max(Cabinet.display_order), -1)).where(
                        Cabinet.clinic_id == clinic_id
                    )
                )
            ).scalar_one()
            data["display_order"] = int(max_order) + 1
        if data.get("is_active") is None:
            data["is_active"] = True

        cabinet = Cabinet(clinic_id=clinic_id, **data)
        db.add(cabinet)
        await db.flush()
        await db.refresh(cabinet)
        return cabinet

    @staticmethod
    async def update_cabinet(db: AsyncSession, cabinet: Cabinet, data: dict) -> Cabinet:
        old_name = cabinet.name
        for key, value in data.items():
            if value is not None:
                setattr(cabinet, key, value)
        await db.flush()

        # Keep the denormalized appointments.cabinet string in sync.
        if "name" in data and data["name"] != old_name:
            from sqlalchemy import update as sql_update

            await db.execute(
                sql_update(Appointment)
                .where(
                    Appointment.clinic_id == cabinet.clinic_id,
                    Appointment.cabinet_id == cabinet.id,
                )
                .values(cabinet=cabinet.name)
            )

        return cabinet

    @staticmethod
    async def delete_cabinet(db: AsyncSession, cabinet: Cabinet) -> None:
        await db.delete(cabinet)
        await db.flush()


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

        count_query = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_query)).scalar() or 0

        query = query.order_by(Appointment.start_time)
        query = query.offset(offset).limit(page_size)
        result = await db.execute(query)
        return list(result.scalars().all()), total

    @staticmethod
    async def get_appointment(
        db: AsyncSession, clinic_id: UUID, appointment_id: UUID
    ) -> Appointment | None:
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
    async def validate_patient_access(db: AsyncSession, clinic_id: UUID, patient_id: UUID) -> bool:
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
        db: AsyncSession, clinic_id: UUID, professional_id: UUID
    ) -> bool:
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

        Raises ValueError with details if validation fails.
        """
        if not planned_item_ids:
            return

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
    async def _resolve_cabinet(db: AsyncSession, clinic_id: UUID, data: dict) -> None:
        """Ensure ``data`` ends up with matching cabinet_id + cabinet (name).

        Accepts either cabinet_id or cabinet; rejects both if absent.
        Mutates ``data`` in place. Raises ValueError when unresolved.
        """
        cabinet_id = data.get("cabinet_id")
        cabinet_name = data.get("cabinet")

        cab: Cabinet | None = None
        if cabinet_id:
            cab = await CabinetService.get_cabinet(db, clinic_id, cabinet_id)
            if cab is None:
                raise ValueError(f"Cabinet not found: {cabinet_id}")
        elif cabinet_name:
            cab = await CabinetService.get_by_name(db, clinic_id, cabinet_name)
            if cab is None:
                raise ValueError(f"Cabinet not found: {cabinet_name}")
        else:
            raise ValueError("Either cabinet_id or cabinet (name) is required")

        data["cabinet_id"] = cab.id
        data["cabinet"] = cab.name

    @staticmethod
    async def create_appointment(db: AsyncSession, clinic_id: UUID, data: dict) -> Appointment:
        """Create an appointment. Raises IntegrityError on slot conflict."""
        planned_item_ids = data.pop("planned_item_ids", None)

        await AppointmentService._resolve_cabinet(db, clinic_id, data)

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

        if planned_item_ids:
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

        event_bus.publish(
            EventType.APPOINTMENT_SCHEDULED,
            {
                "appointment_id": str(appointment.id),
                "clinic_id": str(appointment.clinic_id),
                "patient_id": str(appointment.patient_id) if appointment.patient_id else None,
                "professional_id": str(appointment.professional_id),
                "start_time": appointment.start_time.isoformat(),
                "end_time": appointment.end_time.isoformat(),
                "treatment_type": appointment.treatment_type,
                "cabinet": appointment.cabinet,
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
        db: AsyncSession, appointment: Appointment, data: dict
    ) -> Appointment:
        """Update an appointment."""
        old_status = appointment.status

        planned_item_ids = data.pop("planned_item_ids", None)

        # Resolve cabinet change (accepts cabinet_id or cabinet name).
        if data.get("cabinet_id") or data.get("cabinet"):
            await AppointmentService._resolve_cabinet(db, appointment.clinic_id, data)

        if planned_item_ids:
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

        if planned_item_ids is not None:
            for existing in list(appointment.treatments):
                await db.delete(existing)
            await db.flush()

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

            await db.refresh(appointment, ["treatments"])
            for treatment in appointment.treatments:
                await db.refresh(treatment, ["planned_item", "catalog_item"])
                if treatment.planned_item:
                    await db.refresh(treatment.planned_item, ["treatment", "treatment_plan"])
                    if treatment.planned_item.treatment:
                        await db.refresh(
                            treatment.planned_item.treatment, ["teeth", "catalog_item"]
                        )

        new_status = appointment.status
        if old_status != new_status:
            payload = {
                "appointment_id": str(appointment.id),
                "clinic_id": str(appointment.clinic_id),
                "patient_id": (str(appointment.patient_id) if appointment.patient_id else None),
                "professional_id": str(appointment.professional_id),
                "treatment_type": appointment.treatment_type,
                "cabinet": appointment.cabinet,
                "start_time": appointment.start_time.isoformat(),
                "end_time": appointment.end_time.isoformat(),
                "notes": appointment.notes,
            }
            if new_status == "completed":
                event_bus.publish(EventType.APPOINTMENT_COMPLETED, payload)
            elif new_status == "cancelled":
                event_bus.publish(EventType.APPOINTMENT_CANCELLED, payload)
            elif new_status == "no_show":
                event_bus.publish(EventType.APPOINTMENT_NO_SHOW, payload)
        else:
            event_bus.publish(
                EventType.APPOINTMENT_UPDATED,
                {
                    "appointment_id": str(appointment.id),
                    "clinic_id": str(appointment.clinic_id),
                    "patient_id": (str(appointment.patient_id) if appointment.patient_id else None),
                },
            )

        return appointment

    @staticmethod
    async def cancel_appointment(db: AsyncSession, appointment: Appointment) -> Appointment:
        """Cancel an appointment."""
        appointment.status = "cancelled"
        await db.flush()

        event_bus.publish(
            EventType.APPOINTMENT_CANCELLED,
            {
                "appointment_id": str(appointment.id),
                "clinic_id": str(appointment.clinic_id),
                "patient_id": (str(appointment.patient_id) if appointment.patient_id else None),
                "professional_id": str(appointment.professional_id),
                "treatment_type": appointment.treatment_type,
                "cabinet": appointment.cabinet,
                "start_time": appointment.start_time.isoformat(),
                "end_time": appointment.end_time.isoformat(),
            },
        )

        return appointment
