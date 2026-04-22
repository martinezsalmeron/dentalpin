import type { AppointmentStatus } from '~~/app/types'

/**
 * Canonical appointment status lifecycle — mirrored from the backend
 * (`app.modules.agenda.service.VALID_TRANSITIONS`). A parity test
 * (`tests/test_state_machine_parity.py`) fails CI if these diverge.
 *
 * Everything visual (colour, icon, label key) for appointment status lives
 * here so cards in every view (weekly, daily, kanban) look identical.
 */

export const APPOINTMENT_STATUSES: readonly AppointmentStatus[] = [
  'scheduled',
  'confirmed',
  'checked_in',
  'in_treatment',
  'completed',
  'cancelled',
  'no_show'
] as const

export const VALID_TRANSITIONS: Record<AppointmentStatus, readonly AppointmentStatus[]> = {
  scheduled: ['confirmed', 'checked_in', 'cancelled', 'no_show'],
  confirmed: ['checked_in', 'cancelled', 'no_show'],
  checked_in: ['in_treatment', 'cancelled'],
  in_treatment: ['completed', 'cancelled'],
  completed: [],
  cancelled: [],
  no_show: []
}

export const TERMINAL_STATUSES: readonly AppointmentStatus[] = [
  'completed',
  'cancelled',
  'no_show'
]

export interface TransitionDescriptor {
  to: AppointmentStatus
  labelKey: string
  icon: string
  destructive?: boolean
}

/**
 * Next-logical transition menu, ordered so the primary action for the
 * current state is always item 0. Destructive transitions (cancel,
 * no_show) always land at the end and require a confirmation.
 */
export const NEXT_TRANSITIONS: Record<AppointmentStatus, readonly TransitionDescriptor[]> = {
  scheduled: [
    { to: 'checked_in', labelKey: 'appointments.transitions.checked_in', icon: 'i-lucide-door-open' },
    { to: 'confirmed', labelKey: 'appointments.transitions.confirmed', icon: 'i-lucide-check' },
    { to: 'no_show', labelKey: 'appointments.transitions.no_show', icon: 'i-lucide-user-x', destructive: true },
    { to: 'cancelled', labelKey: 'appointments.transitions.cancelled', icon: 'i-lucide-x', destructive: true }
  ],
  confirmed: [
    { to: 'checked_in', labelKey: 'appointments.transitions.checked_in', icon: 'i-lucide-door-open' },
    { to: 'no_show', labelKey: 'appointments.transitions.no_show', icon: 'i-lucide-user-x', destructive: true },
    { to: 'cancelled', labelKey: 'appointments.transitions.cancelled', icon: 'i-lucide-x', destructive: true }
  ],
  checked_in: [
    { to: 'in_treatment', labelKey: 'appointments.transitions.in_treatment', icon: 'i-lucide-stethoscope' },
    { to: 'cancelled', labelKey: 'appointments.transitions.cancelled', icon: 'i-lucide-x', destructive: true }
  ],
  in_treatment: [
    { to: 'completed', labelKey: 'appointments.transitions.completed', icon: 'i-lucide-check-check' },
    { to: 'cancelled', labelKey: 'appointments.transitions.cancelled', icon: 'i-lucide-x', destructive: true }
  ],
  completed: [],
  cancelled: [],
  no_show: []
}

/** Status → hex colour used for the card left border and chip accent. */
const STATUS_COLOUR: Record<AppointmentStatus, string> = {
  scheduled: '#60A5FA', // blue-400
  confirmed: '#2563EB', // blue-600
  checked_in: '#F59E0B', // amber-500
  in_treatment: '#8B5CF6', // violet-500
  completed: '#22C55E', // green-500
  cancelled: '#9CA3AF', // gray-400
  no_show: '#EF4444' // red-500
}

const STATUS_ICON: Record<AppointmentStatus, string> = {
  scheduled: 'i-lucide-calendar',
  confirmed: 'i-lucide-check',
  checked_in: 'i-lucide-door-open',
  in_treatment: 'i-lucide-stethoscope',
  completed: 'i-lucide-check-check',
  cancelled: 'i-lucide-x',
  no_show: 'i-lucide-user-x'
}

export function useAppointmentStatus() {
  const { t } = useI18n()

  function statusColour(status: AppointmentStatus): string {
    return STATUS_COLOUR[status] ?? '#9CA3AF'
  }

  function statusIcon(status: AppointmentStatus): string {
    return STATUS_ICON[status] ?? 'i-lucide-circle'
  }

  function statusLabel(status: AppointmentStatus): string {
    return t(`appointments.status.${status}`)
  }

  function nextTransitions(status: AppointmentStatus): readonly TransitionDescriptor[] {
    return NEXT_TRANSITIONS[status] ?? []
  }

  function canTransition(from: AppointmentStatus, to: AppointmentStatus): boolean {
    return VALID_TRANSITIONS[from]?.includes(to) ?? false
  }

  function isTerminal(status: AppointmentStatus): boolean {
    return TERMINAL_STATUSES.includes(status)
  }

  return {
    statusColour,
    statusIcon,
    statusLabel,
    nextTransitions,
    canTransition,
    isTerminal
  }
}
