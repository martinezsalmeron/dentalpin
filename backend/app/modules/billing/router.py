"""Billing module API router."""

from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import ClinicContext, get_clinic_context, require_permission
from app.core.schemas import ApiResponse, PaginatedApiResponse
from app.database import get_db

from .hooks import BillingHookRegistry
from .models import PAYMENT_METHODS
from .schemas import (
    BillingSettingsResponse,
    BillingSettingsUpdate,
    BillingSummary,
    CreditNoteCreate,
    InvoiceCreate,
    InvoiceDetailResponse,
    InvoiceFromBudgetCreate,
    InvoiceHistoryResponse,
    InvoiceIssueRequest,
    InvoiceItemCreate,
    InvoiceItemResponse,
    InvoiceItemUpdate,
    InvoiceListResponse,
    InvoiceResponse,
    InvoiceSeriesCreate,
    InvoiceSeriesResponse,
    InvoiceSeriesUpdate,
    InvoiceUpdate,
    NumberingGap,
    OverdueInvoice,
    PaymentCreate,
    PaymentMethodSummary,
    PaymentResponse,
    PaymentVoidRequest,
    ProfessionalBillingSummary,
    VatSummaryItem,
)
from .service import (
    InvoiceHistoryService,
    InvoiceItemService,
    InvoiceSeriesService,
    InvoiceService,
    PaymentService,
)
from .workflow import InvoiceWorkflowError, InvoiceWorkflowService

router = APIRouter()


# ============================================================================
# Invoice Series Endpoints
# ============================================================================


@router.get("/series", response_model=ApiResponse[list[InvoiceSeriesResponse]])
async def list_series(
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("billing.admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    series_type: str | None = Query(default=None),
    active_only: bool = Query(default=True),
) -> ApiResponse[list[InvoiceSeriesResponse]]:
    """List invoice series for the clinic."""
    series = await InvoiceSeriesService.list_series(
        db, ctx.clinic_id, series_type=series_type, active_only=active_only
    )
    return ApiResponse(data=[InvoiceSeriesResponse.model_validate(s) for s in series])


@router.post("/series", response_model=ApiResponse[InvoiceSeriesResponse], status_code=201)
async def create_series(
    data: InvoiceSeriesCreate,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("billing.admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[InvoiceSeriesResponse]:
    """Create a new invoice series."""
    try:
        series = await InvoiceSeriesService.create_series(db, ctx.clinic_id, data.model_dump())
        await db.commit()
        return ApiResponse(data=InvoiceSeriesResponse.model_validate(series))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/series/{series_id}", response_model=ApiResponse[InvoiceSeriesResponse])
async def update_series(
    series_id: UUID,
    data: InvoiceSeriesUpdate,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("billing.admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[InvoiceSeriesResponse]:
    """Update an invoice series."""
    from sqlalchemy import select

    from .models import InvoiceSeries

    result = await db.execute(
        select(InvoiceSeries).where(
            InvoiceSeries.id == series_id,
            InvoiceSeries.clinic_id == ctx.clinic_id,
        )
    )
    series = result.scalar_one_or_none()

    if not series:
        raise HTTPException(status_code=404, detail="Series not found")

    try:
        series = await InvoiceSeriesService.update_series(
            db, series, data.model_dump(exclude_unset=True)
        )
        await db.commit()
        return ApiResponse(data=InvoiceSeriesResponse.model_validate(series))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Invoice CRUD Endpoints
# ============================================================================


@router.get("/invoices", response_model=PaginatedApiResponse[InvoiceListResponse])
async def list_invoices(
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("billing.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    patient_id: UUID | None = None,
    status: list[str] | None = Query(default=None),
    date_from: date | None = None,
    date_to: date | None = None,
    due_from: date | None = None,
    due_to: date | None = None,
    overdue: bool | None = None,
    search: str | None = None,
    budget_id: UUID | None = None,
    is_credit_note: bool | None = None,
) -> PaginatedApiResponse[InvoiceListResponse]:
    """List invoices with filtering and pagination."""
    invoices, total = await InvoiceService.list_invoices(
        db,
        ctx.clinic_id,
        page=page,
        page_size=page_size,
        patient_id=patient_id,
        status=status,
        date_from=date_from,
        date_to=date_to,
        due_from=due_from,
        due_to=due_to,
        overdue=overdue,
        search=search,
        budget_id=budget_id,
        is_credit_note=is_credit_note,
    )
    return PaginatedApiResponse(
        data=[InvoiceListResponse.model_validate(i) for i in invoices],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/invoices/{invoice_id}", response_model=ApiResponse[InvoiceDetailResponse])
async def get_invoice(
    invoice_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("billing.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[InvoiceDetailResponse]:
    """Get invoice details with items and payments."""
    invoice = await InvoiceService.get_invoice(
        db, ctx.clinic_id, invoice_id, include_items=True, include_payments=True
    )
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    return ApiResponse(data=InvoiceDetailResponse.model_validate(invoice))


@router.post("/invoices", response_model=ApiResponse[InvoiceResponse], status_code=201)
async def create_invoice(
    data: InvoiceCreate,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("billing.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[InvoiceResponse]:
    """Create a new invoice manually."""
    try:
        billing_data = None
        if data.billing_name or data.billing_tax_id or data.billing_address or data.billing_email:
            billing_data = {
                "billing_name": data.billing_name,
                "billing_tax_id": data.billing_tax_id,
                "billing_address": data.billing_address.model_dump()
                if data.billing_address
                else None,
                "billing_email": data.billing_email,
            }

        notes = {
            "internal_notes": data.internal_notes,
            "public_notes": data.public_notes,
        }

        invoice = await InvoiceService.create_invoice(
            db,
            clinic_id=ctx.clinic_id,
            created_by=ctx.user_id,
            patient_id=data.patient_id,
            series_id=data.series_id,
            billing_data=billing_data,
            payment_term_days=data.payment_term_days,
            due_date=data.due_date,
            notes=notes,
        )

        # Add items if provided
        for item_data in data.items:
            await InvoiceItemService.create_item(db, ctx.clinic_id, invoice, item_data.model_dump())

        await db.commit()
        await db.refresh(invoice)

        return ApiResponse(data=InvoiceResponse.model_validate(invoice))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/invoices/from-budget/{budget_id}",
    response_model=ApiResponse[InvoiceResponse],
    status_code=201,
)
async def create_invoice_from_budget(
    budget_id: UUID,
    data: InvoiceFromBudgetCreate,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("billing.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[InvoiceResponse]:
    """Create an invoice from a budget with partial invoicing support."""
    try:
        billing_data = None
        if data.billing_name or data.billing_tax_id or data.billing_address or data.billing_email:
            billing_data = {
                "billing_name": data.billing_name,
                "billing_tax_id": data.billing_tax_id,
                "billing_address": data.billing_address.model_dump()
                if data.billing_address
                else None,
                "billing_email": data.billing_email,
            }

        notes = {
            "internal_notes": data.internal_notes,
            "public_notes": data.public_notes,
        }

        items = [
            {"budget_item_id": item.budget_item_id, "quantity": item.quantity}
            for item in data.items
        ]

        invoice = await InvoiceService.create_from_budget(
            db,
            clinic_id=ctx.clinic_id,
            created_by=ctx.user_id,
            budget_id=budget_id,
            items=items,
            billing_data=billing_data,
            payment_term_days=data.payment_term_days,
            due_date=data.due_date,
            notes=notes,
        )

        await db.commit()
        await db.refresh(invoice)

        return ApiResponse(data=InvoiceResponse.model_validate(invoice))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/invoices/{invoice_id}", response_model=ApiResponse[InvoiceResponse])
async def update_invoice(
    invoice_id: UUID,
    data: InvoiceUpdate,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("billing.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[InvoiceResponse]:
    """Update an invoice (only drafts)."""
    invoice = await InvoiceService.get_invoice(
        db, ctx.clinic_id, invoice_id, include_items=False, include_payments=False
    )
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    try:
        update_data = data.model_dump(exclude_unset=True)
        if "billing_address" in update_data and update_data["billing_address"]:
            update_data["billing_address"] = update_data["billing_address"]

        invoice = await InvoiceService.update_invoice(db, invoice, ctx.user_id, update_data)
        await db.commit()
        return ApiResponse(data=InvoiceResponse.model_validate(invoice))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/invoices/{invoice_id}", status_code=204)
async def delete_invoice(
    invoice_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("billing.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Soft delete an invoice (only drafts)."""
    invoice = await InvoiceService.get_invoice(
        db, ctx.clinic_id, invoice_id, include_items=False, include_payments=False
    )
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    try:
        await InvoiceService.delete_invoice(db, invoice, ctx.user_id)
        await db.commit()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Invoice Item Endpoints
# ============================================================================


@router.post(
    "/invoices/{invoice_id}/items",
    response_model=ApiResponse[InvoiceItemResponse],
    status_code=201,
)
async def add_invoice_item(
    invoice_id: UUID,
    data: InvoiceItemCreate,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("billing.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[InvoiceItemResponse]:
    """Add an item to an invoice."""
    invoice = await InvoiceService.get_invoice(
        db, ctx.clinic_id, invoice_id, include_items=True, include_payments=False
    )
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if not InvoiceWorkflowService.can_edit(invoice):
        raise HTTPException(status_code=400, detail="Can only edit draft invoices")

    try:
        item = await InvoiceItemService.create_item(db, ctx.clinic_id, invoice, data.model_dump())
        await db.commit()
        return ApiResponse(data=InvoiceItemResponse.model_validate(item))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put(
    "/invoices/{invoice_id}/items/{item_id}",
    response_model=ApiResponse[InvoiceItemResponse],
)
async def update_invoice_item(
    invoice_id: UUID,
    item_id: UUID,
    data: InvoiceItemUpdate,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("billing.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[InvoiceItemResponse]:
    """Update an invoice item."""
    invoice = await InvoiceService.get_invoice(
        db, ctx.clinic_id, invoice_id, include_items=True, include_payments=False
    )
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if not InvoiceWorkflowService.can_edit(invoice):
        raise HTTPException(status_code=400, detail="Can only edit draft invoices")

    item = next((i for i in invoice.items if i.id == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    try:
        item = await InvoiceItemService.update_item(
            db, ctx.clinic_id, item, invoice, data.model_dump(exclude_unset=True)
        )
        await db.commit()
        return ApiResponse(data=InvoiceItemResponse.model_validate(item))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/invoices/{invoice_id}/items/{item_id}", status_code=204)
async def delete_invoice_item(
    invoice_id: UUID,
    item_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("billing.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Delete an invoice item."""
    invoice = await InvoiceService.get_invoice(
        db, ctx.clinic_id, invoice_id, include_items=True, include_payments=False
    )
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if not InvoiceWorkflowService.can_edit(invoice):
        raise HTTPException(status_code=400, detail="Can only edit draft invoices")

    item = next((i for i in invoice.items if i.id == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    await InvoiceItemService.delete_item(db, item, invoice)
    await db.commit()


# ============================================================================
# Workflow Endpoints
# ============================================================================


@router.post("/invoices/{invoice_id}/issue", response_model=ApiResponse[InvoiceResponse])
async def issue_invoice(
    invoice_id: UUID,
    data: InvoiceIssueRequest,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("billing.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[InvoiceResponse]:
    """Issue an invoice (transition from draft to issued)."""
    invoice = await InvoiceService.get_invoice(
        db, ctx.clinic_id, invoice_id, include_items=True, include_payments=False
    )
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    try:
        # Get compliance hook if available
        hook = None
        clinic = invoice.clinic
        if clinic:
            hook = BillingHookRegistry.get_for_clinic(clinic)

        hook_callback = None
        if hook:
            # Validate required fields
            for field in hook.get_required_fields():
                value = getattr(invoice, field, None)
                if not value:
                    raise InvoiceWorkflowError(f"Field '{field}' is required")

            # Validate before issue
            is_valid, error = await hook.validate_before_issue(invoice, db)
            if not is_valid:
                raise InvoiceWorkflowError(error)

            # Set up hook callback
            async def hook_callback(inv, db_session):
                return await hook.on_invoice_issued(inv, db_session)

        invoice = await InvoiceWorkflowService.issue_invoice(
            db, invoice, ctx.user_id, issue_date=data.issue_date, hook_callback=hook_callback
        )
        await db.commit()
        return ApiResponse(data=InvoiceResponse.model_validate(invoice))
    except InvoiceWorkflowError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/invoices/{invoice_id}/void", response_model=ApiResponse[InvoiceResponse])
async def void_invoice(
    invoice_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("billing.admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    reason: str | None = None,
) -> ApiResponse[InvoiceResponse]:
    """Void an invoice (only drafts)."""
    invoice = await InvoiceService.get_invoice(
        db, ctx.clinic_id, invoice_id, include_items=False, include_payments=False
    )
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    try:
        invoice = await InvoiceWorkflowService.void_invoice(db, invoice, ctx.user_id, reason)
        await db.commit()
        return ApiResponse(data=InvoiceResponse.model_validate(invoice))
    except InvoiceWorkflowError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/invoices/{invoice_id}/credit-note",
    response_model=ApiResponse[InvoiceResponse],
    status_code=201,
)
async def create_credit_note(
    invoice_id: UUID,
    data: CreditNoteCreate,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("billing.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[InvoiceResponse]:
    """Create a credit note (rectificativa) for an invoice."""
    invoice = await InvoiceService.get_invoice(
        db, ctx.clinic_id, invoice_id, include_items=True, include_payments=False
    )
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    try:
        # Get compliance hook if available
        hook = None
        clinic = invoice.clinic
        if clinic:
            hook = BillingHookRegistry.get_for_clinic(clinic)

        hook_callback = None
        if hook:

            async def hook_callback(credit_note, original, db_session):
                return await hook.on_credit_note_issued(credit_note, original, db_session)

        items = None
        if data.items:
            items = [
                {"invoice_item_id": item.invoice_item_id, "quantity": item.quantity}
                for item in data.items
            ]

        credit_note = await InvoiceWorkflowService.create_credit_note(
            db,
            original_invoice=invoice,
            created_by=ctx.user_id,
            reason=data.reason,
            items=items,
            hook_callback=hook_callback,
        )
        await db.commit()
        return ApiResponse(data=InvoiceResponse.model_validate(credit_note))
    except InvoiceWorkflowError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Payment Endpoints
# ============================================================================


@router.get(
    "/invoices/{invoice_id}/payments",
    response_model=ApiResponse[list[PaymentResponse]],
)
async def list_payments(
    invoice_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("billing.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    include_voided: bool = Query(default=False),
) -> ApiResponse[list[PaymentResponse]]:
    """List payments for an invoice."""
    invoice = await InvoiceService.get_invoice(
        db, ctx.clinic_id, invoice_id, include_items=False, include_payments=False
    )
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    payments = await PaymentService.list_payments(
        db, ctx.clinic_id, invoice_id, include_voided=include_voided
    )
    return ApiResponse(data=[PaymentResponse.model_validate(p) for p in payments])


@router.post(
    "/invoices/{invoice_id}/payments",
    response_model=ApiResponse[PaymentResponse],
    status_code=201,
)
async def record_payment(
    invoice_id: UUID,
    data: PaymentCreate,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("billing.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[PaymentResponse]:
    """Record a payment for an invoice."""
    invoice = await InvoiceService.get_invoice(
        db, ctx.clinic_id, invoice_id, include_items=False, include_payments=False
    )
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Validate payment method
    if data.payment_method not in PAYMENT_METHODS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid payment method. Must be one of: {PAYMENT_METHODS}",
        )

    try:
        payment = await InvoiceWorkflowService.record_payment(
            db,
            invoice=invoice,
            amount=data.amount,
            payment_method=data.payment_method,
            payment_date=data.payment_date,
            recorded_by=ctx.user_id,
            reference=data.reference,
            notes=data.notes,
        )
        await db.commit()
        return ApiResponse(data=PaymentResponse.model_validate(payment))
    except InvoiceWorkflowError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/payments/{payment_id}/void", response_model=ApiResponse[PaymentResponse])
async def void_payment(
    payment_id: UUID,
    data: PaymentVoidRequest,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("billing.admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[PaymentResponse]:
    """Void a payment."""
    payment = await PaymentService.get_payment(db, ctx.clinic_id, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    invoice = payment.invoice
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    try:
        payment = await InvoiceWorkflowService.void_payment(
            db,
            payment=payment,
            invoice=invoice,
            voided_by=ctx.user_id,
            reason=data.reason,
        )
        await db.commit()
        return ApiResponse(data=PaymentResponse.model_validate(payment))
    except InvoiceWorkflowError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# History Endpoints
# ============================================================================


@router.get(
    "/invoices/{invoice_id}/history",
    response_model=ApiResponse[list[InvoiceHistoryResponse]],
)
async def get_invoice_history(
    invoice_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("billing.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[list[InvoiceHistoryResponse]]:
    """Get invoice history/audit log."""
    invoice = await InvoiceService.get_invoice(
        db, ctx.clinic_id, invoice_id, include_items=False, include_payments=False
    )
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    history = await InvoiceHistoryService.list_history(db, ctx.clinic_id, invoice_id)
    return ApiResponse(data=[InvoiceHistoryResponse.model_validate(h) for h in history])


# ============================================================================
# Settings Endpoints
# ============================================================================


@router.get("/settings", response_model=ApiResponse[BillingSettingsResponse])
async def get_billing_settings(
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("billing.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[BillingSettingsResponse]:
    """Get billing settings for the clinic."""
    from sqlalchemy import select

    from app.core.auth.models import Clinic

    result = await db.execute(select(Clinic).where(Clinic.id == ctx.clinic_id))
    clinic = result.scalar_one_or_none()

    if not clinic:
        raise HTTPException(status_code=404, detail="Clinic not found")

    settings = clinic.settings or {}
    billing_settings = settings.get("billing", {})

    return ApiResponse(
        data=BillingSettingsResponse(
            default_payment_term_days=billing_settings.get("default_payment_term_days", 30),
            invoice_footer_text=billing_settings.get("invoice_footer_text"),
            bank_account_info=billing_settings.get("bank_account_info"),
        )
    )


@router.put("/settings", response_model=ApiResponse[BillingSettingsResponse])
async def update_billing_settings(
    data: BillingSettingsUpdate,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("billing.admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[BillingSettingsResponse]:
    """Update billing settings for the clinic."""
    from sqlalchemy import select

    from app.core.auth.models import Clinic

    result = await db.execute(select(Clinic).where(Clinic.id == ctx.clinic_id))
    clinic = result.scalar_one_or_none()

    if not clinic:
        raise HTTPException(status_code=404, detail="Clinic not found")

    settings = clinic.settings or {}
    billing_settings = settings.get("billing", {})

    if data.default_payment_term_days is not None:
        billing_settings["default_payment_term_days"] = data.default_payment_term_days
    if data.invoice_footer_text is not None:
        billing_settings["invoice_footer_text"] = data.invoice_footer_text
    if data.bank_account_info is not None:
        billing_settings["bank_account_info"] = data.bank_account_info

    settings["billing"] = billing_settings
    clinic.settings = settings

    await db.commit()

    return ApiResponse(
        data=BillingSettingsResponse(
            default_payment_term_days=billing_settings.get("default_payment_term_days", 30),
            invoice_footer_text=billing_settings.get("invoice_footer_text"),
            bank_account_info=billing_settings.get("bank_account_info"),
        )
    )


# ============================================================================
# Reports
# ============================================================================


@router.get("/reports/summary", response_model=ApiResponse[BillingSummary])
async def get_billing_summary(
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("billing.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    date_from: date = Query(..., description="Start date for the report period"),
    date_to: date = Query(..., description="End date for the report period"),
) -> ApiResponse[BillingSummary]:
    """Get billing summary for a period.

    Returns total invoiced, total paid, total pending, counts, and VAT breakdown.
    """
    from .service import BillingReportService

    data = await BillingReportService.get_summary(db, ctx.clinic_id, date_from, date_to)
    return ApiResponse(data=BillingSummary(**data))


@router.get("/reports/overdue", response_model=ApiResponse[list[OverdueInvoice]])
async def get_overdue_invoices(
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("billing.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[list[OverdueInvoice]]:
    """Get list of overdue invoices.

    Returns invoices that are past due date and have outstanding balance.
    """
    from .service import BillingReportService

    data = await BillingReportService.get_overdue_invoices(db, ctx.clinic_id)
    return ApiResponse(data=[OverdueInvoice(**item) for item in data])


@router.get("/reports/by-payment-method", response_model=ApiResponse[list[PaymentMethodSummary]])
async def get_by_payment_method(
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("billing.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    date_from: date = Query(..., description="Start date for the report period"),
    date_to: date = Query(..., description="End date for the report period"),
) -> ApiResponse[list[PaymentMethodSummary]]:
    """Get payment breakdown by method.

    Returns total amounts and counts grouped by payment method.
    """
    from .service import BillingReportService

    data = await BillingReportService.get_by_payment_method(db, ctx.clinic_id, date_from, date_to)
    return ApiResponse(data=[PaymentMethodSummary(**item) for item in data])


@router.get(
    "/reports/by-professional", response_model=ApiResponse[list[ProfessionalBillingSummary]]
)
async def get_by_professional(
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("billing.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    date_from: date = Query(..., description="Start date for the report period"),
    date_to: date = Query(..., description="End date for the report period"),
) -> ApiResponse[list[ProfessionalBillingSummary]]:
    """Get billing breakdown by professional (creator).

    Returns total amounts and invoice counts per professional.
    """
    from .service import BillingReportService

    data = await BillingReportService.get_by_professional(db, ctx.clinic_id, date_from, date_to)
    return ApiResponse(data=[ProfessionalBillingSummary(**item) for item in data])


@router.get("/reports/vat-summary", response_model=ApiResponse[list[VatSummaryItem]])
async def get_vat_summary(
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("billing.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    date_from: date = Query(..., description="Start date for the report period"),
    date_to: date = Query(..., description="End date for the report period"),
) -> ApiResponse[list[VatSummaryItem]]:
    """Get VAT summary for accounting.

    Returns base amounts, tax amounts, and totals grouped by VAT rate.
    """
    from .service import BillingReportService

    data = await BillingReportService.get_vat_summary(db, ctx.clinic_id, date_from, date_to)
    return ApiResponse(data=[VatSummaryItem(**item) for item in data])


@router.get("/reports/gaps", response_model=ApiResponse[list[NumberingGap]])
async def get_numbering_gaps(
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("billing.admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[list[NumberingGap]]:
    """Find gaps in invoice numbering.

    Returns missing numbers by series and year.
    Only accessible by billing admin.
    """
    from .service import BillingReportService

    data = await BillingReportService.get_numbering_gaps(db, ctx.clinic_id)
    return ApiResponse(data=[NumberingGap(**item) for item in data])
