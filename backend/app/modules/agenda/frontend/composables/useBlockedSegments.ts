/**
 * Compute blocked-time segments (clinic closed, professional off) for the
 * desktop calendar grid. Returns segments keyed by date so consumers can
 * paint per-day overlays without re-deriving slot math.
 *
 * 404-tolerant via `useScheduleAvailability` — if the schedules module is
 * uninstalled the result is an empty array and the calendar renders normally.
 */
import type { Ref } from 'vue'
import { useScheduleAvailability } from './useScheduleAvailability'

export interface BlockedSegment {
  dateKey: string
  professionalId: string | null
  startSlot: number
  endSlot: number
  state: 'clinic_closed' | 'professional_off'
  reason: string | null
}

interface ProfessionalLike { id: string }

function formatLocalDate(date: Date): string {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

export function useBlockedSegments(opts: {
  startHour: Ref<number>
  endHour: Ref<number>
  slotMinutes: number
}) {
  const { fetch: fetchAvailability } = useScheduleAvailability()

  function timeToSlotIndex(d: Date): number {
    const mins = d.getHours() * 60 + d.getMinutes()
    return (mins - opts.startHour.value * 60) / opts.slotMinutes
  }

  function gridSlotsPerDay(): number {
    return ((opts.endHour.value - opts.startHour.value) * 60) / opts.slotMinutes
  }

  function rangesToSegments(
    ranges: Array<{
      start: string
      end: string
      state: 'open' | 'clinic_closed' | 'professional_off'
      professional_id: string | null
      reason: string | null
    }>,
    professionalId: string | null
  ): BlockedSegment[] {
    const out: BlockedSegment[] = []
    const maxSlot = gridSlotsPerDay()
    for (const r of ranges) {
      if (r.state === 'open') continue
      const startDate = new Date(r.start)
      const endDate = new Date(r.end)
      const startSlot = Math.max(0, timeToSlotIndex(startDate))
      const endSlot = Math.min(maxSlot, timeToSlotIndex(endDate))
      if (endSlot <= startSlot) continue
      out.push({
        dateKey: formatLocalDate(startDate),
        professionalId,
        startSlot,
        endSlot,
        state: r.state,
        reason: r.reason
      })
    }
    return out
  }

  /**
   * Fetch availability for [start, end] and return blocked segments.
   *
   * - Omit `professionals` to get a single clinic-wide call (week view).
   * - Pass professionals to get per-professional segments (day view per-pro
   *   columns). Each professional triggers its own backend call so the
   *   resolver can compose clinic + professional precedence correctly.
   */
  async function compute(args: {
    start: Date
    end: Date
    professionals?: ProfessionalLike[]
  }): Promise<BlockedSegment[]> {
    const isoStart = formatLocalDate(args.start)
    const isoEnd = formatLocalDate(args.end)

    if (!args.professionals || args.professionals.length === 0) {
      const payload = await fetchAvailability({ start: isoStart, end: isoEnd })
      if (!payload) return []
      return rangesToSegments(payload.ranges, null)
    }

    const out: BlockedSegment[] = []
    for (const prof of args.professionals) {
      const payload = await fetchAvailability({
        start: isoStart,
        end: isoEnd,
        professional_id: prof.id
      })
      if (!payload) continue
      out.push(...rangesToSegments(payload.ranges, prof.id))
    }
    return out
  }

  return { compute, formatLocalDate }
}
