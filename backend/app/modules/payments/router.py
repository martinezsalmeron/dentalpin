"""Payments module FastAPI router.

Endpoints under ``/api/v1/payments/``. Reports are nested under
``/api/v1/payments/reports/*`` so the module owns both the operational
and analytic surfaces — consistent with the design that payment KPIs
should not be cross-joined against invoice data.
"""

from __future__ import annotations

from datetime import date
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import ClinicContext, get_clinic_context, require_permission
from app.core.schemas import ApiResponse, PaginatedApiResponse
from app.database import get_db

from .schemas import (
    AgingBuckets,
    AllocationResponse,
    MethodBreakdown,
    PatientLedger,
    PaymentCreate,
    PaymentReallocate,
    PaymentResponse,
    PaymentsSummary,
    PaymentsTrends,
    ProfessionalBreakdown,
    RefundCreate,
    RefundResponse,
    RefundsReport,
)
from .service import (
    LedgerService,
    PaymentReadService,
    PaymentReportsService,
    PaymentService,
)
from .workflow import (
    PaymentWorkflowError,
    reallocate_payment,
    record_payment,
    refund_payment,
)

router = APIRouter()


def _bad_request(exc: Exception) -> HTTPException:
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


# --- Payments ---------------------------------------------------------


@router.get("", response_model=PaginatedApiResponse[PaymentResponse])
async def list_payments(
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("payments.record.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    date_from: date | None = None,
    date_to: date | None = None,
    method: str | None = None,
    patient_id: UUID | None = None,
) -> PaginatedApiResponse[PaymentResponse]:
    items, total = await PaymentService.list(
        db,
        ctx.clinic_id,
        date_from=date_from,
        date_to=date_to,
        method=method,
        patient_id=patient_id,
        page=page,
        page_size=page_size,
    )
    return PaginatedApiResponse(
        data=[PaymentResponse.from_model(p) for p in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=ApiResponse[PaymentResponse], status_code=201)
async def create_payment(
    payload: PaymentCreate,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("payments.record.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[PaymentResponse]:
    try:
        payment = await record_payment(
            db,
            clinic_id=ctx.clinic_id,
            currency=ctx.clinic.currency,
            patient_id=payload.patient_id,
            amount=payload.amount,
            method=payload.method,
            payment_date=payload.payment_date,
            recorded_by=ctx.user_id,
            allocations=[a.model_dump() for a in payload.allocations],
            reference=payload.reference,
            notes=payload.notes,
        )
    except PaymentWorkflowError as exc:
        raise _bad_request(exc)

    fresh = await PaymentService.get(db, ctx.clinic_id, payment.id)
    if fresh is None:  # pragma: no cover - defensive
        raise HTTPException(status_code=500, detail="Payment vanished after create")
    return ApiResponse(data=PaymentResponse.from_model(fresh))


@router.get("/{payment_id}", response_model=ApiResponse[PaymentResponse])
async def get_payment(
    payment_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("payments.record.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[PaymentResponse]:
    payment = await PaymentService.get(db, ctx.clinic_id, payment_id)
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    return ApiResponse(data=PaymentResponse.from_model(payment))


@router.post("/{payment_id}/reallocate", response_model=ApiResponse[PaymentResponse])
async def reallocate(
    payment_id: UUID,
    payload: PaymentReallocate,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("payments.record.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[PaymentResponse]:
    payment = await PaymentService.get(db, ctx.clinic_id, payment_id)
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    try:
        await reallocate_payment(
            db,
            clinic_id=ctx.clinic_id,
            payment=payment,
            new_allocations=[a.model_dump() for a in payload.allocations],
            changed_by=ctx.user_id,
        )
    except PaymentWorkflowError as exc:
        raise _bad_request(exc)

    fresh = await PaymentService.get(db, ctx.clinic_id, payment_id)
    return ApiResponse(data=PaymentResponse.from_model(fresh))


# --- Refunds ----------------------------------------------------------


@router.get("/{payment_id}/refunds", response_model=ApiResponse[list[RefundResponse]])
async def list_refunds(
    payment_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("payments.record.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[list[RefundResponse]]:
    payment = await PaymentService.get(db, ctx.clinic_id, payment_id)
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    return ApiResponse(data=[RefundResponse.model_validate(r) for r in payment.refunds])


@router.post("/{payment_id}/refunds", response_model=ApiResponse[RefundResponse], status_code=201)
async def create_refund(
    payment_id: UUID,
    payload: RefundCreate,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("payments.record.refund"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[RefundResponse]:
    payment = await PaymentService.get(db, ctx.clinic_id, payment_id)
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    try:
        refund = await refund_payment(
            db,
            clinic_id=ctx.clinic_id,
            payment=payment,
            amount=payload.amount,
            method=payload.method,
            reason_code=payload.reason_code,
            reason_note=payload.reason_note,
            refunded_by=ctx.user_id,
        )
    except PaymentWorkflowError as exc:
        raise _bad_request(exc)
    return ApiResponse(data=RefundResponse.model_validate(refund))


# --- Ledger / per-budget ---------------------------------------------


@router.get("/patients/{patient_id}/ledger", response_model=ApiResponse[PatientLedger])
async def patient_ledger(
    patient_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("payments.record.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[PatientLedger]:
    ledger = await LedgerService.get_patient_ledger(
        db, ctx.clinic_id, patient_id, currency=ctx.clinic.currency
    )
    return ApiResponse(data=ledger)


@router.get(
    "/budgets/{budget_id}/allocations",
    response_model=ApiResponse[list[AllocationResponse]],
)
async def allocations_for_budget(
    budget_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("payments.record.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[list[AllocationResponse]]:
    rows = await PaymentReadService.get_allocations_for_budget(db, ctx.clinic_id, budget_id)
    return ApiResponse(data=[AllocationResponse.from_model(r) for r in rows])


# --- Reports ----------------------------------------------------------


@router.get("/reports/summary", response_model=ApiResponse[PaymentsSummary])
async def reports_summary(
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("payments.reports.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    date_from: date = Query(...),
    date_to: date = Query(...),
) -> ApiResponse[PaymentsSummary]:
    data = await PaymentReportsService.summary(
        db, ctx.clinic_id, ctx.clinic.currency, date_from, date_to
    )
    return ApiResponse(data=data)


@router.get("/reports/by-method", response_model=ApiResponse[list[MethodBreakdown]])
async def reports_by_method(
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("payments.reports.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    date_from: date = Query(...),
    date_to: date = Query(...),
) -> ApiResponse[list[MethodBreakdown]]:
    data = await PaymentReportsService.by_method(db, ctx.clinic_id, date_from, date_to)
    return ApiResponse(data=data)


@router.get("/reports/by-professional", response_model=ApiResponse[list[ProfessionalBreakdown]])
async def reports_by_professional(
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("payments.reports.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    date_from: date = Query(...),
    date_to: date = Query(...),
) -> ApiResponse[list[ProfessionalBreakdown]]:
    data = await PaymentReportsService.by_professional(db, ctx.clinic_id, date_from, date_to)
    return ApiResponse(data=data)


@router.get("/reports/aging-receivables", response_model=ApiResponse[AgingBuckets])
async def reports_aging(
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("payments.reports.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[AgingBuckets]:
    data = await PaymentReportsService.aging_receivables(db, ctx.clinic_id, ctx.clinic.currency)
    return ApiResponse(data=data)


@router.get("/reports/refunds", response_model=ApiResponse[RefundsReport])
async def reports_refunds(
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("payments.reports.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    date_from: date = Query(...),
    date_to: date = Query(...),
) -> ApiResponse[RefundsReport]:
    data = await PaymentReportsService.refunds_report(
        db, ctx.clinic_id, ctx.clinic.currency, date_from, date_to
    )
    return ApiResponse(data=data)


@router.get("/reports/trends", response_model=ApiResponse[PaymentsTrends])
async def reports_trends(
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("payments.reports.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    date_from: date = Query(...),
    date_to: date = Query(...),
    granularity: Literal["day", "week", "month", "year"] = "month",
) -> ApiResponse[PaymentsTrends]:
    data = await PaymentReportsService.trends(
        db, ctx.clinic_id, ctx.clinic.currency, date_from, date_to, granularity
    )
    return ApiResponse(data=data)
