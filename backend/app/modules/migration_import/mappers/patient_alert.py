"""Map ``patient_alert`` (Gesdén ``AlertPac``) → ``patients_clinical`` rows.

Gesdén keeps the entire medical history in a single free-text column
(``AlertPac.Texto``). Different clinics fill it in radically different
ways: explicit ``MEDICACION:``/``ALERGIA:`` prefixes, single-keyword
diagnoses, lifestyle notes, anesthesia contraindications, and a long
tail of administrative leftovers.

The mapper hands every alert to :func:`classify_alert` and dispatches:

- ``allergy``        → 1+ :class:`Allergy` rows (one per parsed item)
- ``medication``     → 1+ :class:`Medication` rows
- ``disease``        → 1+ :class:`SystemicDisease` rows
- ``anticoagulant``  → :class:`Medication` row + flips the
                       ``MedicalContext.is_on_anticoagulants`` switch
- ``anesthesia``     → ``MedicalContext.adverse_reactions_to_anesthesia``
                       + ``anesthesia_reaction_details``
- ``smoking``        → ``MedicalContext.is_smoker`` + ``smoking_frequency``
- ``pregnancy``      → ``MedicalContext.is_pregnant``
- ``lactating``      → ``MedicalContext.is_lactating``
- ``bruxism``        → ``MedicalContext.bruxism``
- ``administrative`` → skipped with an info warning
- ``general``        → appended to ``Patient.notes`` (free text)

Every routed alert is idempotent on re-import — the same alert
canonical UUID is registered against the destination row produced.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select

from app.modules.patients.models import Patient
from app.modules.patients_clinical.models import (
    Allergy,
    Medication,
    MedicalContext,
    SystemicDisease,
)

from ..models import ImportWarning
from ._alert_classifier import AlertClassification, classify_alert
from .base import MapperContext


class PatientAlertMapper:
    def __init__(self) -> None:
        # patient_id -> ensured MedicalContext row id. Avoids the
        # repeated 1:1 upsert when a patient has many flag-style
        # alerts (smoking + pregnancy + anesthesia + …).
        self._context_cache: set[UUID] = set()

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
        existing = await ctx.resolver.get("patient_alert", canonical_uuid)
        if existing is not None:
            return existing

        patient_uuid = payload.get("patient_uuid")
        if not patient_uuid:
            return None
        patient_id = await ctx.resolver.get("patient", str(patient_uuid))
        if patient_id is None:
            return None

        result = classify_alert(payload.get("text"))
        dispatcher = _DISPATCH.get(result.category)
        if dispatcher is None:
            await _warn(
                ctx,
                source_id,
                "patient_alert.unknown_category",
                f"Categoría sin manejador: {result.category!r}",
            )
            return None

        target_id = await dispatcher(self, ctx, patient_id, result, source_id)
        if target_id is None:
            return None

        await ctx.resolver.set(
            entity_type="patient_alert",
            canonical_uuid=canonical_uuid,
            source_system=source_system,
            dentalpin_table=_TARGET_TABLE.get(result.category, "patients"),
            dentalpin_id=target_id,
        )
        return target_id

    # ------ Dispatchers ------------------------------------------------

    async def _handle_allergy(
        self,
        ctx: MapperContext,
        patient_id: UUID,
        result: AlertClassification,
        source_id: str,
    ) -> UUID | None:
        names = result.items or [result.raw_text]
        first_id: UUID | None = None
        for name in names:
            allergy = Allergy(
                clinic_id=ctx.clinic_id,
                patient_id=patient_id,
                name=name[:100],
                severity="medium",
                notes=f"Importado dental-bridge AlertPac #{source_id}",
            )
            ctx.db.add(allergy)
            await ctx.db.flush()
            if first_id is None:
                first_id = allergy.id
        return first_id

    async def _handle_medication(
        self,
        ctx: MapperContext,
        patient_id: UUID,
        result: AlertClassification,
        source_id: str,
    ) -> UUID | None:
        names = result.items or [result.raw_text]
        first_id: UUID | None = None
        for name in names:
            dosage, clean_name = _split_dosage(name)
            med = Medication(
                clinic_id=ctx.clinic_id,
                patient_id=patient_id,
                name=clean_name[:100],
                dosage=dosage,
                notes=f"Importado dental-bridge AlertPac #{source_id}",
            )
            ctx.db.add(med)
            await ctx.db.flush()
            if first_id is None:
                first_id = med.id
        return first_id

    async def _handle_disease(
        self,
        ctx: MapperContext,
        patient_id: UUID,
        result: AlertClassification,
        source_id: str,
    ) -> UUID | None:
        names = result.items or [result.raw_text]
        first_id: UUID | None = None
        for name in names:
            disease = SystemicDisease(
                clinic_id=ctx.clinic_id,
                patient_id=patient_id,
                name=name[:100],
                is_controlled=True,
                notes=f"Importado dental-bridge AlertPac #{source_id}",
            )
            ctx.db.add(disease)
            await ctx.db.flush()
            if first_id is None:
                first_id = disease.id
        return first_id

    async def _handle_anesthesia(
        self,
        ctx: MapperContext,
        patient_id: UUID,
        result: AlertClassification,
        source_id: str,
    ) -> UUID | None:
        mc = await self._ensure_context(ctx, patient_id)
        mc.adverse_reactions_to_anesthesia = True
        existing_detail = mc.anesthesia_reaction_details or ""
        merged = _merge_lines(existing_detail, result.raw_text)
        mc.anesthesia_reaction_details = merged[:500]
        await ctx.db.flush()
        return patient_id

    async def _handle_smoking(
        self,
        ctx: MapperContext,
        patient_id: UUID,
        result: AlertClassification,
        source_id: str,
    ) -> UUID | None:
        mc = await self._ensure_context(ctx, patient_id)
        mc.is_smoker = True
        if not mc.smoking_frequency:
            mc.smoking_frequency = result.raw_text[:100]
        await ctx.db.flush()
        return patient_id

    async def _handle_pregnancy(
        self,
        ctx: MapperContext,
        patient_id: UUID,
        result: AlertClassification,
        source_id: str,
    ) -> UUID | None:
        mc = await self._ensure_context(ctx, patient_id)
        mc.is_pregnant = True
        await ctx.db.flush()
        return patient_id

    async def _handle_lactating(
        self,
        ctx: MapperContext,
        patient_id: UUID,
        result: AlertClassification,
        source_id: str,
    ) -> UUID | None:
        mc = await self._ensure_context(ctx, patient_id)
        mc.is_lactating = True
        await ctx.db.flush()
        return patient_id

    async def _handle_anticoagulant(
        self,
        ctx: MapperContext,
        patient_id: UUID,
        result: AlertClassification,
        source_id: str,
    ) -> UUID | None:
        # Capture as Medication AND flip the anticoagulant flag so the
        # clinic banner picks it up.
        med_id = await self._handle_medication(ctx, patient_id, result, source_id)
        mc = await self._ensure_context(ctx, patient_id)
        mc.is_on_anticoagulants = True
        if not mc.anticoagulant_medication:
            mc.anticoagulant_medication = result.raw_text[:100]
        await ctx.db.flush()
        return med_id or patient_id

    async def _handle_bruxism(
        self,
        ctx: MapperContext,
        patient_id: UUID,
        result: AlertClassification,
        source_id: str,
    ) -> UUID | None:
        mc = await self._ensure_context(ctx, patient_id)
        mc.bruxism = True
        await ctx.db.flush()
        return patient_id

    async def _handle_administrative(
        self,
        ctx: MapperContext,
        patient_id: UUID,
        result: AlertClassification,
        source_id: str,
    ) -> UUID | None:
        await _warn(
            ctx,
            source_id,
            "patient_alert.administrative",
            f"Alerta administrativa omitida del historial clínico: {result.raw_text[:100]}",
        )
        return None

    async def _handle_general(
        self,
        ctx: MapperContext,
        patient_id: UUID,
        result: AlertClassification,
        source_id: str,
    ) -> UUID | None:
        # Fallback: append to Patient.notes prefixed with "Alerta:" so
        # the clinician can review unclassified entries in context.
        patient = await ctx.db.get(Patient, patient_id)
        if patient is None:
            return None
        line = f"Alerta importada: {result.raw_text}"
        patient.notes = _merge_lines(patient.notes or "", line)[:4000]
        await ctx.db.flush()
        return patient_id

    # ------ Helpers ----------------------------------------------------

    async def _ensure_context(
        self, ctx: MapperContext, patient_id: UUID
    ) -> MedicalContext:
        """Get-or-create the 1:1 MedicalContext for a patient. Cached
        per-mapper-instance to avoid repeated SELECTs when the patient
        has multiple flag-style alerts."""
        result = await ctx.db.execute(
            select(MedicalContext).where(MedicalContext.patient_id == patient_id)
        )
        mc = result.scalar_one_or_none()
        if mc is None:
            mc = MedicalContext(
                patient_id=patient_id,
                clinic_id=ctx.clinic_id,
                last_updated_at=datetime.now(UTC),
            )
            ctx.db.add(mc)
            await ctx.db.flush()
        self._context_cache.add(patient_id)
        return mc


_DISPATCH = {
    "allergy": PatientAlertMapper._handle_allergy,
    "medication": PatientAlertMapper._handle_medication,
    "disease": PatientAlertMapper._handle_disease,
    "anesthesia": PatientAlertMapper._handle_anesthesia,
    "smoking": PatientAlertMapper._handle_smoking,
    "pregnancy": PatientAlertMapper._handle_pregnancy,
    "lactating": PatientAlertMapper._handle_lactating,
    "anticoagulant": PatientAlertMapper._handle_anticoagulant,
    "bruxism": PatientAlertMapper._handle_bruxism,
    "administrative": PatientAlertMapper._handle_administrative,
    "general": PatientAlertMapper._handle_general,
}

_TARGET_TABLE = {
    "allergy": "patients_clinical_allergy",
    "medication": "patients_clinical_medication",
    "disease": "patients_clinical_systemic_disease",
    "anesthesia": "patients_clinical_medical_context",
    "smoking": "patients_clinical_medical_context",
    "pregnancy": "patients_clinical_medical_context",
    "lactating": "patients_clinical_medical_context",
    "anticoagulant": "patients_clinical_medication",
    "bruxism": "patients_clinical_medical_context",
    "general": "patients",
}


async def _warn(ctx: MapperContext, source_id: str, code: str, message: str) -> None:
    ctx.db.add(
        ImportWarning(
            job_id=ctx.job_id,
            entity_type="patient_alert",
            source_id=source_id,
            severity="info",
            code=code,
            message=message,
        )
    )


_DOSAGE_RE = __import__("re").compile(r"\b(\d+(?:[.,]\d+)?\s*(?:MG|MCG|G|ML|UI))\b", __import__("re").IGNORECASE)


def _split_dosage(name: str) -> tuple[str | None, str]:
    """Pull a leading/trailing dose token out of a medication string.

    ``"ENALAPRIL 20 MG"`` → ``("20 MG", "ENALAPRIL")``.
    Tokens like trailing parenthetical indications (``"(TENSION)"``)
    are kept on the name so the operator sees the clinical context.
    """
    match = _DOSAGE_RE.search(name)
    if not match:
        return None, name
    dose = match.group(1).strip()
    cleaned = (name[: match.start()] + name[match.end():]).strip()
    return dose, cleaned or name


def _merge_lines(existing: str, addition: str) -> str:
    """Append ``addition`` to ``existing`` only if it isn't already there."""
    if not existing:
        return addition
    if addition in existing:
        return existing
    return f"{existing}\n{addition}"
