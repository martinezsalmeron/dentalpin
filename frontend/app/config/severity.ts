/**
 * Single source of truth for status/severity → semantic role mapping.
 *
 * A "role" is one of the DentalPin semantic colours (DESIGN.md §2.4):
 *   'primary' | 'success' | 'info' | 'warning' | 'danger' | 'neutral'
 *
 * These are mapped to Nuxt UI colour names via `roleToUiColor`.
 */

export type SemanticRole
  = | 'primary'
    | 'success'
    | 'info'
    | 'warning'
    | 'danger'
    | 'neutral'

/**
 * Nuxt UI v4 colour names. Maps 1:1 to `app.config.ts` colour aliases.
 */
export type UiColor
  = | 'primary'
    | 'success'
    | 'info'
    | 'warning'
    | 'error'
    | 'neutral'

/**
 * Converts a semantic role to the Nuxt UI colour prop value.
 * In Nuxt UI our `danger` role is named `error`.
 */
export function roleToUiColor(role: SemanticRole): UiColor {
  return role === 'danger' ? 'error' : role
}

// ---------------------------------------------------------------------------
// Patient status
// ---------------------------------------------------------------------------

export type PatientStatus = 'active' | 'inactive' | 'archived'

export const PATIENT_STATUS_ROLE: Record<PatientStatus, SemanticRole> = {
  active: 'success',
  inactive: 'warning',
  archived: 'neutral'
}

// ---------------------------------------------------------------------------
// Appointment status
// ---------------------------------------------------------------------------

export type AppointmentStatus
  = | 'scheduled'
    | 'confirmed'
    | 'checked_in'
    | 'in_treatment'
    | 'completed'
    | 'cancelled'
    | 'no_show'

export const APPOINTMENT_STATUS_ROLE: Record<AppointmentStatus, SemanticRole> = {
  scheduled: 'info',
  confirmed: 'primary',
  checked_in: 'warning',
  in_treatment: 'warning',
  completed: 'success',
  cancelled: 'neutral',
  no_show: 'danger'
}

// ---------------------------------------------------------------------------
// Treatment status (odontogram)
// ---------------------------------------------------------------------------

export type TreatmentStatus
  = | 'diagnosed'
    | 'planned'
    | 'performed'
    | 'cancelled'

export const TREATMENT_STATUS_ROLE: Record<TreatmentStatus, SemanticRole> = {
  diagnosed: 'warning',
  planned: 'info',
  performed: 'success',
  cancelled: 'neutral'
}

// ---------------------------------------------------------------------------
// Treatment plan status
// ---------------------------------------------------------------------------

export type TreatmentPlanStatus
  = | 'draft'
    | 'active'
    | 'completed'
    | 'cancelled'
    | 'on_hold'

export const TREATMENT_PLAN_STATUS_ROLE: Record<TreatmentPlanStatus, SemanticRole> = {
  draft: 'neutral',
  active: 'primary',
  completed: 'success',
  cancelled: 'neutral',
  on_hold: 'warning'
}

// ---------------------------------------------------------------------------
// Budget status
// ---------------------------------------------------------------------------

export type BudgetStatus
  = | 'draft'
    | 'sent'
    | 'accepted'
    | 'rejected'
    | 'expired'
    | 'invoiced'

export const BUDGET_STATUS_ROLE: Record<BudgetStatus, SemanticRole> = {
  draft: 'neutral',
  sent: 'info',
  accepted: 'success',
  rejected: 'danger',
  expired: 'warning',
  invoiced: 'primary'
}

// ---------------------------------------------------------------------------
// Invoice status
// ---------------------------------------------------------------------------

export type InvoiceStatus
  = | 'draft'
    | 'issued'
    | 'paid'
    | 'partial'
    | 'overdue'
    | 'cancelled'

export const INVOICE_STATUS_ROLE: Record<InvoiceStatus, SemanticRole> = {
  draft: 'neutral',
  issued: 'info',
  paid: 'success',
  partial: 'warning',
  overdue: 'danger',
  cancelled: 'neutral'
}

// ---------------------------------------------------------------------------
// Alert severity (patient alerts banner)
// ---------------------------------------------------------------------------

export type AlertSeverity = 'critical' | 'high' | 'medium' | 'low'

export const ALERT_SEVERITY_ROLE: Record<AlertSeverity, SemanticRole> = {
  critical: 'danger',
  high: 'warning',
  medium: 'info',
  low: 'neutral'
}

// ---------------------------------------------------------------------------
// Module lifecycle state (admin module manager)
// ---------------------------------------------------------------------------

export type ModuleStateKey
  = | 'installed'
    | 'uninstalled'
    | 'to_install'
    | 'to_upgrade'
    | 'to_remove'
    | 'disabled'
    | 'error'

export const MODULE_STATE_ROLE: Record<ModuleStateKey, SemanticRole> = {
  installed: 'success',
  uninstalled: 'neutral',
  to_install: 'info',
  to_upgrade: 'info',
  to_remove: 'warning',
  disabled: 'neutral',
  error: 'danger'
}
