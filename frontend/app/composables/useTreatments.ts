/**
 * useTreatments - CRUD for Treatment (header + teeth[] model)
 *
 * Single unified endpoint `/patients/{id}/treatments`. Bridges and uniform multi-tooth
 * treatments use the `mode` parameter; single-tooth is the default.
 */

import type {
  ApiResponse,
  PaginatedResponse,
  ToothRecordWithTreatments,
  Treatment,
  TreatmentCreate,
  TreatmentStatus,
  TreatmentUpdate
} from '~/types'

// ---------------------------------------------------------------------------
// Backend <-> frontend status mapping.
// Backend: 'planned' | 'performed'. Frontend: 'planned' | 'existing' (clinical UI).
// ---------------------------------------------------------------------------

function toBackendStatus(v: TreatmentStatus | undefined): 'planned' | 'performed' | undefined {
  if (v === 'existing') return 'performed'
  return v
}

function fromBackendStatus(v: string | undefined | null): TreatmentStatus {
  return v === 'performed' ? 'existing' : 'planned'
}

function normalizeTreatment<T extends { status: string }>(treatment: T): T {
  return { ...treatment, status: fromBackendStatus(treatment.status) }
}

export function useTreatments() {
  const api = useApi()
  const toast = useToast()
  const { t } = useI18n()

  // ============================================================================
  // State
  // ============================================================================

  const treatments = ref<Treatment[]>([])
  const loading = ref(false)

  // ============================================================================
  // Helpers
  // ============================================================================

  /** Treatments whose teeth[] includes the given tooth. */
  function getToothTreatments(toothNumber: number): Treatment[] {
    return treatments.value.filter(t =>
      t.teeth.some(tt => tt.tooth_number === toothNumber)
    )
  }

  function getTreatmentsByStatus(status: TreatmentStatus): Treatment[] {
    return treatments.value.filter(t => t.status === status)
  }

  function updateLocalTreatment(updated: Treatment): void {
    const index = treatments.value.findIndex(t => t.id === updated.id)
    if (index >= 0) {
      treatments.value[index] = updated
    }
  }

  function removeLocalTreatment(treatmentId: string): void {
    treatments.value = treatments.value.filter(t => t.id !== treatmentId)
  }

  // ============================================================================
  // API
  // ============================================================================

  async function fetchTreatments(
    patientId: string,
    filters?: { status?: TreatmentStatus, tooth_number?: number, clinical_type?: string }
  ): Promise<void> {
    loading.value = true
    try {
      let url = `/api/v1/odontogram/patients/${patientId}/treatments`
      const params = new URLSearchParams()
      if (filters?.status) params.append('status', filters.status)
      if (filters?.tooth_number) params.append('tooth_number', String(filters.tooth_number))
      if (filters?.clinical_type) params.append('clinical_type', filters.clinical_type)
      if (params.toString()) url += `?${params.toString()}`

      const response = await api.get<PaginatedResponse<Treatment>>(url)
      treatments.value = response.data.map(normalizeTreatment)
    } catch (err) {
      console.error('Error fetching treatments:', err)
    } finally {
      loading.value = false
    }
  }

  /** Unified create: single-tooth, bridge or uniform multi-tooth. */
  async function createTreatment(
    patientId: string,
    payload: TreatmentCreate
  ): Promise<Treatment | null> {
    try {
      const body = {
        ...payload,
        status: toBackendStatus(payload.status)
      }
      const response = await api.post<ApiResponse<Treatment>>(
        `/api/v1/odontogram/patients/${patientId}/treatments`,
        body as unknown as Record<string, unknown>
      )
      const normalized = normalizeTreatment(response.data)
      treatments.value.push(normalized)
      return normalized
    } catch (err) {
      toast.add({
        title: t('common.error'),
        description: t('odontogram.messages.error'),
        color: 'error'
      })
      console.error('Error creating treatment:', err)
      return null
    }
  }

  async function updateTreatment(
    treatmentId: string,
    data: TreatmentUpdate
  ): Promise<Treatment | null> {
    try {
      const body = { ...data, status: toBackendStatus(data.status) }
      const response = await api.put<ApiResponse<Treatment>>(
        `/api/v1/odontogram/treatments/${treatmentId}`,
        body as Record<string, unknown>
      )
      const normalized = normalizeTreatment(response.data)
      updateLocalTreatment(normalized)
      toast.add({ title: t('odontogram.messages.updated'), color: 'success' })
      return normalized
    } catch (err) {
      toast.add({
        title: t('common.error'),
        description: t('odontogram.messages.error'),
        color: 'error'
      })
      console.error('Error updating treatment:', err)
      return null
    }
  }

  async function deleteTreatment(treatmentId: string): Promise<boolean> {
    try {
      await api.del(`/api/v1/odontogram/treatments/${treatmentId}`)
      removeLocalTreatment(treatmentId)
      toast.add({ title: t('odontogram.treatments.treatmentDeleted'), color: 'success' })
      return true
    } catch (err) {
      toast.add({
        title: t('common.error'),
        description: t('odontogram.messages.error'),
        color: 'error'
      })
      console.error('Error deleting treatment:', err)
      return false
    }
  }

  async function performTreatment(
    treatmentId: string,
    notes?: string
  ): Promise<Treatment | null> {
    try {
      const response = await api.patch<ApiResponse<Treatment>>(
        `/api/v1/odontogram/treatments/${treatmentId}/perform`,
        { notes } as Record<string, unknown>
      )
      const normalized = normalizeTreatment(response.data)
      updateLocalTreatment(normalized)
      toast.add({ title: t('odontogram.treatments.treatmentPerformed'), color: 'success' })
      return normalized
    } catch (err) {
      toast.add({
        title: t('common.error'),
        description: t('odontogram.messages.error'),
        color: 'error'
      })
      console.error('Error performing treatment:', err)
      return null
    }
  }

  async function fetchToothWithTreatments(
    patientId: string,
    toothNumber: number
  ): Promise<ToothRecordWithTreatments | null> {
    try {
      const response = await api.get<ApiResponse<ToothRecordWithTreatments>>(
        `/api/v1/odontogram/patients/${patientId}/teeth/${toothNumber}/full`
      )
      return {
        ...response.data,
        treatments: (response.data.treatments || []).map(normalizeTreatment)
      }
    } catch (err) {
      console.error('Error fetching tooth with treatments:', err)
      return null
    }
  }

  function reset(): void {
    treatments.value = []
  }

  return {
    // State
    treatments,
    loading,
    // Helpers
    getToothTreatments,
    getTreatmentsByStatus,
    // API
    fetchTreatments,
    createTreatment,
    updateTreatment,
    deleteTreatment,
    performTreatment,
    fetchToothWithTreatments,
    reset
  }
}
