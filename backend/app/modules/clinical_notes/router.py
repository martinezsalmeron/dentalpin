"""Clinical notes module API endpoints.

All routes are mounted at ``/api/v1/clinical_notes/`` by the plugin loader.
"""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import ClinicContext, get_clinic_context, require_permission
from app.core.schemas import ApiResponse
from app.database import get_db

from .schemas import (
    ATTACHMENT_OWNER_PATTERN,
    NOTE_OWNER_PATTERN,
    ClinicalNoteCreate,
    ClinicalNoteEntry,
    ClinicalNoteResponse,
    ClinicalNoteUpdate,
    NoteAttachmentCreate,
    NoteAttachmentResponse,
    NoteTemplateResponse,
    PlanNotesGroup,
    RecentNoteEntry,
)
from .service import (
    AttachmentPatientMismatchError,
    NoteAttachmentService,
    NoteOwnerError,
    NoteService,
    list_grouped_for_patient,
    list_merged_for_plan,
    list_recent_for_patient,
    resolve_owner_patient,
)

router = APIRouter()


def _is_admin_role(ctx: ClinicContext) -> bool:
    return ctx.role == "admin"


# ---------------------------------------------------------------------------
# Notes
# ---------------------------------------------------------------------------


@router.get(
    "/notes",
    response_model=ApiResponse[list[ClinicalNoteResponse]],
)
async def list_notes(
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("clinical_notes.notes.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    owner_type: str = Query(..., pattern=NOTE_OWNER_PATTERN),
    owner_id: UUID = Query(...),
) -> ApiResponse[list[ClinicalNoteResponse]]:
    """List clinical notes for a single owner (patient / treatment / plan)."""
    try:
        # Stable 404 instead of a silently-empty list when the owner does
        # not exist in this clinic — also catches cross-clinic leak attempts.
        await resolve_owner_patient(db, ctx.clinic_id, owner_type, owner_id)
        notes = await NoteService.list_for_owner(db, ctx.clinic_id, owner_type, owner_id)
    except NoteOwnerError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return ApiResponse(data=[ClinicalNoteResponse.model_validate(n) for n in notes])


@router.post(
    "/notes",
    response_model=ApiResponse[ClinicalNoteResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_note(
    data: ClinicalNoteCreate,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("clinical_notes.notes.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[ClinicalNoteResponse]:
    """Create a clinical note. Owner must exist in the same clinic."""
    try:
        note = await NoteService.create(
            db,
            clinic_id=ctx.clinic_id,
            user_id=ctx.user_id,
            note_type=data.note_type,
            owner_type=data.owner_type,
            owner_id=data.owner_id,
            body=data.body,
            tooth_number=data.tooth_number,
            attachment_document_ids=data.attachment_document_ids,
        )
    except NoteOwnerError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except AttachmentPatientMismatchError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return ApiResponse(data=ClinicalNoteResponse.model_validate(note))


@router.patch(
    "/notes/{note_id}",
    response_model=ApiResponse[ClinicalNoteResponse],
)
async def update_note(
    note_id: UUID,
    data: ClinicalNoteUpdate,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("clinical_notes.notes.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[ClinicalNoteResponse]:
    """Edit a note body. Author or admin only."""
    try:
        note = await NoteService.update(
            db,
            clinic_id=ctx.clinic_id,
            note_id=note_id,
            body=data.body,
            user_id=ctx.user_id,
            is_admin=_is_admin_role(ctx),
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    note = await NoteService.get(db, ctx.clinic_id, note_id)
    return ApiResponse(data=ClinicalNoteResponse.model_validate(note))


@router.delete(
    "/notes/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_note(
    note_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("clinical_notes.notes.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Soft-delete a note. Author or admin only."""
    try:
        ok = await NoteService.soft_delete(
            db,
            clinic_id=ctx.clinic_id,
            note_id=note_id,
            user_id=ctx.user_id,
            is_admin=_is_admin_role(ctx),
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    if not ok:
        raise HTTPException(status_code=404, detail="Note not found")


# ---------------------------------------------------------------------------
# Attachments
# ---------------------------------------------------------------------------


@router.get(
    "/attachments",
    response_model=ApiResponse[list[NoteAttachmentResponse]],
)
async def list_attachments(
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("clinical_notes.notes.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    owner_type: str = Query(..., pattern=ATTACHMENT_OWNER_PATTERN),
    owner_id: UUID = Query(...),
) -> ApiResponse[list[NoteAttachmentResponse]]:
    """List attachments for an owner — superset includes appointment_treatment."""
    try:
        rows = await NoteAttachmentService.list_for_owner(db, ctx.clinic_id, owner_type, owner_id)
    except NoteOwnerError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return ApiResponse(data=[NoteAttachmentResponse.model_validate(r) for r in rows])


@router.post(
    "/attachments",
    response_model=ApiResponse[NoteAttachmentResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_attachment(
    data: NoteAttachmentCreate,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("clinical_notes.notes.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[NoteAttachmentResponse]:
    """Link an already-uploaded Document to an owner."""
    try:
        row = await NoteAttachmentService.link(
            db,
            clinic_id=ctx.clinic_id,
            document_id=data.document_id,
            owner_type=data.owner_type,
            owner_id=data.owner_id,
            note_id=data.note_id,
            display_order=data.display_order,
        )
    except NoteOwnerError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except AttachmentPatientMismatchError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return ApiResponse(data=NoteAttachmentResponse.model_validate(row))


@router.delete(
    "/attachments/{attachment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_attachment(
    attachment_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("clinical_notes.notes.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Unlink an attachment (does not delete the underlying Document)."""
    ok = await NoteAttachmentService.unlink(
        db, clinic_id=ctx.clinic_id, attachment_id=attachment_id
    )
    if not ok:
        raise HTTPException(status_code=404, detail="Attachment not found")


# ---------------------------------------------------------------------------
# Aggregate feeds
# ---------------------------------------------------------------------------


@router.get(
    "/patients/{patient_id}/recent",
    response_model=ApiResponse[list[RecentNoteEntry]],
)
async def list_patient_recent_notes(
    patient_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("clinical_notes.notes.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    types: list[str] | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    before: datetime | None = Query(default=None),
) -> ApiResponse[list[RecentNoteEntry]]:
    """Recent notes for a patient — feed for the Summary tab."""
    from .models import NOTE_TYPES

    if types:
        invalid = [t for t in types if t not in NOTE_TYPES]
        if invalid:
            raise HTTPException(
                status_code=422,
                detail=f"Unknown note_type values: {invalid}",
            )
    try:
        entries = await list_recent_for_patient(
            db,
            clinic_id=ctx.clinic_id,
            patient_id=patient_id,
            note_types=types,
            limit=limit,
            before=before,
        )
    except NoteOwnerError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return ApiResponse(data=[RecentNoteEntry.model_validate(e) for e in entries])


@router.get(
    "/patients/{patient_id}/by-plan",
    response_model=ApiResponse[list[PlanNotesGroup]],
)
async def list_patient_clinical_notes_by_plan(
    patient_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("clinical_notes.notes.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[list[PlanNotesGroup]]:
    """Clinical notes grouped by plan → treatment for one patient."""
    groups = await list_grouped_for_patient(db, ctx.clinic_id, patient_id)
    return ApiResponse(data=[PlanNotesGroup.model_validate(g) for g in groups])


@router.get(
    "/treatment-plans/{plan_id}/merged",
    response_model=ApiResponse[list[ClinicalNoteEntry]],
)
async def list_plan_merged_clinical_notes(
    plan_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("clinical_notes.notes.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[list[ClinicalNoteEntry]]:
    """Merged clinical-notes feed for a plan (plan + treatment + visit)."""
    entries = await list_merged_for_plan(db, ctx.clinic_id, plan_id)
    return ApiResponse(data=[ClinicalNoteEntry.model_validate(e) for e in entries])


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------


@router.get(
    "/note-templates",
    response_model=ApiResponse[list[NoteTemplateResponse]],
)
async def list_note_templates(
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("clinical_notes.notes.read"))],
    category: str | None = Query(default=None),
) -> ApiResponse[list[NoteTemplateResponse]]:
    """Return static template catalog, optionally filtered by category."""
    from .note_templates import NOTE_TEMPLATES, list_templates

    entries: list[NoteTemplateResponse] = []
    if category:
        for tpl in list_templates(category):
            entries.append(
                NoteTemplateResponse(
                    id=tpl["id"],
                    category=category,
                    i18n_key=tpl["i18n_key"],
                    body=tpl["body"],
                )
            )
    else:
        for cat, bucket in NOTE_TEMPLATES.items():
            for tpl in bucket:
                entries.append(
                    NoteTemplateResponse(
                        id=tpl["id"],
                        category=cat,
                        i18n_key=tpl["i18n_key"],
                        body=tpl["body"],
                    )
                )
    return ApiResponse(data=entries)
