/**
 * SVG paths for tooth visualization - clean line art style.
 * Inspired by professional dental charts with green outline and white fill.
 */

import type { TreatmentType } from '~/types'
import {
  TREATMENT_COLORS,
  STATUS_STYLES,
  SURFACE_TREATMENTS,
  WHOLE_TOOTH_TREATMENTS,
  getToothCategory as getCategory,
  isUpperTooth as checkIsUpperTooth,
  type TreatmentStatus
} from '~/config/odontogramConstants'

// Re-export from central config for backwards compatibility
export { TREATMENT_COLORS, STATUS_STYLES }

// ============================================================================
// Colors - Sage green theme matching reference
// ============================================================================

export const TOOTH_COLORS = {
  outline: '#5D8E58', // Sage green outline
  outlineLight: '#7BA876', // Lighter green for internal details
  fill: '#FFFFFF', // White fill
  fillShade: '#F0F7EF', // Very light green tint for shading
  root: '#FEFEFE', // Slightly off-white for roots
  rootOutline: '#5D8E58' // Same green for root outline
}

// ============================================================================
// Gradient Definitions
// ============================================================================

export const GRADIENT_DEFINITIONS = `
  <!-- Simple enamel gradient -->
  <linearGradient id="enamel-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
    <stop offset="0%" style="stop-color:#FFFFFF"/>
    <stop offset="100%" style="stop-color:#F5FAF5"/>
  </linearGradient>

  <linearGradient id="enamel-gradient-hover" x1="0%" y1="0%" x2="100%" y2="100%">
    <stop offset="0%" style="stop-color:#FFFFFF"/>
    <stop offset="100%" style="stop-color:#E8F5E9"/>
  </linearGradient>

  <!-- Root gradient - subtle cream -->
  <linearGradient id="root-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
    <stop offset="0%" style="stop-color:#FFFFFF"/>
    <stop offset="100%" style="stop-color:#FAFAFA"/>
  </linearGradient>

  <!-- Crown treatment gradient (metallic gold) -->
  <linearGradient id="crown-gold" x1="0%" y1="0%" x2="100%" y2="100%">
    <stop offset="0%" style="stop-color:#FCD34D"/>
    <stop offset="30%" style="stop-color:#FBBF24"/>
    <stop offset="70%" style="stop-color:#D97706"/>
    <stop offset="100%" style="stop-color:#B45309"/>
  </linearGradient>

  <!-- Implant metallic gradient -->
  <linearGradient id="implant-metal" x1="0%" y1="0%" x2="100%" y2="0%">
    <stop offset="0%" style="stop-color:#9CA3AF"/>
    <stop offset="30%" style="stop-color:#E5E7EB"/>
    <stop offset="50%" style="stop-color:#F3F4F6"/>
    <stop offset="70%" style="stop-color:#E5E7EB"/>
    <stop offset="100%" style="stop-color:#9CA3AF"/>
  </linearGradient>

  <!-- Gum gradient -->
  <linearGradient id="gum-gradient" x1="0%" y1="0%" x2="0%" y2="100%">
    <stop offset="0%" style="stop-color:#FDA4AF"/>
    <stop offset="100%" style="stop-color:#FB7185"/>
  </linearGradient>

  <!-- Selection glow filter -->
  <filter id="selection-glow" x="-50%" y="-50%" width="200%" height="200%">
    <feGaussianBlur stdDeviation="2" result="blur"/>
    <feFlood flood-color="#3B82F6" flood-opacity="0.4"/>
    <feComposite in2="blur" operator="in"/>
    <feMerge>
      <feMergeNode/>
      <feMergeNode in="SourceGraphic"/>
    </feMerge>
  </filter>
`

// ============================================================================
// Helper Functions
// ============================================================================

// Re-export helper functions from central config
export function getToothCategory(toothNumber: number): 'incisor' | 'canine' | 'premolar' | 'molar' {
  return getCategory(toothNumber)
}

export function isUpperTooth(toothNumber: number): boolean {
  return checkIsUpperTooth(toothNumber)
}

// NOTE: getToothName was removed - use getToothNameKey and getToothPositionKeys from
// ~/config/odontogramConstants with i18n's t() function for localized tooth names

// Surface and whole-tooth treatment types are now imported from central config
// Access via: SURFACE_TREATMENTS and WHOLE_TOOTH_TREATMENTS from ~/config/odontogramConstants
export const SURFACE_TREATMENT_TYPES: readonly string[] = SURFACE_TREATMENTS
export const WHOLE_TOOTH_TREATMENT_TYPES: readonly string[] = WHOLE_TOOTH_TREATMENTS

// ============================================================================
// Occlusal View Paths (top-down, 50x50 viewBox)
// Clean line art style with characteristic shapes
// ============================================================================

export const OCCLUSAL_PATHS = {
  // Incisor - rounded rectangle with incisal edge detail
  incisor: {
    outline: 'M 10,8 Q 10,5 25,5 Q 40,5 40,8 L 40,42 Q 40,45 25,45 Q 10,45 10,42 Z',
    innerDetail: 'M 14,12 Q 14,10 25,10 Q 36,10 36,12 L 36,38 Q 36,40 25,40 Q 14,40 14,38 Z',
    surfaces: {
      M: 'M 10,8 Q 10,5 18,5 L 18,45 Q 10,45 10,42 Z',
      D: 'M 40,8 Q 40,5 32,5 L 32,45 Q 40,45 40,42 Z',
      V: 'M 10,8 Q 10,5 25,5 Q 40,5 40,8 L 40,20 L 10,20 Z',
      L: 'M 10,42 Q 10,45 25,45 Q 40,45 40,42 L 40,30 L 10,30 Z',
      O: 'M 18,20 L 32,20 L 32,30 L 18,30 Z'
    }
  },

  // Canine - pointed/shield shape
  canine: {
    outline: 'M 25,3 Q 42,8 42,25 Q 42,42 25,47 Q 8,42 8,25 Q 8,8 25,3 Z',
    innerDetail: 'M 25,8 Q 36,12 36,25 Q 36,38 25,42 Q 14,38 14,25 Q 14,12 25,8 Z',
    surfaces: {
      M: 'M 8,25 Q 8,8 18,6 L 18,44 Q 8,42 8,25 Z',
      D: 'M 42,25 Q 42,8 32,6 L 32,44 Q 42,42 42,25 Z',
      V: 'M 25,3 Q 42,8 42,25 L 25,25 L 8,25 Q 8,8 25,3 Z',
      L: 'M 25,47 Q 42,42 42,25 L 25,25 L 8,25 Q 8,42 25,47 Z',
      O: 'M 18,18 L 32,18 L 32,32 L 18,32 Z'
    }
  },

  // Premolar - rounded square with X-pattern detail
  premolar: {
    outline: 'M 8,8 Q 8,4 25,4 Q 42,4 42,8 L 42,42 Q 42,46 25,46 Q 8,46 8,42 Z',
    innerDetail: 'M 12,12 L 38,12 L 38,38 L 12,38 Z M 25,12 L 25,38 M 12,25 L 38,25',
    crossPattern: 'M 18,18 L 32,18 L 32,32 L 18,32 Z M 25,4 L 25,18 M 25,32 L 25,46 M 4,25 L 18,25 M 32,25 L 46,25',
    surfaces: {
      M: 'M 8,8 Q 8,4 16,4 L 16,46 Q 8,46 8,42 Z',
      D: 'M 42,8 Q 42,4 34,4 L 34,46 Q 42,46 42,42 Z',
      V: 'M 8,8 Q 8,4 25,4 Q 42,4 42,8 L 42,20 L 8,20 Z',
      L: 'M 8,42 Q 8,46 25,46 Q 42,46 42,42 L 42,30 L 8,30 Z',
      O: 'M 16,20 L 34,20 L 34,30 L 16,30 Z'
    }
  },

  // Molar - large rounded square with cross-fissure pattern
  molar: {
    outline: 'M 6,6 Q 6,2 25,2 Q 44,2 44,6 L 44,44 Q 44,48 25,48 Q 6,48 6,44 Z',
    innerDetail: 'M 14,14 L 36,14 L 36,36 L 14,36 Z',
    crossPattern: 'M 25,2 L 25,14 M 25,36 L 25,48 M 6,25 L 14,25 M 36,25 L 44,25 M 14,14 Q 25,18 36,14 M 14,36 Q 25,32 36,36',
    surfaces: {
      M: 'M 6,6 Q 6,2 14,2 L 14,48 Q 6,48 6,44 Z',
      D: 'M 44,6 Q 44,2 36,2 L 36,48 Q 44,48 44,44 Z',
      V: 'M 6,6 Q 6,2 25,2 Q 44,2 44,6 L 44,18 L 6,18 Z',
      L: 'M 6,44 Q 6,48 25,48 Q 44,48 44,44 L 44,32 L 6,32 Z',
      O: 'M 14,18 L 36,18 L 36,32 L 14,32 Z'
    }
  },

  // Fallback
  generic: {
    outline: 'M 8,8 Q 8,4 25,4 Q 42,4 42,8 L 42,42 Q 42,46 25,46 Q 8,46 8,42 Z',
    innerDetail: 'M 14,14 L 36,14 L 36,36 L 14,36 Z',
    surfaces: {
      M: 'M 8,8 L 18,18 L 18,32 L 8,42 Z',
      D: 'M 42,8 L 32,18 L 32,32 L 42,42 Z',
      V: 'M 8,8 Q 8,4 25,4 Q 42,4 42,8 L 32,18 L 18,18 Z',
      L: 'M 8,42 L 18,32 L 32,32 L 42,42 Q 42,46 25,46 Q 8,46 8,42 Z',
      O: 'M 18,18 L 32,18 L 32,32 L 18,32 Z'
    }
  }
}

// ============================================================================
// Lateral View Paths (side view with roots, 50x80 viewBox)
// Clean line art style showing crown and root anatomy
// ============================================================================

export const LATERAL_PATHS = {
  // Incisor - shovel-shaped crown, single tapered root
  incisor: {
    crown: 'M 15,28 C 12,25 10,18 12,10 Q 15,4 25,4 Q 35,4 38,10 C 40,18 38,25 35,28 Z',
    crownInner: 'M 18,26 C 16,23 14,17 16,11 Q 18,6 25,6 Q 32,6 34,11 C 36,17 34,23 32,26 Z',
    crownShading: 'M 20,24 Q 25,20 30,24 L 30,12 Q 25,8 20,12 Z',
    root: 'M 20,28 Q 19,40 20,55 Q 21,68 25,72 Q 29,68 30,55 Q 31,40 30,28 Z',
    rootInner: 'M 22,30 Q 22,45 23,58 Q 24,66 25,68 Q 26,66 27,58 Q 28,45 28,30 Z',
    gumLine: 'M 5,28 Q 25,31 45,28'
  },

  // Canine - pointed crown, long single root
  canine: {
    crown: 'M 14,30 C 10,26 8,18 10,10 Q 14,2 25,2 Q 36,2 40,10 C 42,18 40,26 36,30 Z',
    crownInner: 'M 17,28 C 14,24 12,17 14,11 Q 17,4 25,4 Q 33,4 36,11 C 38,17 36,24 33,28 Z',
    crownShading: 'M 20,26 L 25,8 L 30,26 Z',
    root: 'M 19,30 Q 17,45 18,62 Q 19,75 25,78 Q 31,75 32,62 Q 33,45 31,30 Z',
    rootInner: 'M 21,32 Q 20,48 21,63 Q 22,73 25,75 Q 28,73 29,63 Q 30,48 29,32 Z',
    gumLine: 'M 5,30 Q 25,33 45,30'
  },

  // Premolar - bicuspid crown, 1-2 roots
  premolar: {
    crown: 'M 12,28 C 8,24 6,16 8,8 Q 12,2 25,2 Q 38,2 42,8 C 44,16 42,24 38,28 Z',
    crownInner: 'M 15,26 C 12,22 10,15 12,9 Q 15,4 25,4 Q 35,4 38,9 C 40,15 38,22 35,26 Z',
    crownCusps: 'M 18,8 Q 21,4 25,8 Q 29,4 32,8 L 32,20 Q 25,24 18,20 Z',
    roots: [
      'M 17,28 Q 14,42 15,56 Q 16,66 20,70 Q 24,66 24,56 Q 24,42 22,28 Z',
      'M 28,28 Q 26,42 26,56 Q 26,66 30,70 Q 34,66 35,56 Q 36,42 33,28 Z'
    ],
    rootsInner: [
      'M 18,30 Q 16,44 17,56 Q 18,64 20,66 Q 22,64 22,56 Q 22,44 21,30 Z',
      'M 29,30 Q 28,44 28,56 Q 28,64 30,66 Q 32,64 33,56 Q 34,44 32,30 Z'
    ],
    gumLine: 'M 5,28 Q 25,31 45,28'
  },

  // Molar Upper - wide crown, 3 roots
  molarUpper: {
    crown: 'M 8,26 C 4,22 3,14 5,6 Q 10,0 25,0 Q 40,0 45,6 C 47,14 46,22 42,26 Z',
    crownInner: 'M 11,24 C 8,20 7,13 9,7 Q 13,2 25,2 Q 37,2 41,7 C 43,13 42,20 39,24 Z',
    crownCusps: 'M 14,6 Q 18,2 22,6 L 22,18 L 14,18 Z M 28,6 Q 32,2 36,6 L 36,18 L 28,18 Z',
    roots: [
      'M 10,26 Q 6,40 7,54 Q 8,66 14,72 Q 18,66 18,54 Q 18,40 15,26 Z',
      'M 35,26 Q 32,40 32,54 Q 32,66 36,72 Q 42,66 43,54 Q 44,40 40,26 Z',
      'M 22,26 Q 22,38 23,48 Q 24,56 25,58 Q 26,56 27,48 Q 28,38 28,26 Z'
    ],
    rootsInner: [
      'M 11,28 Q 8,42 9,54 Q 10,64 14,68 Q 17,64 17,54 Q 17,42 14,28 Z',
      'M 36,28 Q 34,42 34,54 Q 34,64 36,68 Q 40,64 41,54 Q 42,42 39,28 Z',
      'M 23,28 Q 23,40 24,50 Q 24,54 25,55 Q 26,54 26,50 Q 27,40 27,28 Z'
    ],
    gumLine: 'M 2,26 Q 25,30 48,26'
  },

  // Molar Lower - wide crown, 2 roots
  molarLower: {
    crown: 'M 8,26 C 4,22 3,14 5,6 Q 10,0 25,0 Q 40,0 45,6 C 47,14 46,22 42,26 Z',
    crownInner: 'M 11,24 C 8,20 7,13 9,7 Q 13,2 25,2 Q 37,2 41,7 C 43,13 42,20 39,24 Z',
    crownCusps: 'M 12,6 Q 17,2 22,6 L 22,18 L 12,18 Z M 28,6 Q 33,2 38,6 L 38,18 L 28,18 Z',
    roots: [
      'M 10,26 Q 6,42 8,58 Q 10,72 17,78 Q 22,72 22,58 Q 22,42 18,26 Z',
      'M 32,26 Q 28,42 28,58 Q 28,72 33,78 Q 40,72 42,58 Q 44,42 40,26 Z'
    ],
    rootsInner: [
      'M 12,28 Q 8,44 10,58 Q 12,70 17,74 Q 21,70 21,58 Q 21,44 17,28 Z',
      'M 33,28 Q 30,44 30,58 Q 30,70 33,74 Q 38,70 40,58 Q 42,44 38,28 Z'
    ],
    gumLine: 'M 2,26 Q 25,30 48,26'
  }
}

// ============================================================================
// Treatment Overlay Paths
// ============================================================================

export const TREATMENT_OVERLAYS = {
  implant: {
    fixture: 'M 18,35 L 17,70 Q 25,76 33,70 L 32,35 Z',
    threads: [
      'M 15,42 L 35,42',
      'M 14,50 L 36,50',
      'M 13,58 L 37,58',
      'M 14,66 L 36,66'
    ],
    abutment: 'M 20,28 L 20,35 L 30,35 L 30,28 C 30,25 20,25 20,28 Z',
    head: 'M 18,22 Q 25,18 32,22 L 32,28 C 32,30 18,30 18,28 Z'
  },

  crownOverlay: {
    outer: 'M 6,28 C 2,22 2,12 6,5 C 12,0 20,-1 25,0 C 30,-1 38,0 44,5 C 48,12 48,22 44,28 Z',
    metalBand: 'M 8,28 Q 25,32 42,28 L 44,20 Q 25,16 6,20 Z'
  },

  rootCanal: {
    indicator: 'M 25,45 m -4,0 a 4,4 0 1,0 8,0 a 4,4 0 1,0 -8,0',
    canalLines: [
      'M 25,35 L 25,55',
      'M 22,40 L 28,40',
      'M 22,50 L 28,50'
    ]
  },

  post: {
    shaft: 'M 22,22 L 22,55 L 28,55 L 28,22 Z',
    head: 'M 18,18 L 18,22 L 32,22 L 32,18 Q 25,12 18,18 Z',
    core: 'M 16,8 Q 25,4 34,8 L 34,18 Q 25,22 16,18 Z'
  },

  missing: {
    line1: 'M 8,8 L 42,42',
    line2: 'M 42,8 L 8,42'
  },

  extractionIndicated: {
    line1: 'M 10,10 L 40,40',
    line2: 'M 40,10 L 10,40',
    dashArray: '4,3'
  },

  veneer: {
    surface: 'M 8,5 Q 25,0 42,5 L 44,32 Q 25,36 6,32 Z'
  },

  bridgePontic: {
    connectorLeft: 'M 0,10 L 8,10 L 8,15 L 0,15',
    connectorRight: 'M 50,10 L 42,10 L 42,15 L 50,15',
    bar: 'M 0,12 L 50,12'
  },

  bridgeAbutment: {
    markerLeft: 'M 0,18 L 10,25 L 0,32 Z',
    markerRight: 'M 50,18 L 40,25 L 50,32 Z'
  }
}

// ============================================================================
// Pattern Definitions
// ============================================================================

export const PATTERN_DEFINITIONS = `
  <defs>
    ${GRADIENT_DEFINITIONS}

    <!-- Planned treatment pattern (diagonal stripes - RED) -->
    <pattern id="pattern-planned" patternUnits="userSpaceOnUse" width="6" height="6" patternTransform="rotate(45)">
      <line x1="0" y1="0" x2="0" y2="6" stroke="#EF4444" stroke-width="2" />
    </pattern>

    <!-- Planned treatment patterns by color -->
    <pattern id="pattern-planned-amber" patternUnits="userSpaceOnUse" width="6" height="6" patternTransform="rotate(45)">
      <line x1="0" y1="0" x2="0" y2="6" stroke="#F59E0B" stroke-width="2" />
    </pattern>
    <pattern id="pattern-planned-blue" patternUnits="userSpaceOnUse" width="6" height="6" patternTransform="rotate(45)">
      <line x1="0" y1="0" x2="0" y2="6" stroke="#3B82F6" stroke-width="2" />
    </pattern>
    <pattern id="pattern-planned-green" patternUnits="userSpaceOnUse" width="6" height="6" patternTransform="rotate(45)">
      <line x1="0" y1="0" x2="0" y2="6" stroke="#22C55E" stroke-width="2" />
    </pattern>

    <!-- Filling texture pattern (green dots) -->
    <pattern id="filling-pattern" patternUnits="userSpaceOnUse" width="3" height="3">
      <rect width="3" height="3" fill="#22C55E"/>
      <circle cx="1.5" cy="1.5" r="0.5" fill="#16A34A"/>
    </pattern>
  </defs>
`

// ============================================================================
// Helper Functions
// ============================================================================

export function getOcclusalPath(toothNumber: number) {
  const category = getToothCategory(toothNumber)
  return OCCLUSAL_PATHS[category] || OCCLUSAL_PATHS.generic
}

export function getLateralPath(toothNumber: number) {
  const category = getToothCategory(toothNumber)
  const isUpper = isUpperTooth(toothNumber)

  if (category === 'molar') {
    return isUpper ? LATERAL_PATHS.molarUpper : LATERAL_PATHS.molarLower
  }

  return LATERAL_PATHS[category] || LATERAL_PATHS.incisor
}

export function getTreatmentFill(
  treatmentType: TreatmentType,
  status: TreatmentStatus
): { fill: string, opacity: number, stroke: string, strokeWidth: number } {
  const baseColor = TREATMENT_COLORS[treatmentType] || '#9CA3AF'
  const statusStyle = STATUS_STYLES[status]

  if (status === 'planned') {
    return {
      fill: `url(#pattern-planned)`,
      opacity: statusStyle.opacity,
      stroke: statusStyle.border,
      strokeWidth: statusStyle.borderWidth
    }
  }

  return {
    fill: baseColor,
    opacity: statusStyle.opacity,
    stroke: statusStyle.border,
    strokeWidth: statusStyle.borderWidth
  }
}

export function usesCrownGradient(treatmentType: TreatmentType): boolean {
  return treatmentType === 'crown'
}

export function replacesTooth(treatmentType: TreatmentType): boolean {
  return treatmentType === 'implant' || treatmentType === 'missing' || treatmentType === 'extraction'
}

export function makesToothTransparent(treatmentType: TreatmentType): boolean {
  return treatmentType === 'extraction' || treatmentType === 'missing'
}
