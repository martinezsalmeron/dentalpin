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

        # Get catalog info from planned_item's relationships if direct catalog_item not set
        if not catalog_item and planned_item:
            if planned_item.catalog_item:
                catalog_item = planned_item.catalog_item
            elif planned_item.tooth_treatment and planned_item.tooth_treatment.catalog_item:
                catalog_item = planned_item.tooth_treatment.catalog_item

        # Get tooth info from planned_item
        tooth_number = None
        surfaces = None
        if planned_item and planned_item.tooth_treatment:
            tooth_number = planned_item.tooth_treatment.tooth_number
            surfaces = planned_item.tooth_treatment.surfaces

        return cls(
            id=apt_treatment.id,
            planned_item_id=apt_treatment.planned_treatment_item_id,
            planned_item_status=planned_item.status if planned_item else "pending",
            catalog_item_id=catalog_item.id if catalog_item else None,
            internal_code=catalog_item.internal_code if catalog_item else "",
            names=catalog_item.names if catalog_item else {},
            default_price=float(catalog_item.default_price)
            if catalog_item and catalog_item.default_price
            else None,
            default_duration_minutes=catalog_item.default_duration_minutes
            if catalog_item
            else None,
            tooth_number=tooth_number,
            surfaces=surfaces,
            is_global=planned_item.is_global if planned_item else False,
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


# Address schema (for patient demographics)
class PatientAddress(BaseModel):
    """Schema for patient address."""

    street: str | None = None
    city: str | None = None
    postal_code: str | None = None
    province: str | None = None
    country: str = "ES"


# Emergency contact schema
class EmergencyContact(BaseModel):
    """Schema for emergency contact."""

    name: str = Field(min_length=1, max_length=100)
    relationship: str | None = Field(default=None, max_length=50)
    phone: str = Field(min_length=1, max_length=20)
    email: EmailStr | None = None
    is_legal_guardian: bool = False


# Legal guardian schema (for minors)
class LegalGuardian(BaseModel):
    """Schema for legal guardian of minor patients."""

    name: str = Field(min_length=1, max_length=100)
    relationship: str = Field(max_length=50)  # parent, grandparent, legal_tutor, other
    dni: str | None = Field(default=None, max_length=20)
    phone: str = Field(min_length=1, max_length=20)
    email: EmailStr | None = None
    address: str | None = Field(default=None, max_length=200)
    notes: str | None = None


# Medical history schemas
class AllergyEntry(BaseModel):
    """Schema for allergy entry in medical history."""

    name: str = Field(min_length=1, max_length=100)
    type: str | None = Field(default=None, max_length=50)  # drug, food, material, environmental
    severity: str = Field(default="medium", max_length=20)  # low, medium, high, critical
    reaction: str | None = Field(default=None, max_length=500)
    notes: str | None = None


class MedicationEntry(BaseModel):
    """Schema for current medication entry."""

    name: str = Field(min_length=1, max_length=100)
    dosage: str | None = Field(default=None, max_length=100)
    frequency: str | None = Field(default=None, max_length=100)
    start_date: date | None = None
    notes: str | None = None


class SystemicDiseaseEntry(BaseModel):
    """Schema for systemic disease entry."""

    name: str = Field(min_length=1, max_length=100)
    type: str | None = Field(
        default=None, max_length=50
    )  # cardiovascular, respiratory, endocrine, etc.
    diagnosis_date: date | None = None
    is_controlled: bool = True
    is_critical: bool = False  # Triggers alert display
    medications: str | None = None
    notes: str | None = None


class SurgicalHistoryEntry(BaseModel):
    """Schema for surgical history entry."""

    procedure: str = Field(min_length=1, max_length=200)
    surgery_date: date | None = None
    complications: str | None = None
    notes: str | None = None


class MedicalHistoryData(BaseModel):
    """Full medical history schema."""

    # Lists
    allergies: list[AllergyEntry] = []
    medications: list[MedicationEntry] = []
    systemic_diseases: list[SystemicDiseaseEntry] = []
    surgical_history: list[SurgicalHistoryEntry] = []

    # Special conditions (pregnancy, lactation)
    is_pregnant: bool = False
    pregnancy_week: int | None = Field(default=None, ge=1, le=42)
    is_lactating: bool = False

    # Anticoagulants
    is_on_anticoagulants: bool = False
    anticoagulant_medication: str | None = Field(default=None, max_length=100)
    inr_value: float | None = Field(default=None, ge=0, le=20)
    last_inr_date: date | None = None

    # Lifestyle
    is_smoker: bool = False
    smoking_frequency: str | None = Field(default=None, max_length=100)  # packs/day
    alcohol_consumption: str | None = Field(
        default=None, max_length=100
    )  # none, occasional, moderate, heavy

    # Dental specific
    bruxism: bool = False

    # Anesthesia
    adverse_reactions_to_anesthesia: bool = False
    anesthesia_reaction_details: str | None = Field(default=None, max_length=500)

    # Metadata
    last_updated_at: datetime | None = None
    last_updated_by: UUID | None = None


class MedicalHistoryUpdate(MedicalHistoryData):
    """Schema for updating medical history."""

    pass


class MedicalHistoryResponse(MedicalHistoryData):
    """Schema for medical history response."""

    pass


# Patient alerts
class PatientAlert(BaseModel):
    """Schema for patient alert."""

    type: str  # allergy, pregnancy, lactating, anticoagulant, anesthesia_reaction, systemic_disease
    severity: str  # low, medium, high, critical
    title: str
    details: str | None = None


class PatientAlertsResponse(BaseModel):
    """Schema for patient alerts response."""

    alerts: list[PatientAlert]


# Extended patient response with new fields
class PatientExtendedResponse(PatientResponse):
    """Extended patient response with all new fields."""

    # Extended demographics
    gender: str | None = None
    national_id: str | None = None
    national_id_type: str | None = None
    profession: str | None = None
    workplace: str | None = None
    preferred_language: str = "es"
    address: PatientAddress | None = None
    photo_url: str | None = None

    # Emergency contact
    emergency_contact: EmergencyContact | None = None

    # Legal guardian (for minors)
    legal_guardian: LegalGuardian | None = None

    # Computed alerts
    active_alerts: list[PatientAlert] = []


class PatientExtendedUpdate(PatientUpdate):
    """Schema for updating patient with extended fields."""

    # Extended demographics
    gender: str | None = Field(default=None, max_length=20)
    national_id: str | None = Field(default=None, max_length=50)
    national_id_type: str | None = Field(default=None, max_length=20)
    profession: str | None = Field(default=None, max_length=100)
    workplace: str | None = Field(default=None, max_length=200)
    preferred_language: str | None = Field(default=None, max_length=10)
    address: PatientAddress | None = None
    photo_url: str | None = Field(default=None, max_length=500)

    # Emergency contact
    emergency_contact: EmergencyContact | None = None

    # Legal guardian (for minors)
    legal_guardian: LegalGuardian | None = None


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
