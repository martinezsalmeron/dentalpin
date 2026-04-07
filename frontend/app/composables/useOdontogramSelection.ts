/**
 * Composable for odontogram selection state management
 * Handles tooth selection, surface selection, treatment selection, and highlighting
 */

import type { Surface, TreatmentStatus, TreatmentType } from '~/types'

export function useOdontogramSelection() {
  // Currently selected tooth (for showing details, editing)
  const selectedTooth = useState<number | null>('odontogram:selectedTooth', () => null)

  // Currently selected surface (for surface-specific treatments)
  const selectedSurface = useState<Surface | null>('odontogram:selectedSurface', () => null)

  // Currently hovered tooth (for visual feedback)
  const hoveredTooth = useState<number | null>('odontogram:hoveredTooth', () => null)

  // Highlighted teeth (from summary panel or search)
  const highlightedTeeth = useState<number[]>('odontogram:highlightedTeeth', () => [])

  // Click-to-apply mode: selected treatment type to apply
  const selectedTreatmentType = useState<TreatmentType | null>('odontogram:selectedTreatmentType', () => null)

  // Click-to-apply mode: selected status for new treatments
  const selectedTreatmentStatus = useState<TreatmentStatus>('odontogram:selectedTreatmentStatus', () => 'existing')

  // Computed: is click-to-apply mode active
  const isClickToApplyMode = computed(() => selectedTreatmentType.value !== null)

  // Selection actions
  function selectTooth(toothNumber: number | null) {
    selectedTooth.value = toothNumber
    if (toothNumber === null) {
      selectedSurface.value = null
    }
  }

  function selectSurface(surface: Surface | null) {
    selectedSurface.value = surface
  }

  function setHoveredTooth(toothNumber: number | null) {
    hoveredTooth.value = toothNumber
  }

  // Highlight actions
  function highlightTeeth(teeth: number[]) {
    highlightedTeeth.value = teeth
  }

  function clearHighlight() {
    highlightedTeeth.value = []
  }

  function isToothHighlighted(toothNumber: number): boolean {
    return highlightedTeeth.value.includes(toothNumber)
  }

  // Click-to-apply mode actions
  function selectTreatment(treatmentType: TreatmentType | null) {
    selectedTreatmentType.value = treatmentType
  }

  function setTreatmentStatus(status: TreatmentStatus) {
    selectedTreatmentStatus.value = status
  }

  function cancelClickToApplyMode() {
    selectedTreatmentType.value = null
    hoveredTooth.value = null
  }

  // Reset all selection state
  function resetSelection() {
    selectedTooth.value = null
    selectedSurface.value = null
    hoveredTooth.value = null
    highlightedTeeth.value = []
    selectedTreatmentType.value = null
    selectedTreatmentStatus.value = 'existing'
  }

  return {
    // State
    selectedTooth,
    selectedSurface,
    hoveredTooth: readonly(hoveredTooth),
    highlightedTeeth: readonly(highlightedTeeth),
    selectedTreatmentType,
    selectedTreatmentStatus,
    isClickToApplyMode,

    // Actions
    selectTooth,
    selectSurface,
    setHoveredTooth,
    highlightTeeth,
    clearHighlight,
    isToothHighlighted,
    selectTreatment,
    setTreatmentStatus,
    cancelClickToApplyMode,
    resetSelection
  }
}
