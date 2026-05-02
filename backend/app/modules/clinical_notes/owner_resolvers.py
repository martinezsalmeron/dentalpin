"""Attachment owner resolvers for the clinical_notes module.

Each function maps an ``owner_id`` to its ``patient_id`` for one of the
owner_type strings this module declares to ``media.attachment_registry``.

These functions are registered at module import (see ``__init__.py``)
and are then called by ``media.AttachmentService`` during link
validation. They MUST filter by ``clinic_id`` themselves — the registry
passes it in but does not enforce.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.media.attachment_registry import OwnerSpec, attachment_registry
from app.modules.odontogram.models import Treatment
from app.modules.patients.models import Patient
from app.modules.treatment_plan.models import TreatmentPlan

from .models import ClinicalNote


async def _resolve_patient(db: AsyncSession, clinic_id: UUID, owner_id: UUID) -> UUID | None:
    result = await db.execute(
        select(Patient.id).where(Patient.id == owner_id, Patient.clinic_id == clinic_id)
    )
    row = result.first()
    return row[0] if row else None


async def _resolve_treatment(db: AsyncSession, clinic_id: UUID, owner_id: UUID) -> UUID | None:
    result = await db.execute(
        select(Treatment.patient_id).where(
            Treatment.id == owner_id,
            Treatment.clinic_id == clinic_id,
            Treatment.deleted_at.is_(None),
        )
    )
    row = result.first()
    return row[0] if row else None


async def _resolve_plan(db: AsyncSession, clinic_id: UUID, owner_id: UUID) -> UUID | None:
    result = await db.execute(
        select(TreatmentPlan.patient_id).where(
            TreatmentPlan.id == owner_id,
            TreatmentPlan.clinic_id == clinic_id,
            TreatmentPlan.deleted_at.is_(None),
        )
    )
    row = result.first()
    return row[0] if row else None


async def _resolve_clinical_note(db: AsyncSession, clinic_id: UUID, owner_id: UUID) -> UUID | None:
    """A note's patient = the patient reachable from its own owner."""
    result = await db.execute(
        select(ClinicalNote.owner_type, ClinicalNote.owner_id).where(
            ClinicalNote.id == owner_id,
            ClinicalNote.clinic_id == clinic_id,
            ClinicalNote.deleted_at.is_(None),
        )
    )
    row = result.first()
    if not row:
        return None
    note_owner_type, note_owner_id = row
    if note_owner_type == "patient":
        return await _resolve_patient(db, clinic_id, note_owner_id)
    if note_owner_type == "treatment":
        return await _resolve_treatment(db, clinic_id, note_owner_id)
    if note_owner_type == "plan":
        return await _resolve_plan(db, clinic_id, note_owner_id)
    return None


def register() -> None:
    """Register every owner_type this module owns. Called from ``__init__.py``."""
    for spec in (
        OwnerSpec(owner_type="patient", resolver=_resolve_patient, label="Paciente"),
        OwnerSpec(owner_type="treatment", resolver=_resolve_treatment, label="Tratamiento"),
        OwnerSpec(owner_type="plan", resolver=_resolve_plan, label="Plan de tratamiento"),
        OwnerSpec(
            owner_type="clinical_note",
            resolver=_resolve_clinical_note,
            label="Nota clínica",
        ),
    ):
        attachment_registry.register(spec)
