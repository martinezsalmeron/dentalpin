"""Event type constants for the event bus."""


class EventType:
    """Constants for event types used across modules.

    Naming convention: {entity}.{action}
    """

    # Patient events
    PATIENT_CREATED = "patient.created"
    PATIENT_UPDATED = "patient.updated"
    PATIENT_ARCHIVED = "patient.archived"

    # Appointment events
    APPOINTMENT_SCHEDULED = "appointment.scheduled"
    APPOINTMENT_UPDATED = "appointment.updated"
    APPOINTMENT_COMPLETED = "appointment.completed"
    APPOINTMENT_CANCELLED = "appointment.cancelled"
    APPOINTMENT_NO_SHOW = "appointment.no_show"

    # Treatment events (for future use)
    TREATMENT_COMPLETED = "treatment.completed"

    # Budget events (for future use)
    BUDGET_CREATED = "budget.created"
    BUDGET_ACCEPTED = "budget.accepted"
    BUDGET_REJECTED = "budget.rejected"

    # Invoice events (for future use)
    INVOICE_CREATED = "invoice.created"
    INVOICE_PAID = "invoice.paid"
