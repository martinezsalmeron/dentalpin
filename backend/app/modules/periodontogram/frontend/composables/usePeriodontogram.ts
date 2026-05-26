/**
 * State + API client for a single patient's periodontogram.
 *
 * Lightweight wrapper around `useApi()`. PR-4 only needs timeline
 * loading and draft creation — full snapshot editing flows wire up in
 * PR-5 / PR-6 once the chart components exist.
 */

import { computed, ref } from 'vue'
import type {
  PerioSite,
  PerioSnapshotDetail,
  PerioTimelineResponse,
  SiteCode
} from '../types'

interface ApiResponse<T> {
  data: T
  message?: string | null
}

export function usePeriodontogram(patientId: () => string) {
  const api = useApi()

  const timeline = ref<PerioTimelineResponse | null>(null)
  const currentSnapshot = ref<PerioSnapshotDetail | null>(null)
  const viewingDate = ref<string | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  const hasDraft = computed(() => Boolean(timeline.value?.draft))
  const closedCount = computed(() => timeline.value?.dates.length ?? 0)
  const isEmpty = computed(() => !hasDraft.value && closedCount.value === 0)

  async function fetchTimeline(): Promise<void> {
    isLoading.value = true
    error.value = null
    try {
      const response = await api.get<ApiResponse<PerioTimelineResponse>>(
        `/api/v1/periodontogram/patients/${patientId()}/timeline`
      )
      timeline.value = response.data
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'load_failed'
    } finally {
      isLoading.value = false
    }
  }

  async function fetchDraft(): Promise<void> {
    const response = await api.get<ApiResponse<PerioSnapshotDetail | null>>(
      `/api/v1/periodontogram/patients/${patientId()}/draft`
    )
    currentSnapshot.value = response.data
    viewingDate.value = null
  }

  async function fetchSnapshot(snapshotId: string): Promise<void> {
    const response = await api.get<ApiResponse<PerioSnapshotDetail>>(
      `/api/v1/periodontogram/snapshots/${snapshotId}`
    )
    currentSnapshot.value = response.data
  }

  // Optimistic mutators — apply a per-tooth or per-site patch directly
  // onto `currentSnapshot.value` so the UI updates on the next frame,
  // before the debounced PATCH lands. Caller (the chart) is responsible
  // for queueing the network write separately.
  function applySitePatch(
    toothNumber: number,
    siteCode: SiteCode,
    patch: Record<string, unknown>
  ): void {
    const snap = currentSnapshot.value
    if (!snap) return
    const tooth = snap.teeth.find(t => t.tooth_number === toothNumber)
    if (!tooth) return
    let site = tooth.sites.find(s => s.site_code === siteCode)
    if (!site) {
      // Backend creates the PeriodontogramSite row lazily on the first
      // PATCH (see service.py: `update_site`). Mirror that here so the
      // optimistic update has a target to mutate — otherwise the very
      // first edit of a site would no-op locally and the marker would
      // only repaint after a refetch.
      site = {
        site_code: siteCode,
        probing_depth_mm: null,
        gingival_margin_mm: null,
        bleeding_on_probing: false,
        plaque: false,
        suppuration: false
      } satisfies PerioSite
      tooth.sites.push(site)
    }
    for (const [key, value] of Object.entries(patch)) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (site as any)[key] = value
    }
  }

  function applyToothPatch(toothNumber: number, patch: Record<string, unknown>): void {
    const snap = currentSnapshot.value
    if (!snap) return
    const tooth = snap.teeth.find(t => t.tooth_number === toothNumber)
    if (!tooth) return
    for (const [key, value] of Object.entries(patch)) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (tooth as any)[key] = value
    }
  }

  async function startDraft(): Promise<PerioSnapshotDetail> {
    const response = await api.post<ApiResponse<PerioSnapshotDetail>>(
      `/api/v1/periodontogram/patients/${patientId()}/draft`,
      {}
    )
    currentSnapshot.value = response.data
    await fetchTimeline()
    return response.data
  }

  return {
    timeline,
    currentSnapshot,
    viewingDate,
    isLoading,
    error,
    hasDraft,
    closedCount,
    isEmpty,
    fetchTimeline,
    fetchDraft,
    fetchSnapshot,
    startDraft,
    applySitePatch,
    applyToothPatch
  }
}
