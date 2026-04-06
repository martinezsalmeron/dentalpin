import type {
  ApiResponse,
  BulkToothUpdate,
  OdontogramData,
  OdontogramHistoryEntry,
  PaginatedResponse,
  Surface,
  ToothCondition,
  ToothRecord,
  ToothRecordUpdate,
  ToothRecordWithTreatments,
  Treatment,
  TreatmentCreate,
  TreatmentStatus,
  TreatmentUpdate
} from '~/types'

// FDI Notation constants
// Visual layout: molars on edges, incisors in center (patient-facing view)
export const PERMANENT_TEETH = {
  upperRight: [18, 17, 16, 15, 14, 13, 12, 11], // Molars→Incisors (left side of screen)
  upperLeft: [21, 22, 23, 24, 25, 26, 27, 28], // Incisors→Molars (right side of screen)
  lowerRight: [48, 47, 46, 45, 44, 43, 42, 41], // Molars→Incisors (left side of screen)
  lowerLeft: [31, 32, 33, 34, 35, 36, 37, 38] // Incisors→Molars (right side of screen)
}

export const DECIDUOUS_TEETH = {
  upperRight: [55, 54, 53, 52, 51], // Molars→Incisors (left side of screen)
  upperLeft: [61, 62, 63, 64, 65], // Incisors→Molars (right side of screen)
  lowerRight: [85, 84, 83, 82, 81], // Molars→Incisors (left side of screen)
  lowerLeft: [71, 72, 73, 74, 75] // Incisors→Molars (right side of screen)
}

// Default condition colors (fallback if not provided by API)
export const CONDITION_COLORS: Record<ToothCondition, string> = {
  healthy: '#FFFFFF',
  caries: '#EF4444',
  filling: '#3B82F6',
  crown: '#F59E0B',
  missing: '#9CA3AF',
  root_canal: '#8B5CF6',
  implant: '#10B981',
  bridge_pontic: '#F97316',
  bridge_abutment: '#FBBF24',
  extraction_indicated: '#DC2626',
  sealant: '#06B6D4',
  fracture: '#BE185D'
}

// Surface labels
export const SURFACE_LABELS: Record<Surface, string> = {
  M: 'Mesial',
  D: 'Distal',
  O: 'Occlusal',
  V: 'Vestibular',
  L: 'Lingual'
}

export function useOdontogram() {
  const api = useApi()
  const toast = useToast()
  const { t } = useI18n()

  // State
  const odontogramData = ref<OdontogramData | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Computed
  const teeth = computed(() => odontogramData.value?.teeth || [])
  const conditionColors = computed(() => odontogramData.value?.condition_colors || CONDITION_COLORS)
  const availableConditions = computed(() => odontogramData.value?.available_conditions || Object.keys(CONDITION_COLORS) as ToothCondition[])

  // Get tooth record by number
  function getToothRecord(toothNumber: number): ToothRecord | undefined {
    return teeth.value.find(t => t.tooth_number === toothNumber)
  }

  // Get condition color
  function getConditionColor(condition: ToothCondition): string {
    return conditionColors.value[condition] || '#FFFFFF'
  }

  // Check if tooth is permanent or deciduous
  function isDeciduousTooth(toothNumber: number): boolean {
    const deciduousNumbers = [
      ...DECIDUOUS_TEETH.upperRight,
      ...DECIDUOUS_TEETH.upperLeft,
      ...DECIDUOUS_TEETH.lowerLeft,
      ...DECIDUOUS_TEETH.lowerRight
    ]
    return deciduousNumbers.includes(toothNumber)
  }

  // Fetch odontogram for a patient
  async function fetchOdontogram(patientId: string): Promise<void> {
    loading.value = true
    error.value = null

    try {
      const response = await api.get<ApiResponse<OdontogramData>>(
        `/api/v1/odontogram/patients/${patientId}/odontogram`
      )
      odontogramData.value = response.data
    } catch (err) {
      error.value = 'Failed to load odontogram'
      console.error('Error fetching odontogram:', err)
    } finally {
      loading.value = false
    }
  }

  // Update a single tooth
  async function updateTooth(
    patientId: string,
    toothNumber: number,
    update: ToothRecordUpdate
  ): Promise<ToothRecord | null> {
    try {
      const response = await api.put<ApiResponse<ToothRecord>>(
        `/api/v1/odontogram/patients/${patientId}/teeth/${toothNumber}`,
        update as Record<string, unknown>
      )

      // Update local state
      if (odontogramData.value) {
        const index = odontogramData.value.teeth.findIndex(t => t.tooth_number === toothNumber)
        if (index >= 0) {
          odontogramData.value.teeth[index] = response.data
        } else {
          odontogramData.value.teeth.push(response.data)
        }
      }

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
      console.error('Error updating tooth:', err)
      return null
    }
  }

  // Bulk update multiple teeth
  async function bulkUpdateTeeth(
    patientId: string,
    updates: BulkToothUpdate[]
  ): Promise<ToothRecord[] | null> {
    try {
      const response = await api.patch<ApiResponse<ToothRecord[]>>(
        `/api/v1/odontogram/patients/${patientId}/teeth/bulk`,
        { updates } as Record<string, unknown>
      )

      // Update local state
      if (odontogramData.value) {
        for (const updatedTooth of response.data) {
          const index = odontogramData.value.teeth.findIndex(
            t => t.tooth_number === updatedTooth.tooth_number
          )
          if (index >= 0) {
            odontogramData.value.teeth[index] = updatedTooth
          } else {
            odontogramData.value.teeth.push(updatedTooth)
          }
        }
      }

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
      console.error('Error bulk updating teeth:', err)
      return null
    }
  }

  // Fetch history for a specific tooth
  async function fetchToothHistory(
    patientId: string,
    toothNumber: number,
    page = 1,
    pageSize = 50
  ): Promise<PaginatedResponse<OdontogramHistoryEntry> | null> {
    try {
      const response = await api.get<PaginatedResponse<OdontogramHistoryEntry>>(
        `/api/v1/odontogram/patients/${patientId}/teeth/${toothNumber}/history?page=${page}&page_size=${pageSize}`
      )
      return response
    } catch (err) {
      console.error('Error fetching tooth history:', err)
      return null
    }
  }

  // Fetch full odontogram history for patient
  async function fetchPatientHistory(
    patientId: string,
    page = 1,
    pageSize = 50
  ): Promise<PaginatedResponse<OdontogramHistoryEntry> | null> {
    try {
      const response = await api.get<PaginatedResponse<OdontogramHistoryEntry>>(
        `/api/v1/odontogram/patients/${patientId}/history?page=${page}&page_size=${pageSize}`
      )
      return response
    } catch (err) {
      console.error('Error fetching patient history:', err)
      return null
    }
  }

  // Reset local state
  function reset(): void {
    odontogramData.value = null
    error.value = null
  }

  // ============================================================================
  // Treatment Methods
  // ============================================================================

  // State for treatments
  const treatments = ref<Treatment[]>([])
  const treatmentsLoading = ref(false)

  // Fetch treatments for a patient
  async function fetchTreatments(
    patientId: string,
    filters?: { status?: TreatmentStatus, tooth_number?: number }
  ): Promise<void> {
    treatmentsLoading.value = true
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
      treatmentsLoading.value = false
    }
  }

  // Create a new treatment
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

      // Add to local state
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

  // Update a treatment
  async function updateTreatment(
    treatmentId: string,
    data: TreatmentUpdate
  ): Promise<Treatment | null> {
    try {
      const response = await api.put<ApiResponse<Treatment>>(
        `/api/v1/odontogram/treatments/${treatmentId}`,
        data as Record<string, unknown>
      )

      // Update local state
      const index = treatments.value.findIndex(t => t.id === treatmentId)
      if (index >= 0) {
        treatments.value[index] = response.data
      }

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

  // Delete a treatment
  async function deleteTreatment(treatmentId: string): Promise<boolean> {
    try {
      await api.del(`/api/v1/odontogram/treatments/${treatmentId}`)

      // Remove from local state
      treatments.value = treatments.value.filter(t => t.id !== treatmentId)

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

  // Mark treatment as performed
  async function performTreatment(
    treatmentId: string,
    notes?: string
  ): Promise<Treatment | null> {
    try {
      const response = await api.patch<ApiResponse<Treatment>>(
        `/api/v1/odontogram/treatments/${treatmentId}/perform`,
        { notes } as Record<string, unknown>
      )

      // Update local state
      const index = treatments.value.findIndex(t => t.id === treatmentId)
      if (index >= 0) {
        treatments.value[index] = response.data
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
      console.error('Error performing treatment:', err)
      return null
    }
  }

  // Fetch tooth with all treatments
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

  // Get treatments for a specific tooth from local state
  function getToothTreatments(toothNumber: number): Treatment[] {
    return treatments.value.filter(t => t.tooth_number === toothNumber)
  }

  // Get treatments by status
  function getTreatmentsByStatus(status: TreatmentStatus): Treatment[] {
    return treatments.value.filter(t => t.status === status)
  }

  return {
    // State
    odontogramData,
    teeth,
    loading,
    error,
    conditionColors,
    availableConditions,
    treatments,
    treatmentsLoading,

    // Methods
    fetchOdontogram,
    updateTooth,
    bulkUpdateTeeth,
    fetchToothHistory,
    fetchPatientHistory,
    getToothRecord,
    getConditionColor,
    isDeciduousTooth,
    reset,

    // Treatment methods
    fetchTreatments,
    createTreatment,
    updateTreatment,
    deleteTreatment,
    performTreatment,
    fetchToothWithTreatments,
    getToothTreatments,
    getTreatmentsByStatus,

    // Constants
    PERMANENT_TEETH,
    DECIDUOUS_TEETH,
    CONDITION_COLORS,
    SURFACE_LABELS
  }
}
