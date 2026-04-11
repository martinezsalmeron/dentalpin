/**
 * LateralViewIcons.ts - SVG icon paths for Rule 3 lateral view treatments
 *
 * These icons are positioned at anchor points on the lateral tooth view.
 * Each icon is designed to be rendered at a specific position (crownCenter, apex, etc.)
 *
 * NOTE: ImplantSVG.vue handles implant rendering separately and should NOT be modified.
 */

export interface LateralIconConfig {
  path: string
  width: number
  height: number
  anchorPosition: 'crownCenter' | 'apex' | 'beyondApex' | 'aboveCrown' | 'besideCrown' | 'rootCenter'
  offsetX?: number
  offsetY?: number
  strokeWidth?: number
  fillOpacity?: number
}

/**
 * SVG icons for Rule 3 treatments on lateral view
 * Each icon is centered at (0,0) and scaled to fit within the specified width/height
 */
export const LATERAL_ICONS: Record<string, LateralIconConfig> = {
  // Fracture - Zigzag crack on crown
  fracture: {
    path: 'M -3,-8 L 0,-4 L -2,0 L 1,4 L -1,8',
    width: 8,
    height: 18,
    anchorPosition: 'crownCenter',
    strokeWidth: 1.5,
    fillOpacity: 0
  },

  // Missing - Black X with reduced opacity
  missing: {
    path: 'M -10,-10 L 10,10 M 10,-10 L -10,10',
    width: 24,
    height: 24,
    anchorPosition: 'crownCenter',
    strokeWidth: 3,
    fillOpacity: 0
  },

  // Periapical lesion small (<2mm)
  periapical_small: {
    path: 'M 0,-3 A 3,3 0 1,1 0,3 A 3,3 0 1,1 0,-3',
    width: 8,
    height: 8,
    anchorPosition: 'apex',
    offsetY: -2,
    fillOpacity: 0.7
  },

  // Periapical lesion medium (2-4mm)
  periapical_medium: {
    path: 'M 0,-5 A 5,5 0 1,1 0,5 A 5,5 0 1,1 0,-5',
    width: 12,
    height: 12,
    anchorPosition: 'apex',
    offsetY: -3,
    fillOpacity: 0.7
  },

  // Periapical lesion large (>4mm)
  periapical_large: {
    path: 'M 0,-8 A 8,8 0 1,1 0,8 A 8,8 0 1,1 0,-8',
    width: 18,
    height: 18,
    anchorPosition: 'apex',
    offsetY: -5,
    fillOpacity: 0.7
  },

  // Rotated - Circular arrow at crown center
  rotated: {
    path: 'M 0,-10 A 10,10 0 1,1 -10,0 M -10,0 L -12,-7 M -10,0 L -3,-2',
    width: 24,
    height: 24,
    anchorPosition: 'crownCenter',
    strokeWidth: 2.5,
    fillOpacity: 0
  },

  // Displaced - Horizontal arrow beside crown
  displaced: {
    path: 'M -16,0 L 16,0 M 10,-6 L 16,0 L 10,6',
    width: 36,
    height: 14,
    anchorPosition: 'besideCrown',
    strokeWidth: 3,
    fillOpacity: 0
  },

  // Apicoectomy - Horizontal line at apex
  apicoectomy: {
    path: 'M -8,0 L 8,0',
    width: 18,
    height: 4,
    anchorPosition: 'apex',
    offsetY: 2,
    strokeWidth: 2,
    fillOpacity: 0
  },

  // Extraction - Red X with reduced opacity
  extraction: {
    path: 'M -10,-10 L 10,10 M 10,-10 L -10,10',
    width: 24,
    height: 24,
    anchorPosition: 'crownCenter',
    strokeWidth: 2.5,
    fillOpacity: 0
  },

  // Post - Cylindrical post in root
  post: {
    path: 'M -2,-15 L -2,10 A 2,2 0 0,0 2,10 L 2,-15 A 2,1 0 0,0 -2,-15',
    width: 6,
    height: 28,
    anchorPosition: 'rootCenter',
    fillOpacity: 1
  },

  // Root canal overfill - Blue line beyond apex
  root_canal_overfill: {
    path: 'M 0,0 L 0,15',
    width: 4,
    height: 18,
    anchorPosition: 'beyondApex',
    strokeWidth: 2,
    fillOpacity: 0
  },

  // Bracket - Small square on crown
  bracket: {
    path: 'M -4,-4 L 4,-4 L 4,4 L -4,4 Z M -6,0 L -4,0 M 4,0 L 6,0',
    width: 14,
    height: 10,
    anchorPosition: 'crownCenter',
    strokeWidth: 1,
    fillOpacity: 0.8
  },

  // Tube - Rectangle with hole on crown
  tube: {
    path: 'M -5,-3 L 5,-3 L 5,3 L -5,3 Z M -3,0 A 1.5,1.5 0 1,1 3,0 A 1.5,1.5 0 1,1 -3,0',
    width: 12,
    height: 8,
    anchorPosition: 'crownCenter',
    strokeWidth: 1,
    fillOpacity: 0.8
  },

  // Band - Two parallel lines wrapping crown
  band: {
    path: 'M -8,-2 L 8,-2 M -8,2 L 8,2',
    width: 18,
    height: 6,
    anchorPosition: 'crownCenter',
    strokeWidth: 1.5,
    fillOpacity: 0
  },

  // Attachment - Solid oval on crown surface
  attachment: {
    path: 'M 0,-3 A 4,3 0 1,1 0,3 A 4,3 0 1,1 0,-3',
    width: 10,
    height: 8,
    anchorPosition: 'crownCenter',
    fillOpacity: 1
  },

  // Retainer - Wavy wire across crown
  retainer: {
    path: 'M -10,0 Q -7,-3 -4,0 Q -1,3 2,0 Q 5,-3 8,0 Q 10,2 10,0',
    width: 22,
    height: 8,
    anchorPosition: 'crownCenter',
    strokeWidth: 1.5,
    fillOpacity: 0
  }
}

/**
 * Get icon configuration for a treatment type
 */
export function getLateralIcon(treatmentType: string): LateralIconConfig | null {
  return LATERAL_ICONS[treatmentType] || null
}

/**
 * Check if a treatment type has a lateral view icon
 */
export function hasLateralIcon(treatmentType: string): boolean {
  return treatmentType in LATERAL_ICONS
}

/**
 * Get all treatment types that use lateral icons
 */
export function getLateralIconTreatments(): string[] {
  return Object.keys(LATERAL_ICONS)
}
