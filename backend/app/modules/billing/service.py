"""Billing module service layer - business logic."""

from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from .models import (
    Invoice,
    InvoiceHistory,
    InvoiceItem,
    InvoiceSeries,
    Payment,
)


class InvoiceNumberService:
    """Service for generating invoice numbers."""

    @staticmethod
    async def generate_number(
        db: AsyncSession,
        clinic_id: UUID,
        series_id: UUID,
    ) -> tuple[str, int]:
        """Generate the next invoice number for a series.

        Handles yearly reset if configured.

        Args:
            db: Database session
            clinic_id: Clinic ID
            series_id: Series ID

        Returns:
            Tuple of (invoice_number, sequential_number)

        Example:
            "FAC-2024-0001", 1
        """
        # Get series with lock for update
        result = await db.execute(
            select(InvoiceSeries)
            .where(
                InvoiceSeries.id == series_id,
                InvoiceSeries.clinic_id == clinic_id,
            )
            .with_for_update()
        )
        series = result.scalar_one_or_none()

        if not series:
            raise ValueError(f"Series {series_id} not found")

        if not series.is_active:
            raise ValueError(f"Series {series.prefix} is not active")

        current_year = date.today().year

        # Check for yearly reset
        if series.reset_yearly and series.last_reset_year != current_year:
            series.current_number = 0
            series.last_reset_year = current_year

        # Increment number
        series.current_number += 1
        sequential_number = series.current_number

        # Format invoice number
        invoice_number = f"{series.prefix}-{current_year}-{sequential_number:04d}"

        await db.flush()

        return invoice_number, sequential_number


class InvoiceSeriesService:
    """Service for invoice series management."""

    @staticmethod
    async def list_series(
        db: AsyncSession,
        clinic_id: UUID,
        series_type: str | None = None,
        active_only: bool = True,
    ) -> list[InvoiceSeries]:
        """List invoice series for a clinic."""
        query = select(InvoiceSeries).where(InvoiceSeries.clinic_id == clinic_id)

        if series_type:
            query = query.where(InvoiceSeries.series_type == series_type)

        if active_only:
            query = query.where(InvoiceSeries.is_active.is_(True))

        query = query.order_by(InvoiceSeries.series_type, InvoiceSeries.prefix)

        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_default_series(
        db: AsyncSession,
        clinic_id: UUID,
        series_type: str,
    ) -> InvoiceSeries | None:
        """Get default series for a type."""
        result = await db.execute(
            select(InvoiceSeries).where(
                InvoiceSeries.clinic_id == clinic_id,
                InvoiceSeries.series_type == series_type,
                InvoiceSeries.is_default.is_(True),
                InvoiceSeries.is_active.is_(True),
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create_series(
        db: AsyncSession,
        clinic_id: UUID,
        data: dict,
    ) -> InvoiceSeries:
        """Create a new invoice series."""
        # If this is default, unset other defaults
        if data.get("is_default"):
            await db.execute(
                select(InvoiceSeries)
                .where(
                    InvoiceSeries.clinic_id == clinic_id,
                    InvoiceSeries.series_type == data["series_type"],
                    InvoiceSeries.is_default.is_(True),
                )
                .with_for_update()
            )
            # SQLAlchemy will handle the update when we flush

        series = InvoiceSeries(
            clinic_id=clinic_id,
            prefix=data["prefix"],
            series_type=data["series_type"],
            description=data.get("description"),
            reset_yearly=data.get("reset_yearly", True),
            is_default=data.get("is_default", False),
            last_reset_year=date.today().year,
        )
        db.add(series)
        await db.flush()

        return series

    @staticmethod
    async def update_series(
        db: AsyncSession,
        series: InvoiceSeries,
        data: dict,
    ) -> InvoiceSeries:
        """Update an invoice series."""
        # If setting as default, unset others
        if data.get("is_default") and not series.is_default:
            result = await db.execute(
                select(InvoiceSeries).where(
                    InvoiceSeries.clinic_id == series.clinic_id,
                    InvoiceSeries.series_type == series.series_type,
                    InvoiceSeries.is_default.is_(True),
                    InvoiceSeries.id != series.id,
                )
            )
            for other_series in result.scalars().all():
                other_series.is_default = False

        if "description" in data:
            series.description = data["description"]
        if "reset_yearly" in data:
            series.reset_yearly = data["reset_yearly"]
        if "is_default" in data:
            series.is_default = data["is_default"]
        if "is_active" in data:
            series.is_active = data["is_active"]

        await db.flush()
        return series


class InvoiceHistoryService:
    """Service for invoice audit log."""

    @staticmethod
    async def add_entry(
        db: AsyncSession,
        clinic_id: UUID,
        invoice_id: UUID,
        action: str,
        changed_by: UUID,
        previous_state: dict | None = None,
        new_state: dict | None = None,
        notes: str | None = None,
    ) -> InvoiceHistory:
        """Add a history entry for an invoice."""
        entry = InvoiceHistory(
            clinic_id=clinic_id,
            invoice_id=invoice_id,
            action=action,
            changed_by=changed_by,
            changed_at=datetime.now(UTC),
            previous_state=previous_state,
            new_state=new_state,
            notes=notes,
        )
        db.add(entry)
        await db.flush()
        return entry

    @staticmethod
    async def list_history(
        db: AsyncSession,
        clinic_id: UUID,
        invoice_id: UUID,
    ) -> list[InvoiceHistory]:
        """List history entries for an invoice."""
        result = await db.execute(
            select(InvoiceHistory)
            .where(
                InvoiceHistory.clinic_id == clinic_id,
                InvoiceHistory.invoice_id == invoice_id,
            )
            .options(joinedload(InvoiceHistory.user))
            .order_by(desc(InvoiceHistory.changed_at))
        )
        return list(result.scalars().all())


class InvoiceItemService:
    """Service for invoice item operations."""

    @staticmethod
    async def create_item(
        db: AsyncSession,
        clinic_id: UUID,
        invoice: Invoice,
        data: dict,
    ) -> InvoiceItem:
        """Create an invoice item."""
        # Get VAT rate from VAT type if provided
        vat_rate = 0.0
        if data.get("vat_type_id"):
            from app.modules.catalog.models import VatType

            result = await db.execute(
                select(VatType).where(
                    VatType.id == data["vat_type_id"],
                    VatType.clinic_id == clinic_id,
                )
            )
            vat_type = result.scalar_one_or_none()
            if vat_type:
                vat_rate = vat_type.rate

        item = InvoiceItem(
            clinic_id=clinic_id,
            invoice_id=invoice.id,
            catalog_item_id=data.get("catalog_item_id"),
            description=data["description"],
            internal_code=data.get("internal_code"),
            unit_price=Decimal(str(data["unit_price"])),
            quantity=data.get("quantity", 1),
            discount_type=data.get("discount_type"),
            discount_value=Decimal(str(data["discount_value"]))
            if data.get("discount_value")
            else None,
            vat_type_id=data.get("vat_type_id"),
            vat_rate=vat_rate,
            vat_exempt_reason=data.get("vat_exempt_reason"),
            tooth_number=data.get("tooth_number"),
            surfaces=data.get("surfaces"),
            display_order=data.get("display_order", 0),
        )
        db.add(item)

        # Calculate line totals
        await InvoiceService.calculate_item_totals(item)

        await db.flush()

        # Recalculate invoice totals
        await InvoiceService.recalculate_totals(db, invoice)

        return item

    @staticmethod
    async def update_item(
        db: AsyncSession,
        clinic_id: UUID,
        item: InvoiceItem,
        invoice: Invoice,
        data: dict,
    ) -> InvoiceItem:
        """Update an invoice item."""
        if "description" in data and data["description"] is not None:
            item.description = data["description"]
        if "unit_price" in data and data["unit_price"] is not None:
            item.unit_price = Decimal(str(data["unit_price"]))
        if "quantity" in data and data["quantity"] is not None:
            item.quantity = data["quantity"]
        if "discount_type" in data:
            item.discount_type = data["discount_type"]
        if "discount_value" in data:
            item.discount_value = (
                Decimal(str(data["discount_value"])) if data["discount_value"] else None
            )
        if "vat_type_id" in data:
            item.vat_type_id = data["vat_type_id"]
            # Update VAT rate
            if data["vat_type_id"]:
                from app.modules.catalog.models import VatType

                result = await db.execute(
                    select(VatType).where(
                        VatType.id == data["vat_type_id"],
                        VatType.clinic_id == clinic_id,
                    )
                )
                vat_type = result.scalar_one_or_none()
                if vat_type:
                    item.vat_rate = vat_type.rate
            else:
                item.vat_rate = 0.0
        if "vat_exempt_reason" in data:
            item.vat_exempt_reason = data["vat_exempt_reason"]
        if "display_order" in data and data["display_order"] is not None:
            item.display_order = data["display_order"]

        # Recalculate line totals
        await InvoiceService.calculate_item_totals(item)

        await db.flush()

        # Recalculate invoice totals
        await InvoiceService.recalculate_totals(db, invoice)

        return item

    @staticmethod
    async def delete_item(
        db: AsyncSession,
        item: InvoiceItem,
        invoice: Invoice,
    ) -> None:
        """Delete an invoice item."""
        await db.delete(item)
        await db.flush()

        # Recalculate invoice totals
        await InvoiceService.recalculate_totals(db, invoice)


class InvoiceService:
    """Service for invoice operations."""

    @staticmethod
    async def calculate_item_totals(item: InvoiceItem) -> None:
        """Calculate line totals for an item."""
        # Line subtotal = unit_price * quantity
        item.line_subtotal = item.unit_price * item.quantity

        # Calculate discount
        item.line_discount = Decimal("0.00")
        if item.discount_type and item.discount_value:
            if item.discount_type == "percentage":
                item.line_discount = item.line_subtotal * item.discount_value / Decimal("100")
            else:  # absolute
                item.line_discount = item.discount_value

        # Subtotal after discount
        taxable_amount = item.line_subtotal - item.line_discount

        # Calculate tax
        item.line_tax = taxable_amount * Decimal(str(item.vat_rate)) / Decimal("100")

        # Line total
        item.line_total = taxable_amount + item.line_tax

    @staticmethod
    async def recalculate_totals(db: AsyncSession, invoice: Invoice) -> None:
        """Recalculate invoice totals from items."""
        # Reload items to ensure fresh data
        await db.refresh(invoice, ["items"])

        subtotal = Decimal("0.00")
        total_discount = Decimal("0.00")
        total_tax = Decimal("0.00")
        total = Decimal("0.00")

        for item in invoice.items:
            subtotal += item.line_subtotal
            total_discount += item.line_discount
            total_tax += item.line_tax
            total += item.line_total

        invoice.subtotal = subtotal
        invoice.total_discount = total_discount
        invoice.total_tax = total_tax
        invoice.total = total

        # Update balance if not draft
        if invoice.status != "draft":
            invoice.balance_due = invoice.total - invoice.total_paid

        await db.flush()

    @staticmethod
    async def list_invoices(
        db: AsyncSession,
        clinic_id: UUID,
        page: int = 1,
        page_size: int = 20,
        patient_id: UUID | None = None,
        status: list[str] | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        due_from: date | None = None,
        due_to: date | None = None,
        overdue: bool | None = None,
        search: str | None = None,
        budget_id: UUID | None = None,
        is_credit_note: bool | None = None,
    ) -> tuple[list[Invoice], int]:
        """List invoices with filtering and pagination."""
        query = (
            select(Invoice)
            .where(
                Invoice.clinic_id == clinic_id,
                Invoice.deleted_at.is_(None),
            )
            .options(
                joinedload(Invoice.patient),
                joinedload(Invoice.creator),
            )
        )

        # Apply filters
        if patient_id:
            query = query.where(Invoice.patient_id == patient_id)

        if status:
            query = query.where(Invoice.status.in_(status))

        if date_from:
            query = query.where(Invoice.issue_date >= date_from)

        if date_to:
            query = query.where(Invoice.issue_date <= date_to)

        if due_from:
            query = query.where(Invoice.due_date >= due_from)

        if due_to:
            query = query.where(Invoice.due_date <= due_to)

        if overdue:
            today = date.today()
            query = query.where(
                and_(
                    Invoice.due_date < today,
                    Invoice.balance_due > 0,
                    Invoice.status.in_(["issued", "partial"]),
                )
            )

        if budget_id:
            query = query.where(Invoice.budget_id == budget_id)

        if is_credit_note is not None:
            if is_credit_note:
                query = query.where(Invoice.credit_note_for_id.isnot(None))
            else:
                query = query.where(Invoice.credit_note_for_id.is_(None))

        if search:
            from app.modules.clinical.models import Patient

            # Search in invoice number or patient name
            search_term = f"%{search}%"
            query = query.outerjoin(Patient).where(
                or_(
                    Invoice.invoice_number.ilike(search_term),
                    Patient.first_name.ilike(search_term),
                    Patient.last_name.ilike(search_term),
                )
            )

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination
        query = query.order_by(desc(Invoice.created_at))
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        invoices = list(result.scalars().unique().all())

        return invoices, total

    @staticmethod
    async def get_invoice(
        db: AsyncSession,
        clinic_id: UUID,
        invoice_id: UUID,
        include_items: bool = True,
        include_payments: bool = True,
    ) -> Invoice | None:
        """Get an invoice by ID with optional related data."""
        query = select(Invoice).where(
            Invoice.id == invoice_id,
            Invoice.clinic_id == clinic_id,
            Invoice.deleted_at.is_(None),
        )

        options = [
            joinedload(Invoice.patient),
            joinedload(Invoice.creator),
            joinedload(Invoice.issuer),
            joinedload(Invoice.budget),
            joinedload(Invoice.credit_note_for),
            joinedload(Invoice.series),
        ]

        if include_items:
            options.append(selectinload(Invoice.items).joinedload(InvoiceItem.catalog_item))
            options.append(selectinload(Invoice.items).joinedload(InvoiceItem.vat_type))

        if include_payments:
            options.append(selectinload(Invoice.payments).joinedload(Payment.recorder))
            options.append(selectinload(Invoice.payments).joinedload(Payment.voider))

        query = query.options(*options)

        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def create_invoice(
        db: AsyncSession,
        clinic_id: UUID,
        created_by: UUID,
        patient_id: UUID,
        series_id: UUID | None = None,
        billing_data: dict | None = None,
        payment_term_days: int = 30,
        due_date: date | None = None,
        notes: dict | None = None,
    ) -> Invoice:
        """Create a new invoice."""
        # Get series (default if not specified)
        if not series_id:
            series = await InvoiceSeriesService.get_default_series(db, clinic_id, "invoice")
            if not series:
                raise ValueError("No default invoice series configured")
            series_id = series.id

        # Generate invoice number
        invoice_number, sequential_number = await InvoiceNumberService.generate_number(
            db, clinic_id, series_id
        )

        # Get patient info for default billing data
        from app.modules.clinical.models import Patient

        result = await db.execute(
            select(Patient).where(
                Patient.id == patient_id,
                Patient.clinic_id == clinic_id,
            )
        )
        patient = result.scalar_one_or_none()
        if not patient:
            raise ValueError("Patient not found")

        # Default billing data from patient
        billing_name = billing_data.get("billing_name") if billing_data else None
        if not billing_name:
            billing_name = f"{patient.first_name} {patient.last_name}"

        invoice = Invoice(
            clinic_id=clinic_id,
            patient_id=patient_id,
            invoice_number=invoice_number,
            series_id=series_id,
            sequential_number=sequential_number,
            status="draft",
            payment_term_days=payment_term_days,
            due_date=due_date,
            billing_name=billing_name,
            billing_tax_id=billing_data.get("billing_tax_id") if billing_data else None,
            billing_address=billing_data.get("billing_address") if billing_data else None,
            billing_email=billing_data.get("billing_email") or patient.email,
            internal_notes=notes.get("internal_notes") if notes else None,
            public_notes=notes.get("public_notes") if notes else None,
            created_by=created_by,
        )
        db.add(invoice)
        await db.flush()

        # Add history
        await InvoiceHistoryService.add_entry(
            db,
            clinic_id=clinic_id,
            invoice_id=invoice.id,
            action="created",
            changed_by=created_by,
            new_state={"invoice_number": invoice_number},
        )

        return invoice

    @staticmethod
    async def update_invoice(
        db: AsyncSession,
        invoice: Invoice,
        updated_by: UUID,
        data: dict,
    ) -> Invoice:
        """Update an invoice (only drafts)."""
        from .workflow import InvoiceWorkflowService

        if not InvoiceWorkflowService.can_edit(invoice):
            raise ValueError("Can only edit draft invoices")

        previous_state = {}

        if "billing_name" in data and data["billing_name"]:
            previous_state["billing_name"] = invoice.billing_name
            invoice.billing_name = data["billing_name"]

        if "billing_tax_id" in data:
            previous_state["billing_tax_id"] = invoice.billing_tax_id
            invoice.billing_tax_id = data["billing_tax_id"]

        if "billing_address" in data:
            previous_state["billing_address"] = invoice.billing_address
            invoice.billing_address = data["billing_address"]

        if "billing_email" in data:
            previous_state["billing_email"] = invoice.billing_email
            invoice.billing_email = data["billing_email"]

        if "payment_term_days" in data and data["payment_term_days"] is not None:
            previous_state["payment_term_days"] = invoice.payment_term_days
            invoice.payment_term_days = data["payment_term_days"]

        if "due_date" in data:
            previous_state["due_date"] = invoice.due_date.isoformat() if invoice.due_date else None
            invoice.due_date = data["due_date"]

        if "internal_notes" in data:
            previous_state["internal_notes"] = invoice.internal_notes
            invoice.internal_notes = data["internal_notes"]

        if "public_notes" in data:
            previous_state["public_notes"] = invoice.public_notes
            invoice.public_notes = data["public_notes"]

        await db.flush()

        # Add history
        if previous_state:
            await InvoiceHistoryService.add_entry(
                db,
                clinic_id=invoice.clinic_id,
                invoice_id=invoice.id,
                action="updated",
                changed_by=updated_by,
                previous_state=previous_state,
                new_state={k: getattr(invoice, k) for k in previous_state.keys()},
            )

        return invoice

    @staticmethod
    async def delete_invoice(
        db: AsyncSession,
        invoice: Invoice,
        deleted_by: UUID,
    ) -> None:
        """Soft delete an invoice (only drafts)."""
        from .workflow import InvoiceWorkflowService

        if not InvoiceWorkflowService.can_edit(invoice):
            raise ValueError("Can only delete draft invoices")

        invoice.deleted_at = datetime.now(UTC)

        await InvoiceHistoryService.add_entry(
            db,
            clinic_id=invoice.clinic_id,
            invoice_id=invoice.id,
            action="deleted",
            changed_by=deleted_by,
        )

        await db.flush()

    @staticmethod
    async def create_from_budget(
        db: AsyncSession,
        clinic_id: UUID,
        created_by: UUID,
        budget_id: UUID,
        items: list[dict],
        billing_data: dict | None = None,
        payment_term_days: int | None = None,
        due_date: date | None = None,
        notes: dict | None = None,
    ) -> Invoice:
        """Create an invoice from a budget with partial invoicing support.

        Args:
            db: Database session
            clinic_id: Clinic ID
            created_by: User creating the invoice
            budget_id: Budget to invoice from
            items: List of items to invoice:
                   [{"budget_item_id": UUID, "quantity": int | None}, ...]
            billing_data: Optional billing data override
            payment_term_days: Optional payment term override
            due_date: Optional due date
            notes: Optional notes

        Returns:
            Created invoice
        """
        from app.modules.budget.models import Budget, BudgetItem

        # Get budget
        result = await db.execute(
            select(Budget)
            .where(
                Budget.id == budget_id,
                Budget.clinic_id == clinic_id,
                Budget.deleted_at.is_(None),
            )
            .options(selectinload(Budget.items).joinedload(BudgetItem.catalog_item))
        )
        budget = result.scalar_one_or_none()

        if not budget:
            raise ValueError("Budget not found")

        # Validate budget status
        if budget.status not in ["accepted", "partially_accepted", "in_progress", "completed"]:
            raise ValueError(f"Cannot invoice budget with status '{budget.status}'")

        # Create invoice
        invoice = await InvoiceService.create_invoice(
            db,
            clinic_id=clinic_id,
            created_by=created_by,
            patient_id=budget.patient_id,
            billing_data=billing_data,
            payment_term_days=payment_term_days or 30,
            due_date=due_date,
            notes=notes,
        )

        # Link to budget
        invoice.budget_id = budget_id

        # Create invoice items from budget items
        budget_items_map = {str(bi.id): bi for bi in budget.items}

        for item_spec in items:
            budget_item_id = str(item_spec["budget_item_id"])
            budget_item = budget_items_map.get(budget_item_id)

            if not budget_item:
                raise ValueError(f"Budget item {budget_item_id} not found")

            if budget_item.item_status not in ["accepted", "in_progress", "completed"]:
                raise ValueError(
                    f"Budget item {budget_item_id} is not accepted (status: {budget_item.item_status})"
                )

            # Calculate available quantity
            invoiced_qty = getattr(budget_item, "invoiced_quantity", 0) or 0
            available_qty = budget_item.quantity - invoiced_qty

            if available_qty <= 0:
                raise ValueError(f"Budget item {budget_item_id} is fully invoiced")

            # Determine quantity to invoice
            requested_qty = item_spec.get("quantity")
            if requested_qty is None:
                quantity = available_qty
            else:
                if requested_qty > available_qty:
                    raise ValueError(
                        f"Requested quantity ({requested_qty}) exceeds available ({available_qty})"
                    )
                quantity = requested_qty

            # Get description from catalog item
            description = "Unknown treatment"
            internal_code = None
            if budget_item.catalog_item:
                names = budget_item.catalog_item.names or {}
                description = names.get("es") or names.get("en") or description
                internal_code = budget_item.catalog_item.internal_code

            # Create invoice item
            invoice_item = InvoiceItem(
                clinic_id=clinic_id,
                invoice_id=invoice.id,
                budget_item_id=budget_item.id,
                catalog_item_id=budget_item.catalog_item_id,
                description=description,
                internal_code=internal_code,
                unit_price=budget_item.unit_price,
                quantity=quantity,
                discount_type=budget_item.discount_type,
                discount_value=budget_item.discount_value,
                vat_type_id=budget_item.vat_type_id,
                vat_rate=budget_item.vat_rate,
                tooth_number=budget_item.tooth_number,
                surfaces=budget_item.surfaces,
                display_order=budget_item.display_order,
            )
            db.add(invoice_item)

            # Calculate line totals
            await InvoiceService.calculate_item_totals(invoice_item)

            # Update budget item invoiced quantity
            budget_item.invoiced_quantity = invoiced_qty + quantity

        await db.flush()

        # Recalculate invoice totals
        await InvoiceService.recalculate_totals(db, invoice)

        # Check if budget is fully invoiced
        all_invoiced = all(
            (getattr(bi, "invoiced_quantity", 0) or 0) >= bi.quantity
            for bi in budget.items
            if bi.item_status in ["accepted", "in_progress", "completed"]
        )

        if all_invoiced and budget.status == "completed":
            from app.modules.budget.workflow import BudgetWorkflowService

            if BudgetWorkflowService.can_transition(budget.status, "invoiced"):
                budget.status = "invoiced"

        await db.flush()

        return invoice

    @staticmethod
    async def on_budget_completed(event_data: dict[str, Any]) -> None:
        """Event handler for budget.completed event.

        Marks budget as ready for invoicing (notification only).
        """
        # This is a placeholder for future notification integration
        pass


class PaymentService:
    """Service for payment operations."""

    @staticmethod
    async def list_payments(
        db: AsyncSession,
        clinic_id: UUID,
        invoice_id: UUID,
        include_voided: bool = False,
    ) -> list[Payment]:
        """List payments for an invoice."""
        query = (
            select(Payment)
            .where(
                Payment.clinic_id == clinic_id,
                Payment.invoice_id == invoice_id,
            )
            .options(
                joinedload(Payment.recorder),
                joinedload(Payment.voider),
            )
            .order_by(desc(Payment.payment_date))
        )

        if not include_voided:
            query = query.where(Payment.is_voided.is_(False))

        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_payment(
        db: AsyncSession,
        clinic_id: UUID,
        payment_id: UUID,
    ) -> Payment | None:
        """Get a payment by ID."""
        result = await db.execute(
            select(Payment)
            .where(
                Payment.id == payment_id,
                Payment.clinic_id == clinic_id,
            )
            .options(
                joinedload(Payment.recorder),
                joinedload(Payment.voider),
                joinedload(Payment.invoice),
            )
        )
        return result.scalar_one_or_none()


class BillingReportService:
    """Service for billing reports."""

    @staticmethod
    async def get_summary(
        db: AsyncSession,
        clinic_id: UUID,
        date_from: date,
        date_to: date,
    ) -> dict[str, Any]:
        """Get billing summary for a period.

        Returns:
            - total_invoiced: Total amount invoiced (issued invoices)
            - total_paid: Total amount paid
            - total_pending: Total balance due
            - invoice_count: Number of invoices issued
            - paid_count: Number of fully paid invoices
            - overdue_count: Number of overdue invoices
            - vat_breakdown: VAT breakdown by rate
        """
        # Get totals for issued invoices in the period
        result = await db.execute(
            select(
                func.count(Invoice.id).label("invoice_count"),
                func.coalesce(func.sum(Invoice.total), 0).label("total_invoiced"),
                func.coalesce(func.sum(Invoice.total_paid), 0).label("total_paid"),
                func.coalesce(func.sum(Invoice.balance_due), 0).label("total_pending"),
            ).where(
                Invoice.clinic_id == clinic_id,
                Invoice.status.notin_(["draft", "voided"]),
                Invoice.issue_date >= date_from,
                Invoice.issue_date <= date_to,
                Invoice.deleted_at.is_(None),
            )
        )
        totals = result.one()

        # Count paid invoices
        result = await db.execute(
            select(func.count(Invoice.id)).where(
                Invoice.clinic_id == clinic_id,
                Invoice.status == "paid",
                Invoice.issue_date >= date_from,
                Invoice.issue_date <= date_to,
                Invoice.deleted_at.is_(None),
            )
        )
        paid_count = result.scalar() or 0

        # Count overdue invoices
        today = date.today()
        result = await db.execute(
            select(func.count(Invoice.id)).where(
                Invoice.clinic_id == clinic_id,
                Invoice.status.in_(["issued", "partial"]),
                Invoice.due_date < today,
                Invoice.balance_due > 0,
                Invoice.deleted_at.is_(None),
            )
        )
        overdue_count = result.scalar() or 0

        # Get VAT breakdown
        from app.modules.catalog.models import VatType

        result = await db.execute(
            select(
                InvoiceItem.vat_type_id,
                InvoiceItem.vat_rate,
                func.coalesce(
                    func.sum(InvoiceItem.line_subtotal - InvoiceItem.line_discount), 0
                ).label("base_amount"),
                func.coalesce(func.sum(InvoiceItem.line_tax), 0).label("tax_amount"),
            )
            .join(Invoice, InvoiceItem.invoice_id == Invoice.id)
            .where(
                Invoice.clinic_id == clinic_id,
                Invoice.status.notin_(["draft", "voided"]),
                Invoice.issue_date >= date_from,
                Invoice.issue_date <= date_to,
                Invoice.deleted_at.is_(None),
            )
            .group_by(InvoiceItem.vat_type_id, InvoiceItem.vat_rate)
        )
        vat_rows = result.all()

        # Get VAT type names
        vat_type_ids = [r.vat_type_id for r in vat_rows if r.vat_type_id]
        vat_names = {}
        if vat_type_ids:
            result = await db.execute(select(VatType).where(VatType.id.in_(vat_type_ids)))
            for vt in result.scalars():
                vat_names[vt.id] = vt.names.get("es", f"IVA {vt.rate}%")

        vat_breakdown = []
        for row in vat_rows:
            vat_breakdown.append(
                {
                    "vat_type_id": row.vat_type_id,
                    "vat_rate": row.vat_rate,
                    "vat_name": vat_names.get(row.vat_type_id, f"IVA {row.vat_rate}%"),
                    "base_amount": row.base_amount,
                    "tax_amount": row.tax_amount,
                    "total_amount": row.base_amount + row.tax_amount,
                }
            )

        return {
            "period_start": date_from,
            "period_end": date_to,
            "total_invoiced": totals.total_invoiced,
            "total_paid": totals.total_paid,
            "total_pending": totals.total_pending,
            "invoice_count": totals.invoice_count,
            "paid_count": paid_count,
            "overdue_count": overdue_count,
            "vat_breakdown": vat_breakdown,
        }

    @staticmethod
    async def get_overdue_invoices(
        db: AsyncSession,
        clinic_id: UUID,
    ) -> list[dict[str, Any]]:
        """Get list of overdue invoices."""
        today = date.today()

        result = await db.execute(
            select(Invoice)
            .where(
                Invoice.clinic_id == clinic_id,
                Invoice.status.in_(["issued", "partial"]),
                Invoice.due_date < today,
                Invoice.balance_due > 0,
                Invoice.deleted_at.is_(None),
            )
            .options(joinedload(Invoice.patient))
            .order_by(Invoice.due_date)
        )

        invoices = result.scalars().all()

        return [
            {
                "id": inv.id,
                "invoice_number": inv.invoice_number,
                "patient_name": f"{inv.patient.last_name}, {inv.patient.first_name}"
                if inv.patient
                else "-",
                "issue_date": inv.issue_date,
                "due_date": inv.due_date,
                "days_overdue": (today - inv.due_date).days,
                "balance_due": inv.balance_due,
            }
            for inv in invoices
        ]

    @staticmethod
    async def get_by_payment_method(
        db: AsyncSession,
        clinic_id: UUID,
        date_from: date,
        date_to: date,
    ) -> list[dict[str, Any]]:
        """Get payments breakdown by payment method."""
        result = await db.execute(
            select(
                Payment.payment_method,
                func.count(Payment.id).label("payment_count"),
                func.coalesce(func.sum(Payment.amount), 0).label("total_amount"),
            )
            .where(
                Payment.clinic_id == clinic_id,
                Payment.payment_date >= date_from,
                Payment.payment_date <= date_to,
                Payment.is_voided.is_(False),
            )
            .group_by(Payment.payment_method)
            .order_by(desc("total_amount"))
        )

        return [
            {
                "payment_method": row.payment_method,
                "total_amount": row.total_amount,
                "payment_count": row.payment_count,
            }
            for row in result.all()
        ]

    @staticmethod
    async def get_by_professional(
        db: AsyncSession,
        clinic_id: UUID,
        date_from: date,
        date_to: date,
    ) -> list[dict[str, Any]]:
        """Get billing breakdown by professional (creator)."""
        from app.core.auth.models import User

        result = await db.execute(
            select(
                Invoice.created_by,
                func.count(Invoice.id).label("invoice_count"),
                func.coalesce(func.sum(Invoice.total), 0).label("total_invoiced"),
            )
            .where(
                Invoice.clinic_id == clinic_id,
                Invoice.status.notin_(["draft", "voided"]),
                Invoice.issue_date >= date_from,
                Invoice.issue_date <= date_to,
                Invoice.deleted_at.is_(None),
            )
            .group_by(Invoice.created_by)
        )
        rows = result.all()

        # Get user names
        user_ids = [r.created_by for r in rows]
        user_names = {}
        if user_ids:
            result = await db.execute(select(User).where(User.id.in_(user_ids)))
            for user in result.scalars():
                user_names[user.id] = f"{user.first_name} {user.last_name}"

        return [
            {
                "professional_id": row.created_by,
                "professional_name": user_names.get(row.created_by, "-"),
                "total_invoiced": row.total_invoiced,
                "invoice_count": row.invoice_count,
            }
            for row in rows
        ]

    @staticmethod
    async def get_vat_summary(
        db: AsyncSession,
        clinic_id: UUID,
        date_from: date,
        date_to: date,
    ) -> list[dict[str, Any]]:
        """Get VAT summary for accounting."""
        from app.modules.catalog.models import VatType

        result = await db.execute(
            select(
                InvoiceItem.vat_type_id,
                InvoiceItem.vat_rate,
                func.coalesce(
                    func.sum(InvoiceItem.line_subtotal - InvoiceItem.line_discount), 0
                ).label("base_amount"),
                func.coalesce(func.sum(InvoiceItem.line_tax), 0).label("tax_amount"),
            )
            .join(Invoice, InvoiceItem.invoice_id == Invoice.id)
            .where(
                Invoice.clinic_id == clinic_id,
                Invoice.status.notin_(["draft", "voided"]),
                Invoice.issue_date >= date_from,
                Invoice.issue_date <= date_to,
                Invoice.deleted_at.is_(None),
            )
            .group_by(InvoiceItem.vat_type_id, InvoiceItem.vat_rate)
            .order_by(InvoiceItem.vat_rate)
        )
        rows = result.all()

        # Get VAT type names
        vat_type_ids = [r.vat_type_id for r in rows if r.vat_type_id]
        vat_names = {}
        if vat_type_ids:
            result = await db.execute(select(VatType).where(VatType.id.in_(vat_type_ids)))
            for vt in result.scalars():
                vat_names[vt.id] = vt.names.get("es", f"IVA {vt.rate}%")

        return [
            {
                "vat_type_id": row.vat_type_id,
                "vat_rate": row.vat_rate,
                "vat_name": vat_names.get(row.vat_type_id, f"IVA {row.vat_rate}%"),
                "base_amount": row.base_amount,
                "tax_amount": row.tax_amount,
                "total_amount": row.base_amount + row.tax_amount,
            }
            for row in rows
        ]

    @staticmethod
    async def get_numbering_gaps(
        db: AsyncSession,
        clinic_id: UUID,
    ) -> list[dict[str, Any]]:
        """Find gaps in invoice numbering.

        Returns list of gaps by series and year.
        """
        # Get all series for the clinic
        result = await db.execute(
            select(InvoiceSeries).where(
                InvoiceSeries.clinic_id == clinic_id,
                InvoiceSeries.is_active.is_(True),
            )
        )
        series_list = result.scalars().all()

        gaps = []

        for series in series_list:
            # Get all sequential numbers for this series, grouped by year
            result = await db.execute(
                select(
                    func.extract("year", Invoice.created_at).label("year"),
                    Invoice.sequential_number,
                )
                .where(
                    Invoice.clinic_id == clinic_id,
                    Invoice.series_id == series.id,
                    Invoice.deleted_at.is_(None),
                )
                .order_by("year", Invoice.sequential_number)
            )
            rows = result.all()

            # Group by year
            by_year: dict[int, list[int]] = {}
            for row in rows:
                year = int(row.year)
                if year not in by_year:
                    by_year[year] = []
                by_year[year].append(row.sequential_number)

            # Find gaps in each year
            for year, numbers in by_year.items():
                if not numbers:
                    continue

                numbers = sorted(set(numbers))
                expected = set(range(1, max(numbers) + 1))
                found = set(numbers)
                missing = sorted(expected - found)

                if missing:
                    gaps.append(
                        {
                            "series_prefix": series.prefix,
                            "year": year,
                            "missing_numbers": missing,
                        }
                    )

        return gaps
