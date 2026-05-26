/**
 * Heatmap colour mapping for probing depth.
 *
 * Discrete scale chosen to match the calm-design palette: a measured
 * site is rendered in one of four tones depending on its pocket depth,
 * and unmeasured sites stay neutral. Frontend-only — backend never
 * cares about colours.
 */

export type HeatmapTone = 'neutral' | 'success' | 'warning-low' | 'warning-high' | 'error'

// Calm-design pastel mapping — matches DentalPin's status badge tonal
// scale (soft fill + accent ring + dark readable text). A site marker
// should *signal* the pocket-depth bucket without shouting; the saturated
// 500/600 tones used to dominate the SEPA chart visually.
const TONE_TO_CLASS: Record<HeatmapTone, string> = {
  'neutral': 'bg-gray-100 ring-gray-300 text-gray-500 dark:bg-gray-700/70 dark:ring-gray-500 dark:text-gray-300',
  'success': 'bg-emerald-50 ring-emerald-400 text-emerald-700 dark:bg-emerald-900/50 dark:ring-emerald-500 dark:text-emerald-200',
  'warning-low': 'bg-amber-50 ring-amber-400 text-amber-700 dark:bg-amber-900/50 dark:ring-amber-500 dark:text-amber-200',
  'warning-high': 'bg-orange-50 ring-orange-500 text-orange-700 dark:bg-orange-900/50 dark:ring-orange-500 dark:text-orange-200',
  'error': 'bg-rose-50 ring-rose-400 text-rose-700 dark:bg-rose-900/50 dark:ring-rose-500 dark:text-rose-200'
}

const TONE_TO_HEX: Record<HeatmapTone, string> = {
  'neutral': '#d1d5db', // gray-300
  'success': '#34d399', // emerald-400
  'warning-low': '#fbbf24', // amber-400
  'warning-high': '#f97316', // orange-500
  'error': '#fb7185' // rose-400
}

export function probingDepthTone(pd: number | null | undefined): HeatmapTone {
  if (pd === null || pd === undefined) return 'neutral'
  if (pd <= 3) return 'success'
  if (pd === 4) return 'warning-low'
  if (pd <= 6) return 'warning-high'
  return 'error'
}

export function probingDepthClasses(pd: number | null | undefined): string {
  return TONE_TO_CLASS[probingDepthTone(pd)]
}

export function probingDepthHex(pd: number | null | undefined): string {
  return TONE_TO_HEX[probingDepthTone(pd)]
}
