"""Pydantic schemas for clinical module."""
from datetime import date, datetime
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response."""

    data: list[T]
    total: int
    page: int
    page_size: int


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

    class Config:
        from_attributes = True


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
    cabinets: list

    class Config:
        from_attributes = True
