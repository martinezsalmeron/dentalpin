/**
 * Compute mobile-agenda timeline entries (busy / free / blocked) for a
 * single resource (professional or cabinet) on a given day.
 *
 * Pure client-side: subtracts existing appointments + availability
 * blocked ranges from the day window. Issue #61.
 */
import type { Appointment } from '~~/app/types'
import type { AvailabilityPayload } from './useScheduleAvailability'

export type ResourceKind = 'professional' | 'cabinet'

export interface ResourceRef {
  kind: ResourceKind
  id: string
}

export interface FreeSlotEntry {
  type: 'free'
  start: Date
  end: Date
  durationMin: number
  qualifies: boolean
}

export interface BusyEntry {
  type: 'busy'
  start: Date
  end: Date
  appointment: Appointment
}

export interface BlockedEntry {
  type: 'blocked'
  start: Date
  end: Date
  reason: 'clinic_closed' | 'professional_off' | 'on_break'
}

export type TimelineEntry = FreeSlotEntry | BusyEntry | BlockedEntry

export interface DaySummary {
  totalFreeMin: number
  nextFreeStart: Date | null
  nextFreeDurationMin: number | null
  qualifyingGapsCount: number
}

export interface DayBounds {
  startHour: number
  endHour: number
}

interface Interval {
  start: Date
  end: Date
}

function isSameDay(a: Date, b: Date): boolean {
  return a.getFullYear() === b.getFullYear()
    && a.getMonth() === b.getMonth()
    && a.getDate() === b.getDate()
}

function dayWindow(date: Date, bounds: DayBounds): Interval {
  const start = new Date(date)
  start.setHours(bounds.startHour, 0, 0, 0)
  const end = new Date(date)
  if (bounds.endHour >= 24) {
    end.setHours(23, 59, 59, 999)
  } else {
    end.setHours(bounds.endHour, 0, 0, 0)
  }
  return { start, end }
}

function clamp(interval: Interval, window: Interval): Interval | null {
  const start = interval.start < window.start ? window.start : interval.start
  const end = interval.end > window.end ? window.end : interval.end
  if (end <= start) return null
  return { start, end }
}

function mergeIntervals(intervals: Interval[]): Interval[] {
  if (intervals.length === 0) return []
  const sorted = [...intervals].sort((a, b) => a.start.getTime() - b.start.getTime())
  const merged: Interval[] = []
  let cur = { start: new Date(sorted[0]!.start), end: new Date(sorted[0]!.end) }
  for (let i = 1; i < sorted.length; i++) {
    const next = sorted[i]!
    if (next.start.getTime() <= cur.end.getTime()) {
      if (next.end.getTime() > cur.end.getTime()) cur.end = new Date(next.end)
    } else {
      merged.push(cur)
      cur = { start: new Date(next.start), end: new Date(next.end) }
    }
  }
  merged.push(cur)
  return merged
}

function complement(window: Interval, busy: Interval[]): Interval[] {
  const free: Interval[] = []
  let cursor = window.start.getTime()
  for (const b of busy) {
    if (b.start.getTime() > cursor) {
      free.push({ start: new Date(cursor), end: new Date(b.start) })
    }
    cursor = Math.max(cursor, b.end.getTime())
  }
  if (cursor < window.end.getTime()) {
    free.push({ start: new Date(cursor), end: new Date(window.end) })
  }
  return free
}

function durationMinutes(interval: Interval): number {
  return Math.round((interval.end.getTime() - interval.start.getTime()) / 60000)
}

export function useFreeSlots(opts: {
  appointments: Ref<readonly Appointment[]> | ComputedRef<readonly Appointment[]>
  availability: Ref<AvailabilityPayload | null>
  resource: Ref<ResourceRef | null>
  date: Ref<Date>
  minDurationMin: Ref<number>
  bounds: Ref<DayBounds>
}) {
  const { appointments, availability, resource, date, minDurationMin, bounds } = opts

  const window = computed<Interval>(() => dayWindow(date.value, bounds.value))

  // Appointments for this resource on this day, excluding cancelled.
  const resourceAppointments = computed<Appointment[]>(() => {
    const res = resource.value
    if (!res) return []
    return appointments.value.filter((apt) => {
      if (apt.status === 'cancelled') return false
      const start = new Date(apt.start_time)
      if (!isSameDay(start, date.value)) return false
      if (res.kind === 'professional') return apt.professional_id === res.id
      // Cabinet: name-based match (Appointment.cabinet stores cabinet name).
      // Unassigned cabinet appointments must NOT count as busy for any
      // specific cabinet — they belong nowhere yet.
      return apt.cabinet === res.id
    })
  })

  // Blocked ranges from availability (clinic closed, professional off).
  const blockedRanges = computed<BlockedEntry[]>(() => {
    const payload = availability.value
    if (!payload) return []
    const res = resource.value
    const window_ = window.value
    const out: BlockedEntry[] = []
    for (const r of payload.ranges) {
      if (r.state === 'open') continue
      // Filter by resource: if we are showing a cabinet, only clinic_closed
      // applies; professional_off ranges are scoped to a specific
      // professional and shouldn't gray out other cabinets.
      if (res?.kind === 'cabinet' && r.state === 'professional_off') continue
      if (res?.kind === 'professional' && r.state === 'professional_off') {
        if (r.professional_id && r.professional_id !== res.id) continue
      }
      const clamped = clamp(
        { start: new Date(r.start), end: new Date(r.end) },
        window_
      )
      if (!clamped) continue
      const reason: BlockedEntry['reason']
        = r.state === 'clinic_closed' ? 'clinic_closed' : 'professional_off'
      out.push({ type: 'blocked', start: clamped.start, end: clamped.end, reason })
    }
    return out
  })

  // Busy = appointments + blocked, merged.
  const busyMerged = computed<Interval[]>(() => {
    const intervals: Interval[] = []
    for (const apt of resourceAppointments.value) {
      const clamped = clamp(
        { start: new Date(apt.start_time), end: new Date(apt.end_time) },
        window.value
      )
      if (clamped) intervals.push(clamped)
    }
    for (const b of blockedRanges.value) {
      intervals.push({ start: b.start, end: b.end })
    }
    return mergeIntervals(intervals)
  })

  const freeIntervals = computed<FreeSlotEntry[]>(() => {
    const min = minDurationMin.value
    return complement(window.value, busyMerged.value).map((iv) => {
      const dur = durationMinutes(iv)
      return {
        type: 'free' as const,
        start: iv.start,
        end: iv.end,
        durationMin: dur,
        qualifies: dur >= min
      }
    })
  })

  // Chronological union for the timeline view.
  const entries = computed<TimelineEntry[]>(() => {
    const out: TimelineEntry[] = []
    for (const apt of resourceAppointments.value) {
      out.push({
        type: 'busy',
        start: new Date(apt.start_time),
        end: new Date(apt.end_time),
        appointment: apt
      })
    }
    for (const b of blockedRanges.value) {
      out.push(b)
    }
    for (const f of freeIntervals.value) {
      // Drop zero-length artefacts that can appear when busy intervals
      // touch the window edges.
      if (f.durationMin > 0) out.push(f)
    }
    out.sort((a, b) => a.start.getTime() - b.start.getTime())
    return out
  })

  const summary = computed<DaySummary>(() => {
    const slots = freeIntervals.value
    const min = minDurationMin.value
    const now = new Date()
    let totalFreeMin = 0
    let qualifyingGapsCount = 0
    let nextFreeStart: Date | null = null
    let nextFreeDurationMin: number | null = null
    for (const s of slots) {
      if (!s.qualifies) continue
      totalFreeMin += s.durationMin
      qualifyingGapsCount += 1
      if (s.end.getTime() <= now.getTime()) continue
      if (nextFreeStart === null || s.start.getTime() < nextFreeStart.getTime()) {
        nextFreeStart = s.start
        nextFreeDurationMin = s.durationMin
      }
    }
    // If no future qualifying slot but the day is in the future, surface
    // the first qualifying one regardless of clock.
    if (nextFreeStart === null && slots.length > 0 && !isSameDay(date.value, now)) {
      const first = slots.find(s => s.qualifies)
      if (first) {
        nextFreeStart = first.start
        nextFreeDurationMin = first.durationMin
      }
    }
    void min
    return { totalFreeMin, nextFreeStart, nextFreeDurationMin, qualifyingGapsCount }
  })

  return { entries, summary, freeIntervals }
}

/**
 * Format a duration in minutes as Spanish/English-friendly short label.
 * Examples: 30 -> "30 min", 75 -> "1 h 15 min", 60 -> "1 h".
 */
export function formatDuration(min: number): string {
  if (min < 60) return `${min} min`
  const h = Math.floor(min / 60)
  const m = min % 60
  if (m === 0) return `${h} h`
  return `${h} h ${m} min`
}
