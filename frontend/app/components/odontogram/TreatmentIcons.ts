/**
 * SVG icons for treatment types
 * Each icon is designed to fit in a 24x24 viewBox
 */

import {
  SURFACE_TREATMENTS,
  TREATMENT_CATEGORIES,
  isSurfaceTreatment as checkIsSurfaceTreatment
} from '~/config/odontogramConstants'

// Re-export from central config
export { SURFACE_TREATMENTS, TREATMENT_CATEGORIES }

export const TREATMENT_ICONS: Record<string, string> = {
  // ============================================================================
  // DIAGNÓSTICO
  // ============================================================================

  // Pulpitis - tooth with red/inflamed pulp
  pulpitis: `
    <path d="M8 2C8 1 10 0 12 0C14 0 16 1 16 2V10C16 12 14 14 12 14C10 14 8 12 8 10V2Z" fill="none" stroke="currentColor" stroke-width="1.5"/>
    <path d="M10 14V20" stroke="currentColor" stroke-width="1.5"/>
    <path d="M14 14V20" stroke="currentColor" stroke-width="1.5"/>
    <path d="M11 4C11 4 10 6 10 8C10 10 12 11 12 11C12 11 14 10 14 8C14 6 13 4 13 4" fill="currentColor" fill-opacity="0.6"/>
    <circle cx="12" cy="7" r="2" fill="currentColor"/>
  `,

  // Caries - tooth with decay
  caries: `
    <path d="M7 2C7 1 9 0 12 0C15 0 17 1 17 2V10C17 12 15 14 12 14C9 14 7 12 7 10V2Z" fill="none" stroke="currentColor" stroke-width="1.5"/>
    <circle cx="11" cy="5" r="2" fill="currentColor"/>
    <circle cx="13" cy="7" r="1.5" fill="currentColor"/>
    <path d="M10 16V21" stroke="currentColor" stroke-width="1.5"/>
    <path d="M14 16V21" stroke="currentColor" stroke-width="1.5"/>
  `,

  // Incipient caries - small dot indicator
  incipient_caries: `
    <path d="M8 2C8 1 10 0 12 0C14 0 16 1 16 2V10C16 12 14 14 12 14C10 14 8 12 8 10V2Z" fill="none" stroke="currentColor" stroke-width="1.5"/>
    <circle cx="12" cy="5" r="2.5" fill="currentColor" fill-opacity="0.5"/>
    <circle cx="12" cy="5" r="1" fill="currentColor"/>
    <path d="M10 16V21" stroke="currentColor" stroke-width="1.5"/>
    <path d="M14 16V21" stroke="currentColor" stroke-width="1.5"/>
  `,

  // Pigmentation - brown spot
  pigmentation: `
    <path d="M8 2C8 1 10 0 12 0C14 0 16 1 16 2V10C16 12 14 14 12 14C10 14 8 12 8 10V2Z" fill="none" stroke="currentColor" stroke-width="1.5"/>
    <ellipse cx="12" cy="5" rx="2" ry="1.5" fill="currentColor" fill-opacity="0.6"/>
    <path d="M10 16V21" stroke="currentColor" stroke-width="1.5"/>
    <path d="M14 16V21" stroke="currentColor" stroke-width="1.5"/>
  `,

  // Fracture - cracked tooth
  fracture: `
    <path d="M8 2C8 1 10 0 12 0C14 0 16 1 16 2V12C16 14 14 16 12 16C10 16 8 14 8 12V2Z" fill="none" stroke="currentColor" stroke-width="1.5"/>
    <path d="M10 3L11 6L9 9L12 12L10 15" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
    <path d="M10 18V22" stroke="currentColor" stroke-width="1.5"/>
    <path d="M14 18V22" stroke="currentColor" stroke-width="1.5"/>
  `,

  // Missing - empty socket
  missing: `
    <ellipse cx="12" cy="12" rx="8" ry="6" fill="none" stroke="currentColor" stroke-width="1.5" stroke-dasharray="3,2"/>
    <line x1="6" y1="8" x2="18" y2="16" stroke="currentColor" stroke-width="1.5"/>
    <line x1="18" y1="8" x2="6" y2="16" stroke="currentColor" stroke-width="1.5"/>
  `,

  // Periapical lesion small (<2mm)
  periapical_small: `
    <path d="M8 2C8 1 10 0 12 0C14 0 16 1 16 2V10C16 12 14 14 12 14C10 14 8 12 8 10V2Z" fill="none" stroke="currentColor" stroke-width="1.5"/>
    <path d="M10 14V18" stroke="currentColor" stroke-width="1.5"/>
    <path d="M14 14V18" stroke="currentColor" stroke-width="1.5"/>
    <circle cx="12" cy="20" r="2" fill="currentColor" fill-opacity="0.7" stroke="currentColor" stroke-width="0.5"/>
  `,

  // Periapical lesion medium (2-4mm)
  periapical_medium: `
    <path d="M8 2C8 1 10 0 12 0C14 0 16 1 16 2V10C16 12 14 14 12 14C10 14 8 12 8 10V2Z" fill="none" stroke="currentColor" stroke-width="1.5"/>
    <path d="M10 14V17" stroke="currentColor" stroke-width="1.5"/>
    <path d="M14 14V17" stroke="currentColor" stroke-width="1.5"/>
    <circle cx="12" cy="20" r="3.5" fill="currentColor" fill-opacity="0.7" stroke="currentColor" stroke-width="0.5"/>
  `,

  // Periapical lesion large (>4mm)
  periapical_large: `
    <path d="M8 2C8 1 10 0 12 0C14 0 16 1 16 2V10C16 12 14 14 12 14C10 14 8 12 8 10V2Z" fill="none" stroke="currentColor" stroke-width="1.5"/>
    <path d="M10 14V16" stroke="currentColor" stroke-width="1.5"/>
    <path d="M14 14V16" stroke="currentColor" stroke-width="1.5"/>
    <circle cx="12" cy="19" r="5" fill="currentColor" fill-opacity="0.7" stroke="currentColor" stroke-width="0.5"/>
  `,

  // Rotated - circular rotation arrow (clockwise)
  rotated: `
    <path d="M21 12a9 9 0 1 1-9-9c2.52 0 4.93 1 6.74 2.74L21 8" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    <path d="M21 3v5h-5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
  `,

  // Displaced - arrows pointing outward
  displaced: `
    <path d="M12 4V10" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <path d="M12 4L9 7" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <path d="M12 4L15 7" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <path d="M12 20V14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <path d="M12 20L9 17" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <path d="M12 20L15 17" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <path d="M4 12H10" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <path d="M4 12L7 9" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <path d="M4 12L7 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <path d="M20 12H14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <path d="M20 12L17 9" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <path d="M20 12L17 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
  `,

  // Unerupted - tooth beneath surface
  unerupted: `
    <line x1="4" y1="8" x2="20" y2="8" stroke="currentColor" stroke-width="2"/>
    <path d="M8 12C8 10 10 9 12 9C14 9 16 10 16 12V18C16 20 14 22 12 22C10 22 8 20 8 18V12Z" fill="currentColor" fill-opacity="0.2" stroke="currentColor" stroke-width="1.5" stroke-dasharray="2,2"/>
    <line x1="4" y1="10" x2="7" y2="14" stroke="currentColor" stroke-width="1"/>
    <line x1="20" y1="10" x2="17" y2="14" stroke="currentColor" stroke-width="1"/>
  `,

  // ============================================================================
  // RESTAURADORA
  // ============================================================================

  // Extraction - tooth with X (moved here but also used in cirugia)
  extraction: `
    <path d="M8 4C8 2.5 10 1 12 1C14 1 16 2.5 16 4V10C16 11.5 15 14 12 14C9 14 8 11.5 8 10V4Z" fill="currentColor" fill-opacity="0.3" stroke="currentColor" stroke-width="1.5"/>
    <path d="M5 18L19 18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <path d="M7 15L17 21" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <path d="M17 15L7 21" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
  `,

  // Filling composite - tooth with blue fill
  filling_composite: `
    <path d="M7 3C7 1.5 9.5 0 12 0C14.5 0 17 1.5 17 3V12C17 14 15.5 16 12 16C8.5 16 7 14 7 12V3Z" fill="none" stroke="currentColor" stroke-width="1.5"/>
    <rect x="9" y="5" width="6" height="5" rx="1" fill="currentColor"/>
    <path d="M10 18V22" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
    <path d="M14 18V22" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
  `,

  // Filling amalgam - tooth with gray/silver fill
  filling_amalgam: `
    <path d="M7 3C7 1.5 9.5 0 12 0C14.5 0 17 1.5 17 3V12C17 14 15.5 16 12 16C8.5 16 7 14 7 12V3Z" fill="none" stroke="currentColor" stroke-width="1.5"/>
    <rect x="9" y="5" width="6" height="5" rx="1" fill="currentColor" fill-opacity="0.7"/>
    <line x1="9.5" y1="6" x2="14.5" y2="6" stroke="currentColor" stroke-width="0.5" stroke-opacity="0.5"/>
    <line x1="9.5" y1="8" x2="14.5" y2="8" stroke="currentColor" stroke-width="0.5" stroke-opacity="0.5"/>
    <path d="M10 18V22" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
    <path d="M14 18V22" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
  `,

  // Filling temporary - tooth with green fill and clock indicator
  filling_temporary: `
    <path d="M7 3C7 1.5 9.5 0 12 0C14.5 0 17 1.5 17 3V12C17 14 15.5 16 12 16C8.5 16 7 14 7 12V3Z" fill="none" stroke="currentColor" stroke-width="1.5"/>
    <rect x="9" y="5" width="6" height="5" rx="1" fill="currentColor" fill-opacity="0.6"/>
    <circle cx="12" cy="7.5" r="1.5" fill="none" stroke="currentColor" stroke-width="0.75"/>
    <path d="M12 6.5V7.5L12.75 8" stroke="currentColor" stroke-width="0.5" stroke-linecap="round"/>
    <path d="M10 18V22" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
    <path d="M14 18V22" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
  `,

  // Filling (legacy) - tooth with filled surface
  filling: `
    <path d="M7 3C7 1.5 9.5 0 12 0C14.5 0 17 1.5 17 3V12C17 14 15.5 16 12 16C8.5 16 7 14 7 12V3Z" fill="none" stroke="currentColor" stroke-width="1.5"/>
    <rect x="9" y="5" width="6" height="5" rx="1" fill="currentColor"/>
    <path d="M10 18V22" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
    <path d="M14 18V22" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
  `,

  // Sealant - tooth with protective layer
  sealant: `
    <path d="M7 2C7 1 9 0 12 0C15 0 17 1 17 2V10C17 12 15 14 12 14C9 14 7 12 7 10V2Z" fill="none" stroke="currentColor" stroke-width="1.5"/>
    <path d="M8 4C8 3 9.5 2 12 2C14.5 2 16 3 16 4V6C16 7 14.5 8 12 8C9.5 8 8 7 8 6V4Z" fill="currentColor" fill-opacity="0.4" stroke="currentColor" stroke-width="1"/>
    <path d="M10 16V20" stroke="currentColor" stroke-width="1.5"/>
    <path d="M14 16V20" stroke="currentColor" stroke-width="1.5"/>
  `,

  // Veneer - front surface layer
  veneer: `
    <path d="M8 2C8 1 10 0 12 0C14 0 16 1 16 2V12C16 14 14 16 12 16C10 16 8 14 8 12V2Z" fill="none" stroke="currentColor" stroke-width="1.5"/>
    <path d="M8 3C8 2 9.5 1.5 12 1.5C14.5 1.5 16 2 16 3V11C16 12.5 14.5 14 12 14C9.5 14 8 12.5 8 11V3Z" fill="currentColor" fill-opacity="0.3"/>
    <path d="M10 17V21" stroke="currentColor" stroke-width="1.5"/>
    <path d="M14 17V21" stroke="currentColor" stroke-width="1.5"/>
  `,

  // Inlay - dotted pattern inside tooth
  inlay: `
    <path d="M7 2C7 1 9 0 12 0C15 0 17 1 17 2V10C17 12 15 14 12 14C9 14 7 12 7 10V2Z" fill="none" stroke="currentColor" stroke-width="1.5"/>
    <rect x="9" y="4" width="6" height="6" rx="1" fill="currentColor" fill-opacity="0.3" stroke="currentColor" stroke-width="1"/>
    <circle cx="10.5" cy="5.5" r="0.5" fill="currentColor"/>
    <circle cx="13.5" cy="5.5" r="0.5" fill="currentColor"/>
    <circle cx="12" cy="7" r="0.5" fill="currentColor"/>
    <circle cx="10.5" cy="8.5" r="0.5" fill="currentColor"/>
    <circle cx="13.5" cy="8.5" r="0.5" fill="currentColor"/>
    <path d="M10 16V21" stroke="currentColor" stroke-width="1.5"/>
    <path d="M14 16V21" stroke="currentColor" stroke-width="1.5"/>
  `,

  // Overlay - covers entire occlusal surface
  overlay: `
    <path d="M7 2C7 1 9 0 12 0C15 0 17 1 17 2V10C17 12 15 14 12 14C9 14 7 12 7 10V2Z" fill="none" stroke="currentColor" stroke-width="1.5"/>
    <path d="M7 2C7 1 9 0 12 0C15 0 17 1 17 2V5C17 6 15 7 12 7C9 7 7 6 7 5V2Z" fill="currentColor" fill-opacity="0.4" stroke="currentColor" stroke-width="1"/>
    <line x1="8" y1="3" x2="16" y2="3" stroke="currentColor" stroke-width="0.5"/>
    <line x1="8" y1="5" x2="16" y2="5" stroke="currentColor" stroke-width="0.5"/>
    <path d="M10 16V21" stroke="currentColor" stroke-width="1.5"/>
    <path d="M14 16V21" stroke="currentColor" stroke-width="1.5"/>
  `,

  // Crown - crown shape
  crown: `
    <path d="M4 10L6 3H18L20 10L18 11L16 8L14 12L12 7L10 12L8 8L6 11L4 10Z" fill="currentColor" fill-opacity="0.3" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
    <path d="M6 11V20C6 21 7 22 12 22C17 22 18 21 18 20V11" fill="none" stroke="currentColor" stroke-width="1.5"/>
    <ellipse cx="12" cy="11" rx="6" ry="2" fill="currentColor" fill-opacity="0.2"/>
  `,

  // Pontic - suspended tooth (new name for bridge_pontic)
  pontic: `
    <line x1="2" y1="4" x2="22" y2="4" stroke="currentColor" stroke-width="2"/>
    <line x1="4" y1="4" x2="4" y2="7" stroke="currentColor" stroke-width="1.5"/>
    <line x1="20" y1="4" x2="20" y2="7" stroke="currentColor" stroke-width="1.5"/>
    <path d="M8 8C8 7 10 6 12 6C14 6 16 7 16 8V16C16 18 14 20 12 20C10 20 8 18 8 16V8Z" fill="currentColor" fill-opacity="0.3" stroke="currentColor" stroke-width="1.5"/>
    <rect x="9" y="9" width="6" height="2" fill="currentColor" fill-opacity="0.2"/>
  `,

  // Bridge pontic (legacy)
  bridge_pontic: `
    <line x1="2" y1="4" x2="22" y2="4" stroke="currentColor" stroke-width="2"/>
    <line x1="4" y1="4" x2="4" y2="7" stroke="currentColor" stroke-width="1.5"/>
    <line x1="20" y1="4" x2="20" y2="7" stroke="currentColor" stroke-width="1.5"/>
    <path d="M8 8C8 7 10 6 12 6C14 6 16 7 16 8V16C16 18 14 20 12 20C10 20 8 18 8 16V8Z" fill="currentColor" fill-opacity="0.3" stroke="currentColor" stroke-width="1.5"/>
  `,

  // Bridge abutment - anchor tooth
  bridge_abutment: `
    <path d="M8 4C8 2 10 1 12 1C14 1 16 2 16 4V12C16 14 14 16 12 16C10 16 8 14 8 12V4Z" fill="none" stroke="currentColor" stroke-width="1.5"/>
    <path d="M2 8L6 12L2 16" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    <path d="M22 8L18 12L22 16" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    <path d="M10 18V22" stroke="currentColor" stroke-width="1.5"/>
    <path d="M14 18V22" stroke="currentColor" stroke-width="1.5"/>
  `,

  // Bridge (generic) - 3-unit: two abutments flanking a pontic, joined by arch bar
  bridge: `
    <line x1="2" y1="5" x2="22" y2="5" stroke="currentColor" stroke-width="1.5"/>
    <path d="M3 7C3 6 4 5.5 5.5 5.5C7 5.5 8 6 8 7V15C8 17 7 19 5.5 19C4 19 3 17 3 15V7Z" fill="currentColor" fill-opacity="0.25" stroke="currentColor" stroke-width="1.5"/>
    <path d="M9.5 8C9.5 7 10.5 6.5 12 6.5C13.5 6.5 14.5 7 14.5 8V15C14.5 16.5 13.5 17.5 12 17.5C10.5 17.5 9.5 16.5 9.5 15V8Z" fill="currentColor" fill-opacity="0.15" stroke="currentColor" stroke-width="1.5"/>
    <path d="M16 7C16 6 17 5.5 18.5 5.5C20 5.5 21 6 21 7V15C21 17 20 19 18.5 19C17 19 16 17 16 15V7Z" fill="currentColor" fill-opacity="0.25" stroke="currentColor" stroke-width="1.5"/>
  `,

  // Bridge metal-ceramic — bridge with a dark metal base band under ceramic shells
  bridge_metal_ceramic: `
    <line x1="2" y1="5" x2="22" y2="5" stroke="currentColor" stroke-width="1.5"/>
    <path d="M3 7C3 6 4 5.5 5.5 5.5C7 5.5 8 6 8 7V15C8 17 7 19 5.5 19C4 19 3 17 3 15V7Z" fill="none" stroke="currentColor" stroke-width="1.5"/>
    <path d="M3 12H8V15C8 17 7 19 5.5 19C4 19 3 17 3 15V12Z" fill="currentColor" fill-opacity="0.55"/>
    <path d="M9.5 8C9.5 7 10.5 6.5 12 6.5C13.5 6.5 14.5 7 14.5 8V15C14.5 16.5 13.5 17.5 12 17.5C10.5 17.5 9.5 16.5 9.5 15V8Z" fill="none" stroke="currentColor" stroke-width="1.5"/>
    <path d="M9.5 12H14.5V15C14.5 16.5 13.5 17.5 12 17.5C10.5 17.5 9.5 16.5 9.5 15V12Z" fill="currentColor" fill-opacity="0.55"/>
    <path d="M16 7C16 6 17 5.5 18.5 5.5C20 5.5 21 6 21 7V15C21 17 20 19 18.5 19C17 19 16 17 16 15V7Z" fill="none" stroke="currentColor" stroke-width="1.5"/>
    <path d="M16 12H21V15C21 17 20 19 18.5 19C17 19 16 17 16 15V12Z" fill="currentColor" fill-opacity="0.55"/>
  `,

  // Bridge zirconia — bridge with sparkle/diamond motif on the pontic
  bridge_zirconia: `
    <line x1="2" y1="5" x2="22" y2="5" stroke="currentColor" stroke-width="1.5"/>
    <path d="M3 7C3 6 4 5.5 5.5 5.5C7 5.5 8 6 8 7V15C8 17 7 19 5.5 19C4 19 3 17 3 15V7Z" fill="currentColor" fill-opacity="0.15" stroke="currentColor" stroke-width="1.5"/>
    <path d="M9.5 8C9.5 7 10.5 6.5 12 6.5C13.5 6.5 14.5 7 14.5 8V15C14.5 16.5 13.5 17.5 12 17.5C10.5 17.5 9.5 16.5 9.5 15V8Z" fill="currentColor" fill-opacity="0.15" stroke="currentColor" stroke-width="1.5"/>
    <path d="M16 7C16 6 17 5.5 18.5 5.5C20 5.5 21 6 21 7V15C21 17 20 19 18.5 19C17 19 16 17 16 15V7Z" fill="currentColor" fill-opacity="0.15" stroke="currentColor" stroke-width="1.5"/>
    <path d="M12 9L12.8 11.2L15 12L12.8 12.8L12 15L11.2 12.8L9 12L11.2 11.2Z" fill="currentColor"/>
  `,

  // Bridge Maryland — central pontic with thin bonded retention wings, no abutment crowns
  bridge_maryland: `
    <line x1="2" y1="5" x2="22" y2="5" stroke="currentColor" stroke-width="1.5"/>
    <path d="M2 8H9V11H2Z" fill="currentColor" fill-opacity="0.35" stroke="currentColor" stroke-width="1.25" stroke-linejoin="round"/>
    <path d="M8.5 7C8.5 5.5 10 4.5 12 4.5C14 4.5 15.5 5.5 15.5 7V17C15.5 19 14 21 12 21C10 21 8.5 19 8.5 17V7Z" fill="currentColor" fill-opacity="0.2" stroke="currentColor" stroke-width="1.5"/>
    <path d="M15 8H22V11H15Z" fill="currentColor" fill-opacity="0.35" stroke="currentColor" stroke-width="1.25" stroke-linejoin="round"/>
  `,

  // Splint (generic) — horseshoe arch
  splint: `
    <path d="M3 10C3 6 6 3.5 12 3.5C18 3.5 21 6 21 10V14C21 16.5 18 19 12 19C6 19 3 16.5 3 14V10Z" fill="currentColor" fill-opacity="0.2" stroke="currentColor" stroke-width="1.5"/>
    <ellipse cx="12" cy="11.5" rx="6.5" ry="3.5" fill="none" stroke="currentColor" stroke-width="1" stroke-dasharray="2,1.5"/>
  `,

  // Occlusal splint (férula de descarga) — arch with occlusal bite contact marks
  splint_occlusal: `
    <path d="M3 10C3 6 6 3.5 12 3.5C18 3.5 21 6 21 10V14C21 16.5 18 19 12 19C6 19 3 16.5 3 14V10Z" fill="currentColor" fill-opacity="0.22" stroke="currentColor" stroke-width="1.5"/>
    <line x1="6" y1="11.5" x2="18" y2="11.5" stroke="currentColor" stroke-width="1.25" stroke-linecap="round"/>
    <circle cx="8" cy="11.5" r="1" fill="currentColor"/>
    <circle cx="12" cy="11.5" r="1" fill="currentColor"/>
    <circle cx="16" cy="11.5" r="1" fill="currentColor"/>
  `,

  // Periodontal retention splint (férula periodontal) — row of teeth joined by a bonded wire
  splint_periodontal: `
    <path d="M3 3.5C3 2.75 3.75 2 5 2C6.25 2 7 2.75 7 3.5V11C7 12.5 6.25 13.5 5 13.5C3.75 13.5 3 12.5 3 11V3.5Z" fill="none" stroke="currentColor" stroke-width="1.25"/>
    <path d="M10 3.5C10 2.75 10.75 2 12 2C13.25 2 14 2.75 14 3.5V11C14 12.5 13.25 13.5 12 13.5C10.75 13.5 10 12.5 10 11V3.5Z" fill="none" stroke="currentColor" stroke-width="1.25"/>
    <path d="M17 3.5C17 2.75 17.75 2 19 2C20.25 2 21 2.75 21 3.5V11C21 12.5 20.25 13.5 19 13.5C17.75 13.5 17 12.5 17 11V3.5Z" fill="none" stroke="currentColor" stroke-width="1.25"/>
    <path d="M3 16H21" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <circle cx="5" cy="16" r="1.25" fill="currentColor"/>
    <circle cx="12" cy="16" r="1.25" fill="currentColor"/>
    <circle cx="19" cy="16" r="1.25" fill="currentColor"/>
    <path d="M4.5 13.5V21" stroke="currentColor" stroke-width="1"/>
    <path d="M5.5 13.5V21" stroke="currentColor" stroke-width="1"/>
    <path d="M11.5 13.5V21" stroke="currentColor" stroke-width="1"/>
    <path d="M12.5 13.5V21" stroke="currentColor" stroke-width="1"/>
    <path d="M18.5 13.5V21" stroke="currentColor" stroke-width="1"/>
    <path d="M19.5 13.5V21" stroke="currentColor" stroke-width="1"/>
  `,

  // ============================================================================
  // CIRUGÍA
  // ============================================================================

  // Implant - screw shape
  implant: `
    <rect x="10" y="1" width="4" height="4" rx="1" fill="currentColor"/>
    <path d="M9 5H15V8H9V5Z" fill="currentColor" fill-opacity="0.5"/>
    <path d="M8 8L16 8L15 22L9 22L8 8Z" fill="none" stroke="currentColor" stroke-width="1.5"/>
    <line x1="7" y1="11" x2="17" y2="11" stroke="currentColor" stroke-width="1"/>
    <line x1="7.5" y1="14" x2="16.5" y2="14" stroke="currentColor" stroke-width="1"/>
    <line x1="8" y1="17" x2="16" y2="17" stroke="currentColor" stroke-width="1"/>
    <line x1="8.5" y1="20" x2="15.5" y2="20" stroke="currentColor" stroke-width="1"/>
  `,

  // Apicoectomy - root tip surgery
  apicoectomy: `
    <path d="M8 2C8 1 10 0 12 0C14 0 16 1 16 2V10C16 12 14 14 12 14C10 14 8 12 8 10V2Z" fill="none" stroke="currentColor" stroke-width="1.5"/>
    <path d="M10 14V18" stroke="currentColor" stroke-width="1.5"/>
    <path d="M14 14V18" stroke="currentColor" stroke-width="1.5"/>
    <line x1="8" y1="20" x2="16" y2="20" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <circle cx="12" cy="22" r="1.5" fill="currentColor"/>
  `,

  // ============================================================================
  // ENDODONCIA
  // ============================================================================

  // Root canal full - complete endodontic treatment
  root_canal_full: `
    <path d="M7 2C7 1 9 0 12 0C15 0 17 1 17 2V10C17 12 15 14 12 14C9 14 7 12 7 10V2Z" fill="none" stroke="currentColor" stroke-width="1.5"/>
    <path d="M10 14V21C10 22.5 11 23 12 23C13 23 14 22.5 14 21V14" fill="none" stroke="currentColor" stroke-width="1.5"/>
    <path d="M12 4V21" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
  `,

  // Root canal two thirds
  root_canal_two_thirds: `
    <path d="M7 2C7 1 9 0 12 0C15 0 17 1 17 2V10C17 12 15 14 12 14C9 14 7 12 7 10V2Z" fill="none" stroke="currentColor" stroke-width="1.5"/>
    <path d="M10 14V21C10 22.5 11 23 12 23C13 23 14 22.5 14 21V14" fill="none" stroke="currentColor" stroke-width="1.5"/>
    <path d="M12 4V16" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
    <text x="18" y="12" font-size="6" fill="currentColor">⅔</text>
  `,

  // Root canal half
  root_canal_half: `
    <path d="M7 2C7 1 9 0 12 0C15 0 17 1 17 2V10C17 12 15 14 12 14C9 14 7 12 7 10V2Z" fill="none" stroke="currentColor" stroke-width="1.5"/>
    <path d="M10 14V21C10 22.5 11 23 12 23C13 23 14 22.5 14 21V14" fill="none" stroke="currentColor" stroke-width="1.5"/>
    <path d="M12 4V12" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
    <text x="18" y="12" font-size="6" fill="currentColor">½</text>
  `,

  // Root canal (legacy)
  root_canal: `
    <path d="M7 2C7 1 9 0 12 0C15 0 17 1 17 2V10C17 12 15 14 12 14C9 14 7 12 7 10V2Z" fill="none" stroke="currentColor" stroke-width="1.5"/>
    <path d="M10 14V21C10 22.5 11 23 12 23C13 23 14 22.5 14 21V14" fill="none" stroke="currentColor" stroke-width="1.5"/>
    <path d="M12 6V20" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <circle cx="12" cy="17" r="2" fill="currentColor"/>
  `,

  // Post - post and core
  post: `
    <path d="M8 2C8 1 10 0 12 0C14 0 16 1 16 2V8H8V2Z" fill="currentColor" fill-opacity="0.3" stroke="currentColor" stroke-width="1.5"/>
    <rect x="10" y="8" width="4" height="14" fill="currentColor"/>
    <rect x="9" y="6" width="6" height="3" rx="0.5" fill="currentColor"/>
  `,

  // Root canal overfill - material beyond apex
  root_canal_overfill: `
    <path d="M7 2C7 1 9 0 12 0C15 0 17 1 17 2V10C17 12 15 14 12 14C9 14 7 12 7 10V2Z" fill="none" stroke="currentColor" stroke-width="1.5"/>
    <path d="M10 14V20" stroke="currentColor" stroke-width="1.5"/>
    <path d="M14 14V20" stroke="currentColor" stroke-width="1.5"/>
    <path d="M12 4V20" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
    <path d="M12 20V23" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-dasharray="1,1"/>
    <circle cx="12" cy="22" r="1" fill="currentColor" fill-opacity="0.6"/>
  `,

  // ============================================================================
  // ORTODONCIA
  // ============================================================================

  // Bracket - orthodontic bracket
  bracket: `
    <rect x="8" y="8" width="8" height="8" rx="1" fill="currentColor" fill-opacity="0.3" stroke="currentColor" stroke-width="1.5"/>
    <line x1="3" y1="12" x2="8" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <line x1="16" y1="12" x2="21" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <rect x="10" y="10" width="4" height="4" fill="currentColor"/>
  `,

  // Tube - orthodontic tube (on molars)
  tube: `
    <rect x="6" y="8" width="12" height="8" rx="2" fill="currentColor" fill-opacity="0.3" stroke="currentColor" stroke-width="1.5"/>
    <ellipse cx="12" cy="12" rx="3" ry="2" fill="none" stroke="currentColor" stroke-width="1.5"/>
    <line x1="3" y1="12" x2="6" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <line x1="18" y1="12" x2="21" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
  `,

  // Band - orthodontic band (ring around tooth)
  band: `
    <ellipse cx="12" cy="12" rx="8" ry="6" fill="none" stroke="currentColor" stroke-width="2"/>
    <ellipse cx="12" cy="12" rx="5" ry="3.5" fill="currentColor" fill-opacity="0.2"/>
    <rect x="10" y="10" width="4" height="4" rx="0.5" fill="currentColor"/>
    <line x1="3" y1="12" x2="4" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <line x1="20" y1="12" x2="21" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
  `,

  // Attachment - clear aligner attachment (small bump)
  attachment: `
    <path d="M8 6C8 4 10 2 12 2C14 2 16 4 16 6V14C16 16 14 18 12 18C10 18 8 16 8 14V6Z" fill="none" stroke="currentColor" stroke-width="1.5"/>
    <ellipse cx="12" cy="10" rx="3" ry="2" fill="currentColor"/>
    <path d="M10 19V22" stroke="currentColor" stroke-width="1.5"/>
    <path d="M14 19V22" stroke="currentColor" stroke-width="1.5"/>
  `,

  // Retainer - wire retainer
  retainer: `
    <path d="M4 14C4 8 8 4 12 4C16 4 20 8 20 14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <circle cx="4" cy="14" r="2" fill="currentColor"/>
    <circle cx="20" cy="14" r="2" fill="currentColor"/>
    <path d="M8 10C8 10 10 8 12 8C14 8 16 10 16 10" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
    <line x1="8" y1="18" x2="16" y2="18" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
  `,

  // ============================================================================
  // POSITION ACTIONS (legacy aliases)
  // ============================================================================

  // Rotate - circular rotation arrow (clockwise)
  rotate: `
    <path d="M21 12a9 9 0 1 1-9-9c2.52 0 4.93 1 6.74 2.74L21 8" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    <path d="M21 3v5h-5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
  `,

  // Displace - tooth position indicator (arrows pointing outward)
  displace: `
    <path d="M12 4V10" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <path d="M12 4L9 7" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <path d="M12 4L15 7" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <path d="M12 20V14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <path d="M12 20L9 17" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <path d="M12 20L15 17" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <path d="M4 12H10" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <path d="M4 12L7 9" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <path d="M4 12L7 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <path d="M20 12H14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <path d="M20 12L17 9" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <path d="M20 12L17 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
  `
}

// Catalog internal_code → icon key.
// Lets catalog items that share an odontogram_treatment_type (e.g. three bridge
// variants) render distinct icons in the TreatmentBar.
export const TREATMENT_ICON_BY_INTERNAL_CODE: Record<string, string> = {
  'REST-BRIDGE-MC': 'bridge_metal_ceramic',
  'REST-BRIDGE-ZIR': 'bridge_zirconia',
  'REST-BRIDGE-MARY': 'bridge_maryland',
  'REST-SPLINT-OCC': 'splint_occlusal',
  'REST-SPLINT-PERIO': 'splint_periodontal'
}

export function resolveTreatmentIconKey(
  odontogramType: string,
  internalCode?: string | null
): string {
  if (internalCode && TREATMENT_ICON_BY_INTERNAL_CODE[internalCode]) {
    return TREATMENT_ICON_BY_INTERNAL_CODE[internalCode]
  }
  return odontogramType
}

// Get icon SVG for a treatment type
export function getTreatmentIcon(treatmentType: string): string {
  return TREATMENT_ICONS[treatmentType] || TREATMENT_ICONS.filling
}

// Check if treatment requires surface selection (re-export with same name for compatibility)
export function isSurfaceTreatment(treatmentType: string): boolean {
  return checkIsSurfaceTreatment(treatmentType)
}
