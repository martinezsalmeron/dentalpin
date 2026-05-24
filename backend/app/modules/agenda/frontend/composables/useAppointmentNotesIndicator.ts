import type { ApiResponse } from '~~/app/types'

/**
 * Reactive "has notes" indicator for appointments.
 *
 * Agenda views (weekly/daily/kanban) call ``fetchFor`` with the list of
 * appointment ids currently rendered. The composable does a single
 * batched GET against the clinical_notes module's bulk-counts endpoint
 * and exposes a reactive map so cards can render a sticky-note icon
 * without an N+1 round-trip.
 *
 * Backed by a ``Record<string, true>`` (not a ``Set``) because Nuxt
 * serializes ``useState`` for SSR → hydration; a ``Set`` round-trips
 * as ``{}`` and loses its prototype, breaking ``.has`` on the client.
 *
 * Cross-module shape stays clean: agenda backend does NOT import
 * clinical_notes; the frontend calls the public HTTP endpoint.
 */
export function useAppointmentNotesIndicator() {
  const api = useApi()
  const { can } = usePermissions()

  // Global so every view sees the same map.
  const idsWithNotes = useState<Record<string, true>>(
    'agenda:appointment-notes:map',
    () => ({})
  )
  const fetching = useState<boolean>(
    'agenda:appointment-notes:fetching',
    () => false
  )

  function has(appointmentId: string | null | undefined): boolean {
    if (!appointmentId) return false
    return idsWithNotes.value[appointmentId] === true
  }

  async function fetchFor(appointmentIds: string[]): Promise<void> {
    // Receptionist + clinical roles all have ``clinical_notes.notes.read``
    // by default. Skip the round-trip when the current user doesn't.
    if (!can('clinical_notes.notes.read')) return
    const unique = Array.from(new Set(appointmentIds.filter(Boolean)))
    if (unique.length === 0) {
      idsWithNotes.value = {}
      return
    }

    fetching.value = true
    try {
      // ``owner_ids`` is repeated for each id — keeps the URL under the
      // server's 500-cap (`max_length=500` on the endpoint).
      const params = new URLSearchParams()
      params.set('owner_type', 'appointment')
      for (const id of unique) params.append('owner_ids', id)
      const response = await api.get<ApiResponse<Record<string, number>>>(
        `/api/v1/clinical_notes/notes/counts?${params.toString()}`
      )
      const next: Record<string, true> = {}
      for (const [id, count] of Object.entries(response.data || {})) {
        if (count > 0) next[id] = true
      }
      idsWithNotes.value = next
    } catch (e) {
      console.error('Failed to fetch appointment note counts:', e)
    } finally {
      fetching.value = false
    }
  }

  function markHasNotes(appointmentId: string): void {
    if (!idsWithNotes.value[appointmentId]) {
      idsWithNotes.value = { ...idsWithNotes.value, [appointmentId]: true }
    }
  }

  function clear(): void {
    idsWithNotes.value = {}
  }

  return {
    idsWithNotes: readonly(idsWithNotes),
    fetching: readonly(fetching),
    has,
    fetchFor,
    markHasNotes,
    clear
  }
}
