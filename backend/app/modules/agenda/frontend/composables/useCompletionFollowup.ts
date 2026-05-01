import type { Appointment } from '~~/app/types'

/**
 * Singleton state for the post-completion follow-up modal.
 *
 * Any code that transitions an appointment to ``completed`` should
 * call ``trigger(appointment)`` after the backend confirms the
 * transition. The agenda page mounts the modal once (via
 * ``CompletionFollowupHost.vue``) and renders any components
 * registered into the ``appointment.completed.followup`` slot.
 *
 * Two call-sites today:
 *   - ``AppointmentQuickActions.vue`` — the per-card dropdown menu.
 *   - ``AppointmentKanbanView.vue`` — drag-drop into "Finalizadas".
 *
 * Lifting this out of the components keeps both paths consistent
 * and avoids duplicated modal markup.
 */
export function useCompletionFollowup() {
  const open = useState<boolean>('agenda:completion-followup:open', () => false)
  const appointment = useState<Appointment | null>(
    'agenda:completion-followup:appointment',
    () => null
  )

  function trigger(apt: Appointment) {
    appointment.value = { ...apt, status: 'completed' }
    open.value = true
  }

  function dismiss() {
    open.value = false
    appointment.value = null
  }

  return { open, appointment, trigger, dismiss }
}
