"""Pydantic schemas for clinical module.

Fase B transition:
- Patient + medical-history schemas live in ``app.modules.patients.schemas``.
- Appointment + cabinet schemas live in ``app.modules.agenda.schemas``.
- Timeline schemas live in ``app.modules.patient_timeline.schemas``.

All re-exported here for callers using the old import path. Only the
Clinic metadata schemas (ClinicUpdate, ClinicResponse, AddressUpdate)
remain implemented in this module.
"""

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

# Re-export timeline schemas for legacy imports.
from app.modules.patient_timeline.schemas import (  # noqa: F401
    TimelineEntry,
    TimelineResponse,
)

# Re-export patient schemas for legacy imports.
from app.modules.patients.schemas import (  # noqa: F401
    BillingAddress,
    PatientAddress,
    PatientBrief,
    PatientCreate,
    PatientExtendedResponse,
    PatientExtendedUpdate,
    PatientResponse,
    PatientUpdate,
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


# Timeline schemas live in ``app.modules.patient_timeline.schemas``
# and are re-exported at the top of this module.
