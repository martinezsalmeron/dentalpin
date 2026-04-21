/**
 * Compute [startHour, endHour] bounds for the calendar based on the
 * clinic's actual opening hours. Falls back to 8–21 when the schedules
 * module is uninstalled (fetch returns null).
 */
import { useScheduleAvailability } from './useScheduleAvailability'

const DEFAULT_START = 8
const DEFAULT_END = 21

export interface CalendarBounds {
  startHour: number
  endHour: number
}

export function useCalendarBounds() {
  const { fetchOpenRanges } = useScheduleAvailability()

  async function compute(range: { start: Date, end: Date }): Promise<CalendarBounds> {
    const isoStart = range.start.toISOString().slice(0, 10)
    const isoEnd = range.end.toISOString().slice(0, 10)
    const open = await fetchOpenRanges({ start: isoStart, end: isoEnd })
    if (!open || open.length === 0) {
      return { startHour: DEFAULT_START, endHour: DEFAULT_END }
    }

    let minHour = 24
    let maxHour = 0
    for (const r of open) {
      const s = new Date(r.start)
      const e = new Date(r.end)
      minHour = Math.min(minHour, s.getHours())
      // Round up the end hour so the last slot is included.
      const endHour = e.getMinutes() > 0 || e.getSeconds() > 0 ? e.getHours() + 1 : e.getHours()
      maxHour = Math.max(maxHour, endHour)
    }
    // Safety clamp: keep within [0, 24] and at least 1 hour wide.
    minHour = Math.max(0, Math.min(minHour, 23))
    maxHour = Math.max(minHour + 1, Math.min(maxHour, 24))
    return { startHour: minHour, endHour: maxHour }
  }

  return { compute }
}
