"""Event handlers for the notifications module.

These handlers listen to events from other modules and trigger
notification emails when appropriate.
"""

import asyncio
import logging
from typing import Any
from uuid import UUID

from sqlalchemy import select

from app.database import async_session_maker

logger = logging.getLogger(__name__)


class NotificationHandlers:
    """Event handlers for notification triggers."""

    @staticmethod
    def on_appointment_scheduled(data: dict[str, Any]) -> None:
        """Handle appointment.scheduled event.

        Sends appointment confirmation email to patient.
        """
        asyncio.create_task(NotificationHandlers._handle_appointment_scheduled(data))

    @staticmethod
    async def _handle_appointment_scheduled(data: dict[str, Any]) -> None:
        """Async handler for appointment scheduled."""
        from app.modules.agenda.models import Appointment
        from app.modules.notifications.service import NotificationService
        from app.modules.patients.models import Patient

        try:
            clinic_id = UUID(data["clinic_id"])
            appointment_id = UUID(data["appointment_id"])

            async with async_session_maker() as db:
                # Get appointment with patient
                result = await db.execute(
                    select(Appointment).where(Appointment.id == appointment_id)
                )
                appointment = result.scalar_one_or_none()
                if not appointment:
                    logger.error(f"Appointment not found: {appointment_id}")
                    return

                # Get patient
                result = await db.execute(
                    select(Patient).where(Patient.id == appointment.patient_id)
                )
                patient = result.scalar_one_or_none()
                if not patient or not patient.email:
                    logger.info(
                        f"Patient has no email, skipping notification: {appointment.patient_id}"
                    )
                    return

                # Get clinic info
                from app.core.auth.models import Clinic

                result = await db.execute(select(Clinic).where(Clinic.id == clinic_id))
                clinic = result.scalar_one_or_none()

                # Get professional info if assigned
                professional_name = None
                if appointment.professional_id:
                    from app.core.auth.models import User

                    result = await db.execute(
                        select(User).where(User.id == appointment.professional_id)
                    )
                    professional = result.scalar_one_or_none()
                    if professional:
                        professional_name = f"{professional.first_name} {professional.last_name}"

                # Build context
                context = {
                    "patient_name": f"{patient.first_name} {patient.last_name}",
                    "appointment_date": appointment.start_time.strftime("%d/%m/%Y"),
                    "appointment_time": appointment.start_time.strftime("%H:%M"),
                    "professional_name": professional_name,
                    "clinic_name": clinic.name if clinic else "DentalPin",
                    "clinic_phone": clinic.phone if clinic else None,
                    "clinic_address": clinic.address if clinic else None,
                    "notes": appointment.notes,
                }

                # Send notification
                await NotificationService.send_notification(
                    db=db,
                    clinic_id=clinic_id,
                    notification_type="appointment_confirmation",
                    to_email=patient.email,
                    context=context,
                    patient_id=patient.id,
                    triggered_by_event="appointment.scheduled",
                )

        except Exception as e:
            logger.error(f"Error handling appointment.scheduled: {e}", exc_info=True)

    @staticmethod
    def on_appointment_cancelled(data: dict[str, Any]) -> None:
        """Handle appointment.cancelled event.

        Sends appointment cancellation email to patient.
        """
        asyncio.create_task(NotificationHandlers._handle_appointment_cancelled(data))

    @staticmethod
    async def _handle_appointment_cancelled(data: dict[str, Any]) -> None:
        """Async handler for appointment cancelled."""
        from app.modules.agenda.models import Appointment
        from app.modules.notifications.service import NotificationService
        from app.modules.patients.models import Patient

        try:
            clinic_id = UUID(data["clinic_id"])
            appointment_id = UUID(data["appointment_id"])
            cancellation_reason = data.get("reason")

            async with async_session_maker() as db:
                # Get appointment
                result = await db.execute(
                    select(Appointment).where(Appointment.id == appointment_id)
                )
                appointment = result.scalar_one_or_none()
                if not appointment:
                    return

                # Get patient
                result = await db.execute(
                    select(Patient).where(Patient.id == appointment.patient_id)
                )
                patient = result.scalar_one_or_none()
                if not patient or not patient.email:
                    return

                # Get clinic info
                from app.core.auth.models import Clinic

                result = await db.execute(select(Clinic).where(Clinic.id == clinic_id))
                clinic = result.scalar_one_or_none()

                # Get professional info
                professional_name = None
                if appointment.professional_id:
                    from app.core.auth.models import User

                    result = await db.execute(
                        select(User).where(User.id == appointment.professional_id)
                    )
                    professional = result.scalar_one_or_none()
                    if professional:
                        professional_name = f"{professional.first_name} {professional.last_name}"

                # Build context
                context = {
                    "patient_name": f"{patient.first_name} {patient.last_name}",
                    "appointment_date": appointment.start_time.strftime("%d/%m/%Y"),
                    "appointment_time": appointment.start_time.strftime("%H:%M"),
                    "professional_name": professional_name,
                    "cancellation_reason": cancellation_reason,
                    "clinic_name": clinic.name if clinic else "DentalPin",
                    "clinic_phone": clinic.phone if clinic else None,
                }

                await NotificationService.send_notification(
                    db=db,
                    clinic_id=clinic_id,
                    notification_type="appointment_cancelled",
                    to_email=patient.email,
                    context=context,
                    patient_id=patient.id,
                    triggered_by_event="appointment.cancelled",
                )

        except Exception as e:
            logger.error(f"Error handling appointment.cancelled: {e}", exc_info=True)

    @staticmethod
    def on_patient_created(data: dict[str, Any]) -> None:
        """Handle patient.created event.

        Sends welcome email to new patient (if auto_send is enabled).
        """
        asyncio.create_task(NotificationHandlers._handle_patient_created(data))

    @staticmethod
    async def _handle_patient_created(data: dict[str, Any]) -> None:
        """Async handler for patient created."""
        from app.modules.notifications.service import NotificationService
        from app.modules.patients.models import Patient

        try:
            clinic_id = UUID(data["clinic_id"])
            patient_id = UUID(data["patient_id"])

            async with async_session_maker() as db:
                # Get patient
                result = await db.execute(select(Patient).where(Patient.id == patient_id))
                patient = result.scalar_one_or_none()
                if not patient or not patient.email:
                    return

                # Get clinic info
                from app.core.auth.models import Clinic

                result = await db.execute(select(Clinic).where(Clinic.id == clinic_id))
                clinic = result.scalar_one_or_none()

                # Build context
                context = {
                    "patient_name": f"{patient.first_name} {patient.last_name}",
                    "clinic_name": clinic.name if clinic else "DentalPin",
                    "clinic_phone": clinic.phone if clinic else None,
                    "clinic_address": clinic.address if clinic else None,
                }

                await NotificationService.send_notification(
                    db=db,
                    clinic_id=clinic_id,
                    notification_type="welcome",
                    to_email=patient.email,
                    context=context,
                    patient_id=patient.id,
                    triggered_by_event="patient.created",
                )

        except Exception as e:
            logger.error(f"Error handling patient.created: {e}", exc_info=True)

    @staticmethod
    def on_budget_sent(data: dict[str, Any]) -> None:
        """Handle budget.sent event.

        Sends budget email to patient.
        """
        asyncio.create_task(NotificationHandlers._handle_budget_sent(data))

    @staticmethod
    async def _handle_budget_sent(data: dict[str, Any]) -> None:
        """Async handler for budget sent.

        Only sends email if send_method is "email".
        Manual sends (printed/handed) don't trigger email.
        """
        from app.modules.budget.models import Budget, BudgetItem
        from app.modules.notifications.service import NotificationService
        from app.modules.patients.models import Patient

        # Only send email if explicitly requested
        send_method = data.get("send_method", "manual")
        if send_method != "email":
            logger.info(
                f"Budget sent manually (not by email), skipping notification: {data.get('budget_id')}"
            )
            return

        try:
            clinic_id = UUID(data["clinic_id"])
            budget_id = UUID(data["budget_id"])

            async with async_session_maker() as db:
                # Get budget with items
                result = await db.execute(select(Budget).where(Budget.id == budget_id))
                budget = result.scalar_one_or_none()
                if not budget:
                    return

                # Get patient
                result = await db.execute(select(Patient).where(Patient.id == budget.patient_id))
                patient = result.scalar_one_or_none()
                if not patient or not patient.email:
                    return

                # Get clinic info
                from app.core.auth.models import Clinic

                result = await db.execute(select(Clinic).where(Clinic.id == clinic_id))
                clinic = result.scalar_one_or_none()

                # Get budget items
                result = await db.execute(
                    select(BudgetItem).where(BudgetItem.budget_id == budget_id)
                )
                items = result.scalars().all()

                # Build treatments list for template
                treatments = []
                for item in items:
                    # Get catalog item name
                    from app.modules.catalog.models import TreatmentCatalogItem

                    result = await db.execute(
                        select(TreatmentCatalogItem).where(
                            TreatmentCatalogItem.id == item.catalog_item_id
                        )
                    )
                    catalog_item = result.scalar_one_or_none()
                    treatments.append(
                        {
                            "name": catalog_item.name if catalog_item else "Tratamiento",
                            "tooth": item.tooth_number,
                            "price": float(item.line_total),
                        }
                    )

                # Build context
                context = {
                    "patient_name": f"{patient.first_name} {patient.last_name}",
                    "budget_number": budget.budget_number,
                    "budget_date": budget.valid_from.strftime("%d/%m/%Y"),
                    "treatments": treatments,
                    "subtotal": float(budget.subtotal),
                    "discount_amount": float(budget.total_discount)
                    if budget.total_discount
                    else None,
                    "total": float(budget.total),
                    "validity_days": (budget.valid_until - budget.valid_from).days
                    if budget.valid_until
                    else None,
                    "notes": budget.patient_notes,
                    "custom_message": data.get("custom_message"),
                    "clinic_name": clinic.name if clinic else "DentalPin",
                    "clinic_phone": clinic.phone if clinic else None,
                }

                await NotificationService.send_notification(
                    db=db,
                    clinic_id=clinic_id,
                    notification_type="budget_sent",
                    to_email=patient.email,
                    context=context,
                    patient_id=patient.id,
                    triggered_by_event="budget.sent",
                )

        except Exception as e:
            logger.error(f"Error handling budget.sent: {e}", exc_info=True)

    @staticmethod
    def on_invoice_sent(data: dict[str, Any]) -> None:
        """Handle invoice.sent event.

        Sends invoice email to patient.
        """
        asyncio.create_task(NotificationHandlers._handle_invoice_sent(data))

    @staticmethod
    async def _handle_invoice_sent(data: dict[str, Any]) -> None:
        """Async handler for invoice sent.

        Only sends email if send_method is "email".
        Manual sends don't trigger email.
        """
        from app.modules.billing.models import Invoice, InvoiceItem
        from app.modules.notifications.service import NotificationService
        from app.modules.patients.models import Patient

        # Only send email if explicitly requested
        send_method = data.get("send_method", "manual")
        if send_method != "email":
            logger.info(
                f"Invoice sent manually (not by email), skipping notification: {data.get('invoice_id')}"
            )
            return

        try:
            clinic_id = UUID(data["clinic_id"])
            invoice_id = UUID(data["invoice_id"])

            async with async_session_maker() as db:
                # Get invoice with items
                result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
                invoice = result.scalar_one_or_none()
                if not invoice:
                    return

                # Get patient
                result = await db.execute(select(Patient).where(Patient.id == invoice.patient_id))
                patient = result.scalar_one_or_none()
                if not patient or not patient.email:
                    return

                # Get clinic info
                from app.core.auth.models import Clinic

                result = await db.execute(select(Clinic).where(Clinic.id == clinic_id))
                clinic = result.scalar_one_or_none()

                # Get invoice items
                result = await db.execute(
                    select(InvoiceItem).where(InvoiceItem.invoice_id == invoice_id)
                )
                items = result.scalars().all()

                # Build items list for template
                invoice_items = []
                for item in items:
                    invoice_items.append(
                        {
                            "description": item.description,
                            "quantity": item.quantity,
                            "unit_price": float(item.unit_price),
                            "line_total": float(item.line_total),
                        }
                    )

                # Build context
                context = {
                    "patient_name": f"{patient.first_name} {patient.last_name}",
                    "invoice_number": invoice.invoice_number,
                    "invoice_date": invoice.issue_date.strftime("%d/%m/%Y")
                    if invoice.issue_date
                    else None,
                    "due_date": invoice.due_date.strftime("%d/%m/%Y") if invoice.due_date else None,
                    "items": invoice_items,
                    "subtotal": float(invoice.subtotal),
                    "total_discount": float(invoice.total_discount)
                    if invoice.total_discount
                    else None,
                    "total_tax": float(invoice.total_tax) if invoice.total_tax else None,
                    "total": float(invoice.total),
                    "balance_due": float(invoice.balance_due),
                    "billing_name": invoice.billing_name,
                    "custom_message": data.get("custom_message"),
                    "clinic_name": clinic.name if clinic else "DentalPin",
                    "clinic_phone": clinic.phone if clinic else None,
                    "clinic_address": clinic.address if clinic else None,
                }

                await NotificationService.send_notification(
                    db=db,
                    clinic_id=clinic_id,
                    notification_type="invoice_sent",
                    to_email=patient.email,
                    context=context,
                    patient_id=patient.id,
                    triggered_by_event="invoice.sent",
                )

        except Exception as e:
            logger.error(f"Error handling invoice.sent: {e}", exc_info=True)

    @staticmethod
    def on_budget_accepted(data: dict[str, Any]) -> None:
        """Handle budget.accepted event.

        Sends budget acceptance confirmation to patient.
        """
        asyncio.create_task(NotificationHandlers._handle_budget_accepted(data))

    @staticmethod
    async def _handle_budget_accepted(data: dict[str, Any]) -> None:
        """Async handler for budget accepted."""
        from app.modules.budget.models import Budget
        from app.modules.notifications.service import NotificationService
        from app.modules.patients.models import Patient

        try:
            clinic_id = UUID(data["clinic_id"])
            budget_id = UUID(data["budget_id"])

            async with async_session_maker() as db:
                # Get budget
                result = await db.execute(select(Budget).where(Budget.id == budget_id))
                budget = result.scalar_one_or_none()
                if not budget:
                    return

                # Get patient
                result = await db.execute(select(Patient).where(Patient.id == budget.patient_id))
                patient = result.scalar_one_or_none()
                if not patient or not patient.email:
                    return

                # Get clinic info
                from app.core.auth.models import Clinic

                result = await db.execute(select(Clinic).where(Clinic.id == clinic_id))
                clinic = result.scalar_one_or_none()

                # Build context
                context = {
                    "patient_name": f"{patient.first_name} {patient.last_name}",
                    "budget_number": budget.budget_number,
                    "accepted_date": budget.updated_at.strftime("%d/%m/%Y"),
                    "total": float(budget.total),
                    "notes": budget.patient_notes,
                    "clinic_name": clinic.name if clinic else "DentalPin",
                    "clinic_phone": clinic.phone if clinic else None,
                }

                await NotificationService.send_notification(
                    db=db,
                    clinic_id=clinic_id,
                    notification_type="budget_accepted",
                    to_email=patient.email,
                    context=context,
                    patient_id=patient.id,
                    triggered_by_event="budget.accepted",
                )

        except Exception as e:
            logger.error(f"Error handling budget.accepted: {e}", exc_info=True)
