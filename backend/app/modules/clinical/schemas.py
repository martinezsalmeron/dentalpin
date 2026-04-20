"""Pydantic schemas for clinical module.

Patient + medical-history schemas live in
``app.modules.patients.schemas`` after Fase B.1 chunk 2. They are
re-exported here for callers that still import them via the old path.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, model_validator

# Re-export patient schemas for legacy imports.
from app.modules.patients.schemas import (  # noqa: F401
    AllergyEntry,
    BillingAddress,
    EmergencyContact,
    LegalGuardian,
    MedicalHistoryData,
    MedicalHistoryResponse,
    MedicalHistoryUpdate,
    MedicationEntry,
    PatientAddress,
    PatientAlert,
    PatientAlertsResponse,
    PatientBrief,
    PatientCreate,
    PatientExtendedResponse,
    PatientExtendedUpdate,
    PatientResponse,
    PatientUpdate,
    SurgicalHistoryEntry,
    SystemicDiseaseEntry,
)


class ProfessionalBrief(BaseModel):
    """Brief professional info for appointment references."""

    id: UUID
    first_name: str
    last_name: str

    class Config:
        from_attributes = True


# Treatment brief for appointment responses
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
        """Create from AppointmentTreatment model with planned_item and catalog_item loaded."""
        planned_item = apt_treatment.planned_item
        catalog_item = apt_treatment.catalog_item

        treatment = planned_item.treatment if planned_item else None

        # Resolve catalog item through Treatment if not set directly.
        if not catalog_item and treatment:
            catalog_item = treatment.catalog_item

        # Tooth info from first member of the Treatment (primary tooth).
        tooth_number = None
        surfaces = None
        is_global = True
        if treatment and treatment.teeth:
            primary = treatment.teeth[0]
            tooth_number = primary.tooth_number
            surfaces = primary.surfaces
            is_global = False

        # Prefer the frozen price snapshot when available, fall back to catalog default.
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


# Appointment schemas
class AppointmentCreate(BaseModel):
    """Schema for creating an appointment."""

    patient_id: UUID | None = None
    professional_id: UUID
    cabinet: str = Field(min_length=1, max_length=50)
    start_time: datetime
    end_time: datetime
    treatment_type: str | None = Field(default=None, max_length=100)  # Legacy field
    planned_item_ids: list[UUID] | None = None  # List of PlannedTreatmentItem IDs
    notes: str | None = None
    color: str | None = Field(default=None, max_length=7)


class AppointmentUpdate(BaseModel):
    """Schema for updating an appointment."""

    patient_id: UUID | None = None
    professional_id: UUID | None = None
    cabinet: str | None = Field(default=None, min_length=1, max_length=50)
    start_time: datetime | None = None
    end_time: datetime | None = None
    treatment_type: str | None = Field(default=None, max_length=100)  # Legacy field
    planned_item_ids: list[UUID] | None = None  # List of PlannedTreatmentItem IDs
    status: str | None = None
    notes: str | None = None
    color: str | None = Field(default=None, max_length=7)


class AppointmentResponse(BaseModel):
    """Schema for appointment response."""

    id: UUID
    clinic_id: UUID
    patient_id: UUID | None
    professional_id: UUID
    cabinet: str
    start_time: datetime
    end_time: datetime
    treatment_type: str | None  # Legacy field
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
        # Handle ORM model
        if hasattr(data, "treatments"):
            treatments_raw = data.treatments
            treatments_list = []
            if treatments_raw:
                for t in treatments_raw:
                    # Only include treatments with valid planned_item
                    if t.planned_treatment_item_id:
                        treatments_list.append(
                            AppointmentTreatmentBrief.from_appointment_treatment(t)
                        )
            data_dict = {
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
            return data_dict
        return data

    class Config:
        from_attributes = True


# Clinic update schemas
class AddressUpdate(BaseModel):
    """Schema for address fields."""

    street: str | None = Field(default=None, max_length=200)
    city: str | None = Field(default=None, max_length=100)
    postal_code: str | None = Field(default=None, max_length=20)
    country: str | None = Field(default=None, max_length=100)


class ClinicUpdate(BaseModel):
    """Schema for updating clinic info."""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    tax_id: str | None = Field(default=None, max_length=20)
    address: AddressUpdate | None = None
    phone: str | None = Field(default=None, max_length=20)
    email: EmailStr | None = None


# Cabinet schemas
class CabinetBase(BaseModel):
    """Base schema for cabinet."""

    name: str = Field(min_length=1, max_length=50)
    color: str = Field(min_length=4, max_length=7, pattern=r"^#[0-9A-Fa-f]{3,6}$")


class CabinetCreate(CabinetBase):
    """Schema for creating a cabinet."""

    pass


class CabinetUpdate(BaseModel):
    """Schema for updating a cabinet."""

    name: str | None = Field(default=None, min_length=1, max_length=50)
    color: str | None = Field(
        default=None, min_length=4, max_length=7, pattern=r"^#[0-9A-Fa-f]{3,6}$"
    )


class CabinetResponse(CabinetBase):
    """Schema for cabinet response."""

    pass


# Clinic schemas
class ClinicResponse(BaseModel):
    """Schema for clinic response."""

    id: UUID
    name: str
    tax_id: str
    address: dict | None
    phone: str | None
    email: str | None
    settings: dict
    cabinets: list[CabinetResponse]

    class Config:
        from_attributes = True


# Patient demographic / medical schemas now live in
# ``app.modules.patients.schemas`` and are re-exported at the top of
# this file for callers using the old import path.


# PatientAlert, PatientAlertsResponse, PatientExtendedResponse and
# PatientExtendedUpdate live in app.modules.patients.schemas and are
# re-exported at the top of this file.


# Timeline schemas
class TimelineEntry(BaseModel):
    """Schema for timeline entry."""

    id: UUID
    event_type: str
    event_category: str  # visit, treatment, financial, communication, medical
    source_table: str
    source_id: UUID
    title: str
    description: str | None = None
    event_data: dict | None = None
    occurred_at: datetime
    created_by: UUID | None = None

    class Config:
        from_attributes = True


class TimelineResponse(BaseModel):
    """Paginated timeline response."""

    entries: list[TimelineEntry]
    total: int
    page: int
    page_size: int
    has_more: bool
