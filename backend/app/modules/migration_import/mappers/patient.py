"""Map ``patient`` → :class:`patients.Patient`.

Field mapping from `CanonicalPatient` (DPMF v0.1):

| DPMF                                | DentalPin                                |
|-------------------------------------|------------------------------------------|
| given_name                          | first_name (required)                    |
| family_name                         | last_name  (required)                    |
| national_id                         | national_id                              |
| date_of_birth                       | date_of_birth                            |
| sex                                 | gender (mapped)                          |
| patient_number / registered_at      | notes prefix (no dedicated columns)      |
| gdpr_consent (``AceptaLOPD``)       | ``do_not_contact = not gdpr_consent``    |
| deceased / deactivated_at           | ``status='archived'``                    |
| default client (via ``IdCliDefec``) | billing_name / billing_tax_id (fallback) |
| phone / mobile_phone / fax          | ``phone`` (mobile preferred)             |
| email                               | ``email`` (patient wins, client fallback)|
| address_street / address_postal_code| ``address`` (JSONB ``{street, postal}``) |
| sms_consent                         | augments ``do_not_contact`` when false   |
| tenant_label                        | _ignored_ — DentalPin's clinic_id wins   |

Patient-level contact data shipped from dental-bridge ``0.0.3``+; pre-0.0.3
DPMFs only carried client-level email, so old files still import (the
missing fields silently no-op) but won't have phone or address.

Unmapped DPMF fields (default_center_uuid, default_professional_uuid,
guardian_client_uuid, referrer_patient_uuid) survive in
``raw_source_data`` for later passes — querying that table is the
forward-compat escape hatch.
"""

from __future__ import annotations

import json
import logging
from datetime import date
from typing import Any
from uuid import UUID

from app.modules.patients.service import PatientService

from .base import MapperContext
from .patient_alert import PatientAlertMapper

logger = logging.getLogger(__name__)

_SEX_MAP: dict[str, str] = {
    "male": "male",
    "female": "female",
    "other": "other",
    "unknown": "prefer_not_say",
}


def _normalize_id(value: Any) -> str | None:
    if value is None:
        return None
    s = str(value).strip()
    return s or None


class PatientMapper:
    def __init__(self) -> None:
        # Reuse the alert pipeline across patients so the
        # ``_context_cache`` inside it amortises the
        # ``MedicalContext`` upsert. Created lazily — clinics whose
        # source has no ``Pacientes.Notas`` content pay nothing.
        self._alert_pipeline: PatientAlertMapper | None = None
        # ``client.source_id`` → parsed payload, scoped per job_id.
        # ``client`` rows are processed after patients in the topo
        # order (FALLBACK_MAPPER writes RawEntity) but we need their
        # contact + billing data when materialising each Patient. Lazy
        # one-pass scan over ``ctx.handle.entity_iter('client')``.
        self._loaded_job_id: UUID | None = None
        self._clients_by_source_id: dict[str, dict[str, Any]] = {}

    def _ensure_clients_loaded(self, ctx: MapperContext) -> None:
        if self._loaded_job_id == ctx.job_id:
            return
        self._clients_by_source_id = {}
        if ctx.handle is None:
            self._loaded_job_id = ctx.job_id
            return
        try:
            counts = ctx.handle.entity_counts()
            if "client" not in counts:
                self._loaded_job_id = ctx.job_id
                return
            for row in ctx.handle.entity_iter("client"):
                _, src_id, _, payload_json, _, _ = row
                try:
                    payload = (
                        json.loads(payload_json) if isinstance(payload_json, str) else payload_json
                    )
                except (TypeError, ValueError):
                    continue
                sid = _normalize_id(src_id)
                if sid and isinstance(payload, dict):
                    self._clients_by_source_id[sid] = payload
        except Exception:  # noqa: BLE001 - never fail a patient on cache load
            logger.exception("patient mapper: failed to preload clients")
        self._loaded_job_id = ctx.job_id

    def _default_client_for(self, raw: dict[str, Any]) -> dict[str, Any] | None:
        """Pick the Gesdén client that represents this patient's payer.

        Gesdén stores up to four references on ``Pacientes``: ``IdCliDefec``
        (preferred billing), ``IdCliPac`` (the client row for the patient),
        ``IdCli`` (current), ``IdCliTutor`` (guardian). We try them in
        precedence order, returning the first hit so a missing default
        falls back to whatever client is closest to the patient.
        """
        for key in ("IdCliDefec", "IdCliPac", "IdCli", "IdCliTutor"):
            sid = _normalize_id(raw.get(key))
            if sid and sid in self._clients_by_source_id:
                return self._clients_by_source_id[sid]
        return None

    async def apply(
        self,
        ctx: MapperContext,
        *,
        entity_type: str,
        payload: dict[str, Any],
        raw: dict[str, Any],
        canonical_uuid: str,
        source_id: str,
        source_system: str,
    ) -> UUID | None:
        existing = await ctx.resolver.get("patient", canonical_uuid)
        if existing is not None:
            return existing

        self._ensure_clients_loaded(ctx)

        first_name = (payload.get("given_name") or "").strip() or "Sin nombre"
        last_name = (payload.get("family_name") or "").strip() or "—"

        dob_raw = payload.get("date_of_birth")
        dob: date | None = None
        if dob_raw:
            try:
                dob = date.fromisoformat(dob_raw)
            except (TypeError, ValueError):
                dob = None

        gender = _SEX_MAP.get((payload.get("sex") or "").lower())

        national_id = payload.get("national_id") or None
        national_id_type = "nif" if national_id else None

        # Lifecycle: Gesdén marks ``Inactivo`` ("S") and ``Exitus``
        # (deceased). DentalPin's Patient status enum is binary
        # (active/archived), so both states collapse to archived; the
        # underlying reason survives in notes so the operator can
        # tell them apart in the chart.
        deceased = bool(payload.get("deceased"))
        deactivated_at = payload.get("deactivated_at")
        status = "archived" if (deceased or deactivated_at) else "active"

        # GDPR/LOPD: Gesdén's ``AceptaLOPD`` defaults to False on legacy
        # rows that pre-date the consent flow, so we only flag
        # ``do_not_contact`` when the source row explicitly says the
        # patient did NOT consent. Missing → assume consent (False).
        gdpr_consent_raw = payload.get("gdpr_consent")
        do_not_contact = gdpr_consent_raw is False

        client = self._default_client_for(raw)
        billing_name = None
        billing_tax_id = None
        if client:
            client_nid = (client.get("national_id") or "").strip() or None
            client_legal = (client.get("legal_name") or "").strip() or None
            # Third-party payer: client and patient have distinct NIFs
            # (typical for company/insurance/family member). Mirror onto
            # billing_* so invoices carry the legal payer, not the
            # patient. Same-NIF clients are the patient themselves —
            # no billing override needed.
            if client_nid and client_nid != national_id:
                billing_tax_id = client_nid
                billing_name = client_legal

        # Contact data — DPMF v0.0.3+ ships patient.* phone/email/address.
        # Pacientes.* is the authoritative copy in Gesdén; the Clientes
        # mirror is a fallback (some clinics only maintain the client
        # record). Mobile beats landline when both exist.
        def _first_str(*candidates: Any) -> str | None:
            for c in candidates:
                if c is None:
                    continue
                s = str(c).strip()
                if s:
                    return s
            return None

        client_payload = client or {}
        phone = _first_str(
            payload.get("mobile_phone"),
            payload.get("phone"),
            payload.get("phone_secondary"),
            client_payload.get("mobile_phone"),
            client_payload.get("phone"),
            client_payload.get("phone_secondary"),
        )
        # Patient.phone is varchar(20) — Gesdén occasionally stores annotated
        # numbers (``600 11 22 33 / fijo``) that would overflow. Truncate
        # defensively so the import never fails on a verbose phone column.
        if phone and len(phone) > 20:
            phone = phone[:20]

        email = _first_str(payload.get("email"), client_payload.get("email"))

        street = _first_str(payload.get("address_street"), client_payload.get("address_street"))
        postal_code = _first_str(
            payload.get("address_postal_code"), client_payload.get("address_postal_code")
        )
        address: dict[str, str] | None = None
        if street or postal_code:
            address = {}
            if street:
                address["street"] = street
            if postal_code:
                address["postal_code"] = postal_code

        # SMS opt-out is a separate consent in Gesdén (``AceptaSMS``);
        # treat an explicit false on either LOPD or SMS as a contact
        # restriction. Marketing consent is informational only — kept
        # in raw_source_data for future channel-aware messaging.
        sms_consent_raw = payload.get("sms_consent")
        if sms_consent_raw is False:
            do_not_contact = True

        patient_number = payload.get("patient_number")
        registered_at = payload.get("registered_at")
        note_lines: list[str] = []
        if patient_number:
            note_lines.append(f"Migración dental-bridge: nº paciente origen {patient_number}")
        if registered_at:
            note_lines.append(f"Alta en origen: {registered_at}")
        if deceased:
            note_lines.append("Marcado como Exitus en origen.")
        elif deactivated_at:
            note_lines.append(f"Inactivo en origen desde {deactivated_at}.")
        notes = "\n".join(note_lines) if note_lines else None

        data: dict[str, Any] = {
            "first_name": first_name,
            "last_name": last_name,
            "date_of_birth": dob,
            "gender": gender,
            "national_id": national_id,
            "national_id_type": national_id_type,
            "phone": phone,
            "email": email,
            "address": address,
            "billing_name": billing_name,
            "billing_tax_id": billing_tax_id,
            "notes": notes,
            "status": status,
            "do_not_contact": do_not_contact,
            "preferred_language": "es",
        }
        # Drop None to let SQLAlchemy column defaults apply.
        data = {k: v for k, v in data.items() if v is not None}

        patient = await PatientService.create_patient(ctx.db, ctx.clinic_id, data)

        # Gesdén stores a free-text patient-level narrative in
        # ``Pacientes.Notas`` (dental-bridge exports it as
        # ``payload['notes']`` from adapter_version 0.0.2). Clinics
        # use it interchangeably with the ``AlertPac`` popup table —
        # allergies, medications, conditions and admin tags routinely
        # appear in *both* places. Run each non-empty line through the
        # same classifier the patient_alert mapper uses so the
        # structured destinations (Allergy, Medication,
        # SystemicDisease, MedicalContext flags) absorb whatever fits
        # the rules; the catch-all "general" branch appends the
        # remainder to ``Patient.notes``.
        notes_blob = (payload.get("notes") or "").strip()
        if notes_blob:
            await self._absorb_patient_notes(ctx, patient.id, notes_blob, source_id)

        await ctx.resolver.set(
            entity_type="patient",
            canonical_uuid=canonical_uuid,
            source_system=source_system,
            dentalpin_table="patients",
            dentalpin_id=patient.id,
        )
        return patient.id

    async def _absorb_patient_notes(
        self,
        ctx: MapperContext,
        patient_id: UUID,
        notes_blob: str,
        source_id: str,
    ) -> None:
        """Split ``Pacientes.Notas`` by newline and pipe each line
        through the alert classifier. Empty lines and pure separators
        are skipped. We never raise — a single weird line can't fail
        the whole patient row."""
        if self._alert_pipeline is None:
            self._alert_pipeline = PatientAlertMapper()
        lines = [
            ln.strip(" .-") for ln in notes_blob.replace("\r", "\n").split("\n") if ln.strip(" .-")
        ]
        for idx, line in enumerate(lines):
            await self._alert_pipeline.dispatch_freetext(
                ctx,
                patient_id,
                line,
                source_id=f"patient_notes:{source_id}:{idx}",
            )
