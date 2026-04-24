"""Clinical notes + polymorphic attachments service layer.

Owns CRUD for ``clinical_notes`` and ``clinical_note_attachments``. Events
are published so ``patient_timeline`` (and any future subscriber) can react
without importing this module.
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

from .models import (
    ATTACHMENT_OWNER_APPOINTMENT_TREATMENT,
    ATTACHMENT_OWNER_TYPES,
    NOTE_OWNER_PLAN,
    NOTE_OWNER_PLAN_ITEM,
    NOTE_OWNER_TYPES,
    ClinicalNote,
    ClinicalNoteAttachment,
    PlannedTreatmentItem,
    TreatmentPlan,
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
    """Owner (plan / plan_item) does not exist in this clinic."""


class AttachmentPatientMismatchError(ValueError):
    """Document belongs to a different patient than the note owner."""


class NoteService:
    """CRUD for plan and plan_item clinical notes."""

    # -----------------------------------------------------------------
    # Owner resolution
    # -----------------------------------------------------------------

    @staticmethod
    async def _resolve_plan_patient(
        db: AsyncSession, clinic_id: UUID, plan_id: UUID
    ) -> tuple[TreatmentPlan, UUID]:
        result = await db.execute(
            select(TreatmentPlan).where(
                TreatmentPlan.id == plan_id,
                TreatmentPlan.clinic_id == clinic_id,
                TreatmentPlan.deleted_at.is_(None),
            )
        )
        plan = result.scalar_one_or_none()
        if plan is None:
            raise NoteOwnerError(f"treatment_plan {plan_id} not found")
        return plan, plan.patient_id

    @staticmethod
    async def _resolve_item_patient(
        db: AsyncSession, clinic_id: UUID, item_id: UUID
    ) -> tuple[PlannedTreatmentItem, UUID, UUID]:
        result = await db.execute(
            select(PlannedTreatmentItem)
            .where(
                PlannedTreatmentItem.id == item_id,
                PlannedTreatmentItem.clinic_id == clinic_id,
            )
            .options(selectinload(PlannedTreatmentItem.treatment_plan))
        )
        item = result.scalar_one_or_none()
        if item is None or item.treatment_plan is None:
            raise NoteOwnerError(f"planned_treatment_item {item_id} not found")
        return item, item.treatment_plan_id, item.treatment_plan.patient_id

    @classmethod
    async def resolve_owner_patient(
        cls,
        db: AsyncSession,
        clinic_id: UUID,
        owner_type: str,
        owner_id: UUID,
    ) -> tuple[UUID | None, UUID]:
        """Return (plan_id, patient_id) for a note owner, or raise NoteOwnerError.

        ``plan_id`` is None when owner_type is ``plan`` (plan_id == owner_id).
        """
        if owner_type == NOTE_OWNER_PLAN:
            plan, patient_id = await cls._resolve_plan_patient(db, clinic_id, owner_id)
            return plan.id, patient_id
        if owner_type == NOTE_OWNER_PLAN_ITEM:
            item, plan_id, patient_id = await cls._resolve_item_patient(db, clinic_id, owner_id)
            return plan_id, patient_id
        raise NoteOwnerError(f"unsupported note owner_type {owner_type!r}")

    # -----------------------------------------------------------------
    # Queries
    # -----------------------------------------------------------------

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

    # -----------------------------------------------------------------
    # Mutations
    # -----------------------------------------------------------------

    @classmethod
    async def create(
        cls,
        db: AsyncSession,
        *,
        clinic_id: UUID,
        user_id: UUID,
        owner_type: str,
        owner_id: UUID,
        body: str,
        attachment_document_ids: Iterable[UUID] | None = None,
    ) -> ClinicalNote:
        plan_id, patient_id = await cls.resolve_owner_patient(db, clinic_id, owner_type, owner_id)

        note = ClinicalNote(
            clinic_id=clinic_id,
            owner_type=owner_type,
            owner_id=owner_id,
            body=body,
            author_id=user_id,
        )
        db.add(note)
        await db.flush()  # populate note.id for attachment links

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

        publish_event = (
            EventType.TREATMENT_PLAN_NOTE_CREATED
            if owner_type == NOTE_OWNER_PLAN
            else EventType.TREATMENT_PLAN_ITEM_NOTE_CREATED
        )
        event_bus.publish(
            publish_event,
            {
                "clinic_id": str(clinic_id),
                "patient_id": str(patient_id),
                "plan_id": str(plan_id) if plan_id else None,
                "plan_item_id": str(owner_id) if owner_type == NOTE_OWNER_PLAN_ITEM else None,
                "note_id": str(note.id),
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


class NoteAttachmentService:
    """Polymorphic link between ``media.Document`` and a notes owner."""

    # -----------------------------------------------------------------
    # Owner patient resolution
    # -----------------------------------------------------------------

    @staticmethod
    async def _resolve_appointment_treatment_patient(
        db: AsyncSession, clinic_id: UUID, appointment_treatment_id: UUID
    ) -> UUID:
        # Deferred import: agenda is a sibling module; accessing it by model
        # is the same pattern used by treatment_plan.events.on_appointment_completed.
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

    @classmethod
    async def _resolve_owner_patient(
        cls,
        db: AsyncSession,
        clinic_id: UUID,
        owner_type: str,
        owner_id: UUID,
    ) -> UUID:
        if owner_type == ATTACHMENT_OWNER_APPOINTMENT_TREATMENT:
            return await cls._resolve_appointment_treatment_patient(db, clinic_id, owner_id)
        # plan + plan_item resolve via NoteService
        _, patient_id = await NoteService.resolve_owner_patient(db, clinic_id, owner_type, owner_id)
        return patient_id

    # -----------------------------------------------------------------
    # Queries
    # -----------------------------------------------------------------

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

    # -----------------------------------------------------------------
    # Mutations
    # -----------------------------------------------------------------

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
            owner_patient_id = await cls._resolve_owner_patient(db, clinic_id, owner_type, owner_id)

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
            owner_patient_id = await cls._resolve_owner_patient(db, clinic_id, owner_type, owner_id)
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


async def list_merged_for_plan(db: AsyncSession, clinic_id: UUID, plan_id: UUID) -> list[dict]:
    """Merged feed: plan notes + item notes + visit notes (AppointmentTreatment).

    Returned shape matches :class:`.schemas.ClinicalNoteEntry`. Sorted by
    ``created_at`` desc across sources.
    """
    # Import inside function — agenda is a sibling module; see rationale in
    # NoteAttachmentService._resolve_appointment_treatment_patient.
    from app.modules.agenda.models import Appointment, AppointmentTreatment

    # Resolve plan + item IDs for this plan
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
        select(PlannedTreatmentItem.id).where(
            PlannedTreatmentItem.treatment_plan_id == plan_id,
            PlannedTreatmentItem.clinic_id == clinic_id,
        )
    )
    item_ids = [row[0] for row in items_result.all()]

    # Plan + item notes
    item_clause = ClinicalNote.owner_id.in_(item_ids) if item_ids else false()
    owner_filter = or_(
        and_(
            ClinicalNote.owner_type == NOTE_OWNER_PLAN,
            ClinicalNote.owner_id == plan_id,
        ),
        and_(
            ClinicalNote.owner_type == NOTE_OWNER_PLAN_ITEM,
            item_clause,
        ),
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
        is_item = note.owner_type == NOTE_OWNER_PLAN_ITEM
        entries.append(
            {
                "source": "plan_item" if is_item else "plan",
                "note_id": note.id,
                "owner_id": note.owner_id,
                "plan_item_id": note.owner_id if is_item else None,
                "body": note.body,
                "author_id": note.author_id,
                "created_at": note.created_at,
                "updated_at": note.updated_at,
                "attachments": list(note.attachments),
            }
        )

    # Visit notes — AppointmentTreatment rows linked to any plan_item of this plan
    if item_ids:
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
        visit_rows = visit_result.all()
        for apt_tr, apt_created in visit_rows:
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
    """Patient-level feed: plans ordered by created_at desc, each with its
    plan-level notes and a per-treatment bucket of plan_item + visit notes.

    Returned shape matches :class:`.schemas.PlanNotesGroup`. The UI renders
    this as ``Plan → Tratamiento → Notas`` without additional lookups.
    """
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

    from .service import TreatmentPlanService

    groups: list[dict] = []
    for plan in plans:
        # Load full plan w/ items + treatment relationships (needed for UI labels).
        plan_full = await TreatmentPlanService.get(db, clinic_id, plan.id)
        if plan_full is None:
            continue
        plan_full.item_count = len(plan_full.items or [])
        plan_full.completed_count = sum(
            1 for i in (plan_full.items or []) if i.status == "completed"
        )
        plan_full.total = sum(
            float(i.treatment.price_snapshot) if i.treatment and i.treatment.price_snapshot else 0
            for i in (plan_full.items or [])
        )

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

        # Sort items by sequence_order so the UI mirrors the plan detail view.
        items_sorted = sorted(plan_full.items or [], key=lambda i: i.sequence_order)
        treatment_groups = [
            {"plan_item": item, "notes": by_item.get(item.id, [])} for item in items_sorted
        ]

        groups.append(
            {
                "plan": plan_full,
                "plan_notes": plan_notes,
                "treatments": treatment_groups,
            }
        )
    return groups
