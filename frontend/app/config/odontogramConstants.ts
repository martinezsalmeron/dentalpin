/**
 * Odontogram Constants - Single Source of Truth
 *
 * This file defines all treatment types, visualization rules, and their categorization.
 * All odontogram components should import from here instead of defining locally.
 */

import type { MultiToothTreatmentConfig } from '~/types'

// ============================================================================
// Visualization Rules
// ============================================================================

export type VisualizationRule = 'pulp_fill' | 'occlusal_surface' | 'lateral_icon' | 'pattern_fill'

/**
 * Visualization rules for rendering treatments:
 * - pulp_fill: Fill pulp chamber in lateral view
 * - occlusal_surface: Surface fill/dot in cenital view
 * - lateral_icon: SVG icon overlay on lateral view
 * - pattern_fill: Pattern fill on cenital view
 */
export const VISUALIZATION_RULES: Record<VisualizationRule, string[]> = {
  // Rule 1: Pulp fill (lateral view)
  pulp_fill: [
    'pulpitis',
    'root_canal_full',
    'root_canal_two_thirds',
    'root_canal_half',
    'root_canal_overfill' // Also uses lateral_icon
  ],
  // Rule 2: Occlusal surface (cenital view)
  occlusal_surface: [
    'caries',
    'incipient_caries',
    'pigmentation',
    'filling_composite',
    'filling_amalgam',
    'filling_temporary',
    'sealant',
    'veneer'
  ],
  // Rule 3: Lateral icon (lateral view)
  lateral_icon: [
    'fracture',
    'missing',
    'periapical_small',
    'periapical_medium',
    'periapical_large',
    'rotated',
    'displaced',
    'implant',
    'apicoectomy',
    'extraction',
    'post',
    'root_canal_overfill', // Also uses pulp_fill
    'bracket',
    'tube',
    'band',
    'attachment',
    'retainer',
    'splint'
  ],
  // Rule 4: Pattern fill (cenital view)
  pattern_fill: [
    'unerupted',
    'inlay',
    'pontic',
    'bridge_abutment',
    'overlay',
    'crown'
  ]
}

// ============================================================================
// Occlusal Surface Visualization Config
// ============================================================================

export type OcclusalVisualizationType = 'solid_fill' | 'dot' | 'outline'

export interface OcclusalVisualizationConfig {
  type: OcclusalVisualizationType
  color: string
  darkColor?: string
}

/**
 * How each treatment renders on occlusal/cenital view
 */
export const OCCLUSAL_VISUALIZATION: Record<string, OcclusalVisualizationConfig> = {
  caries: { type: 'solid_fill', color: '#EF4444' },
  incipient_caries: { type: 'dot', color: '#F97316' },
  pigmentation: { type: 'dot', color: '#92400E', darkColor: '#D97706' },
  filling_composite: { type: 'solid_fill', color: '#3B82F6' },
  filling_amalgam: { type: 'solid_fill', color: '#6B7280', darkColor: '#9CA3AF' },
  filling_temporary: { type: 'solid_fill', color: '#22C55E' },
  sealant: { type: 'outline', color: '#7DD3FC' },
  veneer: { type: 'solid_fill', color: '#FEF3C7', darkColor: '#FDE68A' } // V surface only
}

// ============================================================================
// Pattern Definitions for Rule 4
// ============================================================================

export type PatternType = 'diagonal_stripes' | 'dots' | 'grid' | 'vertical_stripes' | 'horizontal_stripes'

export interface PatternConfig {
  type: PatternType
  color: string
  darkColor?: string
}

/**
 * Pattern configurations for Rule 4 treatments
 */
export const PATTERN_CONFIG: Record<string, PatternConfig> = {
  unerupted: { type: 'diagonal_stripes', color: '#9CA3AF' },
  inlay: { type: 'dots', color: '#3B82F6' },
  pontic: { type: 'grid', color: '#3B82F6' },
  bridge_abutment: { type: 'vertical_stripes', color: '#3B82F6' },
  overlay: { type: 'horizontal_stripes', color: '#3B82F6' },
  crown: { type: 'diagonal_stripes', color: '#F59E0B' }
}

// ============================================================================
// Pulp Fill Configuration for Rule 1
// ============================================================================

export type PulpFillLevel = 'full' | 'two_thirds' | 'half'

export interface PulpFillConfig {
  level: PulpFillLevel
  color: string
}

/**
 * Pulp fill configurations for Rule 1 treatments
 */
export const PULP_FILL_CONFIG: Record<string, PulpFillConfig> = {
  pulpitis: { level: 'full', color: '#EF4444' },
  root_canal_full: { level: 'full', color: '#3B82F6' },
  root_canal_two_thirds: { level: 'two_thirds', color: '#3B82F6' },
  root_canal_half: { level: 'half', color: '#3B82F6' },
  root_canal_overfill: { level: 'full', color: '#3B82F6' } // Also has lateral icon
}

// ============================================================================
// Treatment Type Definitions
// ============================================================================

/**
 * Surface treatments - treatments that affect specific tooth surfaces (M, D, O, V, L)
 */
export const SURFACE_TREATMENTS = [
  'caries',
  'incipient_caries',
  'pigmentation',
  'filling_composite',
  'filling_amalgam',
  'filling_temporary',
  'sealant',
  'veneer',
  'inlay',
  // Legacy
  'filling'
] as const

/**
 * Whole tooth treatments - treatments that affect the entire tooth
 */
export const WHOLE_TOOTH_TREATMENTS = [
  'pulpitis',
  'fracture',
  'missing',
  'periapical_small',
  'periapical_medium',
  'periapical_large',
  'rotated',
  'displaced',
  'unerupted',
  'overlay',
  'crown',
  'pontic',
  'bridge_abutment',
  'extraction',
  'implant',
  'apicoectomy',
  'root_canal_full',
  'root_canal_two_thirds',
  'root_canal_half',
  'post',
  'root_canal_overfill',
  'bracket',
  'tube',
  'band',
  'attachment',
  'retainer',
  // Legacy
  'root_canal',
  'bridge_pontic'
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

export type TreatmentStatus = 'existing' | 'planned'
export type TreatmentCategory = 'surface' | 'whole_tooth'

export type ToothSurface = 'M' | 'D' | 'O' | 'V' | 'L'

// ============================================================================
// Legacy Treatment Mapping
// ============================================================================

export const LEGACY_TREATMENT_MAPPING: Record<string, string> = {
  filling: 'filling_composite',
  root_canal: 'root_canal_full',
  bridge_pontic: 'pontic'
}

export function normalizeTreatmentType(treatmentType: string): string {
  return LEGACY_TREATMENT_MAPPING[treatmentType] || treatmentType
}

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Check if a treatment type requires surface selection
 */
export function isSurfaceTreatment(treatmentType: string): boolean {
  const normalized = normalizeTreatmentType(treatmentType)
  return (SURFACE_TREATMENTS as readonly string[]).includes(normalized)
}

/**
 * Check if a treatment type affects the whole tooth
 */
export function isWholeToothTreatment(treatmentType: string): boolean {
  const normalized = normalizeTreatmentType(treatmentType)
  return (WHOLE_TOOTH_TREATMENTS as readonly string[]).includes(normalized)
}

/**
 * Get the category of a treatment type
 */
export function getTreatmentCategory(treatmentType: string): TreatmentCategory {
  return isSurfaceTreatment(treatmentType) ? 'surface' : 'whole_tooth'
}

/**
 * Get visualization rules for a treatment type
 */
export function getVisualizationRules(treatmentType: string): VisualizationRule[] {
  const normalized = normalizeTreatmentType(treatmentType)
  const rules: VisualizationRule[] = []
  for (const [rule, treatments] of Object.entries(VISUALIZATION_RULES)) {
    if (treatments.includes(normalized)) {
      rules.push(rule as VisualizationRule)
    }
  }
  return rules
}

/**
 * Check if a treatment uses a specific visualization rule
 */
export function hasVisualizationRule(treatmentType: string, rule: VisualizationRule): boolean {
  const normalized = normalizeTreatmentType(treatmentType)
  return VISUALIZATION_RULES[rule].includes(normalized)
}

// ============================================================================
// Treatment Colors (with light/dark mode support)
// ============================================================================

export interface TreatmentColorConfig {
  light: string
  dark: string
}

export const TREATMENT_COLORS: Record<string, TreatmentColorConfig> = {
  // Diagnóstico
  pulpitis: { light: '#EF4444', dark: '#F87171' },
  caries: { light: '#EF4444', dark: '#F87171' },
  incipient_caries: { light: '#F97316', dark: '#FB923C' },
  pigmentation: { light: '#92400E', dark: '#D97706' },
  fracture: { light: '#BE185D', dark: '#EC4899' },
  missing: { light: '#6B7280', dark: '#9CA3AF' },
  periapical_small: { light: '#EF4444', dark: '#F87171' },
  periapical_medium: { light: '#DC2626', dark: '#EF4444' },
  periapical_large: { light: '#B91C1C', dark: '#DC2626' },
  rotated: { light: '#8B5CF6', dark: '#A78BFA' },
  displaced: { light: '#F59E0B', dark: '#FBBF24' },
  unerupted: { light: '#9CA3AF', dark: '#D1D5DB' },

  // Restauradora
  filling_composite: { light: '#3B82F6', dark: '#60A5FA' },
  filling_amalgam: { light: '#6B7280', dark: '#9CA3AF' },
  filling_temporary: { light: '#22C55E', dark: '#4ADE80' },
  sealant: { light: '#06B6D4', dark: '#22D3EE' },
  veneer: { light: '#EC4899', dark: '#F472B6' },
  inlay: { light: '#3B82F6', dark: '#60A5FA' },
  overlay: { light: '#3B82F6', dark: '#60A5FA' },
  crown: { light: '#F59E0B', dark: '#FBBF24' },
  pontic: { light: '#F97316', dark: '#FB923C' },
  bridge_abutment: { light: '#FBBF24', dark: '#FDE68A' },
  bridge: { light: '#F59E0B', dark: '#FBBF24' },
  splint: { light: '#3B82F6', dark: '#60A5FA' },

  // Cirugía
  extraction: { light: '#DC2626', dark: '#EF4444' },
  implant: { light: '#10B981', dark: '#34D399' },
  apicoectomy: { light: '#6366F1', dark: '#818CF8' },

  // Endodoncia
  root_canal_full: { light: '#8B5CF6', dark: '#A78BFA' },
  root_canal_two_thirds: { light: '#8B5CF6', dark: '#A78BFA' },
  root_canal_half: { light: '#8B5CF6', dark: '#A78BFA' },
  post: { light: '#7C3AED', dark: '#A855F7' },
  root_canal_overfill: { light: '#3B82F6', dark: '#60A5FA' },

  // Ortodoncia
  bracket: { light: '#6366F1', dark: '#818CF8' },
  tube: { light: '#6366F1', dark: '#818CF8' },
  band: { light: '#8B5CF6', dark: '#A78BFA' },
  attachment: { light: '#EC4899', dark: '#F472B6' },
  retainer: { light: '#14B8A6', dark: '#2DD4BF' },

  // Legacy (redirects)
  filling: { light: '#3B82F6', dark: '#60A5FA' },
  root_canal: { light: '#8B5CF6', dark: '#A78BFA' },
  bridge_pontic: { light: '#F97316', dark: '#FB923C' },

  // Position actions
  rotate: { light: '#8B5CF6', dark: '#A78BFA' },
  displace: { light: '#F59E0B', dark: '#FBBF24' }
}

/**
 * Get treatment color for current mode
 */
export function getTreatmentColor(treatmentType: string, darkMode: boolean = false): string {
  const normalized = normalizeTreatmentType(treatmentType)
  const config = TREATMENT_COLORS[normalized] || { light: '#6B7280', dark: '#9CA3AF' }
  return darkMode ? config.dark : config.light
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
  existing: {
    fill: 'solid',
    opacity: 1.0,
    border: null,
    borderWidth: 0
  },
  planned: {
    fill: 'solid',
    opacity: 0.7,
    border: null,
    borderWidth: 0
  }
}

/**
 * Color for the "P" indicator on planned treatments
 */
export const PLANNED_INDICATOR_COLOR = '#EF4444'

// ============================================================================
// Tooth Categories
// ============================================================================

export type ToothCategory = 'incisor' | 'canine' | 'premolar' | 'molar'

/**
 * Check if a tooth is deciduous (baby tooth).
 * Deciduous teeth are in quadrants 5, 6, 7, 8.
 */
export function isDeciduousTooth(toothNumber: number): boolean {
  const quadrant = Math.floor(toothNumber / 10)
  return quadrant >= 5 && quadrant <= 8
}

/**
 * Get the category of a tooth based on its FDI number.
 * For deciduous teeth (quadrants 5-8), positions 4 and 5 are MOLARS (not premolars).
 */
export function getToothCategory(toothNumber: number): ToothCategory {
  const quadrant = Math.floor(toothNumber / 10)
  const num = toothNumber % 10

  // Deciduous teeth (quadrants 5, 6, 7, 8)
  if (quadrant >= 5 && quadrant <= 8) {
    if (num === 1 || num === 2) return 'incisor'
    if (num === 3) return 'canine'
    return 'molar' // 4,5 are deciduous MOLARS, not premolars
  }

  // Permanent teeth (quadrants 1, 2, 3, 4)
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

export type TreatmentClinicalCategory = 'diagnostico' | 'restauradora' | 'cirugia' | 'endodoncia' | 'ortodoncia'

/**
 * Categories that are diagnostic (existing conditions only, not treatments).
 * Used by TreatmentBar to filter categories based on mode.
 */
export const DIAGNOSTIC_CATEGORIES: TreatmentClinicalCategory[] = ['diagnostico']

/**
 * Categories that are therapeutic (actual treatments that can be planned).
 */
export const THERAPEUTIC_CATEGORIES: TreatmentClinicalCategory[] = ['restauradora', 'cirugia', 'endodoncia', 'ortodoncia']

export const TREATMENT_CATEGORIES: Array<{
  key: TreatmentClinicalCategory
  labelKey: string
  treatments: string[]
}> = [
  {
    key: 'diagnostico',
    labelKey: 'odontogram.treatments.categories.diagnostico',
    treatments: [
      'pulpitis',
      'caries',
      'incipient_caries',
      'pigmentation',
      'fracture',
      'missing',
      'periapical_small',
      'periapical_medium',
      'periapical_large',
      'rotated',
      'displaced',
      'unerupted'
    ]
  },
  {
    key: 'restauradora',
    labelKey: 'odontogram.treatments.categories.restauradora',
    treatments: [
      'filling_composite',
      'filling_amalgam',
      'filling_temporary',
      'sealant',
      'veneer',
      'inlay',
      'overlay',
      'crown'
      // pontic, bridge_abutment and splint are exposed via the Multi-tooth section
      // of the TreatmentBar, not as standalone buttons. They are only valid inside
      // a treatment group.
    ]
  },
  {
    key: 'cirugia',
    labelKey: 'odontogram.treatments.categories.cirugia',
    treatments: [
      'extraction',
      'implant',
      'apicoectomy'
    ]
  },
  {
    key: 'endodoncia',
    labelKey: 'odontogram.treatments.categories.endodoncia',
    treatments: [
      'root_canal_full',
      'root_canal_two_thirds',
      'root_canal_half',
      'post',
      'root_canal_overfill'
    ]
  },
  {
    key: 'ortodoncia',
    labelKey: 'odontogram.treatments.categories.ortodoncia',
    treatments: [
      'bracket',
      'tube',
      'band',
      'attachment',
      'retainer'
    ]
  }
]

// ============================================================================
// Tooth Name i18n Keys
// ============================================================================

/**
 * Get the i18n key for a tooth name based on its number.
 * Returns the key to use with t() function.
 * Handles both permanent and deciduous teeth naming.
 */
export function getToothNameKey(toothNumber: number): string {
  const num = toothNumber % 10

  // Deciduous teeth have different naming (no premolars)
  if (isDeciduousTooth(toothNumber)) {
    const deciduousKeys: Record<number, string> = {
      1: 'centralIncisor',
      2: 'lateralIncisor',
      3: 'canine',
      4: 'firstMolar', // Deciduous first molar (not premolar)
      5: 'secondMolar' // Deciduous second molar (not premolar)
    }
    return `odontogram.toothNames.${deciduousKeys[num] || 'unknown'}`
  }

  // Permanent teeth naming
  const permanentKeys: Record<number, string> = {
    1: 'centralIncisor',
    2: 'lateralIncisor',
    3: 'canine',
    4: 'firstPremolar',
    5: 'secondPremolar',
    6: 'firstMolar',
    7: 'secondMolar',
    8: 'thirdMolar'
  }
  return `odontogram.toothNames.${permanentKeys[num] || 'unknown'}`
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
 * Diagnostic category only allows "existing" status (current conditions, not planned).
 */
export const CATEGORY_STATUS_RESTRICTIONS: Record<TreatmentClinicalCategory, TreatmentStatus[]> = {
  diagnostico: ['existing'], // Diagnoses are always existing conditions
  restauradora: ['existing', 'planned'],
  cirugia: ['existing', 'planned'],
  endodoncia: ['existing', 'planned'],
  ortodoncia: ['existing', 'planned']
}

/**
 * Get the category key for a treatment type.
 */
export function getCategoryForTreatment(treatmentType: string): TreatmentClinicalCategory | null {
  const normalized = normalizeTreatmentType(treatmentType)
  for (const category of TREATMENT_CATEGORIES) {
    if (category.treatments.includes(normalized)) {
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
  return ['existing', 'planned']
}

// ============================================================================
// Multi-tooth Treatment Groups (bridges, splints, multiple veneers/crowns)
// ============================================================================

/**
 * Registry of treatments that require selecting more than one tooth at a time.
 * Each entry drives the selection UX (range vs free) and the backend payload.
 */
export const MULTI_TOOTH_TREATMENTS: Record<string, MultiToothTreatmentConfig> = {
  bridge: {
    key: 'bridge',
    labelKey: 'odontogram.multiTooth.bridge.label',
    mode: 'bridge',
    selectionMode: 'range',
    minTeeth: 2,
    maxTeeth: 14,
    requiresSameArch: true,
    category: 'restauradora'
  },
  splint: {
    key: 'splint',
    labelKey: 'odontogram.multiTooth.splint.label',
    mode: 'uniform',
    selectionMode: 'free',
    minTeeth: 2,
    maxTeeth: 14,
    requiresSameArch: true,
    category: 'restauradora'
  },
  multiple_veneers: {
    key: 'veneer',
    labelKey: 'odontogram.multiTooth.veneers.label',
    mode: 'uniform',
    selectionMode: 'free',
    minTeeth: 2,
    maxTeeth: 10,
    requiresSameArch: false,
    category: 'restauradora'
  },
  multiple_crowns: {
    key: 'crown',
    labelKey: 'odontogram.multiTooth.crowns.label',
    mode: 'uniform',
    selectionMode: 'free',
    minTeeth: 2,
    maxTeeth: 28,
    requiresSameArch: false,
    category: 'restauradora'
  }
}

export function getMultiToothConfig(key: string): MultiToothTreatmentConfig | null {
  return MULTI_TOOTH_TREATMENTS[key] ?? null
}

export function isMultiToothTreatment(key: string): boolean {
  return key in MULTI_TOOTH_TREATMENTS
}

/**
 * Treatment types that exist only as inner members of a multi-tooth group and never
 * as a standalone clinical act (a "pontic" alone makes no sense — it's only valid
 * inside a bridge). The TreatmentBar hides these even if the catalog exposes them.
 *
 * Note: `bridge` and `splint` are NOT here — they are atomic multi-tooth types and
 * the TreatmentBar renders them as clickable catalog buttons that enter multi-tooth
 * selection mode immediately.
 */
export const MULTI_TOOTH_ONLY_TYPES: ReadonlySet<string> = new Set([
  'pontic',
  'bridge_abutment'
])

/**
 * Atomic multi-tooth types: a single Treatment of this type spans ≥2 teeth and
 * cannot exist on a single tooth. Clicking a catalog button of this type enters
 * multi-tooth selection mode immediately (no single/multi toggle).
 */
export const ATOMIC_MULTI_TOOTH_TYPES: ReadonlySet<string> = new Set([
  'bridge',
  'splint'
])

/**
 * Types that support BOTH single-tooth and multi-tooth uniform application. A user
 * picks the catalog variant first, then a dropdown lets them choose how many teeth
 * to apply it to. Maps the single-tooth type to the corresponding wrapper key in
 * MULTI_TOOTH_TREATMENTS.
 */
export const MULTI_TOOTH_WRAPPER_BY_TYPE: Readonly<Record<string, string>> = {
  crown: 'multiple_crowns',
  veneer: 'multiple_veneers'
}

export function supportsBothModes(odontogramType: string): boolean {
  return odontogramType in MULTI_TOOTH_WRAPPER_BY_TYPE
}

export function isMultiToothOnlyType(treatmentType: string): boolean {
  return MULTI_TOOTH_ONLY_TYPES.has(treatmentType)
}

/**
 * Ordered FDI tooth sequences per arch, left-to-right across the midline.
 * Used to compute contiguous ranges for bridge selection and arch membership.
 */
export const UPPER_ARCH_ORDER: number[] = [18, 17, 16, 15, 14, 13, 12, 11, 21, 22, 23, 24, 25, 26, 27, 28]
export const LOWER_ARCH_ORDER: number[] = [48, 47, 46, 45, 44, 43, 42, 41, 31, 32, 33, 34, 35, 36, 37, 38]

export function getArchOrder(toothNumber: number): number[] | null {
  if (UPPER_ARCH_ORDER.includes(toothNumber)) return UPPER_ARCH_ORDER
  if (LOWER_ARCH_ORDER.includes(toothNumber)) return LOWER_ARCH_ORDER
  return null
}

/**
 * Return contiguous teeth between `start` and `end` (inclusive) along the same arch.
 * Order is irrelevant: calculateToothRange(16, 14) === calculateToothRange(14, 16).
 * Throws 'same_arch_required' if the two teeth are not in the same permanent arch.
 */
export function calculateToothRange(start: number, end: number): number[] {
  const arch = getArchOrder(start)
  if (!arch || !arch.includes(end)) {
    throw new Error('same_arch_required')
  }
  const i = arch.indexOf(start)
  const j = arch.indexOf(end)
  const [a, b] = i <= j ? [i, j] : [j, i]
  return arch.slice(a, b + 1)
}

export function isSameArch(teeth: number[]): boolean {
  if (teeth.length <= 1) return true
  const first = getArchOrder(teeth[0]!)
  if (!first) return false
  return teeth.every(t => getArchOrder(t) === first)
}
