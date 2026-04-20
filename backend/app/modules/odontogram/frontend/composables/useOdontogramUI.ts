/**
 * Composable for odontogram UI state management
 * Handles view mode, dentition selection, and panel visibility
 */

import { PERMANENT_TEETH, DECIDUOUS_TEETH } from '~/composables/useOdontogram'

export type DentitionMode = 'permanent' | 'deciduous'

export function useOdontogramUI() {
  // Dentition mode (permanent vs deciduous/primary teeth)
  const dentitionMode = useState<DentitionMode>('odontogram:dentitionMode', () => 'permanent')

  // Show lateral (side) view alongside occlusal view
  const showLateral = useState<boolean>('odontogram:showLateral', () => true)

  // Show history panel
  const showHistory = useState<boolean>('odontogram:showHistory', () => false)

  // Computed teeth layout based on dentition mode
  const teethLayout = computed(() => {
    if (dentitionMode.value === 'permanent') {
      return PERMANENT_TEETH
    }
    return DECIDUOUS_TEETH
  })

  // Toggle functions
  function toggleDentition() {
    dentitionMode.value = dentitionMode.value === 'permanent' ? 'deciduous' : 'permanent'
  }

  function setDentition(mode: DentitionMode) {
    dentitionMode.value = mode
  }

  function toggleLateral() {
    showLateral.value = !showLateral.value
  }

  function toggleHistory() {
    showHistory.value = !showHistory.value
  }

  // Reset UI state
  function resetUI() {
    dentitionMode.value = 'permanent'
    showLateral.value = true
    showHistory.value = false
  }

  return {
    // State
    dentitionMode: readonly(dentitionMode),
    showLateral: readonly(showLateral),
    showHistory,
    teethLayout,

    // Actions
    toggleDentition,
    setDentition,
    toggleLateral,
    toggleHistory,
    resetUI
  }
}
