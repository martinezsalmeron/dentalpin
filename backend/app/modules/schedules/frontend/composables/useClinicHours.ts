import type { ApiResponse } from '~~/app/types'

export interface Shift {
  id?: string
  start_time: string
  end_time: string
}

export interface WeekdayShifts {
  weekday: number
  shifts: Shift[]
}

export interface ClinicHours {
  id: string
  clinic_id: string
  timezone: string
  is_active: boolean
  days: WeekdayShifts[]
}

export interface ClinicOverride {
  id: string
  clinic_id: string
  start_date: string
  end_date: string
  kind: 'closed' | 'custom_hours'
  reason: string | null
  shifts: Shift[]
}

export interface ClinicOverridePayload {
  start_date: string
  end_date: string
  kind: 'closed' | 'custom_hours'
  reason?: string | null
  shifts: { start_time: string, end_time: string }[]
}

export function useClinicHours() {
  const api = useApi()

  async function fetchHours(): Promise<ClinicHours> {
    const res = await api.get<ApiResponse<ClinicHours>>('/api/v1/schedules/clinic-hours')
    return res.data
  }

  async function updateHours(payload: { timezone?: string, days: WeekdayShifts[] }): Promise<ClinicHours> {
    const res = await api.put<ApiResponse<ClinicHours>>('/api/v1/schedules/clinic-hours', payload)
    return res.data
  }

  async function fetchOverrides(params?: { start?: string, end?: string }): Promise<ClinicOverride[]> {
    const query = new URLSearchParams()
    if (params?.start) query.set('start', params.start)
    if (params?.end) query.set('end', params.end)
    const url = query.toString()
      ? `/api/v1/schedules/clinic-overrides?${query.toString()}`
      : '/api/v1/schedules/clinic-overrides'
    const res = await api.get<ApiResponse<ClinicOverride[]>>(url)
    return res.data
  }

  async function createOverride(payload: ClinicOverridePayload): Promise<ClinicOverride> {
    const res = await api.post<ApiResponse<ClinicOverride>>('/api/v1/schedules/clinic-overrides', payload)
    return res.data
  }

  async function updateOverride(id: string, payload: ClinicOverridePayload): Promise<ClinicOverride> {
    const res = await api.put<ApiResponse<ClinicOverride>>(`/api/v1/schedules/clinic-overrides/${id}`, payload)
    return res.data
  }

  async function deleteOverride(id: string): Promise<void> {
    await api.del(`/api/v1/schedules/clinic-overrides/${id}`)
  }

  return {
    fetchHours,
    updateHours,
    fetchOverrides,
    createOverride,
    updateOverride,
    deleteOverride
  }
}
