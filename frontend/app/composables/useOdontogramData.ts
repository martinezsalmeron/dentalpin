/**
 * useOdontogramData - Manages odontogram tooth records and conditions
 *
 * Handles:
 * - Fetching odontogram data for a patient
 * - Updating individual teeth
 * - Bulk tooth updates
 * - Tooth history
 */

import type {
  ApiResponse,
  BulkToothUpdate,
  OdontogramData,
  OdontogramHistoryEntry,
  PaginatedResponse,
  ToothCondition,
  ToothRecord,
  ToothRecordUpdate
} from '~/types'
import { ALL_DECIDUOUS_NUMBERS, CONDITION_COLORS } from '~/constants/odontogram'

export function useOdontogramData() {
  const api = useApi()
  const toast = useToast()
  const { t } = useI18n()

  // ============================================================================
  // State
  // ============================================================================

  const odontogramData = ref<OdontogramData | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // ============================================================================
  // Computed
  // ============================================================================

  const teeth = computed(() => odontogramData.value?.teeth || [])

  const conditionColors = computed(() =>
    odontogramData.value?.condition_colors || CONDITION_COLORS
  )

  const availableConditions = computed(() =>
    odontogramData.value?.available_conditions || Object.keys(CONDITION_COLORS) as ToothCondition[]
  )

  // ============================================================================
  // Helpers
  // ============================================================================

  /** Get tooth record by number */
  function getToothRecord(toothNumber: number): ToothRecord | undefined {
    return teeth.value.find(t => t.tooth_number === toothNumber)
  }

  /** Get color for a condition */
  function getConditionColor(condition: ToothCondition): string {
    return conditionColors.value[condition] || '#FFFFFF'
  }

  /** Check if tooth is deciduous (baby tooth) */
  function isDeciduousTooth(toothNumber: number): boolean {
    return ALL_DECIDUOUS_NUMBERS.includes(toothNumber as typeof ALL_DECIDUOUS_NUMBERS[number])
  }

  // ============================================================================
  // API Methods
  // ============================================================================

  /** Fetch odontogram for a patient */
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

  /** Update a single tooth */
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

  /** Bulk update multiple teeth */
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

  /** Fetch history for a specific tooth */
  async function fetchToothHistory(
    patientId: string,
    toothNumber: number,
    page = 1,
    pageSize = 50
  ): Promise<PaginatedResponse<OdontogramHistoryEntry> | null> {
    try {
      return await api.get<PaginatedResponse<OdontogramHistoryEntry>>(
        `/api/v1/odontogram/patients/${patientId}/teeth/${toothNumber}/history?page=${page}&page_size=${pageSize}`
      )
    } catch (err) {
      console.error('Error fetching tooth history:', err)
      return null
    }
  }

  /** Fetch full odontogram history for patient */
  async function fetchPatientHistory(
    patientId: string,
    page = 1,
    pageSize = 50
  ): Promise<PaginatedResponse<OdontogramHistoryEntry> | null> {
    try {
      return await api.get<PaginatedResponse<OdontogramHistoryEntry>>(
        `/api/v1/odontogram/patients/${patientId}/history?page=${page}&page_size=${pageSize}`
      )
    } catch (err) {
      console.error('Error fetching patient history:', err)
      return null
    }
  }

  /** Reset local state */
  function reset(): void {
    odontogramData.value = null
    error.value = null
  }

  // ============================================================================
  // Return
  // ============================================================================

  return {
    // State
    odontogramData,
    teeth,
    loading,
    error,
    conditionColors,
    availableConditions,

    // Helpers
    getToothRecord,
    getConditionColor,
    isDeciduousTooth,

    // API
    fetchOdontogram,
    updateTooth,
    bulkUpdateTeeth,
    fetchToothHistory,
    fetchPatientHistory,
    reset
  }
}
