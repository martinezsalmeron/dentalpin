/**
 * Format a Date as ``YYYY-MM-DD`` in the local timezone. Used across the
 * agenda module to match appointment ``start_time`` date prefixes (which
 * are stored as ISO strings whose date component is interpreted in the
 * server's local zone) when bucketing / filtering by day.
 */
export function formatLocalDate(date: Date): string {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}
