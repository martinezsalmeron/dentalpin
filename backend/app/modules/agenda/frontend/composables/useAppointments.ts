import type { Appointment, AppointmentCreate, AppointmentStatus, AppointmentUpdate, PaginatedResponse, ApiResponse } from '~~/app/types'

export function useAppointments() {
  const api = useApi()

  // State
  const appointments = useState<Appointment[]>('appointments:list', () => [])
  const isLoading = useState<boolean>('appointments:loading', () => false)
  const error = useState<string | null>('appointments:error', () => null)

  // Actions
  async function fetchAppointments(startDate: Date, endDate: Date): Promise<Appointment[]> {
    isLoading.value = true
    error.value = null

    try {
      const params = new URLSearchParams({
        start_date: startDate.toISOString(),
        end_date: endDate.toISOString(),
        page_size: '500'
      })

      const response = await api.get<PaginatedResponse<Appointment>>(
        `/api/v1/agenda/appointments?${params.toString()}`
      )

      appointments.value = response.data
      return response.data
    } catch (e) {
      error.value = 'Failed to fetch appointments'
      console.error('Failed to fetch appointments:', e)
      return []
    } finally {
      isLoading.value = false
    }
  }

  async function createAppointment(data: AppointmentCreate): Promise<Appointment> {
    const response = await api.post<ApiResponse<Appointment>>(
      '/api/v1/agenda/appointments',
      data as unknown as Record<string, unknown>
    )

    // Add to local state
    appointments.value = [...appointments.value, response.data]

    return response.data
  }

  async function updateAppointment(id: string, data: AppointmentUpdate): Promise<Appointment> {
    const response = await api.put<ApiResponse<Appointment>>(
      `/api/v1/agenda/appointments/${id}`,
      data as unknown as Record<string, unknown>
    )

    // Update local state
    appointments.value = appointments.value.map(apt =>
      apt.id === id ? response.data : apt
    )

    return response.data
  }

  async function cancelAppointment(id: string): Promise<void> {
    await api.del(`/api/v1/agenda/appointments/${id}`)

    // Update local state - mark as cancelled
    appointments.value = appointments.value.map(apt =>
      apt.id === id ? { ...apt, status: 'cancelled' as const } : apt
    )
  }

  async function updateAppointmentStatus(id: string, status: Appointment['status']): Promise<Appointment> {
    return await updateAppointment(id, { status })
  }

  /**
   * Assign, reassign or unassign (``cabinet_id=null``) a cabinet.
   * Optimistic local update + rollback on failure.
   */
  async function assignCabinet(
    id: string,
    cabinetId: string | null,
    note?: string
  ): Promise<Appointment> {
    const previous = appointments.value.find(apt => apt.id === id)
    const optimisticNow = new Date().toISOString()

    if (previous) {
      appointments.value = appointments.value.map(apt =>
        apt.id === id
          ? {
              ...apt,
              cabinet_id: cabinetId,
              cabinet: cabinetId === null ? null : apt.cabinet,
              cabinet_assigned_at: cabinetId === null ? null : optimisticNow
            }
          : apt
      )
    }

    try {
      const response = await api.patch<ApiResponse<Appointment>>(
        `/api/v1/agenda/appointments/${id}/cabinet`,
        { cabinet_id: cabinetId, note: note ?? null }
      )
      appointments.value = appointments.value.map(apt =>
        apt.id === id ? response.data : apt
      )
      return response.data
    } catch (err) {
      if (previous) {
        appointments.value = appointments.value.map(apt =>
          apt.id === id ? previous : apt
        )
      }
      throw err
    }
  }

  /**
   * Transition an appointment through the status lifecycle. Updates the
   * local list optimistically (``status`` + ``current_status_since``) and
   * rolls back on failure. Returns the server's authoritative response.
   */
  async function transition(
    id: string,
    to: AppointmentStatus,
    note?: string
  ): Promise<Appointment> {
    const previous = appointments.value.find(apt => apt.id === id)
    const optimisticSince = new Date().toISOString()

    if (previous) {
      appointments.value = appointments.value.map(apt =>
        apt.id === id
          ? { ...apt, status: to, current_status_since: optimisticSince }
          : apt
      )
    }

    try {
      const response = await api.post<ApiResponse<Appointment>>(
        `/api/v1/agenda/appointments/${id}/transitions`,
        { to_status: to, note: note ?? null }
      )
      appointments.value = appointments.value.map(apt =>
        apt.id === id ? response.data : apt
      )
      return response.data
    } catch (err) {
      if (previous) {
        appointments.value = appointments.value.map(apt =>
          apt.id === id ? previous : apt
        )
      }
      throw err
    }
  }

  return {
    appointments: readonly(appointments),
    isLoading: readonly(isLoading),
    error: readonly(error),
    fetchAppointments,
    createAppointment,
    updateAppointment,
    cancelAppointment,
    updateAppointmentStatus,
    transition,
    assignCabinet
  }
}
