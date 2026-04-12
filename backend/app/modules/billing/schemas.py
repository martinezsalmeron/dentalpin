"""Billing module Pydantic schemas for API request/response."""

from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

# ============================================================================
# Invoice Status and Payment Types
# ============================================================================

InvoiceStatus = Literal["draft", "issued", "partial", "paid", "cancelled", "voided"]

PaymentMethod = Literal["cash", "card", "bank_transfer", "direct_debit", "other"]

SeriesType = Literal["invoice", "credit_note"]

DiscountType = Literal["percentage", "absolute"]


# ============================================================================
# Brief Schemas (for nested responses)
# ============================================================================


class PatientBrief(BaseModel):
    """Brief patient info for invoice responses."""

    id: UUID
    first_name: str
    last_name: str
    email: str | None = None

    class Config:
        from_attributes = True


class UserBrief(BaseModel):
    """Brief user info for invoice responses."""

    id: UUID
    first_name: str
    last_name: str

    class Config:
        from_attributes = True


class BudgetBrief(BaseModel):
    """Brief budget info for invoice responses."""

    id: UUID
    budget_number: str
    status: str
    total: Decimal

    class Config:
        from_attributes = True


class CatalogItemBrief(BaseModel):
    """Brief catalog item info for invoice items."""

    id: UUID
    internal_code: str
    names: dict[str, str]
    default_price: Decimal | None

    class Config:
        from_attributes = True


class VatTypeBrief(BaseModel):
    """Brief VAT type info for invoice items."""

    id: UUID
    names: dict[str, str]
    rate: float

    class Config:
        from_attributes = True


class InvoiceBrief(BaseModel):
    """Brief invoice info for credit note references."""

    id: UUID
    invoice_number: str
    status: str
    total: Decimal
    issue_date: date | None

    class Config:
        from_attributes = True


# ============================================================================
# Invoice Series Schemas
# ============================================================================


class InvoiceSeriesCreate(BaseModel):
    """Schema for creating an invoice series."""

    prefix: str = Field(min_length=1, max_length=20)
    series_type: SeriesType
    description: str | None = None
    reset_yearly: bool = True
    is_default: bool = False


class InvoiceSeriesUpdate(BaseModel):
    """Schema for updating an invoice series."""

    description: str | None = None
    reset_yearly: bool | None = None
    is_default: bool | None = None
    is_active: bool | None = None


class InvoiceSeriesResponse(BaseModel):
    """Schema for invoice series response."""

    id: UUID
    clinic_id: UUID
    prefix: str
    series_type: str
    description: str | None
    current_number: int
    reset_yearly: bool
    last_reset_year: int | None
    is_default: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Invoice Item Schemas
# ============================================================================


class InvoiceItemCreate(BaseModel):
    """Schema for creating an invoice item."""

    # For manual items
    description: str = Field(min_length=1, max_length=500)
    internal_code: str | None = None
    catalog_item_id: UUID | None = None

    # Pricing
    unit_price: Decimal = Field(ge=0)
    quantity: int = Field(default=1, ge=1)

    # Discounts
    discount_type: DiscountType | None = None
    discount_value: Decimal | None = Field(default=None, ge=0)

    # VAT
    vat_type_id: UUID | None = None
    vat_exempt_reason: str | None = None

    # Dental context
    tooth_number: int | None = Field(default=None, ge=11, le=85)
    surfaces: list[str] | None = None

    # Display
    display_order: int = 0


class InvoiceItemFromBudget(BaseModel):
    """Schema for creating invoice item from budget item."""

    budget_item_id: UUID
    quantity: int | None = Field(default=None, ge=1)  # None = invoice remaining quantity


class InvoiceItemUpdate(BaseModel):
    """Schema for updating an invoice item."""

    description: str | None = Field(default=None, min_length=1, max_length=500)
    unit_price: Decimal | None = Field(default=None, ge=0)
    quantity: int | None = Field(default=None, ge=1)

    # Discounts
    discount_type: DiscountType | None = None
    discount_value: Decimal | None = Field(default=None, ge=0)

    # VAT
    vat_type_id: UUID | None = None
    vat_exempt_reason: str | None = None

    # Display
    display_order: int | None = None


class InvoiceItemResponse(BaseModel):
    """Schema for invoice item response."""

    id: UUID
    invoice_id: UUID
    budget_item_id: UUID | None
    catalog_item_id: UUID | None

    # Description
    description: str
    internal_code: str | None

    # Pricing
    unit_price: Decimal
    quantity: int

    # Discounts
    discount_type: str | None
    discount_value: Decimal | None

    # VAT
    vat_type_id: UUID | None
    vat_rate: float
    vat_exempt_reason: str | None

    # Calculated totals
    line_subtotal: Decimal
    line_discount: Decimal
    line_tax: Decimal
    line_total: Decimal

    # Dental context
    tooth_number: int | None
    surfaces: list[str] | None

    # Display
    display_order: int

    # Timestamps
    created_at: datetime
    updated_at: datetime

    # Related
    catalog_item: CatalogItemBrief | None = None
    vat_type: VatTypeBrief | None = None

    class Config:
        from_attributes = True


# ============================================================================
# Payment Schemas
# ============================================================================


class PaymentCreate(BaseModel):
    """Schema for recording a payment."""

    amount: Decimal = Field(gt=0)
    payment_method: PaymentMethod
    payment_date: date = Field(default_factory=date.today)
    reference: str | None = Field(default=None, max_length=100)
    notes: str | None = None

    @field_validator("reference", "notes", mode="before")
    @classmethod
    def empty_string_to_none(cls, v: str | None) -> str | None:
        """Convert empty or whitespace-only strings to None for optional fields."""
        if isinstance(v, str):
            v = v.strip()
            if v == "":
                return None
        return v


class PaymentVoidRequest(BaseModel):
    """Schema for voiding a payment."""

    reason: str = Field(min_length=1)


class PaymentResponse(BaseModel):
    """Schema for payment response."""

    id: UUID
    invoice_id: UUID
    amount: Decimal
    payment_method: str
    payment_date: date
    reference: str | None
    notes: str | None
    recorded_by: UUID
    created_at: datetime

    # Voiding
    is_voided: bool
    voided_at: datetime | None
    voided_by: UUID | None
    void_reason: str | None

    # Related
    recorder: UserBrief | None = None
    voider: UserBrief | None = None

    class Config:
        from_attributes = True


# ============================================================================
# Invoice History Schemas
# ============================================================================


class InvoiceHistoryResponse(BaseModel):
    """Schema for invoice history response."""

    id: UUID
    invoice_id: UUID
    action: str
    changed_by: UUID
    changed_at: datetime
    previous_state: dict | None
    new_state: dict | None
    notes: str | None

    # Related
    user: UserBrief | None = None

    class Config:
        from_attributes = True


# ============================================================================
# Invoice Schemas
# ============================================================================


class BillingAddress(BaseModel):
    """Schema for billing address."""

    street: str | None = None
    city: str | None = None
    postal_code: str | None = None
    province: str | None = None
    country: str = "ES"


class InvoiceCreate(BaseModel):
    """Schema for creating an invoice manually."""

    patient_id: UUID

    # Series (if not provided, uses default)
    series_id: UUID | None = None

    # Billing data (if not provided, uses patient data)
    billing_name: str | None = None
    billing_tax_id: str | None = None
    billing_address: BillingAddress | None = None
    billing_email: str | None = None

    # Payment terms
    payment_term_days: int = Field(default=30, ge=0)
    due_date: date | None = None

    # Notes
    internal_notes: str | None = None
    public_notes: str | None = None

    # Items (optional, can be added later)
    items: list[InvoiceItemCreate] = Field(default_factory=list)


class InvoiceFromBudgetCreate(BaseModel):
    """Schema for creating an invoice from a budget."""

    # Items to invoice (supports partial invoicing)
    items: list[InvoiceItemFromBudget]

    # Override billing data (optional)
    billing_name: str | None = None
    billing_tax_id: str | None = None
    billing_address: BillingAddress | None = None
    billing_email: str | None = None

    # Payment terms
    payment_term_days: int | None = None
    due_date: date | None = None

    # Notes
    internal_notes: str | None = None
    public_notes: str | None = None


class InvoiceUpdate(BaseModel):
    """Schema for updating an invoice (only allowed in draft status)."""

    # Billing data
    billing_name: str | None = None
    billing_tax_id: str | None = None
    billing_address: BillingAddress | None = None
    billing_email: str | None = None

    # Payment terms
    payment_term_days: int | None = Field(default=None, ge=0)
    due_date: date | None = None

    # Notes
    internal_notes: str | None = None
    public_notes: str | None = None


class InvoiceResponse(BaseModel):
    """Schema for invoice response."""

    id: UUID
    clinic_id: UUID
    patient_id: UUID

    # Identification (null for drafts, assigned when issued)
    invoice_number: str | None
    sequential_number: int | None
    series_id: UUID | None

    # Links
    budget_id: UUID | None
    credit_note_for_id: UUID | None

    # Status
    status: str

    # Dates
    issue_date: date | None
    due_date: date | None
    payment_term_days: int

    # Billing data
    billing_name: str
    billing_tax_id: str | None
    billing_address: dict | None
    billing_email: str | None

    # Totals
    subtotal: Decimal
    total_discount: Decimal
    total_tax: Decimal
    total: Decimal
    total_paid: Decimal
    balance_due: Decimal
    currency: str

    # Notes
    internal_notes: str | None
    public_notes: str | None

    # Extensibility
    compliance_data: dict | None
    document_hash: str | None

    # Audit
    created_by: UUID
    issued_by: UUID | None

    # Timestamps
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None

    # Related
    patient: PatientBrief | None = None
    creator: UserBrief | None = None
    issuer: UserBrief | None = None
    budget: BudgetBrief | None = None
    credit_note_for: InvoiceBrief | None = None

    class Config:
        from_attributes = True


class InvoiceDetailResponse(InvoiceResponse):
    """Schema for invoice with full details including items and payments."""

    items: list[InvoiceItemResponse] = []
    payments: list[PaymentResponse] = []

    class Config:
        from_attributes = True


class InvoiceListResponse(BaseModel):
    """Schema for invoice list item (lighter than full response)."""

    id: UUID
    invoice_number: str | None  # Null for drafts (assigned when issued)
    status: str
    issue_date: date | None
    due_date: date | None
    total: Decimal
    total_paid: Decimal
    balance_due: Decimal
    currency: str
    created_at: datetime

    # Related (brief)
    patient: PatientBrief | None = None
    creator: UserBrief | None = None

    class Config:
        from_attributes = True


# ============================================================================
# Workflow Schemas
# ============================================================================


class InvoiceIssueRequest(BaseModel):
    """Schema for issuing an invoice."""

    issue_date: date = Field(default_factory=date.today)


class CreditNoteItemSelect(BaseModel):
    """Schema for selecting items for a credit note."""

    invoice_item_id: UUID
    quantity: int | None = Field(default=None, ge=1)  # None = full quantity of original item


class CreditNoteCreate(BaseModel):
    """Schema for creating a credit note."""

    reason: str = Field(min_length=1, max_length=500)

    # Partial credit note: specify items to rectify
    # If empty, creates full credit note for entire invoice
    items: list[CreditNoteItemSelect] = Field(default_factory=list)

    # Notes
    internal_notes: str | None = None
    public_notes: str | None = None


# ============================================================================
# Report Schemas
# ============================================================================


class BillingSummary(BaseModel):
    """Schema for billing summary report."""

    period_start: date
    period_end: date

    total_invoiced: Decimal
    total_paid: Decimal
    total_pending: Decimal

    invoice_count: int
    paid_count: int
    overdue_count: int

    vat_breakdown: list["VatSummaryItem"]


class VatSummaryItem(BaseModel):
    """Schema for VAT breakdown item."""

    vat_type_id: UUID | None
    vat_rate: float
    vat_name: str
    base_amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal


class PaymentMethodSummary(BaseModel):
    """Schema for payment method breakdown."""

    payment_method: str
    total_amount: Decimal
    payment_count: int


class ProfessionalBillingSummary(BaseModel):
    """Schema for billing by professional."""

    professional_id: UUID
    professional_name: str
    total_invoiced: Decimal
    invoice_count: int


class OverdueInvoice(BaseModel):
    """Schema for overdue invoice item."""

    id: UUID
    invoice_number: str
    patient_name: str
    issue_date: date
    due_date: date
    days_overdue: int
    balance_due: Decimal


class NumberingGap(BaseModel):
    """Schema for numbering gap report."""

    series_prefix: str
    year: int
    missing_numbers: list[int]


# ============================================================================
# Settings Schemas
# ============================================================================


class BillingSettingsResponse(BaseModel):
    """Schema for clinic billing settings."""

    default_payment_term_days: int
    invoice_footer_text: str | None
    bank_account_info: str | None


class BillingSettingsUpdate(BaseModel):
    """Schema for updating clinic billing settings."""

    default_payment_term_days: int | None = Field(default=None, ge=0, le=365)
    invoice_footer_text: str | None = None
    bank_account_info: str | None = None


# ============================================================================
# Search/Filter Schemas
# ============================================================================


class InvoiceSearchParams(BaseModel):
    """Search parameters for invoices."""

    patient_id: UUID | None = None
    status: list[InvoiceStatus] | None = None
    date_from: date | None = None
    date_to: date | None = None
    due_from: date | None = None
    due_to: date | None = None
    overdue: bool | None = None
    search: str | None = None  # invoice_number or patient name
    budget_id: UUID | None = None
    is_credit_note: bool | None = None
