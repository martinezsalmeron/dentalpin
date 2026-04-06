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
  // Extraction - tooth with X or forceps
  extraction: `
    <path d="M8 4C8 2.5 10 1 12 1C14 1 16 2.5 16 4V10C16 11.5 15 14 12 14C9 14 8 11.5 8 10V4Z" fill="currentColor" fill-opacity="0.3" stroke="currentColor" stroke-width="1.5"/>
    <path d="M5 18L19 18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <path d="M7 15L17 21" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <path d="M17 15L7 21" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
  `,

  // Filling - tooth with filled surface
  filling: `
    <path d="M7 3C7 1.5 9.5 0 12 0C14.5 0 17 1.5 17 3V12C17 14 15.5 16 12 16C8.5 16 7 14 7 12V3Z" fill="none" stroke="currentColor" stroke-width="1.5"/>
    <rect x="9" y="5" width="6" height="5" rx="1" fill="currentColor"/>
    <path d="M10 18V22" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
    <path d="M14 18V22" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
  `,

  // Root canal - tooth with canal marked
  root_canal: `
    <path d="M7 2C7 1 9 0 12 0C15 0 17 1 17 2V10C17 12 15 14 12 14C9 14 7 12 7 10V2Z" fill="none" stroke="currentColor" stroke-width="1.5"/>
    <path d="M10 14V21C10 22.5 11 23 12 23C13 23 14 22.5 14 21V14" fill="none" stroke="currentColor" stroke-width="1.5"/>
    <path d="M12 6V20" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <circle cx="12" cy="17" r="2" fill="currentColor"/>
  `,

  // Crown - crown shape
  crown: `
    <path d="M4 10L6 3H18L20 10L18 11L16 8L14 12L12 7L10 12L8 8L6 11L4 10Z" fill="currentColor" fill-opacity="0.3" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
    <path d="M6 11V20C6 21 7 22 12 22C17 22 18 21 18 20V11" fill="none" stroke="currentColor" stroke-width="1.5"/>
    <ellipse cx="12" cy="11" rx="6" ry="2" fill="currentColor" fill-opacity="0.2"/>
  `,

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

  // Caries - tooth with decay
  caries: `
    <path d="M7 2C7 1 9 0 12 0C15 0 17 1 17 2V10C17 12 15 14 12 14C9 14 7 12 7 10V2Z" fill="none" stroke="currentColor" stroke-width="1.5"/>
    <circle cx="11" cy="5" r="2" fill="currentColor"/>
    <circle cx="13" cy="7" r="1.5" fill="currentColor"/>
    <path d="M10 16V21" stroke="currentColor" stroke-width="1.5"/>
    <path d="M14 16V21" stroke="currentColor" stroke-width="1.5"/>
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

  // Post - post and core
  post: `
    <path d="M8 2C8 1 10 0 12 0C14 0 16 1 16 2V8H8V2Z" fill="currentColor" fill-opacity="0.3" stroke="currentColor" stroke-width="1.5"/>
    <rect x="10" y="8" width="4" height="14" fill="currentColor"/>
    <rect x="9" y="6" width="6" height="3" rx="0.5" fill="currentColor"/>
  `,

  // Bridge pontic - suspended tooth
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

  // Missing - empty socket
  missing: `
    <ellipse cx="12" cy="12" rx="8" ry="6" fill="none" stroke="currentColor" stroke-width="1.5" stroke-dasharray="3,2"/>
    <line x1="6" y1="8" x2="18" y2="16" stroke="currentColor" stroke-width="1.5"/>
    <line x1="18" y1="8" x2="6" y2="16" stroke="currentColor" stroke-width="1.5"/>
  `,

  // Fracture - cracked tooth
  fracture: `
    <path d="M8 2C8 1 10 0 12 0C14 0 16 1 16 2V12C16 14 14 16 12 16C10 16 8 14 8 12V2Z" fill="none" stroke="currentColor" stroke-width="1.5"/>
    <path d="M10 3L11 6L9 9L12 12L10 15" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
    <path d="M10 18V22" stroke="currentColor" stroke-width="1.5"/>
    <path d="M14 18V22" stroke="currentColor" stroke-width="1.5"/>
  `,

  // Apicoectomy - root tip surgery
  apicoectomy: `
    <path d="M8 2C8 1 10 0 12 0C14 0 16 1 16 2V10C16 12 14 14 12 14C10 14 8 12 8 10V2Z" fill="none" stroke="currentColor" stroke-width="1.5"/>
    <path d="M10 14V18" stroke="currentColor" stroke-width="1.5"/>
    <path d="M14 14V18" stroke="currentColor" stroke-width="1.5"/>
    <line x1="8" y1="20" x2="16" y2="20" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <circle cx="12" cy="22" r="1.5" fill="currentColor"/>
  `,

  // Rotate - tooth position indicator (circular arrow)
  rotate: `
    <path d="M12 4C16.4 4 20 7.6 20 12" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round"/>
    <path d="M20 12L17 9" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <path d="M20 12L17 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <path d="M12 20C7.6 20 4 16.4 4 12" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round"/>
    <path d="M4 12L7 9" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <path d="M4 12L7 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
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
  `,

  // Bracket - orthodontic bracket
  bracket: `
    <rect x="8" y="8" width="8" height="8" rx="1" fill="currentColor" fill-opacity="0.3" stroke="currentColor" stroke-width="1.5"/>
    <line x1="3" y1="12" x2="8" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <line x1="16" y1="12" x2="21" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <rect x="10" y="10" width="4" height="4" fill="currentColor"/>
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
  `
}

// Get icon SVG for a treatment type
export function getTreatmentIcon(treatmentType: string): string {
  return TREATMENT_ICONS[treatmentType] || TREATMENT_ICONS.filling
}

// Check if treatment requires surface selection (re-export with same name for compatibility)
export function isSurfaceTreatment(treatmentType: string): boolean {
  return checkIsSurfaceTreatment(treatmentType)
}
