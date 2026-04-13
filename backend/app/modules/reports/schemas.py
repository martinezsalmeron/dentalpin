"""Report schemas for all report types."""

from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

# ============================================================================
# Common
# ============================================================================


class DateRangeParams(BaseModel):
    """Common date range parameters for reports."""

    date_from: date
    date_to: date


# ============================================================================
# Billing Reports
# ============================================================================


class VatSummaryItem(BaseModel):
    """VAT breakdown item."""

    vat_type_id: UUID | None
    vat_rate: float
    vat_name: str
    base_amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal


class BillingSummary(BaseModel):
    """Billing summary for a period."""

    period_start: date
    period_end: date

    total_invoiced: Decimal
    total_paid: Decimal
    total_pending: Decimal

    invoice_count: int
    paid_count: int
    overdue_count: int

    vat_breakdown: list[VatSummaryItem]


class PaymentMethodSummary(BaseModel):
    """Payment breakdown by method."""

    payment_method: str
    total_amount: Decimal
    payment_count: int


class ProfessionalBillingSummary(BaseModel):
    """Billing breakdown by professional."""

    professional_id: UUID
    professional_name: str
    total_invoiced: Decimal
    invoice_count: int


class OverdueInvoice(BaseModel):
    """Overdue invoice item."""

    id: UUID
    invoice_number: str
    patient_name: str
    issue_date: date
    due_date: date
    days_overdue: int
    balance_due: Decimal


class NumberingGap(BaseModel):
    """Invoice numbering gap."""

    series_prefix: str
    year: int
    missing_numbers: list[int]


class PatientBillingSummary(BaseModel):
    """Patient billing summary (budgets + invoices)."""

    patient_id: UUID
    currency: str

    # Budget metrics
    total_budgeted: Decimal
    work_in_progress: Decimal
    work_completed: Decimal

    # Invoice metrics
    total_invoiced: Decimal
    total_paid: Decimal
    balance_pending: Decimal


# ============================================================================
# Budget Reports
# ============================================================================


class BudgetSummary(BaseModel):
    """Budget summary for a period."""

    period_start: date
    period_end: date

    total_created: int
    total_amount: Decimal

    accepted_count: int
    accepted_amount: Decimal

    rejected_count: int
    pending_count: int
    completed_count: int
    completed_amount: Decimal

    acceptance_rate: float = Field(description="Percentage 0-100")
    average_value: Decimal


class BudgetByProfessional(BaseModel):
    """Budget breakdown by professional."""

    professional_id: UUID | None
    professional_name: str
    budget_count: int
    total_amount: Decimal
    accepted_count: int
    acceptance_rate: float


class BudgetByTreatment(BaseModel):
    """Most common treatments in budgets."""

    catalog_item_id: UUID | None
    treatment_name: str
    occurrence_count: int
    total_quantity: int
    total_amount: Decimal


class BudgetByStatus(BaseModel):
    """Budget breakdown by status."""

    status: str
    count: int
    total_amount: Decimal


# ============================================================================
# Scheduling Reports
# ============================================================================


class SchedulingSummary(BaseModel):
    """Scheduling summary for a period."""

    period_start: date
    period_end: date
    total_appointments: int
    completed: int
    cancelled: int
    no_show: int
    scheduled: int
    confirmed: int
    in_progress: int
    completion_rate: float = Field(description="Percentage 0-100")
    cancellation_rate: float = Field(description="Percentage 0-100")
    no_show_rate: float = Field(description="Percentage 0-100")


class FirstVisitsSummary(BaseModel):
    """New patients per period."""

    period_start: date
    period_end: date
    new_patients: int
    total_appointments: int
    first_visit_rate: float = Field(description="Percentage 0-100")


class HoursByProfessional(BaseModel):
    """Hours worked by professional."""

    professional_id: UUID | None
    professional_name: str
    appointment_count: int
    completed_count: int
    cancelled_count: int
    no_show_count: int
    total_minutes: int
    total_hours: float


class CabinetUtilization(BaseModel):
    """Cabinet/chair utilization."""

    cabinet: str
    appointment_count: int
    completed_count: int
    total_minutes: int
    total_hours: float


class DayOfWeekStats(BaseModel):
    """Appointment distribution by day of week."""

    day_of_week: int = Field(description="0=Sunday, 1=Monday, ..., 6=Saturday")
    day_name: str
    appointment_count: int
    completed_count: int
    cancelled_count: int
    no_show_count: int
