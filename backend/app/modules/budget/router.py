"""Budget module API router."""

from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import ClinicContext, get_clinic_context, require_permission
from app.core.schemas import ApiResponse, PaginatedApiResponse
from app.database import get_db

from .pdf import BudgetPDFService
from .schemas import (
    BudgetAcceptRequest,
    BudgetCancelRequest,
    BudgetCreate,
    BudgetDetailResponse,
    BudgetHistoryResponse,
    BudgetItemCreate,
    BudgetItemResponse,
    BudgetItemUpdate,
    BudgetListResponse,
    BudgetRejectRequest,
    BudgetResponse,
    BudgetSendRequest,
    BudgetUpdate,
    BudgetVersionListResponse,
    BudgetVersionResponse,
    TreatmentPlanBrief,
)
from .service import BudgetHistoryService, BudgetItemService, BudgetService
from .workflow import BudgetWorkflowError, BudgetWorkflowService

router = APIRouter()


# ============================================================================
# Budget CRUD Endpoints
# ============================================================================


@router.get("/budgets", response_model=PaginatedApiResponse[BudgetListResponse])
async def list_budgets(
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("budget.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    patient_id: UUID | None = Query(default=None),
    status: list[str] | None = Query(default=None),
    created_by: UUID | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    expired: bool | None = Query(default=None),
    search: str | None = Query(default=None, max_length=100),
) -> PaginatedApiResponse[BudgetListResponse]:
    """List budgets with filtering and pagination."""
    budgets, total = await BudgetService.list_budgets(
        db,
        ctx.clinic_id,
        page=page,
        page_size=page_size,
        patient_id=patient_id,
        status=status,
        created_by=created_by,
        date_from=date_from,
        date_to=date_to,
        expired=expired,
        search=search,
    )
    return PaginatedApiResponse(
        data=[BudgetListResponse.model_validate(b) for b in budgets],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/budgets/{budget_id}", response_model=ApiResponse[BudgetDetailResponse])
async def get_budget(
    budget_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("budget.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[BudgetDetailResponse]:
    """Get a budget by ID with full details."""
    budget = await BudgetService.get_budget(db, ctx.clinic_id, budget_id, include_items=True)
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    # Query for treatment plan that references this budget (reverse lookup)
    from app.modules.treatment_plan.models import TreatmentPlan

    result = await db.execute(
        select(TreatmentPlan).where(
            TreatmentPlan.budget_id == budget_id,
            TreatmentPlan.clinic_id == ctx.clinic_id,
            TreatmentPlan.deleted_at.is_(None),
        )
    )
    treatment_plan = result.scalar_one_or_none()

    # Build response with treatment plan
    response_data = BudgetDetailResponse.model_validate(budget)
    if treatment_plan:
        response_data.treatment_plan = TreatmentPlanBrief.model_validate(treatment_plan)

    return ApiResponse(data=response_data)


@router.post(
    "/budgets",
    response_model=ApiResponse[BudgetDetailResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_budget(
    data: BudgetCreate,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("budget.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[BudgetDetailResponse]:
    """Create a new budget."""
    # Verify patient exists
    from app.modules.clinical.models import Patient

    patient = await db.get(Patient, data.patient_id)
    if not patient or patient.clinic_id != ctx.clinic_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Patient not found",
        )

    budget = await BudgetService.create_budget(db, ctx.clinic_id, ctx.user_id, data.model_dump())

    # Reload with relationships
    budget = await BudgetService.get_budget(db, ctx.clinic_id, budget.id, include_items=True)
    return ApiResponse(data=BudgetDetailResponse.model_validate(budget))


@router.put("/budgets/{budget_id}", response_model=ApiResponse[BudgetDetailResponse])
async def update_budget(
    budget_id: UUID,
    data: BudgetUpdate,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("budget.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[BudgetDetailResponse]:
    """Update a budget (only allowed in draft status)."""
    budget = await BudgetService.get_budget(db, ctx.clinic_id, budget_id, include_items=True)
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    try:
        budget = await BudgetService.update_budget(
            db, budget, data.model_dump(exclude_unset=True), ctx.user_id
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Reload with relationships
    budget = await BudgetService.get_budget(db, ctx.clinic_id, budget.id, include_items=True)
    return ApiResponse(data=BudgetDetailResponse.model_validate(budget))


@router.delete("/budgets/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_budget(
    budget_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("budget.admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Soft-delete a budget."""
    budget = await BudgetService.get_budget(db, ctx.clinic_id, budget_id, include_items=False)
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    await BudgetService.delete_budget(db, budget, ctx.user_id)


# ============================================================================
# Budget Items Endpoints
# ============================================================================


@router.post(
    "/budgets/{budget_id}/items",
    response_model=ApiResponse[BudgetItemResponse],
    status_code=status.HTTP_201_CREATED,
)
async def add_budget_item(
    budget_id: UUID,
    data: BudgetItemCreate,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("budget.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[BudgetItemResponse]:
    """Add an item to a budget."""
    budget = await BudgetService.get_budget(db, ctx.clinic_id, budget_id, include_items=True)
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    try:
        item = await BudgetService.add_item(db, budget, data.model_dump(), ctx.user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return ApiResponse(data=BudgetItemResponse.model_validate(item))


@router.put(
    "/budgets/{budget_id}/items/{item_id}",
    response_model=ApiResponse[BudgetItemResponse],
)
async def update_budget_item(
    budget_id: UUID,
    item_id: UUID,
    data: BudgetItemUpdate,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("budget.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[BudgetItemResponse]:
    """Update a budget item."""
    budget = await BudgetService.get_budget(db, ctx.clinic_id, budget_id, include_items=True)
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    if budget.status != "draft":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Items can only be updated in draft budgets",
        )

    # Find item
    item = next((i for i in budget.items if i.id == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Budget item not found")

    item = await BudgetItemService.update_item(db, item, data.model_dump(exclude_unset=True))

    # Recalculate budget totals
    await BudgetService._recalculate_totals(db, budget)

    return ApiResponse(data=BudgetItemResponse.model_validate(item))


@router.delete(
    "/budgets/{budget_id}/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_budget_item(
    budget_id: UUID,
    item_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("budget.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Remove an item from a budget."""
    budget = await BudgetService.get_budget(db, ctx.clinic_id, budget_id, include_items=True)
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    # Find item
    item = next((i for i in budget.items if i.id == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Budget item not found")

    try:
        await BudgetService.remove_item(db, budget, item, ctx.user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ============================================================================
# Workflow Endpoints
# ============================================================================


@router.post("/budgets/{budget_id}/send", response_model=ApiResponse[BudgetResponse])
async def send_budget(
    budget_id: UUID,
    data: BudgetSendRequest,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("budget.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[BudgetResponse]:
    """Mark budget as sent to patient.

    Can be sent via email or marked as manually delivered (printed/handed).
    Email sending is handled by the notifications module via the budget.sent event.
    """
    budget = await BudgetService.get_budget(db, ctx.clinic_id, budget_id, include_items=True)
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    try:
        # Determine send method
        send_method = "email" if data.send_email else "manual"
        recipient_email = None

        if data.send_email:
            # Get patient email for sending
            from app.modules.clinical.models import Patient

            patient = await db.get(Patient, budget.patient_id)
            if not patient or not patient.email:
                raise BudgetWorkflowError("Patient has no email address")
            recipient_email = patient.email

        # This will publish the budget.sent event, which the notifications
        # module will handle (sending email if send_method="email" and
        # the clinic has budget_sent notifications enabled)
        budget = await BudgetWorkflowService.send_budget(
            db,
            budget,
            ctx.user_id,
            send_method=send_method,
            recipient_email=recipient_email,
            custom_message=data.custom_message,
        )

    except BudgetWorkflowError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return ApiResponse(data=BudgetResponse.model_validate(budget))


@router.post("/budgets/{budget_id}/accept", response_model=ApiResponse[BudgetResponse])
async def accept_budget(
    budget_id: UUID,
    data: BudgetAcceptRequest,
    request: Request,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("budget.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[BudgetResponse]:
    """Accept entire budget with signature.

    All items in the budget are accepted together. Partial acceptance is not supported.
    """
    budget = await BudgetService.get_budget(db, ctx.clinic_id, budget_id, include_items=True)
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    # Get client info for audit
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    try:
        budget = await BudgetWorkflowService.accept_budget(
            db,
            budget,
            data.signature.model_dump(),
            ctx.user_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
    except BudgetWorkflowError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return ApiResponse(data=BudgetResponse.model_validate(budget))


@router.post("/budgets/{budget_id}/reject", response_model=ApiResponse[BudgetResponse])
async def reject_budget(
    budget_id: UUID,
    data: BudgetRejectRequest,
    request: Request,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("budget.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[BudgetResponse]:
    """Reject a budget."""
    budget = await BudgetService.get_budget(db, ctx.clinic_id, budget_id, include_items=True)
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    # Get client info for audit
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    signature_data = data.signature.model_dump() if data.signature else None

    try:
        budget = await BudgetWorkflowService.reject_budget(
            db,
            budget,
            ctx.user_id,
            data.reason,
            signature_data=signature_data,
            ip_address=ip_address,
            user_agent=user_agent,
        )
    except BudgetWorkflowError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return ApiResponse(data=BudgetResponse.model_validate(budget))


@router.post("/budgets/{budget_id}/cancel", response_model=ApiResponse[BudgetResponse])
async def cancel_budget(
    budget_id: UUID,
    data: BudgetCancelRequest,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("budget.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[BudgetResponse]:
    """Cancel a budget."""
    budget = await BudgetService.get_budget(db, ctx.clinic_id, budget_id, include_items=True)
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    try:
        budget = await BudgetWorkflowService.cancel_budget(db, budget, ctx.user_id, data.reason)
    except BudgetWorkflowError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return ApiResponse(data=BudgetResponse.model_validate(budget))


@router.post("/budgets/{budget_id}/complete", response_model=ApiResponse[BudgetResponse])
async def complete_budget(
    budget_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("budget.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[BudgetResponse]:
    """Mark budget as completed (all treatments done)."""
    budget = await BudgetService.get_budget(db, ctx.clinic_id, budget_id, include_items=True)
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    try:
        budget = await BudgetWorkflowService.complete_budget(db, budget, ctx.user_id)
    except BudgetWorkflowError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return ApiResponse(data=BudgetResponse.model_validate(budget))


@router.post(
    "/budgets/{budget_id}/duplicate",
    response_model=ApiResponse[BudgetDetailResponse],
    status_code=status.HTTP_201_CREATED,
)
async def duplicate_budget(
    budget_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("budget.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[BudgetDetailResponse]:
    """Create a new version of a budget."""
    budget = await BudgetService.get_budget(db, ctx.clinic_id, budget_id, include_items=True)
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    new_budget = await BudgetService.duplicate_budget(db, budget, ctx.user_id)

    # Reload with relationships
    new_budget = await BudgetService.get_budget(
        db, ctx.clinic_id, new_budget.id, include_items=True
    )
    return ApiResponse(data=BudgetDetailResponse.model_validate(new_budget))


# ============================================================================
# Versions and History Endpoints
# ============================================================================


@router.get(
    "/budgets/{budget_id}/versions",
    response_model=ApiResponse[BudgetVersionListResponse],
)
async def get_budget_versions(
    budget_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("budget.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[BudgetVersionListResponse]:
    """Get all versions of a budget."""
    budget = await BudgetService.get_budget(db, ctx.clinic_id, budget_id, include_items=False)
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    versions = await BudgetService.get_versions(db, ctx.clinic_id, budget.budget_number)

    version_responses = [
        BudgetVersionResponse(
            id=v.id,
            version=v.version,
            status=v.status,
            total=v.total,
            created_at=v.created_at,
            is_current=(v.id == budget_id),
        )
        for v in versions
    ]

    return ApiResponse(
        data=BudgetVersionListResponse(
            budget_number=budget.budget_number,
            versions=version_responses,
            current_version=budget.version,
        )
    )


@router.get(
    "/budgets/{budget_id}/history",
    response_model=ApiResponse[list[BudgetHistoryResponse]],
)
async def get_budget_history(
    budget_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("budget.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[list[BudgetHistoryResponse]]:
    """Get history/audit log for a budget."""
    budget = await BudgetService.get_budget(db, ctx.clinic_id, budget_id, include_items=False)
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    history = await BudgetHistoryService.get_history(db, ctx.clinic_id, budget_id)

    return ApiResponse(data=[BudgetHistoryResponse.model_validate(h) for h in history])


# ============================================================================
# PDF Endpoints
# ============================================================================


@router.get("/budgets/{budget_id}/pdf")
async def download_budget_pdf(
    budget_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("budget.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    locale: str = Query(default="es", pattern="^(es|en)$"),
) -> Response:
    """Download budget as PDF."""
    budget = await BudgetService.get_budget(db, ctx.clinic_id, budget_id, include_items=True)
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    # Get clinic for branding
    from app.core.auth.models import Clinic

    clinic = await db.get(Clinic, ctx.clinic_id)

    pdf_bytes = BudgetPDFService.generate_pdf(
        budget,
        clinic,
        is_preview=False,
        locale=locale,
    )

    filename = f"presupuesto_{budget.budget_number}_v{budget.version}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/budgets/{budget_id}/pdf/preview")
async def preview_budget_pdf(
    budget_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("budget.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    locale: str = Query(default="es", pattern="^(es|en)$"),
) -> Response:
    """Preview budget PDF (with watermark for drafts)."""
    budget = await BudgetService.get_budget(db, ctx.clinic_id, budget_id, include_items=True)
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    # Get clinic for branding
    from app.core.auth.models import Clinic

    clinic = await db.get(Clinic, ctx.clinic_id)

    pdf_bytes = BudgetPDFService.generate_pdf(
        budget,
        clinic,
        is_preview=True,
        locale=locale,
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "inline"},
    )
