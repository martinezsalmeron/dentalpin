"""Pydantic schemas for the Verifactu admin API."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class VerifactuSettingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    clinic_id: UUID
    enabled: bool
    environment: str
    nif_emisor: str | None = None
    nombre_razon_emisor: str | None = None
    numero_instalacion: str
    last_huella: str | None
    next_send_after: datetime | None
    last_aeat_response_at: datetime | None
    has_active_certificate: bool = False
    producer_nif: str | None = None
    producer_name: str | None = None
    producer_id_sistema: str = "DP"
    producer_version: str | None = None
    declaracion_responsable_signed_at: datetime | None = None
    declaracion_responsable_signed_by: UUID | None = None


class VerifactuSettingsUpdate(BaseModel):
    enabled: bool | None = None
    environment: str | None = Field(default=None, pattern=r"^(test|prod)$")


class ProducerInfoUpdate(BaseModel):
    """Payload for the SIF producer wizard."""

    producer_nif: str = Field(min_length=8, max_length=20)
    producer_name: str = Field(min_length=2, max_length=200)
    producer_id_sistema: str = Field(default="DP", min_length=1, max_length=2)
    producer_version: str = Field(min_length=1, max_length=20)
    sign_declaracion: bool = Field(
        description=(
            "El usuario confirma que firma la declaración responsable como "
            "productor del SIF (RD 1007/2023 art. 13)."
        )
    )


class ProducerDefaultsResponse(BaseModel):
    """Env-var-driven defaults shown by the wizard before saving."""

    name: str
    nif: str
    id_sistema: str
    version: str


class VerifactuCertificateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    clinic_id: UUID
    subject_cn: str | None
    issuer_cn: str | None
    nif_titular: str | None
    valid_from: datetime | None
    valid_until: datetime | None
    is_active: bool
    uploaded_by: UUID | None
    created_at: datetime


class VerifactuRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    clinic_id: UUID
    invoice_id: UUID
    record_type: str
    tipo_factura: str
    tipo_rectificativa: str | None
    serie_numero: str
    fecha_expedicion: date
    cuota_total: Decimal
    importe_total: Decimal
    huella: str
    huella_anterior: str | None
    is_first_record: bool
    state: str
    aeat_csv: str | None
    aeat_estado_envio: str | None
    aeat_estado_registro: str | None
    aeat_codigo_error: int | None
    aeat_descripcion_error: str | None
    aeat_timestamp_presentacion: datetime | None
    subsanacion: bool
    submission_attempt: int
    last_attempt_at: datetime | None
    created_at: datetime


class VerifactuRecordDetailResponse(VerifactuRecordResponse):
    xml_payload: str | None
    aeat_response_xml: str | None


class VerifactuQueueItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    invoice_id: UUID
    serie_numero: str
    importe_total: Decimal
    state: str
    aeat_codigo_error: int | None
    aeat_descripcion_error: str | None
    submission_attempt: int
    last_attempt_at: datetime | None


class VerifactuHealthResponse(BaseModel):
    enabled: bool
    environment: str | None
    has_certificate: bool
    certificate_valid_until: datetime | None
    last_aeat_response_at: datetime | None
    next_send_after: datetime | None
    pending_count: int
    rejected_count: int


class VatClassificationItem(BaseModel):
    """One row in the AEAT VAT classification panel.

    Combines catalog data (``vat_type_id``, label, rate) with the
    optional Verifactu override and the heuristic-derived default so
    the UI can display "Auto: N1 → override: E1" affordances.
    """

    vat_type_id: UUID
    label: str
    rate: Decimal
    is_default: bool
    inferred_classification: str
    inferred_exemption_cause: str | None = None
    override_classification: str | None = None
    override_exemption_cause: str | None = None
    override_notes: str | None = None


class VatClassificationListResponse(BaseModel):
    items: list[VatClassificationItem]


class VatClassificationUpdate(BaseModel):
    """Payload to set/clear an override.

    A ``classification=null`` body clears the override (DELETE-equivalent
    via PUT, kept for ergonomics). Otherwise the value must be one of
    the AEAT codes ``S1, S2, E1, E2, E3, E4, E5, E6, N1, N2``.
    """

    classification: str | None = Field(
        default=None,
        pattern=r"^(S1|S2|E1|E2|E3|E4|E5|E6|N1|N2)$",
    )
    exemption_cause: str | None = Field(default=None, pattern=r"^E[1-6]$")
    notes: str | None = Field(default=None, max_length=500)


class CertificateUploadResponse(BaseModel):
    """Returned after a successful PFX upload."""

    id: UUID
    subject_cn: str | None
    issuer_cn: str | None
    nif_titular: str | None
    valid_from: datetime
    valid_until: datetime
    is_active: bool
