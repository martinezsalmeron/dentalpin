"""Pydantic schemas for clinical module."""

from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, model_validator


# Billing address schema
class BillingAddress(BaseModel):
    """Schema for billing address."""

    street: str | None = None
    city: str | None = None
    postal_code: str | None = None
    province: str | None = None
    country: str = "ES"


# Patient schemas
class PatientCreate(BaseModel):
    """Schema for creating a patient."""

    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    phone: str | None = Field(default=None, max_length=20)
    email: EmailStr | None = None
    date_of_birth: date | None = None
    notes: str | None = None
    # Billing fields
    billing_name: str | None = Field(default=None, max_length=200)
    billing_tax_id: str | None = Field(default=None, max_length=50)
    billing_address: BillingAddress | None = None
    billing_email: EmailStr | None = None


class PatientUpdate(BaseModel):
    """Schema for updating a patient."""

    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    phone: str | None = Field(default=None, max_length=20)
    email: EmailStr | None = None
    date_of_birth: date | None = None
    notes: str | None = None
    status: str | None = None
    # Billing fields
    billing_name: str | None = Field(default=None, max_length=200)
    billing_tax_id: str | None = Field(default=None, max_length=50)
    billing_address: BillingAddress | None = None
    billing_email: EmailStr | None = None


class PatientResponse(BaseModel):
    """Schema for patient response."""

    id: UUID
    clinic_id: UUID
    first_name: str
    last_name: str
    phone: str | None
    email: str | None
    date_of_birth: date | None
    notes: str | None
    status: str
    # Billing fields
    billing_name: str | None
    billing_tax_id: str | None
    billing_address: dict | None
    billing_email: str | None
    has_complete_billing_info: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PatientBrief(BaseModel):
    """Brief patient info for lists and references."""

    id: UUID
    first_name: str
    last_name: str
    phone: str | None
    email: str | None

    class Config:
        from_attributes = True


class ProfessionalBrief(BaseModel):
    """Brief professional info for appointment references."""

    id: UUID
    first_name: str
    last_name: str

    class Config:
        from_attributes = True


# Treatment brief for appointment responses
class AppointmentTreatmentBrief(BaseModel):
    """Brief treatment info for appointment responses."""

    id: UUID
    catalog_item_id: UUID
    internal_code: str
    names: dict[str, str]
    default_price: float | None = None
    default_duration_minutes: int | None = None

    @classmethod
    def from_appointment_treatment(cls, apt_treatment: "Any") -> "AppointmentTreatmentBrief":
        """Create from AppointmentTreatment model with catalog_item loaded."""
        catalog_item = apt_treatment.catalog_item
        return cls(
            id=apt_treatment.id,
            catalog_item_id=apt_treatment.catalog_item_id,
            internal_code=catalog_item.internal_code if catalog_item else "",
            names=catalog_item.names if catalog_item else {},
            default_price=float(catalog_item.default_price)
            if catalog_item and catalog_item.default_price
            else None,
            default_duration_minutes=catalog_item.default_duration_minutes
            if catalog_item
            else None,
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
    treatment_ids: list[UUID] | None = None  # New: list of catalog item IDs
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
    treatment_ids: list[UUID] | None = None  # New: list of catalog item IDs
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
            if treatments_raw:
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
                    "treatments": [
                        AppointmentTreatmentBrief.from_appointment_treatment(t)
                        for t in treatments_raw
                    ],
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
