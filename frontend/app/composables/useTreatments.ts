/**
 * useTreatments - Manages dental treatments CRUD operations
 *
 * Handles:
 * - Fetching treatments for a patient
 * - Creating, updating, deleting treatments
 * - Performing planned treatments
 * - Fetching tooth with all treatments
 */

import type {
  ApiResponse,
  PaginatedResponse,
  ToothRecordWithTreatments,
  Treatment,
  TreatmentCreate,
  TreatmentGroupCreate,
  TreatmentStatus,
  TreatmentUpdate
} from '~/types'

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

  /** Get treatments for a specific tooth from local state */
  function getToothTreatments(toothNumber: number): Treatment[] {
    return treatments.value.filter(t => t.tooth_number === toothNumber)
  }

  /** Get treatments by status */
  function getTreatmentsByStatus(status: TreatmentStatus): Treatment[] {
    return treatments.value.filter(t => t.status === status)
  }

  /** Update treatment in local state */
  function updateLocalTreatment(updated: Treatment): void {
    const index = treatments.value.findIndex(t => t.id === updated.id)
    if (index >= 0) {
      treatments.value[index] = updated
    }
  }

  /** Remove treatment from local state */
  function removeLocalTreatment(treatmentId: string): void {
    treatments.value = treatments.value.filter(t => t.id !== treatmentId)
  }

  // ============================================================================
  // API Methods
  // ============================================================================

  /** Fetch treatments for a patient */
  async function fetchTreatments(
    patientId: string,
    filters?: { status?: TreatmentStatus, tooth_number?: number }
  ): Promise<void> {
    loading.value = true
    try {
      let url = `/api/v1/odontogram/patients/${patientId}/treatments`
      const params = new URLSearchParams()
      if (filters?.status) params.append('status', filters.status)
      if (filters?.tooth_number) params.append('tooth_number', String(filters.tooth_number))
      if (params.toString()) url += `?${params.toString()}`

      const response = await api.get<PaginatedResponse<Treatment>>(url)
      treatments.value = response.data
    } catch (err) {
      console.error('Error fetching treatments:', err)
    } finally {
      loading.value = false
    }
  }

  /** Create a new treatment */
  async function createTreatment(
    patientId: string,
    toothNumber: number,
    data: TreatmentCreate
  ): Promise<Treatment | null> {
    try {
      const response = await api.post<ApiResponse<Treatment>>(
        `/api/v1/odontogram/patients/${patientId}/teeth/${toothNumber}/treatments`,
        data as Record<string, unknown>
      )

      treatments.value.push(response.data)

      toast.add({
        title: t('odontogram.treatments.treatmentAdded'),
        color: 'success'
      })

      return response.data
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

  /** Update a treatment */
  async function updateTreatment(
    treatmentId: string,
    data: TreatmentUpdate
  ): Promise<Treatment | null> {
    try {
      const response = await api.put<ApiResponse<Treatment>>(
        `/api/v1/odontogram/treatments/${treatmentId}`,
        data as Record<string, unknown>
      )

      updateLocalTreatment(response.data)

      toast.add({
        title: t('odontogram.messages.updated'),
        color: 'success'
      })

      return response.data
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

  /** Delete a treatment */
  async function deleteTreatment(treatmentId: string): Promise<boolean> {
    try {
      await api.del(`/api/v1/odontogram/treatments/${treatmentId}`)

      removeLocalTreatment(treatmentId)

      toast.add({
        title: t('odontogram.treatments.treatmentDeleted'),
        color: 'success'
      })

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

  /** Mark treatment as performed (existing) */
  async function performTreatment(
    treatmentId: string,
    notes?: string
  ): Promise<Treatment | null> {
    try {
      const response = await api.patch<ApiResponse<Treatment>>(
        `/api/v1/odontogram/treatments/${treatmentId}/perform`,
        { notes } as Record<string, unknown>
      )

      updateLocalTreatment(response.data)

      toast.add({
        title: t('odontogram.treatments.treatmentPerformed'),
        color: 'success'
      })

      return response.data
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

  /** Fetch tooth with all treatments */
  async function fetchToothWithTreatments(
    patientId: string,
    toothNumber: number
  ): Promise<ToothRecordWithTreatments | null> {
    try {
      const response = await api.get<ApiResponse<ToothRecordWithTreatments>>(
        `/api/v1/odontogram/patients/${patientId}/teeth/${toothNumber}/full`
      )
      return response.data
    } catch (err) {
      console.error('Error fetching tooth with treatments:', err)
      return null
    }
  }

  // ============================================================================
  // Multi-tooth treatment groups
  // ============================================================================

  /** Create an atomic multi-tooth treatment group (bridge, splint, etc). */
  async function createTreatmentGroup(
    patientId: string,
    payload: TreatmentGroupCreate
  ): Promise<Treatment[] | null> {
    try {
      const response = await api.post<ApiResponse<Treatment[]>>(
        `/api/v1/odontogram/patients/${patientId}/treatment-groups`,
        payload as unknown as Record<string, unknown>
      )

      treatments.value.push(...response.data)

      toast.add({
        title: t('odontogram.treatments.treatmentAdded'),
        color: 'success'
      })

      return response.data
    } catch (err) {
      toast.add({
        title: t('common.error'),
        description: t('odontogram.messages.error'),
        color: 'error'
      })
      console.error('Error creating treatment group:', err)
      return null
    }
  }

  /** Mark every member of a group as performed. */
  async function performTreatmentGroup(
    groupId: string,
    notes?: string
  ): Promise<Treatment[] | null> {
    try {
      const response = await api.patch<ApiResponse<Treatment[]>>(
        `/api/v1/odontogram/treatment-groups/${groupId}/perform`,
        (notes ? { notes } : {}) as Record<string, unknown>
      )
      for (const updated of response.data) {
        updateLocalTreatment(updated)
      }
      toast.add({
        title: t('odontogram.treatments.treatmentPerformed'),
        color: 'success'
      })
      return response.data
    } catch (err) {
      toast.add({
        title: t('common.error'),
        description: t('odontogram.messages.error'),
        color: 'error'
      })
      console.error('Error performing treatment group:', err)
      return null
    }
  }

  /** Soft-delete every member of a group atomically. */
  async function deleteTreatmentGroup(groupId: string): Promise<boolean> {
    try {
      await api.del(`/api/v1/odontogram/treatment-groups/${groupId}`)
      treatments.value = treatments.value.filter(t => t.treatment_group_id !== groupId)
      toast.add({
        title: t('odontogram.treatments.treatmentDeleted'),
        color: 'success'
      })
      return true
    } catch (err) {
      toast.add({
        title: t('common.error'),
        description: t('odontogram.messages.error'),
        color: 'error'
      })
      console.error('Error deleting treatment group:', err)
      return false
    }
  }

  /** Return every treatment sharing the given group id. */
  function getGroupMembers(groupId: string): Treatment[] {
    return treatments.value.filter(t => t.treatment_group_id === groupId)
  }

  /** Return the group id a tooth participates in, if any. */
  function getGroupIdForTooth(toothNumber: number): string | null {
    const member = treatments.value.find(
      t => t.tooth_number === toothNumber && t.treatment_group_id
    )
    return member?.treatment_group_id ?? null
  }

  /** Reset local state */
  function reset(): void {
    treatments.value = []
  }

  // ============================================================================
  // Return
  // ============================================================================

  return {
    // State
    treatments,
    loading,

    // Helpers
    getToothTreatments,
    getTreatmentsByStatus,
    getGroupMembers,
    getGroupIdForTooth,

    // API
    fetchTreatments,
    createTreatment,
    updateTreatment,
    deleteTreatment,
    performTreatment,
    fetchToothWithTreatments,
    createTreatmentGroup,
    performTreatmentGroup,
    deleteTreatmentGroup,
    reset
  }
}
