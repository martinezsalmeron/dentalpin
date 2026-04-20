"""Pydantic schemas for the agenda module.

Moved from ``app.modules.clinical.schemas`` in Fase B.2 chunk 1.
Patient-related schemas come from ``app.modules.patients.schemas``.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.modules.patients.schemas import PatientBrief

# --- Professional brief -------------------------------------------------


class ProfessionalBrief(BaseModel):
    """Brief professional info for appointment references."""

    id: UUID
    first_name: str
    last_name: str

    class Config:
        from_attributes = True


# --- Treatment brief ----------------------------------------------------


class AppointmentTreatmentBrief(BaseModel):
    """Brief treatment info for appointment responses.

    Includes data from the planned treatment item and its catalog item.
    """

    id: UUID
    planned_item_id: UUID
    planned_item_status: str  # pending, completed, cancelled
    catalog_item_id: UUID | None = None
    internal_code: str
    names: dict[str, str]
    default_price: float | None = None
    default_duration_minutes: int | None = None
    # Dental context from planned item
    tooth_number: int | None = None
    surfaces: list[str] | None = None
    is_global: bool = False
    # Plan info
    plan_id: UUID | None = None
    plan_number: str | None = None
    # Completion tracking
    completed_in_appointment: bool = False

    @classmethod
    def from_appointment_treatment(cls, apt_treatment: "Any") -> "AppointmentTreatmentBrief":
        """Create from AppointmentTreatment with planned_item + catalog_item loaded."""
        planned_item = apt_treatment.planned_item
        catalog_item = apt_treatment.catalog_item

        treatment = planned_item.treatment if planned_item else None

        if not catalog_item and treatment:
            catalog_item = treatment.catalog_item

        tooth_number = None
        surfaces = None
        is_global = True
        if treatment and treatment.teeth:
            primary = treatment.teeth[0]
            tooth_number = primary.tooth_number
            surfaces = primary.surfaces
            is_global = False

        price: float | None = None
        if treatment and treatment.price_snapshot is not None:
            price = float(treatment.price_snapshot)
        elif catalog_item and catalog_item.default_price is not None:
            price = float(catalog_item.default_price)

        return cls(
            id=apt_treatment.id,
            planned_item_id=apt_treatment.planned_treatment_item_id,
            planned_item_status=planned_item.status if planned_item else "pending",
            catalog_item_id=catalog_item.id if catalog_item else None,
            internal_code=catalog_item.internal_code if catalog_item else "",
            names=catalog_item.names if catalog_item else {},
            default_price=price,
            default_duration_minutes=catalog_item.default_duration_minutes
            if catalog_item
            else None,
            tooth_number=tooth_number,
            surfaces=surfaces,
            is_global=is_global,
            plan_id=planned_item.treatment_plan_id if planned_item else None,
            plan_number=planned_item.treatment_plan.plan_number
            if planned_item and planned_item.treatment_plan
            else None,
            completed_in_appointment=apt_treatment.completed_in_appointment,
        )


# --- Appointment CRUD ---------------------------------------------------


class AppointmentCreate(BaseModel):
    patient_id: UUID | None = None
    professional_id: UUID
    cabinet: str = Field(min_length=1, max_length=50)
    start_time: datetime
    end_time: datetime
    treatment_type: str | None = Field(default=None, max_length=100)  # Legacy field
    planned_item_ids: list[UUID] | None = None
    notes: str | None = None
    color: str | None = Field(default=None, max_length=7)


class AppointmentUpdate(BaseModel):
    patient_id: UUID | None = None
    professional_id: UUID | None = None
    cabinet: str | None = Field(default=None, min_length=1, max_length=50)
    start_time: datetime | None = None
    end_time: datetime | None = None
    treatment_type: str | None = Field(default=None, max_length=100)
    planned_item_ids: list[UUID] | None = None
    status: str | None = None
    notes: str | None = None
    color: str | None = Field(default=None, max_length=7)


class AppointmentResponse(BaseModel):
    id: UUID
    clinic_id: UUID
    patient_id: UUID | None
    professional_id: UUID
    cabinet: str
    start_time: datetime
    end_time: datetime
    treatment_type: str | None
    status: str
    notes: str | None
    color: str | None
    created_at: datetime
    updated_at: datetime
    patient: PatientBrief | None = None
    professional: ProfessionalBrief | None = None
    treatments: list[AppointmentTreatmentBrief] = []

    @model_validator(mode="before")
    @classmethod
    def convert_treatments(cls, data: Any) -> Any:
        """Convert AppointmentTreatment models to AppointmentTreatmentBrief."""
        if hasattr(data, "treatments"):
            treatments_raw = data.treatments
            treatments_list = []
            if treatments_raw:
                for t in treatments_raw:
                    if t.planned_treatment_item_id:
                        treatments_list.append(
                            AppointmentTreatmentBrief.from_appointment_treatment(t)
                        )
            return {
                "id": data.id,
                "clinic_id": data.clinic_id,
                "patient_id": data.patient_id,
                "professional_id": data.professional_id,
                "cabinet": data.cabinet,
                "start_time": data.start_time,
                "end_time": data.end_time,
                "treatment_type": data.treatment_type,
                "status": data.status,
                "notes": data.notes,
                "color": data.color,
                "created_at": data.created_at,
                "updated_at": data.updated_at,
                "patient": data.patient,
                "professional": data.professional,
                "treatments": treatments_list,
            }
        return data

    class Config:
        from_attributes = True


# --- Cabinets (JSONB for now; B.2 chunk 3 normalizes) ------------------


class CabinetBase(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    color: str = Field(min_length=4, max_length=7, pattern=r"^#[0-9A-Fa-f]{3,6}$")


class CabinetCreate(CabinetBase):
    pass


class CabinetUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=50)
    color: str | None = Field(
        default=None, min_length=4, max_length=7, pattern=r"^#[0-9A-Fa-f]{3,6}$"
    )


class CabinetResponse(CabinetBase):
    pass
