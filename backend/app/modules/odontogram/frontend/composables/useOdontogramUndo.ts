/**
 * Composable for odontogram undo functionality
 * Tracks treatment actions for undo support
 */

export interface UndoAction {
  treatmentId: string
  tooth: number
  type: string
  timestamp: number
}

const MAX_UNDO_STACK_SIZE = 50

export function useOdontogramUndo() {
  // Undo stack for recent actions
  const undoStack = useState<UndoAction[]>('odontogram:undoStack', () => [])

  // Computed: can undo
  const canUndo = computed(() => undoStack.value.length > 0)

  // Get last action without removing it
  const lastAction = computed(() => {
    if (undoStack.value.length === 0) return null
    return undoStack.value[undoStack.value.length - 1]
  })

  // Push an action to the undo stack
  function pushAction(action: Omit<UndoAction, 'timestamp'>) {
    undoStack.value.push({
      ...action,
      timestamp: Date.now()
    })

    // Limit stack size
    if (undoStack.value.length > MAX_UNDO_STACK_SIZE) {
      undoStack.value.shift()
    }
  }

  // Pop the last action from the stack
  function popAction(): UndoAction | undefined {
    return undoStack.value.pop()
  }

  // Clear the undo stack
  function clearStack() {
    undoStack.value = []
  }

  // Remove a specific action by treatment ID (e.g., if treatment was already deleted)
  function removeAction(treatmentId: string) {
    const index = undoStack.value.findIndex(a => a.treatmentId === treatmentId)
    if (index !== -1) {
      undoStack.value.splice(index, 1)
    }
  }

  return {
    // State
    undoStack: readonly(undoStack),
    canUndo,
    lastAction,

    // Actions
    pushAction,
    popAction,
    clearStack,
    removeAction
  }
}
