<script setup lang="ts">
/**
 * OdontogramChart - Main dental chart component
 *
 * Features:
 * - Interactive tooth visualization with dual view (occlusal + lateral)
 * - Click-to-apply treatment mode with keyboard shortcuts
 * - Timeline slider for historical view
 * - Treatment management (add, edit, delete, perform)
 */

import type { OdontogramHistoryEntry, Surface, Treatment, TreatmentStatus, TreatmentType } from '~/types'
import { PERMANENT_TEETH, DECIDUOUS_TEETH, TREATMENT_SHORTCUTS } from '~/constants/odontogram'
import { isSurfaceTreatment } from './TreatmentIcons'

export type OdontogramMode = 'full' | 'view-only' | 'planning'

const props = withDefaults(defineProps<{
  patientId: string
  mode?: OdontogramMode
  statusFilter?: TreatmentStatus[]
}>(), {
  mode: 'full'
})

const emit = defineEmits<{
  treatmentAdd: [treatment: Treatment]
  treatmentPerform: [treatmentId: string]
}>()

const { t } = useI18n()
const toast = useToast()

// ============================================================================
// Composables
// ============================================================================

const {
  loading,
  fetchOdontogram,
  fetchPatientHistory,
  getToothRecord,
  treatments,
  treatmentsLoading,
  fetchTreatments,
  createTreatment,
  performTreatment,
  deleteTreatment,
  updateTreatment,
  getToothTreatments,
  timelineDates,
  viewingDate,
  timelineLoading,
  isViewingHistory,
  displayTreatments,
  fetchTimeline,
  fetchOdontogramAtDate,
  returnToCurrentView
} = useOdontogram()

// ============================================================================
// State
// ============================================================================

const dentitionMode = ref<'permanent' | 'deciduous'>('permanent')
const selectedTooth = ref<number | null>(null)
const showSurfaceSelector = ref(false)
const hoveredTooth = ref<number | null>(null)
const highlightedTeeth = ref<number[]>([])

// Click-to-apply mode
const selectedTreatmentType = ref<TreatmentType | null>(null)
const selectedTreatmentStatus = ref<TreatmentStatus>('existing')

// Undo stack
const undoStack = ref<Array<{ treatmentId: string, tooth: number, type: string }>>([])

// History section
const historyData = ref<OdontogramHistoryEntry[]>([])
const historyLoading = ref(false)

// Treatment editing
const showTreatmentEditModal = ref(false)
const editingTreatment = ref<Treatment | null>(null)

// Always show dual view
const showLateral = true

// ============================================================================
// Computed
// ============================================================================

const isReadonly = computed(() => props.mode === 'view-only' || isViewingHistory.value)
const isPlanningMode = computed(() => props.mode === 'planning')
const isClickToApplyMode = computed(() => selectedTreatmentType.value !== null)

const teethLayout = computed(() =>
  dentitionMode.value === 'permanent' ? PERMANENT_TEETH : DECIDUOUS_TEETH
)

const pendingTreatment = computed(() => {
  if (!selectedTreatmentType.value) return null
  return {
    type: selectedTreatmentType.value,
    status: selectedTreatmentStatus.value
  }
})

// ============================================================================
// Lifecycle
// ============================================================================

onMounted(async () => {
  await Promise.all([
    fetchOdontogram(props.patientId),
    fetchTreatments(props.patientId),
    fetchTimeline(props.patientId)
  ])
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})

watch(() => props.patientId, async (newId) => {
  if (newId) {
    returnToCurrentView()
    await Promise.all([
      fetchOdontogram(newId),
      fetchTreatments(newId),
      fetchTimeline(newId)
    ])
  }
})

// ============================================================================
// Tooth Data Helpers
// ============================================================================

function getToothData(toothNumber: number) {
  const record = getToothRecord(toothNumber)
  const toothTreatments = getToothTreatments(toothNumber)

  return {
    generalCondition: record?.general_condition || 'healthy',
    isDisplaced: toothTreatments.some(t => t.treatment_type === 'displaced'),
    isRotated: toothTreatments.some(t => t.treatment_type === 'rotated')
  }
}

function getFilteredTreatments(toothNumber: number): Treatment[] {
  const toothTreatments = isViewingHistory.value
    ? displayTreatments.value.filter(t => t.tooth_number === toothNumber)
    : getToothTreatments(toothNumber)

  if (!props.statusFilter?.length) return toothTreatments
  return toothTreatments.filter(t => props.statusFilter?.includes(t.status))
}

// ============================================================================
// Keyboard Shortcuts
// ============================================================================

function handleKeydown(e: KeyboardEvent) {
  if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return

  if (e.key === 'Escape') {
    cancelClickToApplyMode()
    return
  }

  if ((e.ctrlKey || e.metaKey) && e.key === 'z') {
    e.preventDefault()
    handleUndo()
    return
  }

  if (e.key.toLowerCase() === 'p') {
    selectedTreatmentStatus.value = 'planned'
    return
  }

  if (e.key.toLowerCase() === 'e') {
    selectedTreatmentStatus.value = 'existing'
    return
  }

  const shortcut = TREATMENT_SHORTCUTS[e.key]
  if (shortcut && !isReadonly.value) {
    selectedTreatmentType.value = shortcut
  }
}

// ============================================================================
// Click-to-Apply Mode
// ============================================================================

function handleSurfaceClick(toothNumber: number, surface: Surface) {
  if (isReadonly.value || !isClickToApplyMode.value) return

  if (isSurfaceTreatment(selectedTreatmentType.value!)) {
    applyTreatment(toothNumber, [surface])
  } else {
    applyTreatment(toothNumber)
  }
}

function handleToothClick(toothNumber: number) {
  if (isReadonly.value || !isClickToApplyMode.value) return

  if (isSurfaceTreatment(selectedTreatmentType.value!)) {
    selectedTooth.value = toothNumber
    showSurfaceSelector.value = true
  } else {
    applyTreatment(toothNumber)
  }
}

function handleToothContextMenu(toothNumber: number, event: MouseEvent) {
  if (isReadonly.value) return
  event.preventDefault()
  // Context menu could be implemented here if needed
}

async function applyTreatment(toothNumber: number, surfaces?: Surface[]) {
  if (!selectedTreatmentType.value) return

  const data: { treatment_type: TreatmentType, status: TreatmentStatus, surfaces?: Surface[] } = {
    treatment_type: selectedTreatmentType.value,
    status: isPlanningMode.value ? 'planned' : selectedTreatmentStatus.value
  }

  if (surfaces?.length) data.surfaces = surfaces

  const treatment = await createTreatment(props.patientId, toothNumber, data)

  if (treatment) {
    undoStack.value.push({
      treatmentId: treatment.id,
      tooth: toothNumber,
      type: treatment.treatment_type
    })

    toast.add({
      title: `${t(`odontogram.treatments.types.${treatment.treatment_type}`)} - ${t('odontogram.tooth')} ${toothNumber}`,
      description: t('odontogram.treatments.treatmentAdded'),
      color: 'success',
      actions: [{ label: t('common.undo'), click: handleUndo }]
    })

    emit('treatmentAdd', treatment)
    selectedTreatmentType.value = null
  }
}

function handleSurfaceConfirm(surfaces: Surface[]) {
  if (selectedTooth.value && surfaces.length) {
    applyTreatment(selectedTooth.value, surfaces)
  }
  selectedTooth.value = null
}

async function handleUndo() {
  const lastAction = undoStack.value.pop()
  if (lastAction) {
    await deleteTreatment(lastAction.treatmentId)
    toast.add({ title: t('common.undone'), color: 'neutral' })
  }
}

function cancelClickToApplyMode() {
  selectedTreatmentType.value = null
  hoveredTooth.value = null
}

// ============================================================================
// Treatment Editing
// ============================================================================

function handleEditTreatment(treatment: Treatment) {
  editingTreatment.value = treatment
  showTreatmentEditModal.value = true
}

async function handleTreatmentUpdate(
  treatmentId: string,
  data: { status?: TreatmentStatus, surfaces?: Surface[], notes?: string }
) {
  await updateTreatment(treatmentId, data)
  showTreatmentEditModal.value = false
  editingTreatment.value = null
}

async function handleTreatmentDelete(treatmentId: string) {
  await deleteTreatment(treatmentId)
  showTreatmentEditModal.value = false
  editingTreatment.value = null
}

async function handleTreatmentPerform(treatmentId: string) {
  const updated = await performTreatment(treatmentId)
  if (updated) emit('treatmentPerform', treatmentId)
  showTreatmentEditModal.value = false
  editingTreatment.value = null
}

// ============================================================================
// Timeline & History
// ============================================================================

async function handleTimelineDateChange(date: string | null) {
  if (date === null) {
    returnToCurrentView()
  } else {
    await fetchOdontogramAtDate(props.patientId, date)
  }
}

async function onHistoryExpanded(expanded: boolean) {
  if (expanded && !historyData.value.length) {
    historyLoading.value = true
    const response = await fetchPatientHistory(props.patientId)
    if (response) historyData.value = response.data
    historyLoading.value = false
  }
}
</script>

<template>
  <div class="odontogram-chart">
    <!-- Header -->
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center gap-2">
        <h3 class="text-lg font-semibold">
          {{ t('odontogram.title') }}
        </h3>
        <UBadge
          v-if="mode === 'view-only'"
          :label="t('odontogram.readOnly')"
          color="neutral"
          variant="subtle"
        />
        <UBadge
          v-if="mode === 'planning'"
          :label="t('odontogram.planning')"
          color="warning"
          variant="subtle"
        />
        <UBadge
          v-if="isClickToApplyMode"
          :label="t(`odontogram.treatments.types.${selectedTreatmentType}`)"
          color="primary"
          variant="solid"
        />
      </div>

      <!-- Dentition toggle -->
      <UButtonGroup>
        <UButton
          :color="dentitionMode === 'permanent' ? 'primary' : 'neutral'"
          :variant="dentitionMode === 'permanent' ? 'solid' : 'outline'"
          size="sm"
          @click="dentitionMode = 'permanent'"
        >
          {{ t('odontogram.dentition.permanent') }}
        </UButton>
        <UButton
          :color="dentitionMode === 'deciduous' ? 'primary' : 'neutral'"
          :variant="dentitionMode === 'deciduous' ? 'solid' : 'outline'"
          size="sm"
          @click="dentitionMode = 'deciduous'"
        >
          {{ t('odontogram.dentition.deciduous') }}
        </UButton>
      </UButtonGroup>
    </div>

    <!-- Timeline Slider -->
    <TimelineSlider
      v-if="timelineDates.length > 1"
      :dates="timelineDates"
      :current-date="viewingDate"
      :disabled="timelineLoading"
      class="mb-4"
      @update:current-date="handleTimelineDateChange"
    />

    <!-- Loading -->
    <div
      v-if="loading || treatmentsLoading || timelineLoading"
      class="flex items-center justify-center py-16"
    >
      <UIcon name="i-lucide-loader-2" class="w-8 h-8 animate-spin text-gray-400" />
    </div>

    <!-- Chart -->
    <div v-else class="flex flex-col gap-4">
      <div
        class="odontogram-grid bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 p-4"
        :class="{ 'cursor-crosshair': isClickToApplyMode }"
      >
        <!-- Upper arch -->
        <div class="mb-6">
          <div class="text-xs text-gray-500 text-center mb-2">
            {{ t('odontogram.quadrants.upper') }}
          </div>
          <div class="flex justify-center gap-1">
            <ToothQuadrant
              :teeth="teethLayout.upperRight"
              :get-tooth-data="getToothData"
              :get-treatments="getFilteredTreatments"
              :readonly="isReadonly"
              :selected-tooth="selectedTooth"
              :show-lateral="showLateral"
              :hovered-tooth="hoveredTooth"
              :highlighted-teeth="highlightedTeeth"
              :pending-treatment="pendingTreatment"
              @surface-click="handleSurfaceClick"
              @tooth-click="handleToothClick"
              @tooth-context-menu="handleToothContextMenu"
              @tooth-hover="hoveredTooth = $event"
              @edit-treatment="handleEditTreatment"
            />

            <div class="w-px bg-gray-300 dark:bg-gray-600 mx-2" />

            <ToothQuadrant
              :teeth="teethLayout.upperLeft"
              :get-tooth-data="getToothData"
              :get-treatments="getFilteredTreatments"
              :readonly="isReadonly"
              :selected-tooth="selectedTooth"
              :show-lateral="showLateral"
              :hovered-tooth="hoveredTooth"
              :highlighted-teeth="highlightedTeeth"
              :pending-treatment="pendingTreatment"
              @surface-click="handleSurfaceClick"
              @tooth-click="handleToothClick"
              @tooth-context-menu="handleToothContextMenu"
              @tooth-hover="hoveredTooth = $event"
              @edit-treatment="handleEditTreatment"
            />
          </div>
        </div>

        <div class="h-px bg-gray-200 dark:bg-gray-700 my-4" />

        <!-- Lower arch -->
        <div>
          <div class="flex justify-center gap-1">
            <ToothQuadrant
              :teeth="teethLayout.lowerRight"
              :get-tooth-data="getToothData"
              :get-treatments="getFilteredTreatments"
              :readonly="isReadonly"
              :selected-tooth="selectedTooth"
              :show-lateral="showLateral"
              :hovered-tooth="hoveredTooth"
              :highlighted-teeth="highlightedTeeth"
              :pending-treatment="pendingTreatment"
              @surface-click="handleSurfaceClick"
              @tooth-click="handleToothClick"
              @tooth-context-menu="handleToothContextMenu"
              @tooth-hover="hoveredTooth = $event"
              @edit-treatment="handleEditTreatment"
            />

            <div class="w-px bg-gray-300 dark:bg-gray-600 mx-2" />

            <ToothQuadrant
              :teeth="teethLayout.lowerLeft"
              :get-tooth-data="getToothData"
              :get-treatments="getFilteredTreatments"
              :readonly="isReadonly"
              :selected-tooth="selectedTooth"
              :show-lateral="showLateral"
              :hovered-tooth="hoveredTooth"
              :highlighted-teeth="highlightedTeeth"
              :pending-treatment="pendingTreatment"
              @surface-click="handleSurfaceClick"
              @tooth-click="handleToothClick"
              @tooth-context-menu="handleToothContextMenu"
              @tooth-hover="hoveredTooth = $event"
              @edit-treatment="handleEditTreatment"
            />
          </div>
          <div class="text-xs text-gray-500 text-center mt-2">
            {{ t('odontogram.quadrants.lower') }}
          </div>
        </div>
      </div>

      <!-- Treatment Bar -->
      <TreatmentBar
        v-if="!isReadonly"
        v-model:selected-treatment="selectedTreatmentType"
        :selected-status="selectedTreatmentStatus"
        :disabled="isReadonly"
        @update:selected-status="selectedTreatmentStatus = $event"
        @treatment-select="selectedTreatmentType = $event"
        @cancel="cancelClickToApplyMode"
      />

      <!-- Legend -->
      <OdontogramLegend />

      <!-- Treatment List -->
      <TreatmentListSection :treatments="treatments" />

      <!-- History -->
      <ChangeHistorySection
        :history="historyData"
        :treatments="treatments"
        :loading="historyLoading"
        @update:expanded="onHistoryExpanded"
      />
    </div>

    <!-- Surface selector popup -->
    <SurfaceSelectorPopup
      v-model:open="showSurfaceSelector"
      :tooth-number="selectedTooth || 0"
      :treatment-type="selectedTreatmentType || 'filling'"
      :status="selectedTreatmentStatus"
      @confirm="handleSurfaceConfirm"
      @cancel="selectedTooth = null"
    />

    <!-- Treatment edit modal -->
    <TreatmentEditModal
      v-model:open="showTreatmentEditModal"
      :treatment="editingTreatment"
      @update="handleTreatmentUpdate"
      @delete="handleTreatmentDelete"
      @perform="handleTreatmentPerform"
    />
  </div>
</template>

<style scoped>
.odontogram-grid {
  overflow-x: auto;
}
</style>
