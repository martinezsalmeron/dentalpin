/**
 * Odontogram Constants - Single Source of Truth
 *
 * This file defines all treatment types and their categorization.
 * All odontogram components should import from here instead of defining locally.
 */

// ============================================================================
// Treatment Type Definitions
// ============================================================================

/**
 * Surface treatments - treatments that affect specific tooth surfaces (M, D, O, V, L)
 */
export const SURFACE_TREATMENTS = ['filling', 'caries', 'sealant'] as const

/**
 * Whole tooth treatments - treatments that affect the entire tooth
 */
export const WHOLE_TOOTH_TREATMENTS = [
  'crown',
  'root_canal',
  'implant',
  'extraction',
  'missing',
  'post',
  'veneer',
  'bridge_pontic',
  'bridge_abutment',
  'fracture',
  'apicoectomy',
  // Orthodontic treatments
  'bracket',
  'band',
  'attachment',
  'retainer'
] as const

/**
 * All treatment types combined
 */
export const ALL_TREATMENT_TYPES = [...SURFACE_TREATMENTS, ...WHOLE_TOOTH_TREATMENTS] as const

// ============================================================================
// Types
// ============================================================================

export type SurfaceTreatmentType = typeof SURFACE_TREATMENTS[number]
export type WholeToothTreatmentType = typeof WHOLE_TOOTH_TREATMENTS[number]
export type TreatmentType = typeof ALL_TREATMENT_TYPES[number]

export type TreatmentStatus = 'preexisting' | 'planned' | 'performed'
export type TreatmentCategory = 'surface' | 'whole_tooth'

export type ToothSurface = 'M' | 'D' | 'O' | 'V' | 'L'

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Check if a treatment type requires surface selection
 */
export function isSurfaceTreatment(treatmentType: string): boolean {
  return (SURFACE_TREATMENTS as readonly string[]).includes(treatmentType)
}

/**
 * Check if a treatment type affects the whole tooth
 */
export function isWholeToothTreatment(treatmentType: string): boolean {
  return (WHOLE_TOOTH_TREATMENTS as readonly string[]).includes(treatmentType)
}

/**
 * Get the category of a treatment type
 */
export function getTreatmentCategory(treatmentType: string): TreatmentCategory {
  return isSurfaceTreatment(treatmentType) ? 'surface' : 'whole_tooth'
}

// ============================================================================
// Treatment Colors
// ============================================================================

export const TREATMENT_COLORS: Record<string, string> = {
  caries: '#EF4444',
  filling: '#3B82F6',
  sealant: '#06B6D4',
  crown: '#F59E0B',
  root_canal: '#8B5CF6',
  implant: '#10B981',
  bridge_pontic: '#F97316',
  bridge_abutment: '#FBBF24',
  extraction: '#DC2626',
  missing: '#9CA3AF',
  fracture: '#BE185D',
  post: '#7C3AED',
  veneer: '#EC4899',
  apicoectomy: '#6366F1',
  // Orthodontic treatments
  bracket: '#6366F1', // Indigo
  band: '#8B5CF6', // Violet
  attachment: '#EC4899', // Pink
  retainer: '#14B8A6', // Teal
  // Position actions
  rotate: '#8B5CF6', // Violet for rotated
  displace: '#F59E0B' // Amber for displaced
}

// ============================================================================
// Status Styles
// ============================================================================

export const STATUS_STYLES: Record<TreatmentStatus, {
  fill: 'solid'
  opacity: number
  border: string | null
  borderWidth: number
  borderDash?: string
}> = {
  preexisting: {
    fill: 'solid',
    opacity: 1.0,
    border: null,
    borderWidth: 0
  },
  planned: {
    fill: 'solid',
    opacity: 0.7,
    border: '#EF4444',
    borderWidth: 2,
    borderDash: '4,2'
  },
  performed: {
    fill: 'solid',
    opacity: 1.0,
    border: '#22C55E',
    borderWidth: 2.5
  }
}

// ============================================================================
// Tooth Categories
// ============================================================================

export type ToothCategory = 'incisor' | 'canine' | 'premolar' | 'molar'

export function getToothCategory(toothNumber: number): ToothCategory {
  const num = toothNumber % 10
  if (num === 1 || num === 2) return 'incisor'
  if (num === 3) return 'canine'
  if (num === 4 || num === 5) return 'premolar'
  return 'molar'
}

export function isUpperTooth(toothNumber: number): boolean {
  const quadrant = Math.floor(toothNumber / 10)
  return quadrant === 1 || quadrant === 2 || quadrant === 5 || quadrant === 6
}

// ============================================================================
// Treatment Category Definitions (for TreatmentBar)
// ============================================================================

export const TREATMENT_CATEGORIES = [
  {
    key: 'common',
    labelKey: 'odontogram.treatments.categories.common',
    treatments: ['filling', 'crown', 'root_canal', 'extraction', 'implant', 'sealant']
  },
  {
    key: 'restorative',
    labelKey: 'odontogram.treatments.categories.restorative',
    treatments: ['veneer', 'post', 'bridge_pontic', 'bridge_abutment']
  },
  {
    key: 'diagnostic',
    labelKey: 'odontogram.treatments.categories.diagnostic',
    treatments: ['caries', 'fracture', 'missing', 'apicoectomy']
  },
  {
    key: 'orthodontic',
    labelKey: 'odontogram.treatments.categories.orthodontic',
    treatments: ['bracket', 'band', 'attachment', 'retainer']
  },
  {
    key: 'position',
    labelKey: 'odontogram.treatments.categories.position',
    treatments: ['rotate', 'displace']
  }
] as const

// Position actions (not treatments, but tooth properties)
export const POSITION_ACTIONS = ['rotate', 'displace'] as const
export type PositionAction = typeof POSITION_ACTIONS[number]

export function isPositionAction(action: string): boolean {
  return (POSITION_ACTIONS as readonly string[]).includes(action)
}

// ============================================================================
// Tooth Name i18n Keys
// ============================================================================

/**
 * Get the i18n key for a tooth name based on its number.
 * Returns the key to use with t() function.
 */
export function getToothNameKey(toothNumber: number): string {
  const num = toothNumber % 10
  const keys: Record<number, string> = {
    1: 'centralIncisor',
    2: 'lateralIncisor',
    3: 'canine',
    4: 'firstPremolar',
    5: 'secondPremolar',
    6: 'firstMolar',
    7: 'secondMolar',
    8: 'thirdMolar'
  }
  return `odontogram.toothNames.${keys[num] || 'unknown'}`
}

/**
 * Get the i18n position keys for a tooth (upper/lower, left/right).
 */
export function getToothPositionKeys(toothNumber: number): { vertical: string, horizontal: string } {
  const quadrant = Math.floor(toothNumber / 10)
  const isUpper = quadrant === 1 || quadrant === 2 || quadrant === 5 || quadrant === 6
  const isRight = quadrant === 1 || quadrant === 4 || quadrant === 5 || quadrant === 8

  return {
    vertical: isUpper ? 'odontogram.positions.upper' : 'odontogram.positions.lower',
    horizontal: isRight ? 'odontogram.positions.right' : 'odontogram.positions.left'
  }
}

// ============================================================================
// Category Status Restrictions
// ============================================================================

/**
 * Status restrictions by category.
 * Diagnostic and position categories only allow "preexisting" status.
 */
export const CATEGORY_STATUS_RESTRICTIONS: Record<string, TreatmentStatus[]> = {
  common: ['planned', 'performed', 'preexisting'],
  restorative: ['planned', 'performed', 'preexisting'],
  diagnostic: ['preexisting'], // Only preexisting
  orthodontic: ['planned', 'performed', 'preexisting'],
  position: ['preexisting'] // Only preexisting
}

/**
 * Get the category key for a treatment type.
 */
export function getCategoryForTreatment(treatmentType: string): string | null {
  for (const category of TREATMENT_CATEGORIES) {
    if ((category.treatments as readonly string[]).includes(treatmentType)) {
      return category.key
    }
  }
  return null
}

/**
 * Get allowed statuses for a treatment type based on its category.
 */
export function getAllowedStatusesForTreatment(treatmentType: string): TreatmentStatus[] {
  const categoryKey = getCategoryForTreatment(treatmentType)
  if (categoryKey && categoryKey in CATEGORY_STATUS_RESTRICTIONS) {
    return CATEGORY_STATUS_RESTRICTIONS[categoryKey]
  }
  return ['planned', 'performed', 'preexisting']
}
