<script setup lang="ts">
import type { Surface, TreatmentStatus, TreatmentType } from '~/types'
import { getOcclusalPath, getLateralPath, isUpperTooth, TREATMENT_COLORS, PATTERN_DEFINITIONS } from './ToothSVGPaths'
import { getToothNameKey, getToothPositionKeys } from '~/config/odontogramConstants'

const props = defineProps<{
  open: boolean
  toothNumber: number
  treatmentType: TreatmentType
  status: TreatmentStatus
}>()

const emit = defineEmits<{
  'update:open': [value: boolean]
  confirm: [surfaces: Surface[]]
  cancel: []
}>()

const { t } = useI18n()

// Selected surfaces
const selectedSurfaces = ref<Surface[]>([])

// All surfaces
const allSurfaces: Surface[] = ['M', 'D', 'O', 'V', 'L']

// Get paths for the tooth
const occlusalPaths = computed(() => getOcclusalPath(props.toothNumber))
const lateralPaths = computed(() => getLateralPath(props.toothNumber))
const isUpper = computed(() => isUpperTooth(props.toothNumber))
const toothName = computed(() => {
  const nameKey = getToothNameKey(props.toothNumber)
  const positionKeys = getToothPositionKeys(props.toothNumber)
  return `${t(nameKey)} ${t(positionKeys.vertical)} ${t(positionKeys.horizontal)}`
})

// Treatment color
const treatmentColor = computed(() => TREATMENT_COLORS[props.treatmentType] || '#3B82F6')

// Toggle surface selection
function toggleSurface(surface: Surface) {
  const index = selectedSurfaces.value.indexOf(surface)
  if (index >= 0) {
    selectedSurfaces.value.splice(index, 1)
  } else {
    selectedSurfaces.value.push(surface)
  }
}

// Check if surface is selected
function isSurfaceSelected(surface: Surface): boolean {
  return selectedSurfaces.value.includes(surface)
}

// Get surface fill color
function getSurfaceFill(surface: Surface): string {
  if (isSurfaceSelected(surface)) {
    if (props.status === 'planned') {
      return 'url(#surface-pattern)'
    }
    return treatmentColor.value
  }
  return '#FFFFFF'
}

// Get surface opacity
function getSurfaceOpacity(surface: Surface): number {
  return isSurfaceSelected(surface) ? 0.8 : 1
}

// Confirm selection
function handleConfirm() {
  if (selectedSurfaces.value.length > 0) {
    emit('confirm', [...selectedSurfaces.value])
  }
  selectedSurfaces.value = []
  emit('update:open', false)
}

// Cancel selection
function handleCancel() {
  selectedSurfaces.value = []
  emit('cancel')
  emit('update:open', false)
}

// Reset when opening
watch(() => props.open, (isOpen) => {
  if (isOpen) {
    selectedSurfaces.value = []
  }
})
</script>

<template>
  <UModal
    :open="open"
    @update:open="handleCancel"
  >
    <template #header>
      <div class="flex items-center gap-3">
        <div
          class="w-8 h-8 rounded-lg flex items-center justify-center"
          :style="{ backgroundColor: treatmentColor + '20' }"
        >
          <div
            class="w-3 h-3 rounded-full"
            :style="{ backgroundColor: treatmentColor }"
          />
        </div>
        <div>
          <h3 class="text-base font-semibold">
            {{ t('odontogram.selectSurfaces') }}
          </h3>
          <p class="text-sm text-gray-500">
            {{ t(`odontogram.treatments.types.${treatmentType}`) }} - {{ t('odontogram.tooth') }} {{ toothNumber }}
          </p>
        </div>
      </div>
    </template>

    <template #body>
      <div class="surface-selector">
        <!-- Tooth visualization -->
        <div class="tooth-views">
          <!-- Occlusal View -->
          <div class="view-container">
            <div class="view-label">{{ t('odontogram.views.occlusal') }}</div>
            <svg
              width="160"
              height="160"
              viewBox="0 0 50 50"
              class="tooth-svg"
            >
              <!-- Pattern definition -->
              <defs>
                <pattern id="surface-pattern" patternUnits="userSpaceOnUse" width="4" height="4" patternTransform="rotate(45)">
                  <line x1="0" y1="0" x2="0" y2="4" :stroke="treatmentColor" stroke-width="2" />
                </pattern>
              </defs>

              <!-- Outline -->
              <path
                :d="occlusalPaths.outline"
                fill="#F8FAFC"
                stroke="#94A3B8"
                stroke-width="1"
              />

              <!-- Surfaces (clickable) -->
              <path
                v-for="(path, surface) in occlusalPaths.surfaces"
                :key="surface"
                :d="path"
                :fill="getSurfaceFill(surface as Surface)"
                :opacity="getSurfaceOpacity(surface as Surface)"
                :stroke="isSurfaceSelected(surface as Surface) ? treatmentColor : '#CBD5E1'"
                :stroke-width="isSurfaceSelected(surface as Surface) ? 2 : 0.5"
                class="surface-path"
                @click="toggleSurface(surface as Surface)"
              />

              <!-- Surface labels -->
              <text x="4" y="27" class="surface-label" @click="toggleSurface('M')">M</text>
              <text x="43" y="27" class="surface-label" @click="toggleSurface('D')">D</text>
              <text x="24" y="8" class="surface-label" @click="toggleSurface('V')">V</text>
              <text x="24" y="47" class="surface-label" @click="toggleSurface('L')">L</text>
              <text x="24" y="28" class="surface-label-center" @click="toggleSurface('O')">O</text>
            </svg>
          </div>

          <!-- Lateral View -->
          <div class="view-container">
            <div class="view-label">{{ t('odontogram.views.lateral') }}</div>
            <svg
              width="160"
              height="200"
              viewBox="0 0 50 80"
              class="tooth-svg lateral"
              :style="{ transform: isUpper ? 'scaleY(-1)' : 'none' }"
            >
              <!-- Gum line -->
              <path
                :d="lateralPaths.gumLine"
                fill="none"
                stroke="#FDA4AF"
                stroke-width="2"
              />

              <!-- Roots -->
              <template v-if="'root' in lateralPaths">
                <path
                  :d="lateralPaths.root"
                  fill="#FEF3C7"
                  stroke="#D4A574"
                  stroke-width="0.75"
                />
              </template>
              <template v-else-if="'roots' in lateralPaths">
                <path
                  v-for="(rootPath, idx) in lateralPaths.roots"
                  :key="idx"
                  :d="rootPath"
                  fill="#FEF3C7"
                  stroke="#D4A574"
                  stroke-width="0.75"
                />
              </template>

              <!-- Crown -->
              <path
                :d="lateralPaths.crown"
                fill="#F8FAFC"
                stroke="#94A3B8"
                stroke-width="1"
              />
            </svg>
          </div>
        </div>

        <!-- Surface buttons -->
        <div class="surface-buttons">
          <button
            v-for="surface in allSurfaces"
            :key="surface"
            type="button"
            class="surface-btn"
            :class="{ selected: isSurfaceSelected(surface) }"
            :style="isSurfaceSelected(surface) ? { borderColor: treatmentColor, backgroundColor: treatmentColor + '15' } : {}"
            @click="toggleSurface(surface)"
          >
            <span class="surface-letter">{{ surface }}</span>
            <span class="surface-name">{{ t(`odontogram.surfaces.${surface}`) }}</span>
          </button>
        </div>

        <!-- Selected surfaces summary -->
        <div v-if="selectedSurfaces.length > 0" class="selected-summary">
          <span class="summary-label">{{ t('odontogram.selectedSurfaces') }}:</span>
          <div class="summary-badges">
            <span
              v-for="surface in selectedSurfaces"
              :key="surface"
              class="summary-badge"
              :style="{ backgroundColor: treatmentColor + '20', color: treatmentColor }"
            >
              {{ surface }} - {{ t(`odontogram.surfaces.${surface}`) }}
            </span>
          </div>
        </div>

        <!-- Tooth info -->
        <div class="tooth-info">
          <UIcon name="i-lucide-info" class="w-4 h-4" />
          <span>{{ toothName }}</span>
        </div>
      </div>
    </template>

    <template #footer>
      <div class="flex justify-between items-center w-full">
        <span class="text-sm text-gray-500">
          {{ selectedSurfaces.length }} {{ t('odontogram.surfacesSelected') }}
        </span>
        <div class="flex gap-2">
          <UButton
            color="neutral"
            variant="ghost"
            @click="handleCancel"
          >
            {{ t('common.cancel') }}
          </UButton>
          <UButton
            color="primary"
            :disabled="selectedSurfaces.length === 0"
            @click="handleConfirm"
          >
            {{ t('common.confirm') }}
          </UButton>
        </div>
      </div>
    </template>
  </UModal>
</template>

<style scoped>
.surface-selector {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.tooth-views {
  display: flex;
  justify-content: center;
  gap: 32px;
}

.view-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.view-label {
  font-size: 12px;
  font-weight: 500;
  color: #6B7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.tooth-svg {
  background: #FAFAFA;
  border-radius: 12px;
  padding: 8px;
}

:root.dark .tooth-svg {
  background: #27272A;
}

.tooth-svg.lateral {
  transform-origin: center;
}

.surface-path {
  cursor: pointer;
  transition: all 0.15s ease;
}

.surface-path:hover {
  filter: brightness(0.95);
}

.surface-label,
.surface-label-center {
  font-size: 6px;
  font-weight: 600;
  fill: #6B7280;
  text-anchor: middle;
  cursor: pointer;
  user-select: none;
}

.surface-label-center {
  fill: #9CA3AF;
}

/* Surface buttons */
.surface-buttons {
  display: flex;
  justify-content: center;
  gap: 8px;
  flex-wrap: wrap;
}

.surface-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 12px 16px;
  border: 2px solid #E5E7EB;
  border-radius: 10px;
  background: white;
  transition: all 0.15s ease;
  min-width: 80px;
}

:root.dark .surface-btn {
  background: #27272A;
  border-color: #3F3F46;
}

.surface-btn:hover {
  border-color: #93C5FD;
  transform: translateY(-1px);
}

.surface-btn.selected {
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
}

.surface-letter {
  font-size: 18px;
  font-weight: 700;
  color: #374151;
}

:root.dark .surface-letter {
  color: #E5E7EB;
}

.surface-name {
  font-size: 11px;
  color: #6B7280;
}

/* Selected summary */
.selected-summary {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
  background: #F9FAFB;
  border-radius: 8px;
}

:root.dark .selected-summary {
  background: #27272A;
}

.summary-label {
  font-size: 12px;
  font-weight: 500;
  color: #6B7280;
}

.summary-badges {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.summary-badge {
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
}

/* Tooth info */
.tooth-info {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  font-size: 13px;
  color: #6B7280;
  padding: 8px;
  background: #F4F4F5;
  border-radius: 6px;
}

:root.dark .tooth-info {
  background: #27272A;
  color: #A1A1AA;
}
</style>
