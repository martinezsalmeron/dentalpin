/**
 * ToothSVGPaths.ts - Tooth SVG path definitions with quadrant symmetry
 *
 * Implements "napkin unfolding" symmetry:
 * - Q1 (11-18): Original paths (Superior Right)
 * - Q2 (21-28): scaleX(-1) mirror
 * - Q4 (41-48): scaleY(-1) mirror
 * - Q3 (31-38): scaleX(-1) scaleY(-1) mirror
 *
 * Paths extracted from professional dental SVGs with anatomically accurate proportions.
 */

import {
  isDeciduousTooth as isDeciduousToothFn,
  isUpperTooth as isUpperToothFn,
  SURFACE_TREATMENTS,
  WHOLE_TOOTH_TREATMENTS
} from '~/config/odontogramConstants'

// Re-export helpers
export const isUpperTooth = isUpperToothFn
export const isDeciduousTooth = isDeciduousToothFn

// Surface and whole-tooth treatment types
export const SURFACE_TREATMENT_TYPES: readonly string[] = SURFACE_TREATMENTS
export const WHOLE_TOOTH_TREATMENT_TYPES: readonly string[] = WHOLE_TOOTH_TREATMENTS

// Helper functions for treatment types
export function makesToothTransparent(treatmentType: string): boolean {
  return treatmentType === 'extraction' || treatmentType === 'missing'
}

// Treatment colors
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
  bracket: '#6366F1',
  band: '#8B5CF6',
  attachment: '#EC4899',
  retainer: '#14B8A6',
  rotate: '#8B5CF6',
  displace: '#F59E0B'
}

// Pattern definitions for SVG
export const PATTERN_DEFINITIONS = `
  <defs>
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
// QUADRANT SYMMETRY FUNCTIONS
// ============================================================================

/**
 * Get CSS transform for a tooth based on its quadrant
 * Implements "napkin unfolding" symmetry
 */
export function getToothTransform(toothNumber: number): string {
  const quadrant = Math.floor(toothNumber / 10)

  switch (quadrant) {
    case 1: return '' // Q1: Original (Superior Right)
    case 2: return 'scaleX(-1)' // Q2: Horizontal mirror (Superior Left)
    case 3: return 'scaleX(-1) scaleY(-1)' // Q3: Diagonal mirror (Inferior Left)
    case 4: return 'scaleY(-1)' // Q4: Vertical mirror (Inferior Right)
    // Deciduous teeth
    case 5: return '' // Q5: Original (Superior Right)
    case 6: return 'scaleX(-1)' // Q6: Horizontal mirror (Superior Left)
    case 7: return 'scaleX(-1) scaleY(-1)' // Q7: Diagonal mirror (Inferior Left)
    case 8: return 'scaleY(-1)' // Q8: Vertical mirror (Inferior Right)
    default: return ''
  }
}

/**
 * Get tooth position within quadrant (1-8 for permanent, 1-5 for deciduous)
 */
export function getToothPosition(toothNumber: number): number {
  return toothNumber % 10
}

// ============================================================================
// LATERAL VIEW PATHS
// Extracted from professional dental SVGs
// ============================================================================

interface LateralPaths {
  crown: string
  root?: string
  roots?: string[]
  pulp?: string // Pulp chamber outline (for root canal visualization)
  highlight: string[]
  gumLine: string
  viewBox: string
}

// ============================================================================
// LATERAL VIEW DISPLAY CONFIGURATION
// Scale and alignment settings for each tooth position
// ============================================================================

interface ToothDisplayConfig {
  scale: number // Scale factor relative to base display width (55px)
  offsetY: number // Vertical offset to align crowns (positive = down)
  displayHeight: number // Fixed display height for consistent alignment
}

// Configuration to ensure proper alignment and sizing
// Upper teeth: roots point UP, crown at BOTTOM - crown line should be aligned
// Lower teeth: roots point DOWN, crown at TOP - crown line should be aligned
// Scales calibrated so all teeth have similar visual height (~100px)
const TOOTH_DISPLAY_CONFIG: Record<number, ToothDisplayConfig> = {
  // Incisors - narrower teeth, need smaller scale to achieve similar height
  1: { scale: 0.65, offsetY: 0, displayHeight: 100 },
  2: { scale: 0.62, offsetY: 0, displayHeight: 100 },
  // Canine - similar to incisors
  3: { scale: 0.62, offsetY: 0, displayHeight: 100 },
  // Premolars - medium width
  4: { scale: 0.75, offsetY: 0, displayHeight: 100 },
  5: { scale: 0.62, offsetY: 0, displayHeight: 100 },
  // Molars - wider teeth, need larger scale to compensate for aspect ratio
  6: { scale: 0.95, offsetY: 0, displayHeight: 100 },
  7: { scale: 1.0, offsetY: 0, displayHeight: 100 },
  8: { scale: 1.20, offsetY: 0, displayHeight: 100 }
}

export function getToothDisplayConfig(toothNumber: number): ToothDisplayConfig {
  const isDeciduous = isDeciduousTooth(toothNumber)
  let position = getToothPosition(toothNumber)

  if (isDeciduous) {
    position = DECIDUOUS_TO_PERMANENT_MAP[position] || 1
  }

  return TOOTH_DISPLAY_CONFIG[position] || TOOTH_DISPLAY_CONFIG[1]
}

// Paths indexed by position (1-8) - using actual SVG paths from reference
const LATERAL_PATHS_BY_POSITION: Record<number, LateralPaths> = {
  // Position 1: Central Incisor (tooth 11) - viewBox 46x134
  1: {
    viewBox: '0 0 46 134',
    crown: 'M39.2326 94.6438C33.1163 85.5409 14.1409 86.0457 6.65385 94.6438C-0.669089 102.084 0.287887 121.08 3.03399 127.814C15.6411 135.545 38.1091 133.675 43.8511 128.437C46.722 121.828 43.8511 103.747 39.2326 94.6438Z',
    root: 'M18.1375 13.8391C16.1403 42.3702 9.64956 79.4307 6.65381 94.3946C18.9498 99.8859 26.179 100.443 39.8567 95.5168C40.4808 78.9319 40.0564 39.577 33.3659 14.8367C26.953 -8.87723 18.913 2.76033 18.1375 13.8391Z',
    // Pulp chamber - from tooth 11 reference (teeth-root class)
    pulp: 'M24.6596 4.92303C30.269 4.6849 31.2334 104.288 22.1317 95.1425C19.5389 92.7118 23.1687 67.5969 24.3785 42.7689C25.3455 22.9252 23.5958 4.9682 24.6596 4.92303Z',
    highlight: [],
    gumLine: 'M 0,95 Q 23,100 46,95'
  },
  // Position 2: Lateral Incisor (tooth 12) - viewBox 40x125
  2: {
    viewBox: '0 0 40 125',
    crown: 'M36.0861 86.4908C33.7138 80.3598 11.2384 78.6075 6.61846 84.8639C0.82482 92.7098 0.250476 113.268 1.62396 116.146C2.99745 119.024 8.866 122.152 18.6053 123.653C28.3446 125.155 35.7115 121.526 37.959 117.647C40.2066 113.768 38.4585 92.6219 36.0861 86.4908Z',
    root: 'M12.487 53.0815C10.4083 62.2149 9.40701 74.1863 8.61621 83.112C16.2849 89.5132 36.3357 86.7405 36.3357 86.7405C36.3357 86.7405 34.7467 75.1037 35.0871 71.475C37.6081 44.5978 35.3738 25.049 34.213 18.4214C32.6315 12.4571 28.4694 0.328393 22.476 1.0291C14.9842 1.90499 18.3555 19.2973 17.7312 26.8049C17.0027 35.5656 14.1102 45.9493 12.487 53.0815Z',
    // Pulp chamber - from tooth 12 reference
    pulp: 'M23.8494 41.5699C24.8167 21.6581 21.6019 4.15698 23.8495 4.15698C28.1612 4.15698 29.9677 35.6889 27.7202 60.2138C26.8687 78.8752 25.6047 94.7422 20.9135 92.2458C17.2318 87.6165 22.6392 66.4831 23.8494 41.5699Z',
    highlight: [],
    gumLine: 'M 0,85 Q 20,92 40,85'
  },
  // Position 3: Canine (tooth 13) - viewBox 47x146
  3: {
    viewBox: '0 0 47 146',
    crown: 'M44.5622 115.129C42.5478 107.137 40.7902 95.6772 22.907 95.8989C3.61725 96.1381 1 114.898 1 129.988C1 136.106 7.90619 141.245 12.8348 143.598C17.3509 145.755 30.8565 145.156 34.2382 143.598C37.7635 141.975 41.3094 141.201 44.5622 135.108C46.8285 130.862 46.0953 121.211 44.5622 115.129Z',
    root: 'M9.09261 76.4153C8.17217 80.9327 7.17502 95.9485 6.7915 102.892C6.7915 102.892 16.3143 107.776 22.907 107.886C29.8761 108.003 40.0297 102.892 40.0297 102.892C38.1121 97.8724 34.7883 71.2707 35.4275 67.1299C36.0667 62.989 34.4048 42.9121 33.5099 38.3948C32.6151 33.8775 30.3139 20.5764 29.9304 15.0552C29.5469 9.53405 25.9674 0.875868 22.3879 1.00135C18.8084 1.12683 19.0641 4.01289 18.1692 5.51866C17.2743 7.02443 17.1465 16.561 16.763 20.5764C16.3795 24.5917 16.3795 25.5956 14.5897 29.36C12.8 33.1244 11.7772 43.7903 11.7772 47.0528C11.7772 50.3153 10.2432 70.7687 9.09261 76.4153Z',
    // Pulp chamber - from tooth 13 reference
    pulp: 'M19.3901 108.569C20.4638 72.4818 22.0439 6.61914 22.4697 6.61914C26.6797 6.61914 26.8139 49.0405 26.9928 84.7355C27.0356 93.2851 27.8031 101.605 28.0152 108.731C28.0857 111.1 26.141 113.006 23.7516 113.006C21.2913 113.006 19.3176 111.008 19.3901 108.569Z',
    highlight: [],
    gumLine: 'M 0,103 Q 23,110 47,103'
  },
  // Position 4: First Premolar (tooth 14) - viewBox 160x400 (scaled)
  4: {
    viewBox: '0 0 160 400',
    crown: 'M135 250c-15,-16 -94,-16 -106,0 -21,28 -24,61 -24,76 -1,11 10,33 68,40 72,8 82,-30 82,-38 0,-14 -4,-61 -21,-78z',
    roots: [
      'M86 111c10,-31 16,-55 18,-71 1,-7 -6,-34 2,-34 9,0 33,32 36,54 3,21 -2,89 -5,116 -3,22 -3,57 -2,72 -50,30 -72,28 -106,2 0,0 8,-15 10,-50 1,-21 -6,-57 -7,-81 -5,-65 11,-111 22,-113 14,1 14,72 32,103l1 2'
    ],
    // Pulp chamber - from tooth 14 reference (bifurcated pulp)
    pulp: 'M77 154c1,4 0,7 5,10 7,-10 23,-37 28,-72 7,-44 3,-58 3,-61 0,-2 16,-4 10,56 -6,61 -17,86 -20,107 -3,21 -5,24 -7,54 -3,26 -37,21 -37,-3 0,-6 0,-21 0,-30 0,-11 -14,-72 -15,-105 -1,-26 0,-81 5,-85 6,-6 11,53 15,77 4,25 9,34 11,41l1 7z',
    highlight: [],
    gumLine: 'M 0,250 Q 80,270 160,250'
  },
  // Position 5: Second Premolar (tooth 15) - viewBox 40x125
  5: {
    viewBox: '0 0 40 125',
    crown: 'M32.0429 80.3319C25.3641 76.7153 12.3775 76.9648 8.17236 80.3319C2.73036 89.0619 -0.0157515 103.786 1.34475 110.396C2.70524 117.005 18.5365 125.61 21.2575 123.74C24.6402 121.414 38.3256 113.139 38.944 108.4C39.5624 103.661 34.8625 94.5572 34.6151 87.8227C34.4172 82.4352 32.9797 80.8392 32.0429 80.3319Z',
    root: 'M9.01314 60.2618C8.22157 63.8534 8.10614 75.0609 8.14736 80.2156C17.5183 82.1917 23.0911 82.7369 33.6258 81.9617C33.5021 81.0887 32.5126 72.9825 31.6469 65.8739C30.7574 58.5708 31.0285 49.412 31.0285 46.5436C31.0285 43.6752 29.9153 33.3242 28.4311 29.5828C26.947 25.8415 27.5654 18.4834 26.8233 15.3656C26.0812 12.2478 20.8866 0.400168 17.9182 1.02373C14.9498 1.64728 17.1761 6.38633 16.1867 15.9891C15.3951 23.6714 12.8473 34.5296 11.9815 37.0654C10.7447 40.3079 10.0026 55.7721 9.01314 60.2618Z',
    // Pulp chamber - from tooth 15 reference
    pulp: 'M18.6602 6.8971C23.0444 1.05663 24.7882 59.2963 24.4272 85.6725C24.406 87.219 23.1529 88.4437 21.619 88.4437C20.0082 88.4437 18.7249 87.0911 18.7917 85.4684C19.91 58.2791 19.4075 17.8055 18.6602 6.8971Z',
    highlight: [],
    gumLine: 'M 0,80 Q 20,88 40,80'
  },
  // Position 6: First Molar (tooth 16) - viewBox 64x128
  6: {
    viewBox: '0 0 64 128',
    crown: 'M52.5724 83.8192C38.6457 77.1735 21.2542 79.2177 11.7848 82.6763C9.77918 83.4088 8.23738 84.9707 7.35306 86.9098C5.1137 91.8204 1 101.871 1 109.443C1 114.19 5.86637 124.628 14.0266 126.184C20.4417 127.407 24.7345 122.822 31.8129 122.686C39.6605 122.535 44.3969 129.286 51.6033 126.184C58.803 123.084 64.5464 115.023 62.6258 109.443C60.8828 104.378 59.6213 92.6599 54.5345 85.8667C54.0084 85.1642 53.3957 84.2121 52.5724 83.8192Z',
    roots: [
      'M31.6876 1C25.1117 1 26.9905 28.8602 19.7883 35.2319C21.1244 45.8096 28.5513 59.3963 32.3139 60.4685C35.8211 61.468 44.0879 37.2308 45.7162 28.8602C41.0818 22.7385 37.1989 1 31.6876 1Z',
      'M54.537 84.9802C54.537 83.5 52.5329 73.4613 54.537 64.8658C57.0421 54.1215 59.2967 40.8785 59.2967 31.3836C59.2967 22.4209 58.7387 10.8979 52.1445 5.22081C51.5917 4.74482 50.7688 5.08408 50.6455 5.80208C48.2891 19.5153 42.5034 48.131 33.2436 59.8685C30.5486 63.2845 16.6396 32.362 13.0019 10.5877C12.8671 9.78116 11.9139 9.48249 11.4381 10.1484C8.49442 14.2692 4.6997 23.8642 6.43885 39.1295C8.94396 61.1178 9.94601 59.2438 9.94601 68.364C9.94601 72.1459 8.4267 80.7768 7.6531 85.1369'
    ],
    // Pulp chamber - from tooth 16 reference (multi-root pulp)
    pulp: 'M37.1988 80.0831C37.6999 79.4584 46.3425 64.8414 48.7223 53.9721C51.1022 43.1029 55.3609 29.61 51.7285 16.6169C48.0961 3.62377 56.9892 42.1033 32.0634 74.836C28.5169 74.836 11.3588 40.418 11.9479 21.9296C11.9552 21.7004 11.6501 21.6422 11.583 21.8616C6.57857 38.2285 23.1191 71.6539 24.6733 74.8358C25.8632 77.2722 25.5083 79.75 25.4248 80.0831',
    highlight: [],
    gumLine: 'M 0,85 Q 32,95 64,85'
  },
  // Position 7: Second Molar (tooth 17) - viewBox 66x124
  7: {
    viewBox: '0 0 66 124',
    crown: 'M57.655 80.8343C57.2557 80.5265 56.8413 80.2327 56.4129 79.9525C44.8747 72.4037 23.1621 74.6455 11.3233 76.9591C10.1919 77.2013 8.70714 77.8501 7.72107 78.7268C7.41105 79.0024 7.15033 79.3005 6.96539 79.6156C-7.5536 104.353 8.35603 122.835 13.4349 122.835C18.6519 122.835 21.1362 113.835 28.589 112.835C36.0418 111.834 46.4758 124.585 52.6865 122.835C57.5011 121.478 63.8657 109.459 64.8594 104.709C65.8531 99.9594 61.3815 83.8342 57.655 80.8343Z',
    roots: [
      'M23.1237 1.08372C17.9564 4.38375 17.6582 22.6256 18.1551 31.334C20.6394 39.2507 26.8998 54.484 32.0671 52.084C37.2344 49.684 39.1058 39.9172 39.3957 35.3338C34.1787 29.3338 30.2039 17.7089 30.2039 15.3339C30.2039 12.9588 28.2164 -0.166297 23.1237 1.08372Z',
      'M10.79 62.9522C11.6845 68.8711 7 78.5 7.31157 78.7704C27.6459 73.526 38.316 73.7571 56.0109 80C58.3299 72.0579 59.4894 47.6533 54.5201 30.8499C48.5135 10.5393 40.5231 6.64772 37.9971 7.02392C34.767 9.65731 40.7302 23.326 39.7363 31.9786C39.2337 36.3543 34.1459 54.2997 31.1643 51.6663C22.468 45.0201 18.6789 33.6715 17.3744 30.8499C16.2812 28.4853 15.3867 18.31 15.014 15.6766C14.6413 13.0432 12.9641 8.27783 10.79 8.65412C8.61602 9.0304 5.86595 15.8311 4.45422 22.3228C3.33612 27.4642 4.45422 40.0042 5.94496 47.6535C7.37238 54.9779 9.79624 56.3761 10.79 62.9522Z'
    ],
    // Pulp chamber - from tooth 17 reference (multi-root pulp)
    pulp: 'M37.2839 74.5841C36.8698 73.8758 36.2902 72.1841 37.2839 71.0841C38.526 69.7091 46.9105 56.2089 48.5253 44.4588C51.1959 32.146 44.1778 14.3333 40.1408 10.7085C38.7124 12.271 46.9726 27.3962 45.1094 39.2088C43.9915 47.9589 39.8924 61.5835 31.3216 68.0838C25.7321 65.2713 18.3413 47.9586 14.4286 32.146C11.5574 23.0066 11.3488 14.4022 11.0748 14.3333C10.3295 14.1458 9.28612 26.6834 11.0748 35.5835C13.3106 46.7086 17.7823 56.8962 23.9309 68.0838C24.9246 72.7839 24.3657 73.7714 24.3657 75.0839',
    highlight: [],
    gumLine: 'M 0,78 Q 33,88 66,78'
  },
  // Position 8: Third Molar (tooth 18) - viewBox 67x104
  8: {
    viewBox: '0 0 67 104',
    crown: 'M58.1322 63.4319C48.1437 53.9492 13.933 57.9421 8.18956 62.1842C5.31786 66.2599 -0.100915 76.682 1.19759 85.7652C2.33379 93.7129 8.96183 100.615 11.9353 100.987C17.9284 101.735 27.5423 95.3723 33.7851 96.3704C40.028 97.3686 44.0234 103.357 48.7679 102.983C53.5125 102.609 59.8802 99.3649 64.6247 92.8769C69.3693 82.1469 60.5045 70.7928 58.1322 63.4319Z',
    roots: [
      'M30.9758 1.09548C28.5411 1.78154 24.8995 7.08434 24.4209 9.70447C24.2544 20.4602 25.9192 41.1732 33.91 37.9792C41.9008 34.7851 41.4846 20.8761 40.2777 14.3209C39.5285 12.2622 34.1616 0.197776 30.9758 1.09548Z',
      'M40.877 4.12291C58.0573 11.4094 58.1489 46.1284 56.9835 62.1402C38.3215 55.4866 27.3562 55.8281 7.04093 63C9.63795 60.5048 10.1207 54.0303 10.0375 52.1586C9.74852 45.6613 6.60782 42.3046 7.04093 31.8214C7.9399 10.0619 15.1566 3.54066 18.6526 3C24.1687 3 27.3814 27.6287 32.1621 35.9891C32.4602 36.5103 33.1208 36.5476 33.4394 36.0387C34.5725 34.2284 36.4464 30.1401 38.3799 24.5852C41.3765 15.9762 35.7579 2.25139 40.877 4.12291Z'
    ],
    // Pulp chamber - from tooth 18 reference (multi-root pulp)
    pulp: 'M42.0257 57.817C47.6443 47.9604 55.5102 24.5289 42.0257 9.65659C40.5274 7.78507 43.961 19.3885 43.3367 30.8048C42.5876 38.1661 40.5274 51.5788 34.6592 52.8265C31.08 51.9738 23.4096 46.8624 21.362 33.2378C19.558 21.2342 19.5274 12.3845 19.8019 8.34397C19.8479 7.66557 19.2514 7.21362 18.7915 7.71442C16.2381 10.4948 13.7475 20.5912 15.4313 33.2378C17.8659 44.0926 24.7955 56.7565 26.8556 57.817',
    highlight: [],
    gumLine: 'M 0,63 Q 33,73 67,63'
  }
}

// ============================================================================
// OCCLUSAL VIEW PATHS (ViewBox: 0 0 50 50)
// Circular design with 5 treatment zones: center (O) + 4 outer sectors (M,D,V,L)
// All teeth in the same quadrant have identical shape, other quadrants are symmetric
// ============================================================================

interface OcclusalPaths {
  outline: string
  highlight: string[]
  surfaces: Record<string, string>
}

// Circular surfaces for all teeth
// Center: (25, 25), Outer radius: 22, Inner radius: 10
// Diagonal dividers at 45°, 135°, 225°, 315°
// Outer points: (41,9), (9,9), (9,41), (41,41)
// Inner points: (32,18), (18,18), (18,32), (32,32)
const CIRCULAR_SURFACES = {
  // O (occlusal/incisal center): inner circle
  O: 'M 35,25 A 10,10 0 1,1 15,25 A 10,10 0 1,1 35,25 Z',
  // V (vestibular/buccal): top sector (45° to 135°)
  V: 'M 32,18 L 41,9 A 22,22 0 0,0 9,9 L 18,18 A 10,10 0 0,1 32,18 Z',
  // L (lingual/palatal): bottom sector (225° to 315°)
  L: 'M 18,32 L 9,41 A 22,22 0 0,0 41,41 L 32,32 A 10,10 0 0,1 18,32 Z',
  // M (mesial): left sector (135° to 225°)
  M: 'M 18,18 L 9,9 A 22,22 0 0,0 9,41 L 18,32 A 10,10 0 0,1 18,18 Z',
  // D (distal): right sector (315° to 45°)
  D: 'M 32,32 L 41,41 A 22,22 0 0,0 41,9 L 32,18 A 10,10 0 0,1 32,32 Z'
}

// Circular outline for all teeth
const CIRCULAR_OUTLINE = 'M 25,3 A 22,22 0 1,1 25,47 A 22,22 0 1,1 25,3 Z'

// Radial dividers and inner circle (for visual reference, rendered as highlight lines)
const CIRCULAR_DIVIDERS = [
  'M 18,18 L 9,9', // Top-left diagonal
  'M 32,18 L 41,9', // Top-right diagonal
  'M 18,32 L 9,41', // Bottom-left diagonal
  'M 32,32 L 41,41', // Bottom-right diagonal
  'M 35,25 A 10,10 0 1,1 15,25 A 10,10 0 1,1 35,25' // Inner circle outline
]

// All teeth use the same circular occlusal view
// Quadrant symmetry is handled by CSS transform (napkin unfolding)
const OCCLUSAL_PATHS_BY_POSITION: Record<number, OcclusalPaths> = {
  1: { outline: CIRCULAR_OUTLINE, highlight: CIRCULAR_DIVIDERS, surfaces: CIRCULAR_SURFACES },
  2: { outline: CIRCULAR_OUTLINE, highlight: CIRCULAR_DIVIDERS, surfaces: CIRCULAR_SURFACES },
  3: { outline: CIRCULAR_OUTLINE, highlight: CIRCULAR_DIVIDERS, surfaces: CIRCULAR_SURFACES },
  4: { outline: CIRCULAR_OUTLINE, highlight: CIRCULAR_DIVIDERS, surfaces: CIRCULAR_SURFACES },
  5: { outline: CIRCULAR_OUTLINE, highlight: CIRCULAR_DIVIDERS, surfaces: CIRCULAR_SURFACES },
  6: { outline: CIRCULAR_OUTLINE, highlight: CIRCULAR_DIVIDERS, surfaces: CIRCULAR_SURFACES },
  7: { outline: CIRCULAR_OUTLINE, highlight: CIRCULAR_DIVIDERS, surfaces: CIRCULAR_SURFACES },
  8: { outline: CIRCULAR_OUTLINE, highlight: CIRCULAR_DIVIDERS, surfaces: CIRCULAR_SURFACES }
}

// ============================================================================
// DECIDUOUS TEETH (Simplified versions using permanent tooth shapes)
// ============================================================================

// Map deciduous positions to permanent tooth shapes
const DECIDUOUS_TO_PERMANENT_MAP: Record<number, number> = {
  1: 1, // Deciduous central incisor → Central incisor
  2: 2, // Deciduous lateral incisor → Lateral incisor
  3: 3, // Deciduous canine → Canine
  4: 6, // First deciduous molar → First molar shape
  5: 7 // Second deciduous molar → Second molar shape
}

// ============================================================================
// PATH GETTER FUNCTIONS
// ============================================================================

export function getLateralPath(toothNumber: number): LateralPaths {
  const isDeciduous = isDeciduousTooth(toothNumber)
  let position = getToothPosition(toothNumber)

  // Map deciduous positions to permanent shapes
  if (isDeciduous) {
    position = DECIDUOUS_TO_PERMANENT_MAP[position] || 1
  }

  return LATERAL_PATHS_BY_POSITION[position] || LATERAL_PATHS_BY_POSITION[1]
}

export function getOcclusalPath(toothNumber: number): OcclusalPaths {
  const isDeciduous = isDeciduousTooth(toothNumber)
  let position = getToothPosition(toothNumber)

  // Map deciduous positions to permanent shapes
  if (isDeciduous) {
    position = DECIDUOUS_TO_PERMANENT_MAP[position] || 1
  }

  return OCCLUSAL_PATHS_BY_POSITION[position] || OCCLUSAL_PATHS_BY_POSITION[1]
}

// ============================================================================
// TREATMENT OVERLAYS
// ============================================================================

export const TREATMENT_OVERLAYS = {
  implant: {
    fixture: 'M 22,35 L 20,75 Q 30,82 40,75 L 38,35 Z',
    threads: [
      'M 18,42 L 42,42',
      'M 16,52 L 44,52',
      'M 14,62 L 46,62',
      'M 16,72 L 44,72'
    ],
    abutment: 'M 24,28 L 24,35 L 36,35 L 36,28 C 36,24 24,24 24,28 Z',
    head: 'M 22,20 Q 30,16 38,20 L 38,28 C 38,30 22,30 22,28 Z'
  },
  crownOverlay: {
    outer: 'M 10,50 C 5,40 5,25 10,15 C 18,5 25,3 30,3 C 35,3 42,5 50,15 C 55,25 55,40 50,50 Z',
    metalBand: 'M 12,50 Q 30,55 48,50 L 50,40 Q 30,35 10,40 Z'
  },
  rootCanal: {
    indicator: 'M 30,55 m -5,0 a 5,5 0 1,0 10,0 a 5,5 0 1,0 -10,0',
    canalLines: [
      'M 30,45 L 30,65',
      'M 26,50 L 34,50',
      'M 26,60 L 34,60'
    ]
  },
  post: {
    shaft: 'M 28,35 L 28,60 L 32,60 L 32,35 Z'
  },
  veneer: {
    surface: 'M 15,55 C 10,45 10,35 15,25 Q 30,20 45,25 C 50,35 50,45 45,55 Q 30,60 15,55 Z'
  },
  missing: {
    line1: 'M 10,10 L 50,90',
    line2: 'M 50,10 L 10,90'
  },
  extraction: {
    line1: 'M 15,15 L 45,85',
    line2: 'M 45,15 L 15,85',
    dashArray: '5,4'
  }
}

// ============================================================================
// STATUS STYLES
// ============================================================================

export const STATUS_STYLES: Record<string, { opacity: number, border: string, borderWidth: number, borderDash?: string }> = {
  completed: {
    opacity: 1,
    border: 'none',
    borderWidth: 0
  },
  performed: {
    opacity: 1,
    border: 'none',
    borderWidth: 0
  },
  planned: {
    opacity: 0.7,
    border: '#EF4444',
    borderWidth: 2,
    borderDash: '4,2'
  },
  in_progress: {
    opacity: 0.85,
    border: '#F59E0B',
    borderWidth: 1.5
  },
  preexisting: {
    opacity: 0.9,
    border: '#6B7280',
    borderWidth: 1
  }
}
