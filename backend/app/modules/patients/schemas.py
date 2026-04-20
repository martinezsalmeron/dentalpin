"""Pydantic schemas for the patients module.

Moved from ``app.modules.clinical.schemas`` in Fase B.1 chunk 2. The
appointment- and timeline-related schemas stay in clinical for now.
"""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

# --- Billing -------------------------------------------------------------


class BillingAddress(BaseModel):
    street: str | None = None
    city: str | None = None
    postal_code: str | None = None
    province: str | None = None
    country: str = "ES"


# --- Patient CRUD --------------------------------------------------------


class PatientCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    phone: str | None = Field(default=None, max_length=20)
    email: EmailStr | None = None
    date_of_birth: date | None = None
    notes: str | None = None
    billing_name: str | None = Field(default=None, max_length=200)
    billing_tax_id: str | None = Field(default=None, max_length=50)
    billing_address: BillingAddress | None = None
    billing_email: EmailStr | None = None


class PatientUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    phone: str | None = Field(default=None, max_length=20)
    email: EmailStr | None = None
    date_of_birth: date | None = None
    notes: str | None = None
    status: str | None = None
    billing_name: str | None = Field(default=None, max_length=200)
    billing_tax_id: str | None = Field(default=None, max_length=50)
    billing_address: BillingAddress | None = None
    billing_email: EmailStr | None = None


class PatientResponse(BaseModel):
    id: UUID
    clinic_id: UUID
    first_name: str
    last_name: str
    phone: str | None
    email: str | None
    date_of_birth: date | None
    notes: str | None
    status: str
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
    """Brief patient info for lists and references across modules."""

    id: UUID
    first_name: str
    last_name: str
    phone: str | None
    email: str | None

    class Config:
        from_attributes = True


# --- Extended demographics ----------------------------------------------


class PatientAddress(BaseModel):
    street: str | None = None
    city: str | None = None
    postal_code: str | None = None
    province: str | None = None
    country: str = "ES"


class EmergencyContact(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    relationship: str | None = Field(default=None, max_length=50)
    phone: str = Field(min_length=1, max_length=20)
    email: EmailStr | None = None
    is_legal_guardian: bool = False


class LegalGuardian(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    relationship: str = Field(max_length=50)
    dni: str | None = Field(default=None, max_length=20)
    phone: str = Field(min_length=1, max_length=20)
    email: EmailStr | None = None
    address: str | None = Field(default=None, max_length=200)
    notes: str | None = None


# --- Medical history (JSONB shape — normalizes in B.4) -------------------


class AllergyEntry(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    type: str | None = Field(default=None, max_length=50)
    severity: str = Field(default="medium", max_length=20)
    reaction: str | None = Field(default=None, max_length=500)
    notes: str | None = None


class MedicationEntry(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    dosage: str | None = Field(default=None, max_length=100)
    frequency: str | None = Field(default=None, max_length=100)
    start_date: date | None = None
    notes: str | None = None


class SystemicDiseaseEntry(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    type: str | None = Field(default=None, max_length=50)
    diagnosis_date: date | None = None
    is_controlled: bool = True
    is_critical: bool = False
    medications: str | None = None
    notes: str | None = None


class SurgicalHistoryEntry(BaseModel):
    procedure: str = Field(min_length=1, max_length=200)
    surgery_date: date | None = None
    complications: str | None = None
    notes: str | None = None


class MedicalHistoryData(BaseModel):
    allergies: list[AllergyEntry] = []
    medications: list[MedicationEntry] = []
    systemic_diseases: list[SystemicDiseaseEntry] = []
    surgical_history: list[SurgicalHistoryEntry] = []

    is_pregnant: bool = False
    pregnancy_week: int | None = Field(default=None, ge=1, le=42)
    is_lactating: bool = False

    is_on_anticoagulants: bool = False
    anticoagulant_medication: str | None = Field(default=None, max_length=100)
    inr_value: float | None = Field(default=None, ge=0, le=20)
    last_inr_date: date | None = None

    is_smoker: bool = False
    smoking_frequency: str | None = Field(default=None, max_length=100)
    alcohol_consumption: str | None = Field(default=None, max_length=100)

    bruxism: bool = False

    adverse_reactions_to_anesthesia: bool = False
    anesthesia_reaction_details: str | None = Field(default=None, max_length=500)

    last_updated_at: datetime | None = None
    last_updated_by: UUID | None = None


class MedicalHistoryUpdate(MedicalHistoryData):
    pass


class MedicalHistoryResponse(MedicalHistoryData):
    pass


# --- Alerts --------------------------------------------------------------


class PatientAlert(BaseModel):
    type: str
    severity: str
    title: str
    details: str | None = None


class PatientAlertsResponse(BaseModel):
    alerts: list[PatientAlert]


# --- Extended response / update -----------------------------------------


class PatientExtendedResponse(PatientResponse):
    gender: str | None = None
    national_id: str | None = None
    national_id_type: str | None = None
    profession: str | None = None
    workplace: str | None = None
    preferred_language: str = "es"
    address: PatientAddress | None = None
    photo_url: str | None = None

    emergency_contact: EmergencyContact | None = None
    legal_guardian: LegalGuardian | None = None
    active_alerts: list[PatientAlert] = []


class PatientExtendedUpdate(PatientUpdate):
    gender: str | None = Field(default=None, max_length=20)
    national_id: str | None = Field(default=None, max_length=50)
    national_id_type: str | None = Field(default=None, max_length=20)
    profession: str | None = Field(default=None, max_length=100)
    workplace: str | None = Field(default=None, max_length=200)
    preferred_language: str | None = Field(default=None, max_length=10)
    address: PatientAddress | None = None
    photo_url: str | None = Field(default=None, max_length=500)

    emergency_contact: EmergencyContact | None = None
    legal_guardian: LegalGuardian | None = None
