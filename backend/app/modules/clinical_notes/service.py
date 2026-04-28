"""Clinical notes + polymorphic attachments service layer.

CRUD + queries for ``clinical_notes`` and ``clinical_note_attachments``. Owner
existence is validated up-front against the relevant module model (patients,
odontogram, treatment_plan) — the manifest declares those as ``depends`` so
this is a sanctioned cross-module read.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Iterable
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import and_, false, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.events import event_bus
from app.core.events.types import EventType
from app.modules.media.models import Document
from app.modules.odontogram.models import Treatment
from app.modules.patients.models import Patient
from app.modules.treatment_plan.models import PlannedTreatmentItem, TreatmentPlan

from .models import (
    ATTACHMENT_OWNER_APPOINTMENT_TREATMENT,
    ATTACHMENT_OWNER_TYPES,
    NOTE_OWNER_PATIENT,
    NOTE_OWNER_PLAN,
    NOTE_OWNER_TREATMENT,
    NOTE_OWNER_TYPES,
    NOTE_TYPE_ADMINISTRATIVE,
    NOTE_TYPE_DIAGNOSIS,
    NOTE_TYPE_TREATMENT,
    NOTE_TYPE_TREATMENT_PLAN,
    ClinicalNote,
    ClinicalNoteAttachment,
)

logger = logging.getLogger(__name__)

_HTML_TAG_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\s+")
_EXCERPT_MAX = 200


def body_excerpt(body: str) -> str:
    """Strip HTML + collapse whitespace for event payloads / timeline titles."""
    text = _HTML_TAG_RE.sub(" ", body or "")
    text = _WHITESPACE_RE.sub(" ", text).strip()
    return text[:_EXCERPT_MAX]


class NoteOwnerError(ValueError):
    """Owner does not exist in this clinic, or note_type/owner mismatch."""


class AttachmentPatientMismatchError(ValueError):
    """Document belongs to a different patient than the note owner."""


_NOTE_TYPE_TO_EVENT = {
    NOTE_TYPE_ADMINISTRATIVE: EventType.CLINICAL_NOTE_ADMINISTRATIVE_CREATED,
    NOTE_TYPE_DIAGNOSIS: EventType.CLINICAL_NOTE_DIAGNOSIS_CREATED,
    NOTE_TYPE_TREATMENT: EventType.CLINICAL_NOTE_TREATMENT_CREATED,
    NOTE_TYPE_TREATMENT_PLAN: EventType.CLINICAL_NOTE_PLAN_CREATED,
}


# ---------------------------------------------------------------------------
# Owner resolution
# ---------------------------------------------------------------------------


async def _resolve_patient_owner(db: AsyncSession, clinic_id: UUID, patient_id: UUID) -> UUID:
    result = await db.execute(
        select(Patient.id).where(
            Patient.id == patient_id,
            Patient.clinic_id == clinic_id,
        )
    )
    row = result.first()
    if row is None:
        raise NoteOwnerError(f"patient {patient_id} not found")
    return row[0]


async def _resolve_treatment_owner(
    db: AsyncSession, clinic_id: UUID, treatment_id: UUID
) -> tuple[UUID, UUID]:
    """Return (treatment_id, patient_id) when the treatment is live."""
    result = await db.execute(
        select(Treatment.id, Treatment.patient_id).where(
            Treatment.id == treatment_id,
            Treatment.clinic_id == clinic_id,
            Treatment.deleted_at.is_(None),
        )
    )
    row = result.first()
    if row is None:
        raise NoteOwnerError(f"treatment {treatment_id} not found")
    return row[0], row[1]


async def _resolve_plan_owner(
    db: AsyncSession, clinic_id: UUID, plan_id: UUID
) -> tuple[UUID, UUID]:
    """Return (plan_id, patient_id) when the plan is live."""
    result = await db.execute(
        select(TreatmentPlan.id, TreatmentPlan.patient_id).where(
            TreatmentPlan.id == plan_id,
            TreatmentPlan.clinic_id == clinic_id,
            TreatmentPlan.deleted_at.is_(None),
        )
    )
    row = result.first()
    if row is None:
        raise NoteOwnerError(f"treatment_plan {plan_id} not found")
    return row[0], row[1]


async def _resolve_appointment_treatment_patient(
    db: AsyncSession, clinic_id: UUID, appointment_treatment_id: UUID
) -> UUID:
    # Deferred import: agenda is not in our manifest depends on purpose —
    # we only need to read its appointment for attachment validation. The
    # alternative is to expose an HTTP endpoint; keep the read here, behind
    # a function so the dependency is explicit.
    from app.modules.agenda.models import Appointment, AppointmentTreatment

    result = await db.execute(
        select(Appointment.patient_id)
        .join(
            AppointmentTreatment,
            AppointmentTreatment.appointment_id == Appointment.id,
        )
        .where(
            AppointmentTreatment.id == appointment_treatment_id,
            Appointment.clinic_id == clinic_id,
        )
    )
    row = result.first()
    if row is None:
        raise NoteOwnerError(f"appointment_treatment {appointment_treatment_id} not found")
    return row[0]


async def resolve_owner_patient(
    db: AsyncSession,
    clinic_id: UUID,
    owner_type: str,
    owner_id: UUID,
) -> UUID:
    """Return the patient_id reachable from an owner reference, or raise."""
    if owner_type == NOTE_OWNER_PATIENT:
        return await _resolve_patient_owner(db, clinic_id, owner_id)
    if owner_type == NOTE_OWNER_TREATMENT:
        _, patient_id = await _resolve_treatment_owner(db, clinic_id, owner_id)
        return patient_id
    if owner_type == NOTE_OWNER_PLAN:
        _, patient_id = await _resolve_plan_owner(db, clinic_id, owner_id)
        return patient_id
    if owner_type == ATTACHMENT_OWNER_APPOINTMENT_TREATMENT:
        return await _resolve_appointment_treatment_patient(db, clinic_id, owner_id)
    raise NoteOwnerError(f"unsupported owner_type {owner_type!r}")


# ---------------------------------------------------------------------------
# Notes service
# ---------------------------------------------------------------------------


class NoteService:
    """CRUD for clinical notes."""

    @staticmethod
    async def list_for_owner(
        db: AsyncSession,
        clinic_id: UUID,
        owner_type: str,
        owner_id: UUID,
    ) -> list[ClinicalNote]:
        if owner_type not in NOTE_OWNER_TYPES:
            raise NoteOwnerError(f"unsupported note owner_type {owner_type!r}")
        result = await db.execute(
            select(ClinicalNote)
            .where(
                ClinicalNote.clinic_id == clinic_id,
                ClinicalNote.owner_type == owner_type,
                ClinicalNote.owner_id == owner_id,
                ClinicalNote.deleted_at.is_(None),
            )
            .options(selectinload(ClinicalNote.attachments))
            .order_by(ClinicalNote.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get(db: AsyncSession, clinic_id: UUID, note_id: UUID) -> ClinicalNote | None:
        result = await db.execute(
            select(ClinicalNote)
            .where(
                ClinicalNote.id == note_id,
                ClinicalNote.clinic_id == clinic_id,
                ClinicalNote.deleted_at.is_(None),
            )
            .options(selectinload(ClinicalNote.attachments))
        )
        return result.scalar_one_or_none()

    @classmethod
    async def create(
        cls,
        db: AsyncSession,
        *,
        clinic_id: UUID,
        user_id: UUID,
        note_type: str,
        owner_type: str,
        owner_id: UUID,
        body: str,
        tooth_number: int | None = None,
        attachment_document_ids: Iterable[UUID] | None = None,
    ) -> ClinicalNote:
        patient_id = await resolve_owner_patient(db, clinic_id, owner_type, owner_id)

        note = ClinicalNote(
            clinic_id=clinic_id,
            note_type=note_type,
            owner_type=owner_type,
            owner_id=owner_id,
            tooth_number=tooth_number if note_type == NOTE_TYPE_DIAGNOSIS else None,
            body=body,
            author_id=user_id,
        )
        db.add(note)
        await db.flush()

        if attachment_document_ids:
            await NoteAttachmentService.link_many(
                db,
                clinic_id=clinic_id,
                document_ids=list(attachment_document_ids),
                owner_type=owner_type,
                owner_id=owner_id,
                note_id=note.id,
                owner_patient_id=patient_id,
            )

        await db.flush()
        await db.refresh(note, attribute_names=["attachments"])

        event_name = _NOTE_TYPE_TO_EVENT[note_type]
        event_bus.publish(
            event_name,
            {
                "clinic_id": str(clinic_id),
                "patient_id": str(patient_id),
                "note_id": str(note.id),
                "note_type": note_type,
                "owner_type": owner_type,
                "owner_id": str(owner_id),
                "tooth_number": note.tooth_number,
                "user_id": str(user_id),
                "body_excerpt": body_excerpt(body),
                "occurred_at": note.created_at.isoformat() if note.created_at else None,
            },
        )
        return note

    @staticmethod
    async def update(
        db: AsyncSession,
        *,
        clinic_id: UUID,
        note_id: UUID,
        body: str,
        user_id: UUID,
        is_admin: bool,
    ) -> ClinicalNote | None:
        result = await db.execute(
            select(ClinicalNote).where(
                ClinicalNote.id == note_id,
                ClinicalNote.clinic_id == clinic_id,
                ClinicalNote.deleted_at.is_(None),
            )
        )
        note = result.scalar_one_or_none()
        if note is None:
            return None
        if note.author_id != user_id and not is_admin:
            raise PermissionError("Only the author or an admin can edit this note")
        note.body = body
        await db.flush()
        return note

    @staticmethod
    async def soft_delete(
        db: AsyncSession,
        *,
        clinic_id: UUID,
        note_id: UUID,
        user_id: UUID,
        is_admin: bool,
    ) -> bool:
        result = await db.execute(
            select(ClinicalNote).where(
                ClinicalNote.id == note_id,
                ClinicalNote.clinic_id == clinic_id,
                ClinicalNote.deleted_at.is_(None),
            )
        )
        note = result.scalar_one_or_none()
        if note is None:
            return False
        if note.author_id != user_id and not is_admin:
            raise PermissionError("Only the author or an admin can delete this note")
        note.deleted_at = datetime.now(UTC)
        await db.flush()
        return True


# ---------------------------------------------------------------------------
# Attachments service
# ---------------------------------------------------------------------------


class NoteAttachmentService:
    """Polymorphic link between ``media.Document`` and a notes owner."""

    @staticmethod
    async def list_for_owner(
        db: AsyncSession,
        clinic_id: UUID,
        owner_type: str,
        owner_id: UUID,
    ) -> list[ClinicalNoteAttachment]:
        if owner_type not in ATTACHMENT_OWNER_TYPES:
            raise NoteOwnerError(f"unsupported attachment owner_type {owner_type!r}")
        result = await db.execute(
            select(ClinicalNoteAttachment)
            .where(
                ClinicalNoteAttachment.clinic_id == clinic_id,
                ClinicalNoteAttachment.owner_type == owner_type,
                ClinicalNoteAttachment.owner_id == owner_id,
            )
            .order_by(
                ClinicalNoteAttachment.display_order,
                ClinicalNoteAttachment.created_at,
            )
        )
        return list(result.scalars().all())

    @staticmethod
    async def _load_documents(
        db: AsyncSession, clinic_id: UUID, document_ids: list[UUID]
    ) -> list[Document]:
        if not document_ids:
            return []
        result = await db.execute(
            select(Document).where(
                Document.id.in_(document_ids),
                Document.clinic_id == clinic_id,
            )
        )
        return list(result.scalars().all())

    @classmethod
    async def link(
        cls,
        db: AsyncSession,
        *,
        clinic_id: UUID,
        document_id: UUID,
        owner_type: str,
        owner_id: UUID,
        note_id: UUID | None = None,
        display_order: int = 0,
        owner_patient_id: UUID | None = None,
    ) -> ClinicalNoteAttachment:
        if owner_type not in ATTACHMENT_OWNER_TYPES:
            raise NoteOwnerError(f"unsupported attachment owner_type {owner_type!r}")

        if owner_patient_id is None:
            owner_patient_id = await resolve_owner_patient(db, clinic_id, owner_type, owner_id)

        docs = await cls._load_documents(db, clinic_id, [document_id])
        if not docs:
            raise NoteOwnerError(f"document {document_id} not found")
        doc = docs[0]
        if doc.patient_id != owner_patient_id:
            raise AttachmentPatientMismatchError("Document does not belong to the owner's patient")

        link_row = ClinicalNoteAttachment(
            clinic_id=clinic_id,
            document_id=document_id,
            owner_type=owner_type,
            owner_id=owner_id,
            note_id=note_id,
            display_order=display_order,
        )
        db.add(link_row)
        await db.flush()
        return link_row

    @classmethod
    async def link_many(
        cls,
        db: AsyncSession,
        *,
        clinic_id: UUID,
        document_ids: list[UUID],
        owner_type: str,
        owner_id: UUID,
        note_id: UUID | None = None,
        owner_patient_id: UUID | None = None,
    ) -> list[ClinicalNoteAttachment]:
        if not document_ids:
            return []
        if owner_patient_id is None:
            owner_patient_id = await resolve_owner_patient(db, clinic_id, owner_type, owner_id)
        docs = await cls._load_documents(db, clinic_id, document_ids)
        by_id = {d.id: d for d in docs}
        missing = [d for d in document_ids if d not in by_id]
        if missing:
            raise NoteOwnerError(f"documents not found: {missing}")
        for doc in docs:
            if doc.patient_id != owner_patient_id:
                raise AttachmentPatientMismatchError(
                    "Document does not belong to the owner's patient"
                )
        rows: list[ClinicalNoteAttachment] = []
        for order, doc_id in enumerate(document_ids):
            row = ClinicalNoteAttachment(
                clinic_id=clinic_id,
                document_id=doc_id,
                owner_type=owner_type,
                owner_id=owner_id,
                note_id=note_id,
                display_order=order,
            )
            db.add(row)
            rows.append(row)
        await db.flush()
        return rows

    @staticmethod
    async def unlink(db: AsyncSession, *, clinic_id: UUID, attachment_id: UUID) -> bool:
        result = await db.execute(
            select(ClinicalNoteAttachment).where(
                ClinicalNoteAttachment.id == attachment_id,
                ClinicalNoteAttachment.clinic_id == clinic_id,
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            return False
        await db.delete(row)
        await db.flush()
        return True


# ---------------------------------------------------------------------------
# Aggregate feeds — Summary tab + plan-grouped patient view + plan merged
# ---------------------------------------------------------------------------


async def _resolve_treatments_for_patient(
    db: AsyncSession, clinic_id: UUID, patient_id: UUID
) -> dict[UUID, Treatment]:
    """Return live Treatments for this patient indexed by id."""
    result = await db.execute(
        select(Treatment)
        .where(
            Treatment.clinic_id == clinic_id,
            Treatment.patient_id == patient_id,
            Treatment.deleted_at.is_(None),
        )
        .options(
            selectinload(Treatment.teeth),
            selectinload(Treatment.catalog_item),
        )
    )
    return {t.id: t for t in result.scalars().all()}


async def list_recent_for_patient(
    db: AsyncSession,
    *,
    clinic_id: UUID,
    patient_id: UUID,
    note_types: list[str] | None,
    limit: int,
    before: datetime | None,
) -> list[dict]:
    """Recent notes feed for a patient across every owner type.

    Returned entries match :class:`.schemas.RecentNoteEntry`. Includes a
    ``linked`` descriptor so the UI can render contextual chips ("Diente 47",
    "Plan: PLAN-2024-0001") without further fetches.
    """
    # Validate patient is in clinic up-front — also yields a stable 404 vs 200 [].
    await _resolve_patient_owner(db, clinic_id, patient_id)

    treatments_by_id = await _resolve_treatments_for_patient(db, clinic_id, patient_id)
    treatment_ids = list(treatments_by_id.keys())

    plans_result = await db.execute(
        select(TreatmentPlan).where(
            TreatmentPlan.clinic_id == clinic_id,
            TreatmentPlan.patient_id == patient_id,
            TreatmentPlan.deleted_at.is_(None),
        )
    )
    plans = list(plans_result.scalars().all())
    plan_ids = [p.id for p in plans]
    plan_by_id = {p.id: p for p in plans}

    treatment_clause = and_(
        ClinicalNote.owner_type == NOTE_OWNER_TREATMENT,
        ClinicalNote.owner_id.in_(treatment_ids) if treatment_ids else false(),
    )
    plan_clause = and_(
        ClinicalNote.owner_type == NOTE_OWNER_PLAN,
        ClinicalNote.owner_id.in_(plan_ids) if plan_ids else false(),
    )
    patient_clause = and_(
        ClinicalNote.owner_type == NOTE_OWNER_PATIENT,
        ClinicalNote.owner_id == patient_id,
    )
    owner_filter = or_(patient_clause, treatment_clause, plan_clause)

    stmt = (
        select(ClinicalNote)
        .where(
            ClinicalNote.clinic_id == clinic_id,
            ClinicalNote.deleted_at.is_(None),
            owner_filter,
        )
        .options(
            selectinload(ClinicalNote.attachments),
            selectinload(ClinicalNote.author),
        )
        .order_by(ClinicalNote.created_at.desc())
        .limit(limit)
    )
    if note_types:
        stmt = stmt.where(ClinicalNote.note_type.in_(note_types))
    if before is not None:
        stmt = stmt.where(ClinicalNote.created_at < before)

    result = await db.execute(stmt)
    notes = list(result.scalars().all())

    entries: list[dict] = []
    for note in notes:
        linked = _build_linked(note, plan_by_id, treatments_by_id, patient_id)
        entries.append(
            {
                "id": note.id,
                "note_type": note.note_type,
                "owner_type": note.owner_type,
                "owner_id": note.owner_id,
                "tooth_number": note.tooth_number,
                "body": note.body,
                "created_at": note.created_at,
                "updated_at": note.updated_at,
                "author": _author_brief(note.author) if note.author else {"id": note.author_id},
                "linked": linked,
                "attachments": list(note.attachments),
            }
        )
    return entries


def _author_brief(author) -> dict:
    full_name = (
        getattr(author, "full_name", None)
        or " ".join(
            filter(
                None,
                [getattr(author, "first_name", None), getattr(author, "last_name", None)],
            )
        ).strip()
        or None
    )
    return {
        "id": author.id,
        "full_name": full_name,
        "email": getattr(author, "email", None),
    }


def _build_linked(
    note: ClinicalNote,
    plan_by_id: dict[UUID, TreatmentPlan],
    treatments_by_id: dict[UUID, Treatment],
    patient_id: UUID,
) -> dict:
    if note.owner_type == NOTE_OWNER_PATIENT:
        return {
            "kind": "patient",
            "id": patient_id,
            "label": None,
            "tooth_number": note.tooth_number,
        }
    if note.owner_type == NOTE_OWNER_TREATMENT:
        treatment = treatments_by_id.get(note.owner_id)
        teeth = [t.tooth_number for t in (treatment.teeth or [])] if treatment else []
        catalog = treatment.catalog_item if treatment else None
        names = (catalog.names if catalog else None) or {}
        label = (
            names.get("es") or names.get("en") or (treatment.clinical_type if treatment else None)
        )
        return {
            "kind": "treatment",
            "id": note.owner_id,
            "label": label,
            "tooth_number": teeth[0] if teeth else None,
        }
    if note.owner_type == NOTE_OWNER_PLAN:
        plan = plan_by_id.get(note.owner_id)
        label = plan.title or plan.plan_number if plan else None
        return {
            "kind": "plan",
            "id": note.owner_id,
            "label": label,
            "tooth_number": None,
        }
    return {"kind": note.owner_type, "id": note.owner_id, "label": None, "tooth_number": None}


# ---------------------------------------------------------------------------
# Plan-scoped feeds (replaces ``treatment_plan.notes_service`` aggregations)
# ---------------------------------------------------------------------------


async def list_merged_for_plan(db: AsyncSession, clinic_id: UUID, plan_id: UUID) -> list[dict]:
    """Plan + treatment + visit notes for a single plan, newest-first.

    Returned shape matches :class:`.schemas.ClinicalNoteEntry`. Plan-level
    notes use ``source='plan'``; per-treatment notes use ``source='treatment'``;
    appointment-derived notes (``AppointmentTreatment.notes``) use ``source='visit'``.
    """
    from app.modules.agenda.models import Appointment, AppointmentTreatment

    plan_result = await db.execute(
        select(TreatmentPlan).where(
            TreatmentPlan.id == plan_id,
            TreatmentPlan.clinic_id == clinic_id,
            TreatmentPlan.deleted_at.is_(None),
        )
    )
    plan = plan_result.scalar_one_or_none()
    if plan is None:
        return []

    items_result = await db.execute(
        select(PlannedTreatmentItem.id, PlannedTreatmentItem.treatment_id).where(
            PlannedTreatmentItem.treatment_plan_id == plan_id,
            PlannedTreatmentItem.clinic_id == clinic_id,
        )
    )
    item_rows = items_result.all()
    treatment_ids = [row[1] for row in item_rows]
    plan_item_id_for_treatment = {row[1]: row[0] for row in item_rows}

    treatment_clause = (
        and_(
            ClinicalNote.owner_type == NOTE_OWNER_TREATMENT,
            ClinicalNote.owner_id.in_(treatment_ids),
        )
        if treatment_ids
        else false()
    )
    owner_filter = or_(
        and_(
            ClinicalNote.owner_type == NOTE_OWNER_PLAN,
            ClinicalNote.owner_id == plan_id,
        ),
        treatment_clause,
    )
    notes_result = await db.execute(
        select(ClinicalNote)
        .where(
            ClinicalNote.clinic_id == clinic_id,
            ClinicalNote.deleted_at.is_(None),
            owner_filter,
        )
        .options(selectinload(ClinicalNote.attachments))
        .order_by(ClinicalNote.created_at.desc())
    )
    notes = list(notes_result.scalars().all())

    entries: list[dict] = []
    for note in notes:
        is_treatment = note.owner_type == NOTE_OWNER_TREATMENT
        plan_item_id = plan_item_id_for_treatment.get(note.owner_id) if is_treatment else None
        entries.append(
            {
                "source": "treatment" if is_treatment else "plan",
                "note_id": note.id,
                "owner_id": note.owner_id,
                "plan_item_id": plan_item_id,
                "body": note.body,
                "author_id": note.author_id,
                "created_at": note.created_at,
                "updated_at": note.updated_at,
                "attachments": list(note.attachments),
            }
        )

    # Visit notes (live in agenda — read-only here).
    if item_rows:
        item_ids = [row[0] for row in item_rows]
        visit_result = await db.execute(
            select(AppointmentTreatment, Appointment.created_at)
            .join(Appointment, AppointmentTreatment.appointment_id == Appointment.id)
            .where(
                AppointmentTreatment.planned_treatment_item_id.in_(item_ids),
                AppointmentTreatment.notes.is_not(None),
                AppointmentTreatment.notes != "",
                Appointment.clinic_id == clinic_id,
            )
        )
        for apt_tr, apt_created in visit_result.all():
            attachments = await NoteAttachmentService.list_for_owner(
                db,
                clinic_id,
                ATTACHMENT_OWNER_APPOINTMENT_TREATMENT,
                apt_tr.id,
            )
            entries.append(
                {
                    "source": "visit",
                    "note_id": None,
                    "owner_id": apt_tr.id,
                    "plan_item_id": apt_tr.planned_treatment_item_id,
                    "body": apt_tr.notes or "",
                    "author_id": None,
                    "created_at": apt_tr.created_at or apt_created,
                    "updated_at": None,
                    "attachments": attachments,
                }
            )

    entries.sort(key=lambda e: e["created_at"], reverse=True)
    return entries


async def list_grouped_for_patient(
    db: AsyncSession, clinic_id: UUID, patient_id: UUID
) -> list[dict]:
    """Per-plan grouping with plan-level + per-treatment buckets, newest plan first."""
    plans_result = await db.execute(
        select(TreatmentPlan)
        .where(
            TreatmentPlan.patient_id == patient_id,
            TreatmentPlan.clinic_id == clinic_id,
            TreatmentPlan.deleted_at.is_(None),
        )
        .order_by(TreatmentPlan.created_at.desc())
    )
    plans = list(plans_result.scalars().all())
    if not plans:
        return []

    treatments_by_id = await _resolve_treatments_for_patient(db, clinic_id, patient_id)

    groups: list[dict] = []
    for plan in plans:
        items_result = await db.execute(
            select(PlannedTreatmentItem)
            .where(
                PlannedTreatmentItem.treatment_plan_id == plan.id,
                PlannedTreatmentItem.clinic_id == clinic_id,
            )
            .order_by(PlannedTreatmentItem.sequence_order)
        )
        items = list(items_result.scalars().all())

        entries = await list_merged_for_plan(db, clinic_id, plan.id)
        plan_notes = [e for e in entries if e["source"] == "plan"]
        by_item: dict[UUID, list[dict]] = {}
        for e in entries:
            if e["source"] == "plan":
                continue
            pid = e.get("plan_item_id")
            if pid is None:
                continue
            by_item.setdefault(pid, []).append(e)

        treatment_groups = []
        for item in items:
            treatment = treatments_by_id.get(item.treatment_id)
            label = None
            teeth: list[int] = []
            if treatment:
                catalog = treatment.catalog_item
                if catalog and catalog.names:
                    label = catalog.names.get("es") or catalog.names.get("en")
                if not label:
                    label = treatment.clinical_type
                teeth = [t.tooth_number for t in (treatment.teeth or [])]
            treatment_groups.append(
                {
                    "plan_item": {
                        "id": item.id,
                        "treatment_id": item.treatment_id,
                        "sequence_order": item.sequence_order,
                        "status": item.status,
                        "label": label,
                        "teeth": teeth,
                    },
                    "notes": by_item.get(item.id, []),
                }
            )

        groups.append(
            {
                "plan": {
                    "id": plan.id,
                    "plan_number": plan.plan_number,
                    "title": plan.title,
                    "status": plan.status,
                    "created_at": plan.created_at,
                },
                "plan_notes": plan_notes,
                "treatments": treatment_groups,
            }
        )
    return groups
