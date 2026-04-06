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

    # Odontogram events
    ODONTOGRAM_SURFACE_UPDATED = "odontogram.surface.updated"
    ODONTOGRAM_TOOTH_UPDATED = "odontogram.tooth.updated"
    ODONTOGRAM_CONDITION_CHANGED = "odontogram.condition.changed"

    # Tooth treatment events (for budget module integration)
    ODONTOGRAM_TREATMENT_ADDED = "odontogram.treatment.added"
    ODONTOGRAM_TREATMENT_STATUS_CHANGED = "odontogram.treatment.status_changed"
    ODONTOGRAM_TREATMENT_PERFORMED = "odontogram.treatment.performed"
    ODONTOGRAM_TREATMENT_DELETED = "odontogram.treatment.deleted"
