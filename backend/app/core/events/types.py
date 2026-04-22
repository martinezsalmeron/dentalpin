"""Event type constants for the event bus."""


class EventType:
    """Constants for event types used across modules.

    Naming convention: {entity}.{action}
    """

    # Patient events
    PATIENT_CREATED = "patient.created"
    PATIENT_UPDATED = "patient.updated"
    PATIENT_ARCHIVED = "patient.archived"
    PATIENT_MEDICAL_UPDATED = "patient.medical_updated"

    # Appointment events
    APPOINTMENT_SCHEDULED = "appointment.scheduled"
    APPOINTMENT_UPDATED = "appointment.updated"
    APPOINTMENT_COMPLETED = "appointment.completed"
    APPOINTMENT_CANCELLED = "appointment.cancelled"
    APPOINTMENT_NO_SHOW = "appointment.no_show"
    # Generic status transition event — always published by
    # ``AppointmentService.transition`` alongside the specific ones above.
    # Payload carries from_status / to_status / changed_at / changed_by so
    # subscribers can subscribe once and react to any transition without
    # knowing the state machine.
    APPOINTMENT_STATUS_CHANGED = "appointment.status_changed"
    APPOINTMENT_CONFIRMED = "appointment.confirmed"
    APPOINTMENT_CHECKED_IN = "appointment.checked_in"
    APPOINTMENT_IN_TREATMENT = "appointment.in_treatment"

    # Treatment events (for future use)
    TREATMENT_COMPLETED = "treatment.completed"

    # Budget events
    BUDGET_CREATED = "budget.created"
    BUDGET_SENT = "budget.sent"
    BUDGET_ACCEPTED = "budget.accepted"
    BUDGET_REJECTED = "budget.rejected"

    # Email events
    EMAIL_SENT = "email.sent"
    EMAIL_FAILED = "email.failed"

    # Invoice events
    INVOICE_CREATED = "invoice.created"
    INVOICE_ISSUED = "invoice.issued"
    INVOICE_SENT = "invoice.sent"
    INVOICE_PAID = "invoice.paid"
    INVOICE_PARTIAL_PAID = "invoice.partial_paid"
    INVOICE_CANCELLED = "invoice.cancelled"
    INVOICE_VOIDED = "invoice.voided"

    # Payment events
    PAYMENT_RECORDED = "payment.recorded"
    PAYMENT_VOIDED = "payment.voided"

    # Credit note events
    CREDIT_NOTE_ISSUED = "credit_note.issued"

    # Odontogram events
    ODONTOGRAM_SURFACE_UPDATED = "odontogram.surface.updated"
    ODONTOGRAM_TOOTH_UPDATED = "odontogram.tooth.updated"
    ODONTOGRAM_CONDITION_CHANGED = "odontogram.condition.changed"

    # Tooth treatment events (for budget module integration)
    ODONTOGRAM_TREATMENT_ADDED = "odontogram.treatment.added"
    ODONTOGRAM_TREATMENT_STATUS_CHANGED = "odontogram.treatment.status_changed"
    ODONTOGRAM_TREATMENT_PERFORMED = "odontogram.treatment.performed"
    ODONTOGRAM_TREATMENT_DELETED = "odontogram.treatment.deleted"

    # Document events
    DOCUMENT_UPLOADED = "document.uploaded"
    DOCUMENT_DELETED = "document.deleted"
    DOCUMENT_ARCHIVED = "document.archived"

    # Treatment plan events
    TREATMENT_PLAN_CREATED = "treatment_plan.created"
    TREATMENT_PLAN_STATUS_CHANGED = "treatment_plan.status_changed"
    TREATMENT_PLAN_TREATMENT_ADDED = "treatment_plan.treatment_added"
    TREATMENT_PLAN_TREATMENT_REMOVED = "treatment_plan.treatment_removed"
    TREATMENT_PLAN_TREATMENT_COMPLETED = "treatment_plan.treatment_completed"
    TREATMENT_PLAN_BUDGET_SYNC_REQUESTED = "treatment_plan.budget_sync_requested"
