/**
 * Shared types for the periodontogram frontend layer.
 *
 * Mirrors the Pydantic shapes in
 * ``backend/app/modules/periodontogram/schemas.py``.
 */

export type SiteCode = 'MV' | 'V' | 'DV' | 'ML' | 'L' | 'DL'

export const SITE_CODES: readonly SiteCode[] = ['MV', 'V', 'DV', 'ML', 'L', 'DL'] as const
export const VESTIBULAR_SITES: readonly SiteCode[] = ['MV', 'V', 'DV'] as const
export const PALATAL_SITES: readonly SiteCode[] = ['ML', 'L', 'DL'] as const

export type Prognosis = 'good' | 'fair' | 'poor' | 'hopeless'
export type Furcation = '0' | 'I' | 'II' | 'III'
export type SnapshotStatus = 'draft' | 'closed'

export interface PerioSite {
  site_code: SiteCode
  probing_depth_mm: number | null
  gingival_margin_mm: number | null
  bleeding_on_probing: boolean
  plaque: boolean
  suppuration: boolean
}

export interface PerioTooth {
  tooth_number: number
  is_present: boolean
  is_implant: boolean
  mobility: number | null
  prognosis: Prognosis | null
  furcation_buccal: Furcation | null
  furcation_lingual: Furcation | null
  keratinized_gingiva_mm: number | null
  sites: PerioSite[]
}

export interface PerioIndices {
  bop_pct: number
  pi_pct: number
  cal_mean_mm: number
  deep_pockets_count: number
}

export interface PerioSnapshotSummary {
  id: string
  patient_id: string
  status: SnapshotStatus
  recorded_at: string
  closed_at: string | null
}

export interface PerioSnapshotDetail extends PerioSnapshotSummary {
  recorded_by: string
  closed_by: string | null
  notes: string | null
  indices: PerioIndices | null
  teeth: PerioTooth[]
}

export interface PerioTimelineEntry {
  snapshot_id: string
  date: string
  change_count: number
}

export interface PerioTimelineResponse {
  dates: PerioTimelineEntry[]
  draft: PerioSnapshotSummary | null
}
