/**
 * Heatmap colour mapping for probing depth.
 *
 * Discrete scale chosen to match the calm-design palette: a measured
 * site is rendered in one of four tones depending on its pocket depth,
 * and unmeasured sites stay neutral. Frontend-only — backend never
 * cares about colours.
 */

export type HeatmapTone = 'neutral' | 'success' | 'warning-low' | 'warning-high' | 'error'

const TONE_TO_CLASS: Record<HeatmapTone, string> = {
  'neutral': 'bg-gray-300 ring-gray-300 text-gray-700',
  'success': 'bg-success-500 ring-success-500 text-white',
  'warning-low': 'bg-warning-400 ring-warning-400 text-gray-900',
  'warning-high': 'bg-warning-600 ring-warning-600 text-white',
  'error': 'bg-error-500 ring-error-500 text-white'
}

const TONE_TO_HEX: Record<HeatmapTone, string> = {
  'neutral': '#d1d5db', // gray-300
  'success': '#22c55e', // success-500
  'warning-low': '#facc15', // warning-400
  'warning-high': '#d97706', // warning-600
  'error': '#ef4444' // error-500
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
