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
    # Cabinet (re)assignment — published by AppointmentService.assign_cabinet.
    # Consumers that care about where a patient physically is (real-time
    # kanban, occupancy dashboards) subscribe to this event. The payload
    # carries from_cabinet_id / to_cabinet_id / changed_at / changed_by;
    # either cabinet id can be null (first assignment or an unassign).
    APPOINTMENT_CABINET_CHANGED = "appointment.cabinet_changed"

    # Treatment events (for future use)
    TREATMENT_COMPLETED = "treatment.completed"

    # Budget events
    BUDGET_CREATED = "budget.created"
    BUDGET_SENT = "budget.sent"
    BUDGET_ACCEPTED = "budget.accepted"
    BUDGET_REJECTED = "budget.rejected"
    # Auto-expired by the daily cron when ``valid_until < today`` and the
    # budget was still ``sent`` or ``draft``. Payload carries a snapshot
    # (budget_id, plan_id, patient_id, days_overdue) so subscribers do not
    # need to import budget models.
    BUDGET_EXPIRED = "budget.expired"
    # Reception cancelled a sent budget for renegotiation. The companion
    # plan is unlocked back to ``draft``. Payload carries
    # (budget_id, plan_id, patient_id, version, cancelled_at).
    BUDGET_RENEGOTIATED = "budget.renegotiated"
    # Patient opened the public link (first time). Payload carries
    # (budget_id, plan_id, patient_id, viewed_at, ip_hash). Idempotent.
    BUDGET_VIEWED = "budget.viewed"
    # Automatic reminder dispatched to the patient (7d / 14d milestone).
    # Payload carries (budget_id, plan_id, patient_id, milestone_days,
    # sent_at). Only fired when ``budget_reminders_enabled`` for the clinic.
    BUDGET_REMINDER_SENT = "budget.reminder_sent"

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
    # Doctor closed the plan clinically (``draft`` → ``pending``). Payload
    # carries a full snapshot so subscribers (budget for draft creation,
    # patient_timeline for audit) do not need to import treatment_plan
    # models. Snapshot fields: plan_id, plan_number, clinic_id, patient_id,
    # patient_full_name, items[{id, catalog_item_id, tooth, surfaces,
    # quantity, estimated_price}], total_estimated, confirmed_at,
    # confirmed_by_user_id.
    TREATMENT_PLAN_ITEMS_REORDERED = "treatment_plan.items_reordered"
    TREATMENT_PLAN_CONFIRMED = "treatment_plan.confirmed"
    # Plan transitioned to terminal ``closed`` state. Payload:
    # (plan_id, clinic_id, patient_id, closure_reason, closure_note,
    # closed_at, closed_by_user_id, previous_status).
    TREATMENT_PLAN_CLOSED = "treatment_plan.closed"
    # Plan revived from ``closed`` back to ``draft``. Payload:
    # (plan_id, clinic_id, patient_id, previous_closure_reason,
    # reactivated_at, reactivated_by_user_id).
    TREATMENT_PLAN_REACTIVATED = "treatment_plan.reactivated"

    # Treatment-plan completion audit (kept here — emitted by treatment_plan
    # when an item is completed without a clinical note, consumed by
    # patient_timeline for compliance audit).
    TREATMENT_PLAN_ITEM_COMPLETED_WITHOUT_NOTE = "treatment_plan.item_completed_without_note"

    # Clinical-notes events (clinical_notes module — replaces the legacy
    # ``treatment_plan.{plan,item}_note_created`` pair).
    CLINICAL_NOTE_ADMINISTRATIVE_CREATED = "clinical_notes.administrative_created"
    CLINICAL_NOTE_DIAGNOSIS_CREATED = "clinical_notes.diagnosis_created"
    CLINICAL_NOTE_TREATMENT_CREATED = "clinical_notes.treatment_created"
    CLINICAL_NOTE_PLAN_CREATED = "clinical_notes.plan_created"

    # Visit-level note event (agenda module — reuses AppointmentTreatment.notes)
    AGENDA_VISIT_NOTE_UPDATED = "agenda.visit_note_updated"

    # Verifactu compliance events
    VERIFACTU_RECORD_REJECTED = "verifactu.record.rejected"
