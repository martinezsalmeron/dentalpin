<script setup lang="ts">
import type { OdontogramHistoryEntry, Surface, Treatment, TreatmentStatus, TreatmentType } from '~/types'
import { DECIDUOUS_TEETH, PERMANENT_TEETH } from '~/composables/useOdontogram'
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
const {
  loading,
  fetchOdontogram,
  fetchPatientHistory,
  getToothRecord,
  // Treatment methods
  treatments,
  treatmentsLoading,
  fetchTreatments,
  createTreatment,
  performTreatment,
  deleteTreatment,
  updateTreatment,
  getToothTreatments
} = useOdontogram()

// Local state
const dentitionMode = ref<'permanent' | 'deciduous'>('permanent')
const selectedTooth = ref<number | null>(null)
const _selectedSurface = ref<Surface | null>(null)
const showSurfaceSelector = ref(false)
const showContextMenu = ref(false)
const contextMenuTooth = ref<number | null>(null)
// Always show dual view (lateral + occlusal)
const showLateral = ref(true)
const historyData = ref<OdontogramHistoryEntry[]>([])
const historyLoading = ref(false)

// Click-to-apply mode state
const selectedTreatmentType = ref<TreatmentType | null>(null)
const selectedTreatmentStatus = ref<TreatmentStatus>('existing')
const hoveredTooth = ref<number | null>(null)

// Undo stack for quick undo
const undoStack = ref<Array<{ treatmentId: string, tooth: number, type: string }>>([])

// Highlighted teeth (from summary panel)
const highlightedTeeth = ref<number[]>([])

// Show summary panel (now controlled via tooltip hover)
const _showSummary = ref(false)

// Treatment editing
const showTreatmentEditModal = ref(false)
const editingTreatment = ref<Treatment | null>(null)

// Computed
const isReadonly = computed(() => props.mode === 'view-only')
const isPlanningMode = computed(() => props.mode === 'planning')
const isClickToApplyMode = computed(() => selectedTreatmentType.value !== null)

// Computed teeth layout based on dentition mode
const teethLayout = computed(() => {
  if (dentitionMode.value === 'permanent') {
    return PERMANENT_TEETH
  }
  return DECIDUOUS_TEETH
})

// Filter treatments by status if filter is provided
const _filteredTreatments = computed(() => {
  if (!props.statusFilter || props.statusFilter.length === 0) {
    return treatments.value
  }
  return treatments.value.filter(t => props.statusFilter?.includes(t.status))
})

// Load data on mount
onMounted(async () => {
  await Promise.all([
    fetchOdontogram(props.patientId),
    fetchTreatments(props.patientId)
  ])
})

// Watch for patient changes
watch(() => props.patientId, async (newId) => {
  if (newId) {
    await Promise.all([
      fetchOdontogram(newId),
      fetchTreatments(newId)
    ])
  }
})

// Keyboard shortcuts
onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})

// Treatment shortcuts map
const treatmentShortcuts: Record<string, TreatmentType> = {
  1: 'extraction',
  2: 'filling',
  3: 'root_canal',
  4: 'crown',
  5: 'implant',
  6: 'veneer',
  7: 'sealant',
  8: 'caries'
}

function handleKeydown(e: KeyboardEvent) {
  // Ignore if typing in an input
  if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
    return
  }

  // ESC to cancel click-to-apply mode
  if (e.key === 'Escape') {
    cancelClickToApplyMode()
    return
  }

  // Ctrl+Z / Cmd+Z to undo
  if ((e.ctrlKey || e.metaKey) && e.key === 'z') {
    e.preventDefault()
    handleUndo()
    return
  }

  // Status shortcuts: P for planned, E for existing
  if (e.key === 'p' || e.key === 'P') {
    selectedTreatmentStatus.value = 'planned'
    return
  }
  if (e.key === 'e' || e.key === 'E') {
    selectedTreatmentStatus.value = 'existing'
    return
  }

  // Number shortcuts for treatments (1-8)
  if (treatmentShortcuts[e.key] && !isReadonly.value) {
    selectedTreatmentType.value = treatmentShortcuts[e.key]
    return
  }
}

// Get tooth data or defaults
function getToothData(toothNumber: number): {
  generalCondition: string
  isDisplaced: boolean
  isRotated: boolean
} {
  const record = getToothRecord(toothNumber)
  const toothTreatments = getToothTreatments(toothNumber)

  // Derive position states from treatments
  const isDisplaced = toothTreatments.some(t => t.treatment_type === 'displaced')
  const isRotated = toothTreatments.some(t => t.treatment_type === 'rotated')

  return {
    generalCondition: record?.general_condition || 'healthy',
    isDisplaced,
    isRotated
  }
}

// Get treatments for a specific tooth
function getToothTreatmentsFiltered(toothNumber: number): Treatment[] {
  const toothTreatments = getToothTreatments(toothNumber)
  if (!props.statusFilter || props.statusFilter.length === 0) {
    return toothTreatments
  }
  return toothTreatments.filter(t => props.statusFilter?.includes(t.status))
}

// Handle surface click in click-to-apply mode
function handleSurfaceClick(toothNumber: number, surface: Surface) {
  if (isReadonly.value || !isClickToApplyMode.value) return

  // Check if it's a surface treatment - apply to the clicked surface
  if (isSurfaceTreatment(selectedTreatmentType.value!)) {
    applyTreatmentToTooth(toothNumber, [surface])
  } else {
    // For non-surface treatments (crown, extraction, rotated, displaced, etc.), apply to whole tooth
    applyTreatmentToTooth(toothNumber)
  }
}

// Handle tooth click
function handleToothClick(toothNumber: number) {
  if (isReadonly.value || !isClickToApplyMode.value) return

  // Check if it's a surface treatment - need surface selector
  if (isSurfaceTreatment(selectedTreatmentType.value!)) {
    selectedTooth.value = toothNumber
    showSurfaceSelector.value = true
  } else {
    // Apply whole tooth treatment (including rotated, displaced)
    applyTreatmentToTooth(toothNumber)
  }
}

// Handle right-click context menu
function handleToothContextMenu(toothNumber: number, event: MouseEvent) {
  if (isReadonly.value) return
  event.preventDefault()
  contextMenuTooth.value = toothNumber
  showContextMenu.value = true
}

// Close context menu
function _closeContextMenu() {
  showContextMenu.value = false
  contextMenuTooth.value = null
}

// Apply treatment in click-to-apply mode
async function applyTreatmentToTooth(toothNumber: number, surfaces?: Surface[]) {
  if (!selectedTreatmentType.value) return

  const data: {
    treatment_type: TreatmentType
    status: TreatmentStatus
    surfaces?: Surface[]
  } = {
    treatment_type: selectedTreatmentType.value,
    status: isPlanningMode.value ? 'planned' : selectedTreatmentStatus.value
  }

  if (surfaces && surfaces.length > 0) {
    data.surfaces = surfaces
  }

  const treatment = await createTreatment(props.patientId, toothNumber, data)

  if (treatment) {
    // Add to undo stack
    undoStack.value.push({
      treatmentId: treatment.id,
      tooth: toothNumber,
      type: treatment.treatment_type
    })

    // Show undo toast
    toast.add({
      title: `${t(`odontogram.treatments.types.${treatment.treatment_type}`)} - ${t('odontogram.tooth')} ${toothNumber}`,
      description: t('odontogram.treatments.treatmentAdded'),
      color: 'success',
      actions: [{
        label: t('common.undo'),
        click: () => handleUndo()
      }]
    })

    emit('treatmentAdd', treatment)

    // Deselect treatment after applying to prevent accidental double-application
    selectedTreatmentType.value = null
  }
}

// Handle surface selection from popup
function handleSurfaceConfirm(surfaces: Surface[]) {
  if (selectedTooth.value && surfaces.length > 0) {
    applyTreatmentToTooth(selectedTooth.value, surfaces)
  }
  selectedTooth.value = null
}

// Undo last treatment
async function handleUndo() {
  const lastAction = undoStack.value.pop()
  if (lastAction) {
    await deleteTreatment(lastAction.treatmentId)
    toast.add({
      title: t('common.undone'),
      color: 'neutral'
    })
  }
}

// Cancel click-to-apply mode
function cancelClickToApplyMode() {
  selectedTreatmentType.value = null
  hoveredTooth.value = null
}

// Handle treatment selection from bar
function handleTreatmentSelect(treatmentType: TreatmentType) {
  selectedTreatmentType.value = treatmentType
}

// Handle treatment perform
async function _handlePerformTreatment(treatment: Treatment) {
  const updated = await performTreatment(treatment.id)
  if (updated) {
    emit('treatmentPerform', treatment.id)
  }
}

// Handle treatment delete
async function _handleDeleteTreatment(treatment: Treatment) {
  await deleteTreatment(treatment.id)
}

// Selected tooth treatments for panel
const _selectedToothTreatments = computed(() => {
  if (!selectedTooth.value) return []
  return getToothTreatmentsFiltered(selectedTooth.value)
})

// Pending treatment for hover preview
const pendingTreatment = computed(() => {
  if (!selectedTreatmentType.value) return null
  return {
    type: selectedTreatmentType.value,
    status: selectedTreatmentStatus.value
  }
})

// Check if tooth is highlighted
function isToothHighlighted(toothNumber: number): boolean {
  return highlightedTeeth.value.includes(toothNumber)
}

// Handle highlight from summary
function _handleHighlightTeeth(teeth: number[]) {
  highlightedTeeth.value = teeth
}

function _handleClearHighlight() {
  highlightedTeeth.value = []
}

// Handle status filter from summary
function _handleStatusFilter(_status: TreatmentStatus | null) {
  // This could be used to filter the visible treatments
  // For now, just a placeholder for future enhancement
}

// Handle edit treatment from tooltip
function handleEditTreatment(treatment: Treatment) {
  editingTreatment.value = treatment
  showTreatmentEditModal.value = true
}

// Handle treatment update (from edit modal)
async function handleTreatmentUpdateFromModal(treatmentId: string, data: { status?: TreatmentStatus, surfaces?: Surface[], notes?: string }) {
  await updateTreatment(treatmentId, data)
  showTreatmentEditModal.value = false
  editingTreatment.value = null
  toast.add({
    title: t('odontogram.messages.updated'),
    color: 'success'
  })
}

// Handle delete from edit modal
async function handleDeleteFromModal(treatmentId: string) {
  await deleteTreatment(treatmentId)
  showTreatmentEditModal.value = false
  editingTreatment.value = null
  toast.add({
    title: t('odontogram.treatments.treatmentDeleted'),
    color: 'neutral'
  })
}

// Handle perform from edit modal
async function handlePerformFromModal(treatmentId: string) {
  await performTreatment(treatmentId)
  showTreatmentEditModal.value = false
  editingTreatment.value = null
  toast.add({
    title: t('odontogram.treatments.treatmentPerformed'),
    color: 'success'
  })
}

// Handle history section expand (load data on first expand)
async function onHistoryExpanded(expanded: boolean) {
  if (expanded && historyData.value.length === 0) {
    historyLoading.value = true
    const response = await fetchPatientHistory(props.patientId)
    if (response) {
      historyData.value = response.data
    }
    historyLoading.value = false
  }
}
</script>

<template>
  <div class="odontogram-chart">
    <!-- Header with controls -->
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

      <div class="flex items-center gap-2">
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
    </div>

    <!-- Loading state -->
    <div
      v-if="loading || treatmentsLoading"
      class="flex items-center justify-center py-16"
    >
      <UIcon
        name="i-lucide-loader-2"
        class="w-8 h-8 animate-spin text-gray-400"
      />
    </div>

    <!-- Chart -->
    <div
      v-else
      class="flex flex-col gap-4"
    >
      <!-- Main chart area -->
      <div class="flex gap-6">
        <!-- Main chart -->
        <div class="flex-1">
          <div
            class="odontogram-grid bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 p-4"
            :class="{ 'click-to-apply-active': isClickToApplyMode }"
          >
            <!-- Upper arch -->
            <div class="mb-6">
              <div class="text-xs text-gray-500 text-center mb-2">
                {{ t('odontogram.quadrants.upper') }}
              </div>
              <div class="flex justify-center gap-1">
                <!-- Upper right (reversed for visual) -->
                <div class="flex gap-0.5">
                  <UPopover
                    v-for="toothNum in teethLayout.upperRight"
                    :key="toothNum"
                    :open-delay="300"
                    :close-delay="100"
                    :ui="{ width: 'min-w-48 max-w-72' }"
                  >
                    <div
                      class="tooth-cell"
                      :class="{ 'tooth-cell-dual': showLateral }"
                    >
                      <ToothDualView
                        :tooth-number="toothNum"
                        :general-condition="getToothData(toothNum).generalCondition"
                        :treatments="getToothTreatmentsFiltered(toothNum)"
                        :readonly="isReadonly"
                        :selected="selectedTooth === toothNum"
                        :show-lateral="showLateral"
                        :is-displaced="getToothData(toothNum).isDisplaced"
                        :is-rotated="getToothData(toothNum).isRotated"
                        :is-hovered="hoveredTooth === toothNum"
                        :is-highlighted="isToothHighlighted(toothNum)"
                        :pending-treatment="hoveredTooth === toothNum ? pendingTreatment : null"
                        @surface-click="(s) => handleSurfaceClick(toothNum, s)"
                        @tooth-click="handleToothClick(toothNum)"
                        @contextmenu="(e) => handleToothContextMenu(toothNum, e)"
                        @mouseenter="hoveredTooth = toothNum"
                        @mouseleave="hoveredTooth = null"
                      />
                    </div>
                    <template #content>
                      <ToothTooltip
                        :tooth-number="toothNum"
                        :treatments="getToothTreatmentsFiltered(toothNum)"
                        @edit-treatment="handleEditTreatment"
                      />
                    </template>
                  </UPopover>
                </div>

                <!-- Divider -->
                <div class="w-px bg-gray-300 dark:bg-gray-600 mx-2" />

                <!-- Upper left -->
                <div class="flex gap-0.5">
                  <UPopover
                    v-for="toothNum in teethLayout.upperLeft"
                    :key="toothNum"
                    :open-delay="300"
                    :close-delay="100"
                    :ui="{ width: 'min-w-48 max-w-72' }"
                  >
                    <div
                      class="tooth-cell"
                      :class="{ 'tooth-cell-dual': showLateral }"
                    >
                      <ToothDualView
                        :tooth-number="toothNum"
                        :general-condition="getToothData(toothNum).generalCondition"
                        :treatments="getToothTreatmentsFiltered(toothNum)"
                        :readonly="isReadonly"
                        :selected="selectedTooth === toothNum"
                        :show-lateral="showLateral"
                        :is-displaced="getToothData(toothNum).isDisplaced"
                        :is-rotated="getToothData(toothNum).isRotated"
                        :is-hovered="hoveredTooth === toothNum"
                        :is-highlighted="isToothHighlighted(toothNum)"
                        :pending-treatment="hoveredTooth === toothNum ? pendingTreatment : null"
                        @surface-click="(s) => handleSurfaceClick(toothNum, s)"
                        @tooth-click="handleToothClick(toothNum)"
                        @contextmenu="(e) => handleToothContextMenu(toothNum, e)"
                        @mouseenter="hoveredTooth = toothNum"
                        @mouseleave="hoveredTooth = null"
                      />
                    </div>
                    <template #content>
                      <ToothTooltip
                        :tooth-number="toothNum"
                        :treatments="getToothTreatmentsFiltered(toothNum)"
                        @edit-treatment="handleEditTreatment"
                      />
                    </template>
                  </UPopover>
                </div>
              </div>
            </div>

            <!-- Divider between arches -->
            <div class="h-px bg-gray-200 dark:bg-gray-700 my-4" />

            <!-- Lower arch -->
            <div>
              <div class="flex justify-center gap-1">
                <!-- Lower right (reversed for visual) -->
                <div class="flex gap-0.5">
                  <UPopover
                    v-for="toothNum in teethLayout.lowerRight"
                    :key="toothNum"
                    :open-delay="300"
                    :close-delay="100"
                    :ui="{ width: 'min-w-48 max-w-72' }"
                  >
                    <div
                      class="tooth-cell"
                      :class="{ 'tooth-cell-dual': showLateral }"
                    >
                      <ToothDualView
                        :tooth-number="toothNum"
                        :general-condition="getToothData(toothNum).generalCondition"
                        :treatments="getToothTreatmentsFiltered(toothNum)"
                        :readonly="isReadonly"
                        :selected="selectedTooth === toothNum"
                        :show-lateral="showLateral"
                        :is-displaced="getToothData(toothNum).isDisplaced"
                        :is-rotated="getToothData(toothNum).isRotated"
                        :is-hovered="hoveredTooth === toothNum"
                        :is-highlighted="isToothHighlighted(toothNum)"
                        :pending-treatment="hoveredTooth === toothNum ? pendingTreatment : null"
                        @surface-click="(s) => handleSurfaceClick(toothNum, s)"
                        @tooth-click="handleToothClick(toothNum)"
                        @contextmenu="(e) => handleToothContextMenu(toothNum, e)"
                        @mouseenter="hoveredTooth = toothNum"
                        @mouseleave="hoveredTooth = null"
                      />
                    </div>
                    <template #content>
                      <ToothTooltip
                        :tooth-number="toothNum"
                        :treatments="getToothTreatmentsFiltered(toothNum)"
                        @edit-treatment="handleEditTreatment"
                      />
                    </template>
                  </UPopover>
                </div>

                <!-- Divider -->
                <div class="w-px bg-gray-300 dark:bg-gray-600 mx-2" />

                <!-- Lower left -->
                <div class="flex gap-0.5">
                  <UPopover
                    v-for="toothNum in teethLayout.lowerLeft"
                    :key="toothNum"
                    :open-delay="300"
                    :close-delay="100"
                    :ui="{ width: 'min-w-48 max-w-72' }"
                  >
                    <div
                      class="tooth-cell"
                      :class="{ 'tooth-cell-dual': showLateral }"
                    >
                      <ToothDualView
                        :tooth-number="toothNum"
                        :general-condition="getToothData(toothNum).generalCondition"
                        :treatments="getToothTreatmentsFiltered(toothNum)"
                        :readonly="isReadonly"
                        :selected="selectedTooth === toothNum"
                        :show-lateral="showLateral"
                        :is-displaced="getToothData(toothNum).isDisplaced"
                        :is-rotated="getToothData(toothNum).isRotated"
                        :is-hovered="hoveredTooth === toothNum"
                        :is-highlighted="isToothHighlighted(toothNum)"
                        :pending-treatment="hoveredTooth === toothNum ? pendingTreatment : null"
                        @surface-click="(s) => handleSurfaceClick(toothNum, s)"
                        @tooth-click="handleToothClick(toothNum)"
                        @contextmenu="(e) => handleToothContextMenu(toothNum, e)"
                        @mouseenter="hoveredTooth = toothNum"
                        @mouseleave="hoveredTooth = null"
                      />
                    </div>
                    <template #content>
                      <ToothTooltip
                        :tooth-number="toothNum"
                        :treatments="getToothTreatmentsFiltered(toothNum)"
                        @edit-treatment="handleEditTreatment"
                      />
                    </template>
                  </UPopover>
                </div>
              </div>
              <div class="text-xs text-gray-500 text-center mt-2">
                {{ t('odontogram.quadrants.lower') }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Treatment Bar (Bottom, for click-to-apply mode) -->
      <TreatmentBar
        v-if="!isReadonly"
        v-model:selected-treatment="selectedTreatmentType"
        :selected-status="selectedTreatmentStatus"
        :disabled="isReadonly"
        @update:selected-status="selectedTreatmentStatus = $event"
        @treatment-select="handleTreatmentSelect"
        @cancel="cancelClickToApplyMode"
      />

      <!-- Legend (below treatment bar) -->
      <OdontogramLegend />

      <!-- Treatment List Section -->
      <TreatmentListSection :treatments="treatments" />

      <!-- Change History Section (collapsed by default) -->
      <ChangeHistorySection
        :history="historyData"
        :treatments="treatments"
        :loading="historyLoading"
        @update:expanded="onHistoryExpanded"
      />
    </div>

    <!-- Surface selector popup (for surface treatments) -->
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
      @update="handleTreatmentUpdateFromModal"
      @delete="handleDeleteFromModal"
      @perform="handlePerformFromModal"
    />
  </div>
</template>

<style scoped>
.tooth-cell {
  width: 60px;
  height: 75px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.tooth-cell-dual {
  height: 160px;
}

.odontogram-grid {
  overflow-x: auto;
}

.odontogram-grid.click-to-apply-active {
  cursor: crosshair;
}

.odontogram-grid.click-to-apply-active .tooth-cell {
  cursor: crosshair;
}
</style>
