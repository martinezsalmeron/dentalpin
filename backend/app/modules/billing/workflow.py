"""Invoice workflow service - state machine and status transitions."""

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from .models import Invoice, InvoiceItem, Payment

# Valid status transitions
VALID_TRANSITIONS: dict[str, list[str]] = {
    "draft": ["issued", "voided"],
    "issued": ["paid", "partial", "cancelled"],
    "partial": ["paid", "cancelled"],
    "paid": [],  # Terminal (can emit credit note)
    "cancelled": [],  # Terminal
    "voided": [],  # Terminal
}


class InvoiceWorkflowError(Exception):
    """Exception for workflow validation errors."""

    pass


class InvoiceWorkflowService:
    """Service for invoice status transitions and workflow operations."""

    @staticmethod
    def can_transition(current_status: str, new_status: str) -> bool:
        """Check if a status transition is valid."""
        allowed = VALID_TRANSITIONS.get(current_status, [])
        return new_status in allowed

    @staticmethod
    def can_edit(invoice: Invoice) -> bool:
        """Check if invoice can be edited."""
        return invoice.status == "draft"

    @staticmethod
    def can_issue(invoice: Invoice) -> bool:
        """Check if invoice can be issued."""
        return invoice.status == "draft" and len(invoice.items) > 0

    @staticmethod
    def can_record_payment(invoice: Invoice) -> bool:
        """Check if payment can be recorded for invoice."""
        return invoice.status in ["issued", "partial"]

    @staticmethod
    def can_void(invoice: Invoice) -> bool:
        """Check if invoice can be voided (before issue)."""
        return invoice.status == "draft"

    @staticmethod
    def can_create_credit_note(invoice: Invoice) -> bool:
        """Check if credit note can be created for invoice."""
        return invoice.status in ["issued", "partial", "paid"]

    @staticmethod
    async def issue_invoice(
        db: AsyncSession,
        invoice: Invoice,
        issued_by: UUID,
        issue_date: date | None = None,
        hook_callback=None,
    ) -> Invoice:
        """Issue an invoice (transition from draft to issued).

        Args:
            db: Database session
            invoice: Invoice to issue
            issued_by: User ID issuing the invoice
            issue_date: Issue date (defaults to today)
            hook_callback: Optional compliance hook callback

        Returns:
            Updated invoice

        Raises:
            InvoiceWorkflowError: If transition is not valid
        """
        if not InvoiceWorkflowService.can_issue(invoice):
            if invoice.status != "draft":
                raise InvoiceWorkflowError(f"Cannot issue invoice from status '{invoice.status}'")
            if not invoice.items:
                raise InvoiceWorkflowError("Cannot issue empty invoice")

        previous_status = invoice.status
        invoice.status = "issued"
        invoice.issue_date = issue_date or date.today()
        invoice.issued_by = issued_by

        # Calculate due date if not set
        if not invoice.due_date:
            from datetime import timedelta

            invoice.due_date = invoice.issue_date + timedelta(days=invoice.payment_term_days)

        # Initialize balance
        invoice.balance_due = invoice.total

        # Execute compliance hook if provided
        if hook_callback:
            compliance_data = await hook_callback(invoice, db)
            if compliance_data:
                invoice.compliance_data = invoice.compliance_data or {}
                invoice.compliance_data.update(compliance_data)

        # Add history
        from .service import InvoiceHistoryService

        await InvoiceHistoryService.add_entry(
            db,
            clinic_id=invoice.clinic_id,
            invoice_id=invoice.id,
            action="issued",
            changed_by=issued_by,
            previous_state={"status": previous_status},
            new_state={
                "status": "issued",
                "issue_date": invoice.issue_date.isoformat(),
                "due_date": invoice.due_date.isoformat() if invoice.due_date else None,
            },
        )

        await db.flush()

        return invoice

    @staticmethod
    async def void_invoice(
        db: AsyncSession,
        invoice: Invoice,
        voided_by: UUID,
        reason: str | None = None,
    ) -> Invoice:
        """Void an invoice (only allowed for drafts)."""
        if not InvoiceWorkflowService.can_void(invoice):
            raise InvoiceWorkflowError(f"Cannot void invoice from status '{invoice.status}'")

        previous_status = invoice.status
        invoice.status = "voided"
        invoice.deleted_at = datetime.now(UTC)

        # Add history
        from .service import InvoiceHistoryService

        await InvoiceHistoryService.add_entry(
            db,
            clinic_id=invoice.clinic_id,
            invoice_id=invoice.id,
            action="voided",
            changed_by=voided_by,
            previous_state={"status": previous_status},
            new_state={"status": "voided", "reason": reason},
        )

        await db.flush()

        return invoice

    @staticmethod
    async def record_payment(
        db: AsyncSession,
        invoice: Invoice,
        amount: Decimal,
        payment_method: str,
        payment_date: date,
        recorded_by: UUID,
        reference: str | None = None,
        notes: str | None = None,
    ) -> Payment:
        """Record a payment for an invoice.

        Updates invoice status based on payment amount.
        """
        if not InvoiceWorkflowService.can_record_payment(invoice):
            raise InvoiceWorkflowError(
                f"Cannot record payment for invoice with status '{invoice.status}'"
            )

        # Validate amount doesn't exceed balance
        if amount > invoice.balance_due:
            raise InvoiceWorkflowError(
                f"Payment amount ({amount}) exceeds balance due ({invoice.balance_due})"
            )

        # Create payment
        payment = Payment(
            clinic_id=invoice.clinic_id,
            invoice_id=invoice.id,
            amount=amount,
            payment_method=payment_method,
            payment_date=payment_date,
            reference=reference,
            notes=notes,
            recorded_by=recorded_by,
        )
        db.add(payment)

        # Update invoice totals
        invoice.total_paid = invoice.total_paid + amount
        invoice.balance_due = invoice.total - invoice.total_paid

        # Update status based on payment
        previous_status = invoice.status
        if invoice.balance_due <= Decimal("0.00"):
            invoice.status = "paid"
        else:
            invoice.status = "partial"

        # Add history
        from .service import InvoiceHistoryService

        await InvoiceHistoryService.add_entry(
            db,
            clinic_id=invoice.clinic_id,
            invoice_id=invoice.id,
            action="payment_recorded",
            changed_by=recorded_by,
            previous_state={
                "status": previous_status,
                "total_paid": str(invoice.total_paid - amount),
                "balance_due": str(invoice.balance_due + amount),
            },
            new_state={
                "status": invoice.status,
                "total_paid": str(invoice.total_paid),
                "balance_due": str(invoice.balance_due),
                "payment_amount": str(amount),
                "payment_method": payment_method,
            },
        )

        await db.flush()

        return payment

    @staticmethod
    async def void_payment(
        db: AsyncSession,
        payment: Payment,
        invoice: Invoice,
        voided_by: UUID,
        reason: str,
    ) -> Payment:
        """Void a payment and update invoice balance."""
        if payment.is_voided:
            raise InvoiceWorkflowError("Payment is already voided")

        # Void the payment
        payment.is_voided = True
        payment.voided_at = datetime.now(UTC)
        payment.voided_by = voided_by
        payment.void_reason = reason

        # Update invoice totals
        invoice.total_paid = invoice.total_paid - payment.amount
        invoice.balance_due = invoice.total - invoice.total_paid

        # Update status
        previous_status = invoice.status
        if invoice.balance_due >= invoice.total:
            invoice.status = "issued"
        elif invoice.balance_due > Decimal("0.00"):
            invoice.status = "partial"

        # Add history
        from .service import InvoiceHistoryService

        await InvoiceHistoryService.add_entry(
            db,
            clinic_id=invoice.clinic_id,
            invoice_id=invoice.id,
            action="payment_voided",
            changed_by=voided_by,
            previous_state={
                "status": previous_status,
                "total_paid": str(invoice.total_paid + payment.amount),
                "balance_due": str(invoice.balance_due - payment.amount),
            },
            new_state={
                "status": invoice.status,
                "total_paid": str(invoice.total_paid),
                "balance_due": str(invoice.balance_due),
                "voided_payment_amount": str(payment.amount),
                "void_reason": reason,
            },
        )

        await db.flush()

        return payment

    @staticmethod
    async def create_credit_note(
        db: AsyncSession,
        original_invoice: Invoice,
        created_by: UUID,
        reason: str,
        items: list[dict] | None = None,
        series_id: UUID | None = None,
        hook_callback=None,
    ) -> Invoice:
        """Create a credit note (rectificativa) for an invoice.

        Args:
            db: Database session
            original_invoice: Invoice to rectify
            created_by: User creating the credit note
            reason: Reason for the credit note
            items: Optional list of items to rectify (partial credit note)
                   If None, rectifies entire invoice
            series_id: Optional series ID for credit note (uses default if not provided)
            hook_callback: Optional compliance hook callback

        Returns:
            New credit note invoice
        """
        if not InvoiceWorkflowService.can_create_credit_note(original_invoice):
            raise InvoiceWorkflowError(
                f"Cannot create credit note for invoice with status '{original_invoice.status}'"
            )

        from .service import InvoiceNumberService, InvoiceService

        # Get credit note series
        if not series_id:
            from sqlalchemy import select

            from .models import InvoiceSeries

            result = await db.execute(
                select(InvoiceSeries).where(
                    InvoiceSeries.clinic_id == original_invoice.clinic_id,
                    InvoiceSeries.series_type == "credit_note",
                    InvoiceSeries.is_default.is_(True),
                    InvoiceSeries.is_active.is_(True),
                )
            )
            series = result.scalar_one_or_none()
            if not series:
                raise InvoiceWorkflowError("No default credit note series configured")
            series_id = series.id

        # Generate credit note number
        invoice_number, sequential_number = await InvoiceNumberService.generate_number(
            db, original_invoice.clinic_id, series_id
        )

        # Create credit note
        credit_note = Invoice(
            clinic_id=original_invoice.clinic_id,
            patient_id=original_invoice.patient_id,
            invoice_number=invoice_number,
            series_id=series_id,
            sequential_number=sequential_number,
            credit_note_for_id=original_invoice.id,
            status="issued",
            issue_date=date.today(),
            payment_term_days=0,
            billing_name=original_invoice.billing_name,
            billing_tax_id=original_invoice.billing_tax_id,
            billing_address=original_invoice.billing_address,
            billing_email=original_invoice.billing_email,
            currency=original_invoice.currency,
            internal_notes=f"Nota de crédito por: {reason}",
            public_notes=f"Rectificación de factura {original_invoice.invoice_number}",
            created_by=created_by,
            issued_by=created_by,
        )
        db.add(credit_note)
        await db.flush()

        # Create credit note items (negative amounts)
        if items:
            # Partial credit note: only specified items
            for item_spec in items:
                original_item = next(
                    (i for i in original_invoice.items if i.id == item_spec["invoice_item_id"]),
                    None,
                )
                if not original_item:
                    raise InvoiceWorkflowError(
                        f"Item {item_spec['invoice_item_id']} not found in original invoice"
                    )

                quantity = item_spec.get("quantity") or original_item.quantity
                if quantity > original_item.quantity:
                    raise InvoiceWorkflowError(
                        f"Credit note quantity ({quantity}) exceeds original ({original_item.quantity})"
                    )

                credit_item = InvoiceItem(
                    clinic_id=original_invoice.clinic_id,
                    invoice_id=credit_note.id,
                    budget_item_id=original_item.budget_item_id,
                    catalog_item_id=original_item.catalog_item_id,
                    description=original_item.description,
                    internal_code=original_item.internal_code,
                    unit_price=-original_item.unit_price,  # Negative
                    quantity=quantity,
                    discount_type=original_item.discount_type,
                    discount_value=original_item.discount_value,
                    vat_type_id=original_item.vat_type_id,
                    vat_rate=original_item.vat_rate,
                    vat_exempt_reason=original_item.vat_exempt_reason,
                    tooth_number=original_item.tooth_number,
                    surfaces=original_item.surfaces,
                    display_order=original_item.display_order,
                )
                db.add(credit_item)
                await InvoiceService.calculate_item_totals(credit_item)
        else:
            # Full credit note: all items
            for idx, original_item in enumerate(original_invoice.items):
                credit_item = InvoiceItem(
                    clinic_id=original_invoice.clinic_id,
                    invoice_id=credit_note.id,
                    budget_item_id=original_item.budget_item_id,
                    catalog_item_id=original_item.catalog_item_id,
                    description=original_item.description,
                    internal_code=original_item.internal_code,
                    unit_price=-original_item.unit_price,  # Negative
                    quantity=original_item.quantity,
                    discount_type=original_item.discount_type,
                    discount_value=original_item.discount_value,
                    vat_type_id=original_item.vat_type_id,
                    vat_rate=original_item.vat_rate,
                    vat_exempt_reason=original_item.vat_exempt_reason,
                    tooth_number=original_item.tooth_number,
                    surfaces=original_item.surfaces,
                    display_order=idx,
                )
                db.add(credit_item)
                await InvoiceService.calculate_item_totals(credit_item)

        await db.flush()

        # Calculate credit note totals
        await InvoiceService.recalculate_totals(db, credit_note)

        # Credit note is "paid" because it's negative amount
        credit_note.total_paid = credit_note.total
        credit_note.balance_due = Decimal("0.00")
        credit_note.status = "paid"

        # Update original invoice status
        original_invoice.status = "cancelled"

        # Execute compliance hook if provided
        if hook_callback:
            compliance_data = await hook_callback(credit_note, original_invoice, db)
            if compliance_data:
                credit_note.compliance_data = credit_note.compliance_data or {}
                credit_note.compliance_data.update(compliance_data)

        # Add history to credit note
        from .service import InvoiceHistoryService

        await InvoiceHistoryService.add_entry(
            db,
            clinic_id=credit_note.clinic_id,
            invoice_id=credit_note.id,
            action="created",
            changed_by=created_by,
            new_state={
                "credit_note_for": original_invoice.invoice_number,
                "reason": reason,
            },
        )

        # Add history to original invoice
        await InvoiceHistoryService.add_entry(
            db,
            clinic_id=original_invoice.clinic_id,
            invoice_id=original_invoice.id,
            action="credit_note_created",
            changed_by=created_by,
            previous_state={"status": original_invoice.status},
            new_state={
                "status": "cancelled",
                "credit_note_number": credit_note.invoice_number,
                "reason": reason,
            },
        )

        await db.flush()

        return credit_note
