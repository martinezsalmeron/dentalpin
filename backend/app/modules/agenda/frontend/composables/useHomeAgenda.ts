import type { Appointment, PaginatedResponse } from '~~/app/types'

/**
 * Shared state for agenda widgets on the home dashboard. Today's and
 * tomorrow's appointments are fetched once per range and reused across
 * the KPI tiles, timeline strip and unconfirmed panel.
 */
export function useHomeAgenda() {
  const api = useApi()

  const todayAppointments = useState<Appointment[]>('agenda.home:today', () => [])
  const tomorrowUnconfirmed = useState<Appointment[]>('agenda.home:tomorrow-unconfirmed', () => [])
  const todayLoaded = useState<boolean>('agenda.home:today-loaded', () => false)
  const tomorrowLoaded = useState<boolean>('agenda.home:tomorrow-loaded', () => false)

  function rangeFor(offsetDays: number): { start: string, end: string } {
    const now = new Date()
    const base = new Date(now.getFullYear(), now.getMonth(), now.getDate() + offsetDays)
    const start = base.toISOString()
    const end = new Date(base.getFullYear(), base.getMonth(), base.getDate(), 23, 59, 59).toISOString()
    return { start, end }
  }

  async function fetchToday(): Promise<Appointment[]> {
    const { start, end } = rangeFor(0)
    try {
      const res = await api.get<PaginatedResponse<Appointment>>(
        `/api/v1/agenda/appointments?start_date=${start}&end_date=${end}&page_size=500`
      )
      todayAppointments.value = res.data
    } catch {
      todayAppointments.value = []
    } finally {
      todayLoaded.value = true
    }
    return todayAppointments.value
  }

  async function fetchTomorrowUnconfirmed(): Promise<Appointment[]> {
    const { start, end } = rangeFor(1)
    try {
      const res = await api.get<PaginatedResponse<Appointment>>(
        `/api/v1/agenda/appointments?start_date=${start}&end_date=${end}&status=scheduled&page_size=500`
      )
      tomorrowUnconfirmed.value = res.data
    } catch {
      tomorrowUnconfirmed.value = []
    } finally {
      tomorrowLoaded.value = true
    }
    return tomorrowUnconfirmed.value
  }

  function replaceTodayAppointment(updated: Appointment): void {
    todayAppointments.value = todayAppointments.value.map(a =>
      a.id === updated.id ? updated : a
    )
  }

  function removeTomorrowUnconfirmed(id: string): void {
    tomorrowUnconfirmed.value = tomorrowUnconfirmed.value.filter(a => a.id !== id)
  }

  return {
    todayAppointments: readonly(todayAppointments),
    tomorrowUnconfirmed: readonly(tomorrowUnconfirmed),
    todayLoaded: readonly(todayLoaded),
    tomorrowLoaded: readonly(tomorrowLoaded),
    fetchToday,
    fetchTomorrowUnconfirmed,
    replaceTodayAppointment,
    removeTomorrowUnconfirmed
  }
}
