"""Pydantic schemas for clinical module.

Fase B transition:
- Patient + medical-history schemas live in ``app.modules.patients.schemas``.
- Appointment + cabinet schemas live in ``app.modules.agenda.schemas``.
- Both are re-exported here for callers using the old import path.

Clinic + Timeline schemas still live in this module.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

# Re-export agenda schemas for legacy imports.
from app.modules.agenda.schemas import (  # noqa: F401
    AppointmentCreate,
    AppointmentResponse,
    AppointmentTreatmentBrief,
    AppointmentUpdate,
    CabinetBase,
    CabinetCreate,
    CabinetResponse,
    CabinetUpdate,
    ProfessionalBrief,
)

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

# --- Clinic metadata ----------------------------------------------------


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


# --- Timeline schemas --------------------------------------------------


class TimelineEntry(BaseModel):
    """Schema for timeline entry."""

    id: UUID
    event_type: str
    event_category: str
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
