/**
 * 404-tolerant availability fetcher.
 *
 * Lives in the *agenda* layer (not schedules) so that uninstalling the
 * schedules module never breaks agenda's build: this composable only
 * knows the URL of the schedules endpoint and gracefully degrades when
 * the module is absent.
 */
import type { ApiResponse } from '~~/app/types'

export interface AvailabilityRange {
  start: string
  end: string
  state: 'open' | 'clinic_closed' | 'professional_off'
  professional_id: string | null
  reason: string | null
}

export interface AvailabilityPayload {
  timezone: string
  ranges: AvailabilityRange[]
}

export function useScheduleAvailability() {
  const api = useApi()

  async function fetch(
    params: { start: string, end: string, professional_id?: string }
  ): Promise<AvailabilityPayload | null> {
    const query = new URLSearchParams()
    query.set('start', params.start)
    query.set('end', params.end)
    if (params.professional_id) query.set('professional_id', params.professional_id)
    try {
      const res = await api.get<ApiResponse<AvailabilityPayload>>(
        `/api/v1/schedules/availability?${query.toString()}`
      )
      return res.data
    } catch (err: unknown) {
      const code = (err as { statusCode?: number }).statusCode
      if (code === 404 || code === 403) return null
      // Network / unknown — don't block the calendar.
      return null
    }
  }

  /**
   * Convenience: return only open ranges (what the calendar considers
   * available). Useful for computing visible calendar bounds.
   */
  async function fetchOpenRanges(
    params: { start: string, end: string, professional_id?: string }
  ): Promise<AvailabilityRange[] | null> {
    const payload = await fetch(params)
    if (payload === null) return null
    return payload.ranges.filter(r => r.state === 'open')
  }

  return { fetch, fetchOpenRanges }
}
