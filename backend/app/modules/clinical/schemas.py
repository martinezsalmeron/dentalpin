"""Pydantic schemas for clinical module."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# Patient schemas
class PatientCreate(BaseModel):
    """Schema for creating a patient."""

    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    phone: str | None = Field(default=None, max_length=20)
    email: EmailStr | None = None
    date_of_birth: date | None = None
    notes: str | None = None


class PatientUpdate(BaseModel):
    """Schema for updating a patient."""

    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    phone: str | None = Field(default=None, max_length=20)
    email: EmailStr | None = None
    date_of_birth: date | None = None
    notes: str | None = None
    status: str | None = None


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

    class Config:
        from_attributes = True


class ProfessionalBrief(BaseModel):
    """Brief professional info for appointment references."""

    id: UUID
    first_name: str
    last_name: str

    class Config:
        from_attributes = True


# Appointment schemas
class AppointmentCreate(BaseModel):
    """Schema for creating an appointment."""

    patient_id: UUID | None = None
    professional_id: UUID
    cabinet: str = Field(min_length=1, max_length=50)
    start_time: datetime
    end_time: datetime
    treatment_type: str | None = Field(default=None, max_length=100)
    notes: str | None = None
    color: str | None = Field(default=None, max_length=7)


class AppointmentUpdate(BaseModel):
    """Schema for updating an appointment."""

    patient_id: UUID | None = None
    professional_id: UUID | None = None
    cabinet: str | None = Field(default=None, min_length=1, max_length=50)
    start_time: datetime | None = None
    end_time: datetime | None = None
    treatment_type: str | None = Field(default=None, max_length=100)
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
    treatment_type: str | None
    status: str
    notes: str | None
    color: str | None
    created_at: datetime
    updated_at: datetime
    patient: PatientBrief | None = None
    professional: ProfessionalBrief | None = None

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
