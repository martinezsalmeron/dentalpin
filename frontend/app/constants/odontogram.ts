/**
 * Odontogram Constants
 *
 * FDI notation tooth numbers and related constants for dental charts.
 */

import type { Surface, ToothCondition, TreatmentType } from '~/types'

// ============================================================================
// Tooth Layouts (FDI Notation)
// ============================================================================

/**
 * Permanent teeth layout by quadrant.
 * Visual layout: molars on edges, incisors in center (patient-facing view)
 */
export const PERMANENT_TEETH = {
  upperRight: [18, 17, 16, 15, 14, 13, 12, 11], // Molars→Incisors (left side of screen)
  upperLeft: [21, 22, 23, 24, 25, 26, 27, 28], // Incisors→Molars (right side of screen)
  lowerRight: [48, 47, 46, 45, 44, 43, 42, 41], // Molars→Incisors (left side of screen)
  lowerLeft: [31, 32, 33, 34, 35, 36, 37, 38] // Incisors→Molars (right side of screen)
} as const

/**
 * Deciduous (baby) teeth layout by quadrant.
 */
export const DECIDUOUS_TEETH = {
  upperRight: [55, 54, 53, 52, 51],
  upperLeft: [61, 62, 63, 64, 65],
  lowerRight: [85, 84, 83, 82, 81],
  lowerLeft: [71, 72, 73, 74, 75]
} as const

/** All deciduous tooth numbers for quick lookup */
export const ALL_DECIDUOUS_NUMBERS = [
  ...DECIDUOUS_TEETH.upperRight,
  ...DECIDUOUS_TEETH.upperLeft,
  ...DECIDUOUS_TEETH.lowerLeft,
  ...DECIDUOUS_TEETH.lowerRight
] as const

// ============================================================================
// Condition Colors
// ============================================================================

/** Default colors for tooth conditions (fallback if not provided by API) */
export const CONDITION_COLORS: Record<ToothCondition, string> = {
  healthy: '#FFFFFF',
  caries: '#EF4444',
  filling: '#3B82F6',
  crown: '#F59E0B',
  missing: '#9CA3AF',
  root_canal: '#8B5CF6',
  implant: '#10B981',
  bridge_pontic: '#F97316',
  bridge_abutment: '#FBBF24',
  extraction_indicated: '#DC2626',
  sealant: '#06B6D4',
  fracture: '#BE185D'
}

// ============================================================================
// Surface Labels
// ============================================================================

/** Human-readable labels for tooth surfaces */
export const SURFACE_LABELS: Record<Surface, string> = {
  M: 'Mesial',
  D: 'Distal',
  O: 'Occlusal',
  V: 'Vestibular',
  L: 'Lingual'
}

// ============================================================================
// Keyboard Shortcuts
// ============================================================================

/** Keyboard shortcuts for quick treatment selection (1-8 keys) */
export const TREATMENT_SHORTCUTS: Record<string, TreatmentType> = {
  1: 'extraction',
  2: 'filling',
  3: 'root_canal',
  4: 'crown',
  5: 'implant',
  6: 'veneer',
  7: 'sealant',
  8: 'caries'
}

// ============================================================================
// Types
// ============================================================================

export type TeethLayout = typeof PERMANENT_TEETH
export type QuadrantKey = keyof TeethLayout
