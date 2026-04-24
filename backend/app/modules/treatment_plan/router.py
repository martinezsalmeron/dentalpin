"""Treatment plan module API endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import ClinicContext, get_clinic_context, require_permission
from app.core.schemas import ApiResponse, PaginatedApiResponse
from app.database import get_db

from .schemas import (
    ClinicalNoteCreate,
    ClinicalNoteEntry,
    ClinicalNoteResponse,
    ClinicalNoteUpdate,
    CompleteItemRequest,
    GenerateBudgetResponse,
    LinkBudgetRequest,
    NoteAttachmentCreate,
    NoteAttachmentResponse,
    NoteTemplateResponse,
    PlannedTreatmentItemCreate,
    PlannedTreatmentItemResponse,
    PlannedTreatmentItemUpdate,
    PlanNotesGroup,
    ReorderItemsRequest,
    TreatmentMediaCreate,
    TreatmentMediaResponse,
    TreatmentPlanCreate,
    TreatmentPlanDetailResponse,
    TreatmentPlanResponse,
    TreatmentPlanStatusUpdate,
    TreatmentPlanUpdate,
)
from .service import PlanLockedError, TreatmentPlanService

router = APIRouter()


# -----------------------------------------------------------------------------
# Treatment Plans CRUD
# -----------------------------------------------------------------------------


@router.get("/treatment-plans", response_model=PaginatedApiResponse[TreatmentPlanResponse])
async def list_treatment_plans(
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("treatment_plan.plans.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    patient_id: UUID | None = None,
    status: list[str] | None = Query(default=None),
) -> PaginatedApiResponse[TreatmentPlanResponse]:
    """List treatment plans with pagination and filters."""
    plans, total = await TreatmentPlanService.list(
        db, ctx.clinic_id, page, page_size, patient_id=patient_id, status=status
    )
    # Compute counts and totals from loaded items
    for p in plans:
        items = p.items or []
        p.item_count = len(items)
        p.completed_count = sum(1 for i in items if i.status == "completed")
        p.total = sum(
            float(i.treatment.price_snapshot) if i.treatment and i.treatment.price_snapshot else 0
            for i in items
        )
    return PaginatedApiResponse(
        data=[TreatmentPlanResponse.model_validate(p) for p in plans],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/treatment-plans/patient/{patient_id}",
    response_model=PaginatedApiResponse[TreatmentPlanResponse],
)
async def list_patient_plans(
    patient_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("treatment_plan.plans.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> PaginatedApiResponse[TreatmentPlanResponse]:
    """List treatment plans for a specific patient."""
    plans, total = await TreatmentPlanService.list(
        db, ctx.clinic_id, page, page_size, patient_id=patient_id
    )
    # Compute counts and totals from loaded items
    for p in plans:
        items = p.items or []
        p.item_count = len(items)
        p.completed_count = sum(1 for i in items if i.status == "completed")
        p.total = sum(
            float(i.treatment.price_snapshot) if i.treatment and i.treatment.price_snapshot else 0
            for i in items
        )
    return PaginatedApiResponse(
        data=[TreatmentPlanResponse.model_validate(p) for p in plans],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/treatment-plans/{plan_id}",
    response_model=ApiResponse[TreatmentPlanDetailResponse],
)
async def get_treatment_plan(
    plan_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("treatment_plan.plans.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[TreatmentPlanDetailResponse]:
    """Get a treatment plan with full details."""
    plan = await TreatmentPlanService.get(db, ctx.clinic_id, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Treatment plan not found")
    return ApiResponse(data=TreatmentPlanDetailResponse.model_validate(plan))


@router.post(
    "/treatment-plans",
    response_model=ApiResponse[TreatmentPlanResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_treatment_plan(
    data: TreatmentPlanCreate,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("treatment_plan.plans.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[TreatmentPlanResponse]:
    """Create a new treatment plan."""
    try:
        plan = await TreatmentPlanService.create(db, ctx.clinic_id, ctx.user_id, data.model_dump())
        return ApiResponse(data=TreatmentPlanResponse.model_validate(plan))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put(
    "/treatment-plans/{plan_id}",
    response_model=ApiResponse[TreatmentPlanResponse],
)
async def update_treatment_plan(
    plan_id: UUID,
    data: TreatmentPlanUpdate,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("treatment_plan.plans.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[TreatmentPlanResponse]:
    """Update a treatment plan."""
    plan = await TreatmentPlanService.update(
        db, ctx.clinic_id, plan_id, data.model_dump(exclude_unset=True)
    )
    if not plan:
        raise HTTPException(status_code=404, detail="Treatment plan not found")
    return ApiResponse(data=TreatmentPlanResponse.model_validate(plan))


@router.patch(
    "/treatment-plans/{plan_id}/status",
    response_model=ApiResponse[TreatmentPlanResponse],
)
async def update_plan_status(
    plan_id: UUID,
    data: TreatmentPlanStatusUpdate,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("treatment_plan.plans.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[TreatmentPlanResponse]:
    """Change treatment plan status."""
    try:
        plan = await TreatmentPlanService.update_status(
            db, ctx.clinic_id, plan_id, data.status, ctx.user_id
        )
        if not plan:
            raise HTTPException(status_code=404, detail="Treatment plan not found")
        return ApiResponse(data=TreatmentPlanResponse.model_validate(plan))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/treatment-plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_treatment_plan(
    plan_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("treatment_plan.plans.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Soft delete (archive) a treatment plan."""
    deleted = await TreatmentPlanService.delete(db, ctx.clinic_id, plan_id, ctx.user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Treatment plan not found")


# -----------------------------------------------------------------------------
# Plan Items
# -----------------------------------------------------------------------------


@router.post(
    "/treatment-plans/{plan_id}/items",
    response_model=ApiResponse[PlannedTreatmentItemResponse],
    status_code=status.HTTP_201_CREATED,
)
async def add_plan_item(
    plan_id: UUID,
    data: PlannedTreatmentItemCreate,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("treatment_plan.plans.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[PlannedTreatmentItemResponse]:
    """Add a treatment item to the plan."""
    try:
        item = await TreatmentPlanService.add_item(db, ctx.clinic_id, plan_id, data.model_dump())
        return ApiResponse(data=PlannedTreatmentItemResponse.model_validate(item))
    except PlanLockedError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put(
    "/treatment-plans/{plan_id}/items/{item_id}",
    response_model=ApiResponse[PlannedTreatmentItemResponse],
)
async def update_plan_item(
    plan_id: UUID,
    item_id: UUID,
    data: PlannedTreatmentItemUpdate,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("treatment_plan.plans.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[PlannedTreatmentItemResponse]:
    """Update a planned treatment item."""
    try:
        item = await TreatmentPlanService.update_item(
            db, ctx.clinic_id, plan_id, item_id, data.model_dump(exclude_unset=True)
        )
    except PlanLockedError as e:
        raise HTTPException(status_code=409, detail=str(e))
    if not item:
        raise HTTPException(status_code=404, detail="Treatment item not found")
    return ApiResponse(data=PlannedTreatmentItemResponse.model_validate(item))


@router.delete(
    "/treatment-plans/{plan_id}/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_plan_item(
    plan_id: UUID,
    item_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("treatment_plan.plans.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Remove an item from the plan."""
    try:
        removed = await TreatmentPlanService.remove_item(
            db, ctx.clinic_id, plan_id, item_id, ctx.user_id
        )
    except PlanLockedError as e:
        raise HTTPException(status_code=409, detail=str(e))
    if not removed:
        raise HTTPException(status_code=404, detail="Treatment item not found")


@router.patch(
    "/treatment-plans/{plan_id}/items/reorder",
    response_model=ApiResponse[TreatmentPlanDetailResponse],
)
async def reorder_plan_items(
    plan_id: UUID,
    data: ReorderItemsRequest,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("treatment_plan.plans.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[TreatmentPlanDetailResponse]:
    """Reorder all items of a plan in a single atomic call.

    `item_ids` MUST cover exactly the plan's current items. Returns the full plan
    with items in the new order so the caller doesn't need a second round-trip.
    """
    try:
        items = await TreatmentPlanService.reorder_items(db, ctx.clinic_id, plan_id, data.item_ids)
    except PlanLockedError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    if items is None:
        raise HTTPException(status_code=404, detail="Treatment plan not found")

    plan = await TreatmentPlanService.get(db, ctx.clinic_id, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Treatment plan not found")
    return ApiResponse(data=TreatmentPlanDetailResponse.model_validate(plan))


@router.patch(
    "/treatment-plans/{plan_id}/items/{item_id}/complete",
    response_model=ApiResponse[PlannedTreatmentItemResponse],
)
async def complete_plan_item(
    plan_id: UUID,
    item_id: UUID,
    data: CompleteItemRequest,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("treatment_plan.plans.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[PlannedTreatmentItemResponse]:
    """Mark a treatment item as completed."""
    item = await TreatmentPlanService.complete_item(
        db,
        ctx.clinic_id,
        plan_id,
        item_id,
        ctx.user_id,
        data.completed_without_appointment,
        data.notes,
        note_body=data.note_body,
        attachment_document_ids=data.attachment_document_ids,
    )
    if not item:
        raise HTTPException(status_code=404, detail="Treatment item not found")
    return ApiResponse(data=PlannedTreatmentItemResponse.model_validate(item))


# -----------------------------------------------------------------------------
# Budget Integration
# -----------------------------------------------------------------------------


@router.post(
    "/treatment-plans/{plan_id}/link-budget",
    response_model=ApiResponse[TreatmentPlanResponse],
)
async def link_budget_to_plan(
    plan_id: UUID,
    data: LinkBudgetRequest,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("treatment_plan.plans.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[TreatmentPlanResponse]:
    """Link an existing budget to the treatment plan."""
    try:
        plan = await TreatmentPlanService.link_budget(db, ctx.clinic_id, plan_id, data.budget_id)
        if not plan:
            raise HTTPException(status_code=404, detail="Treatment plan not found")
        return ApiResponse(data=TreatmentPlanResponse.model_validate(plan))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/treatment-plans/{plan_id}/sync-budget",
    response_model=ApiResponse[dict],
)
async def sync_plan_with_budget(
    plan_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("treatment_plan.plans.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[dict]:
    """Request synchronization of plan items with linked budget."""
    success = await TreatmentPlanService.request_budget_sync(db, ctx.clinic_id, plan_id)
    if not success:
        raise HTTPException(
            status_code=400,
            detail="Cannot sync: plan not found or no budget linked",
        )
    return ApiResponse(data={"synced": True})


@router.post(
    "/treatment-plans/{plan_id}/unlock",
    response_model=ApiResponse[TreatmentPlanResponse],
)
async def unlock_treatment_plan(
    plan_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("treatment_plan.plans.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[TreatmentPlanResponse]:
    """Unlock a plan by cancelling its linked budget so it can be modified."""
    try:
        plan = await TreatmentPlanService.unlock(db, ctx.clinic_id, plan_id, ctx.user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    if not plan:
        raise HTTPException(status_code=404, detail="Treatment plan not found")
    return ApiResponse(data=TreatmentPlanResponse.model_validate(plan))


@router.post(
    "/treatment-plans/{plan_id}/generate-budget",
    response_model=ApiResponse[GenerateBudgetResponse],
    status_code=status.HTTP_201_CREATED,
)
async def generate_budget_from_plan(
    plan_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("treatment_plan.plans.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[GenerateBudgetResponse]:
    """Generate a new budget from the treatment plan items."""
    from app.modules.budget.service import BudgetService

    plan = await TreatmentPlanService.get(db, ctx.clinic_id, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Treatment plan not found")

    # Check if existing linked budget is cancelled - if so, allow creating new one
    if plan.budget_id:
        from app.modules.budget.models import Budget

        existing_budget = await db.get(Budget, plan.budget_id)
        if existing_budget and existing_budget.status == "cancelled":
            # Unlink cancelled budget to allow new one
            plan.budget_id = None
        else:
            raise HTTPException(status_code=400, detail="Plan already has a budget linked")

    if not plan.items:
        raise HTTPException(status_code=400, detail="Plan has no items to create budget from")

    # Collect catalog items from plan items, resolving everything from Treatment.
    budget_items = []
    for item in plan.items:
        treatment = item.treatment
        if not treatment or not treatment.catalog_item_id:
            continue
        primary_tooth = treatment.teeth[0].tooth_number if treatment.teeth else None
        primary_surfaces = treatment.teeth[0].surfaces if treatment.teeth else None
        budget_items.append(
            {
                "catalog_item_id": str(treatment.catalog_item_id),
                "quantity": 1,
                "tooth_number": primary_tooth,
                "surfaces": primary_surfaces,
                "treatment_id": str(treatment.id),
                "unit_price": treatment.price_snapshot,
            }
        )

    if not budget_items:
        raise HTTPException(
            status_code=400,
            detail="No catalog items found in plan to create budget",
        )

    # Create budget via budget service
    from datetime import date

    budget = await BudgetService.create_budget(
        db,
        ctx.clinic_id,
        ctx.user_id,
        {
            "patient_id": plan.patient_id,
            "valid_from": date.today(),
            "items": budget_items,
            "internal_notes": f"Generated from treatment plan {plan.plan_number}",
        },
    )

    # Link budget to plan
    plan.budget_id = budget.id

    return ApiResponse(
        data=GenerateBudgetResponse(
            budget_id=budget.id,
            budget_number=budget.budget_number,
        )
    )


# -----------------------------------------------------------------------------
# Media
# -----------------------------------------------------------------------------


@router.post(
    "/treatment-plans/items/{item_id}/media",
    response_model=ApiResponse[TreatmentMediaResponse],
    status_code=status.HTTP_201_CREATED,
)
async def add_media_to_item(
    item_id: UUID,
    data: TreatmentMediaCreate,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("treatment_plan.plans.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[TreatmentMediaResponse]:
    """Add media to a treatment item."""
    try:
        media = await TreatmentPlanService.add_media(db, ctx.clinic_id, item_id, data.model_dump())
        return ApiResponse(data=TreatmentMediaResponse.model_validate(media))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/treatment-plans/items/{item_id}/media/{media_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_media_from_item(
    item_id: UUID,
    media_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("treatment_plan.plans.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Remove media from a treatment item."""
    removed = await TreatmentPlanService.remove_media(db, ctx.clinic_id, item_id, media_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Media not found")


# -----------------------------------------------------------------------------
# Clinical notes + polymorphic attachments
# -----------------------------------------------------------------------------


def _is_admin_role(ctx: ClinicContext) -> bool:
    return ctx.role == "admin"


@router.get(
    "/notes",
    response_model=ApiResponse[list[ClinicalNoteResponse]],
)
async def list_notes(
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("treatment_plan.notes.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    owner_type: str = Query(..., pattern="^(plan|plan_item)$"),
    owner_id: UUID = Query(...),
) -> ApiResponse[list[ClinicalNoteResponse]]:
    """List clinical notes for a single plan or plan_item owner."""
    from .notes_service import NoteOwnerError, NoteService

    try:
        # Validate the owner (plan / plan_item) exists in this clinic before
        # listing. Without this, a cross-clinic user gets 200 [] instead of an
        # explicit "not found" — leaks nothing but hides the isolation error.
        await NoteService.resolve_owner_patient(db, ctx.clinic_id, owner_type, owner_id)
        notes = await NoteService.list_for_owner(db, ctx.clinic_id, owner_type, owner_id)
    except NoteOwnerError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return ApiResponse(data=[ClinicalNoteResponse.model_validate(n) for n in notes])


@router.post(
    "/notes",
    response_model=ApiResponse[ClinicalNoteResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_note(
    data: ClinicalNoteCreate,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("treatment_plan.notes.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[ClinicalNoteResponse]:
    """Create a note (plan or plan_item) with optional initial attachments."""
    from .notes_service import (
        AttachmentPatientMismatchError,
        NoteOwnerError,
        NoteService,
    )

    try:
        note = await NoteService.create(
            db,
            clinic_id=ctx.clinic_id,
            user_id=ctx.user_id,
            owner_type=data.owner_type,
            owner_id=data.owner_id,
            body=data.body,
            attachment_document_ids=data.attachment_document_ids,
        )
    except NoteOwnerError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except AttachmentPatientMismatchError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return ApiResponse(data=ClinicalNoteResponse.model_validate(note))


@router.patch(
    "/notes/{note_id}",
    response_model=ApiResponse[ClinicalNoteResponse],
)
async def update_note(
    note_id: UUID,
    data: ClinicalNoteUpdate,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("treatment_plan.notes.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[ClinicalNoteResponse]:
    """Edit a note body. Author or admin only."""
    from .notes_service import NoteService

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
        raise HTTPException(status_code=403, detail=str(e))
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    # Reload with attachments for response
    note = await NoteService.get(db, ctx.clinic_id, note_id)
    return ApiResponse(data=ClinicalNoteResponse.model_validate(note))


@router.delete(
    "/notes/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_note(
    note_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("treatment_plan.notes.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Soft-delete a note. Author or admin only."""
    from .notes_service import NoteService

    try:
        ok = await NoteService.soft_delete(
            db,
            clinic_id=ctx.clinic_id,
            note_id=note_id,
            user_id=ctx.user_id,
            is_admin=_is_admin_role(ctx),
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    if not ok:
        raise HTTPException(status_code=404, detail="Note not found")


@router.get(
    "/attachments",
    response_model=ApiResponse[list[NoteAttachmentResponse]],
)
async def list_attachments(
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("treatment_plan.notes.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    owner_type: str = Query(..., pattern="^(plan|plan_item|appointment_treatment)$"),
    owner_id: UUID = Query(...),
) -> ApiResponse[list[NoteAttachmentResponse]]:
    """List all attachments for an owner, including note-less direct uploads."""
    from .notes_service import NoteAttachmentService, NoteOwnerError

    try:
        rows = await NoteAttachmentService.list_for_owner(db, ctx.clinic_id, owner_type, owner_id)
    except NoteOwnerError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return ApiResponse(data=[NoteAttachmentResponse.model_validate(r) for r in rows])


@router.post(
    "/attachments",
    response_model=ApiResponse[NoteAttachmentResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_attachment(
    data: NoteAttachmentCreate,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("treatment_plan.notes.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[NoteAttachmentResponse]:
    """Link an already-uploaded Document to an owner (plan / plan_item / visit)."""
    from .notes_service import (
        AttachmentPatientMismatchError,
        NoteAttachmentService,
        NoteOwnerError,
    )

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
        raise HTTPException(status_code=404, detail=str(e))
    except AttachmentPatientMismatchError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return ApiResponse(data=NoteAttachmentResponse.model_validate(row))


@router.delete(
    "/attachments/{attachment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_attachment(
    attachment_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("treatment_plan.notes.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Unlink an attachment (does not delete the underlying Document)."""
    from .notes_service import NoteAttachmentService

    ok = await NoteAttachmentService.unlink(
        db, clinic_id=ctx.clinic_id, attachment_id=attachment_id
    )
    if not ok:
        raise HTTPException(status_code=404, detail="Attachment not found")


@router.get(
    "/treatment-plans/{plan_id}/clinical-notes",
    response_model=ApiResponse[list[ClinicalNoteEntry]],
)
async def list_merged_clinical_notes(
    plan_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("treatment_plan.notes.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[list[ClinicalNoteEntry]]:
    """Merged clinical-notes feed for a plan (plan + items + visits)."""
    from .notes_service import list_merged_for_plan

    entries = await list_merged_for_plan(db, ctx.clinic_id, plan_id)
    return ApiResponse(data=[ClinicalNoteEntry.model_validate(e) for e in entries])


@router.get(
    "/patients/{patient_id}/clinical-notes",
    response_model=ApiResponse[list[PlanNotesGroup]],
)
async def list_patient_clinical_notes(
    patient_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("treatment_plan.notes.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[list[PlanNotesGroup]]:
    """Clinical notes grouped by plan → treatment for one patient."""
    from .notes_service import list_grouped_for_patient

    groups = await list_grouped_for_patient(db, ctx.clinic_id, patient_id)
    return ApiResponse(data=[PlanNotesGroup.model_validate(g) for g in groups])


@router.get(
    "/note-templates",
    response_model=ApiResponse[list[NoteTemplateResponse]],
)
async def list_note_templates(
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("treatment_plan.notes.read"))],
    category: str | None = Query(default=None),
) -> ApiResponse[list[NoteTemplateResponse]]:
    """Return static note-template catalog, optionally filtered by category."""
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
