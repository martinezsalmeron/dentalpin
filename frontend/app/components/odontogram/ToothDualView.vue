<script setup lang="ts">
import type { Surface, Treatment, TreatmentStatus } from '~/types'
import {
  getOcclusalPath,
  getLateralPath,
  getToothTransform,
  getToothDisplayConfig,
  isUpperTooth,
  isDeciduousTooth,
  PATTERN_DEFINITIONS,
  STATUS_STYLES,
  TREATMENT_COLORS,
  TREATMENT_OVERLAYS,
  makesToothTransparent,
  SURFACE_TREATMENT_TYPES
} from './ToothSVGPaths'
import { getToothNameKey, getToothPositionKeys } from '~/config/odontogramConstants'

const props = defineProps<{
  toothNumber: number
  generalCondition: string
  treatments?: Treatment[]
  readonly?: boolean
  selected?: boolean
  showLateral?: boolean
  isDisplaced?: boolean
  isRotated?: boolean
  isHovered?: boolean
  isHighlighted?: boolean
  pendingTreatment?: { type: string, status: TreatmentStatus } | null
}>()

const emit = defineEmits<{
  surfaceClick: [surface: Surface]
  toothClick: []
  treatmentClick: [treatment: Treatment]
}>()

const { t } = useI18n()

const isUpper = computed(() => isUpperTooth(props.toothNumber))
const isDeciduous = computed(() => isDeciduousTooth(props.toothNumber))
const occlusalPaths = computed(() => getOcclusalPath(props.toothNumber))
const lateralPaths = computed(() => getLateralPath(props.toothNumber))

// Quadrant-based transform for symmetry (napkin unfolding)
const toothTransform = computed(() => getToothTransform(props.toothNumber))

// Lateral view: use the viewBox from the tooth paths (dynamic per tooth type)
const lateralViewBox = computed(() => lateralPaths.value.viewBox)

// Get display configuration for this tooth (scale and alignment)
const displayConfig = computed(() => getToothDisplayConfig(props.toothNumber))

// Parse viewBox dimensions and calculate display size with proper scaling
const lateralDimensions = computed(() => {
  const vb = lateralViewBox.value.split(' ').map(Number)
  const vbWidth = vb[2] || 60
  const vbHeight = vb[3] || 130
  const aspectRatio = vbWidth / vbHeight

  // Base display width, adjusted by scale factor
  const baseWidth = 55
  const displayWidth = Math.round(baseWidth * displayConfig.value.scale)
  const displayHeight = Math.round(displayWidth / aspectRatio)

  return { displayWidth, displayHeight }
})
const lateralDisplayWidth = computed(() => lateralDimensions.value.displayWidth)
const lateralDisplayHeight = computed(() => lateralDimensions.value.displayHeight)

const _toothName = computed(() => {
  const nameKey = getToothNameKey(props.toothNumber)
  const positionKeys = getToothPositionKeys(props.toothNumber)
  return `${t(nameKey)} ${t(positionKeys.vertical)} ${t(positionKeys.horizontal)}`
})

// Check if tooth should be transparent (extracted/missing)
const isToothTransparent = computed(() => {
  if (props.generalCondition === 'missing' || props.generalCondition === 'extraction_indicated') {
    return true
  }
  return props.treatments?.some(t =>
    makesToothTransparent(t.treatment_type) && t.status === 'performed'
  ) || false
})

const toothOpacity = computed(() => {
  if (isToothTransparent.value) return 0.25
  return 1
})

function handleToothClick() {
  emit('toothClick')
}

const toothTreatments = computed(() => props.treatments || [])

function hasTreatment(type: string, status?: TreatmentStatus): boolean {
  return toothTreatments.value.some(t =>
    t.treatment_type === type && (status === undefined || t.status === status)
  )
}

function getTreatmentOfType(type: string): Treatment | undefined {
  return toothTreatments.value.find(t => t.treatment_type === type)
}

function isSurfaceTreatment(type: string): boolean {
  return SURFACE_TREATMENT_TYPES.includes(type)
}

function getCrownFill(_treatment: Treatment): string {
  return TREATMENT_COLORS.crown || '#F59E0B'
}

function getImplantFill(_treatment: Treatment): string {
  return TREATMENT_COLORS.implant || '#10B981'
}

const showingPreview = computed(() => props.isHovered && props.pendingTreatment)
</script>

<template>
  <div
    class="tooth-dual-view-wrapper"
    :class="{
      'selected': selected,
      'readonly': readonly,
      'displaced': isDisplaced,
      'rotated': isRotated,
      'transparent': isToothTransparent,
      'highlighted': isHighlighted,
      'has-preview': showingPreview,
      'is-upper': isUpper,
      'is-lower': !isUpper,
      'is-deciduous': isDeciduous
    }"
    @click="handleToothClick"
  >
    <!-- Position indicators -->
    <div
      v-if="isDisplaced || isRotated"
      class="position-indicators"
    >
      <span
        v-if="isDisplaced"
        class="indicator-displaced"
        title="Desplazado"
      />
      <span
        v-if="isRotated"
        class="indicator-rotated"
        title="Rotado"
      />
    </div>

    <!-- Lateral View Container - fixed height for alignment -->
    <div
      v-if="showLateral"
      class="lateral-view-container"
      :class="{ upper: isUpper, lower: !isUpper }"
    >
      <svg
        :width="lateralDisplayWidth"
        :height="lateralDisplayHeight"
        :viewBox="lateralViewBox"
        class="lateral-view"
        :style="{
          transform: toothTransform,
          transformOrigin: 'center center',
          opacity: toothOpacity
        }"
      >
        <!-- Roots (render first, behind crown) -->
        <g class="roots">
          <!-- Single root -->
          <template v-if="'root' in lateralPaths && lateralPaths.root">
            <path
              :d="lateralPaths.root"
              class="tooth-root"
              stroke-width="0.6"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </template>
          <!-- Multiple roots -->
          <template v-else-if="'roots' in lateralPaths && lateralPaths.roots">
            <path
              v-for="(rootPath, idx) in lateralPaths.roots"
              :key="idx"
              :d="rootPath"
              class="tooth-root"
              stroke-width="0.6"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </template>
        </g>

        <!-- Crown -->
        <g class="crown">
          <!-- Crown outline -->
          <path
            :d="lateralPaths.crown"
            class="tooth-crown"
            stroke-width="0.6"
            stroke-linecap="round"
            stroke-linejoin="round"
          />

          <!-- Highlight details (enamel lines, cusps) -->
          <path
            v-for="(highlightPath, idx) in lateralPaths.highlight"
            :key="`highlight-${idx}`"
            :d="highlightPath"
            class="tooth-highlight"
            stroke-width="0.35"
            stroke-linecap="round"
            stroke-linejoin="round"
            fill="none"
          />
        </g>

        <!-- Treatment overlays on lateral view -->
        <g class="treatment-overlays-lateral">
          <!-- Surface treatments (filling, caries, sealant) - show as colored area on crown -->
          <template
            v-for="treatment in toothTreatments"
            :key="`lateral-surface-${treatment.id}`"
          >
            <g
              v-if="isSurfaceTreatment(treatment.treatment_type)"
              class="surface-treatment-lateral"
            >
              <path
                :d="lateralPaths.crown"
                :fill="TREATMENT_COLORS[treatment.treatment_type] || '#3B82F6'"
                :fill-opacity="STATUS_STYLES[treatment.status].opacity * 0.5"
                :stroke="STATUS_STYLES[treatment.status].border || 'none'"
                :stroke-width="STATUS_STYLES[treatment.status].borderWidth"
                :stroke-dasharray="STATUS_STYLES[treatment.status].borderDash || 'none'"
              />
            </g>
          </template>

          <!-- Crown treatment - gold crown -->
          <g
            v-if="hasTreatment('crown')"
            class="crown-treatment"
          >
            <path
              :d="lateralPaths.crown"
              :fill="getCrownFill(getTreatmentOfType('crown')!)"
              :stroke="STATUS_STYLES[getTreatmentOfType('crown')!.status].border || 'none'"
              :stroke-width="STATUS_STYLES[getTreatmentOfType('crown')!.status].borderWidth"
              :stroke-dasharray="STATUS_STYLES[getTreatmentOfType('crown')!.status].borderDash || 'none'"
            />
          </g>

          <!-- Implant treatment -->
          <g
            v-if="hasTreatment('implant')"
            class="implant-treatment"
          >
            <path
              :d="TREATMENT_OVERLAYS.implant.fixture"
              :fill="getImplantFill(getTreatmentOfType('implant')!)"
              stroke="#6B7280"
              stroke-width="1"
            />
            <path
              v-for="(thread, idx) in TREATMENT_OVERLAYS.implant.threads"
              :key="idx"
              :d="thread"
              fill="none"
              stroke="#52525B"
              stroke-width="1"
            />
            <path
              :d="TREATMENT_OVERLAYS.implant.abutment"
              :fill="getImplantFill(getTreatmentOfType('implant')!)"
              stroke="#6B7280"
              stroke-width="1"
            />
            <path
              :d="TREATMENT_OVERLAYS.implant.head"
              class="tooth-crown"
              stroke-width="1"
            />
          </g>

          <!-- Root canal indicator -->
          <g
            v-if="hasTreatment('root_canal')"
            class="root-canal-treatment"
          >
            <path
              :d="TREATMENT_OVERLAYS.rootCanal.indicator"
              :fill="TREATMENT_COLORS.root_canal"
              :opacity="STATUS_STYLES[getTreatmentOfType('root_canal')!.status].opacity"
              :stroke="STATUS_STYLES[getTreatmentOfType('root_canal')!.status].border || 'none'"
              stroke-width="1"
              :stroke-dasharray="STATUS_STYLES[getTreatmentOfType('root_canal')!.status].borderDash || 'none'"
            />
          </g>

          <!-- Post indicator -->
          <g
            v-if="hasTreatment('post')"
            class="post-treatment"
          >
            <path
              :d="TREATMENT_OVERLAYS.post.shaft"
              :fill="TREATMENT_COLORS.post"
              :opacity="STATUS_STYLES[getTreatmentOfType('post')!.status].opacity"
              stroke="#6B7280"
              stroke-width="0.5"
            />
          </g>

          <!-- Veneer overlay -->
          <g
            v-if="hasTreatment('veneer')"
            class="veneer-treatment"
          >
            <path
              :d="TREATMENT_OVERLAYS.veneer.surface"
              :fill="TREATMENT_COLORS.veneer"
              :opacity="STATUS_STYLES[getTreatmentOfType('veneer')!.status].opacity * 0.6"
              :stroke="STATUS_STYLES[getTreatmentOfType('veneer')!.status].border || 'none'"
              stroke-width="1"
              :stroke-dasharray="STATUS_STYLES[getTreatmentOfType('veneer')!.status].borderDash || 'none'"
            />
          </g>

          <!-- Extraction indicator on lateral view -->
          <g
            v-if="hasTreatment('extraction')"
            class="extraction-treatment-lateral"
          >
            <line
              x1="12"
              y1="5"
              x2="38"
              y2="25"
              stroke="#DC2626"
              stroke-width="2"
              :stroke-dasharray="STATUS_STYLES[getTreatmentOfType('extraction')!.status].borderDash || 'none'"
              stroke-linecap="round"
            />
            <line
              x1="38"
              y1="5"
              x2="12"
              y2="25"
              stroke="#DC2626"
              stroke-width="2"
              :stroke-dasharray="STATUS_STYLES[getTreatmentOfType('extraction')!.status].borderDash || 'none'"
              stroke-linecap="round"
            />
          </g>
        </g>
      </svg>
    </div>

    <!-- Occlusal View (Top-down) -->
    <svg
      width="55"
      height="55"
      viewBox="0 0 50 50"
      class="occlusal-view"
      :style="{
        opacity: toothOpacity,
        transform: toothTransform,
        transformOrigin: 'center center'
      }"
    >
      <!-- SVG Patterns and Gradients Definition -->
      <defs v-html="PATTERN_DEFINITIONS" />

      <!-- Background - pointer-events none to let clicks pass through to surfaces -->
      <rect
        x="0"
        y="0"
        width="50"
        height="50"
        fill="transparent"
        pointer-events="none"
      />

      <!-- Background outline -->
      <path
        :d="occlusalPaths.outline"
        class="tooth-occlusal"
        stroke-width="1"
        stroke-linecap="round"
        stroke-linejoin="round"
        pointer-events="none"
      />

      <!-- Highlight details (fissures, ridges) -->
      <path
        v-for="(highlightPath, idx) in occlusalPaths.highlight"
        :key="`occlusal-highlight-${idx}`"
        :d="highlightPath"
        class="tooth-highlight"
        stroke-width="0.6"
        stroke-linecap="round"
        stroke-linejoin="round"
        fill="none"
        pointer-events="none"
      />

      <!-- Treatment overlays on occlusal view -->
      <g class="treatment-overlays">
        <template
          v-for="treatment in toothTreatments"
          :key="treatment.id"
        >
          <!-- Surface treatments with specific surfaces -->
          <template v-if="isSurfaceTreatment(treatment.treatment_type) && treatment.surfaces && treatment.surfaces.length > 0">
            <g
              v-for="surface in treatment.surfaces"
              :key="`${treatment.id}-${surface}`"
              class="treatment-surface-overlay"
            >
              <path
                :d="occlusalPaths.surfaces[surface]"
                :fill="TREATMENT_COLORS[treatment.treatment_type] || '#3B82F6'"
                :stroke="STATUS_STYLES[treatment.status].border || TREATMENT_COLORS[treatment.treatment_type] || 'none'"
                :stroke-width="STATUS_STYLES[treatment.status].borderWidth || 1.25"
                :stroke-dasharray="STATUS_STYLES[treatment.status].borderDash || 'none'"
              />
            </g>
          </template>

          <!-- Surface treatments without specific surfaces - show as overlay on occlusal center -->
          <template v-else-if="isSurfaceTreatment(treatment.treatment_type) && (!treatment.surfaces || treatment.surfaces.length === 0)">
            <path
              :d="occlusalPaths.surfaces.O"
              :fill="TREATMENT_COLORS[treatment.treatment_type] || '#3B82F6'"
              :stroke="STATUS_STYLES[treatment.status].border || TREATMENT_COLORS[treatment.treatment_type] || 'none'"
              :stroke-width="STATUS_STYLES[treatment.status].borderWidth || 1.25"
              :stroke-dasharray="STATUS_STYLES[treatment.status].borderDash || 'none'"
              class="treatment-surface-overlay"
            />
          </template>

          <!-- Crown overlay -->
          <g
            v-else-if="treatment.treatment_type === 'crown'"
            class="crown-overlay"
          >
            <path
              :d="occlusalPaths.outline"
              :fill="getCrownFill(treatment)"
              :stroke="STATUS_STYLES[treatment.status].border || 'none'"
              :stroke-width="STATUS_STYLES[treatment.status].borderWidth"
              :stroke-dasharray="STATUS_STYLES[treatment.status].borderDash || 'none'"
            />
          </g>

          <!-- Orthodontic treatments (bracket, band, attachment, retainer) -->
          <g
            v-else-if="['bracket', 'band', 'attachment', 'retainer'].includes(treatment.treatment_type)"
            class="orthodontic-indicator"
          >
            <circle
              cx="40"
              cy="40"
              r="7"
              :fill="TREATMENT_COLORS[treatment.treatment_type] || '#6366F1'"
              :fill-opacity="STATUS_STYLES[treatment.status].opacity"
              :stroke="STATUS_STYLES[treatment.status].border || '#FFFFFF'"
              :stroke-width="STATUS_STYLES[treatment.status].borderWidth || 1.25"
              :stroke-dasharray="STATUS_STYLES[treatment.status].borderDash || 'none'"
            />
            <text
              x="40"
              y="43"
              text-anchor="middle"
              fill="white"
              font-size="7"
              font-weight="bold"
            >
              {{ treatment.treatment_type === 'bracket' ? 'B' : treatment.treatment_type === 'band' ? 'Bd' : treatment.treatment_type === 'attachment' ? 'A' : 'R' }}
            </text>
          </g>

          <!-- Whole tooth treatments (root_canal, extraction, etc.) -->
          <g
            v-else-if="!isSurfaceTreatment(treatment.treatment_type) && treatment.treatment_type !== 'crown' && treatment.treatment_type !== 'implant'"
            class="whole-tooth-indicator"
          >
            <path
              :d="occlusalPaths.outline"
              :fill="TREATMENT_COLORS[treatment.treatment_type] || '#9CA3AF'"
              :fill-opacity="STATUS_STYLES[treatment.status].opacity * 0.4"
              :stroke="STATUS_STYLES[treatment.status].border || TREATMENT_COLORS[treatment.treatment_type] || '#9CA3AF'"
              :stroke-width="STATUS_STYLES[treatment.status].borderWidth || 2"
              :stroke-dasharray="STATUS_STYLES[treatment.status].borderDash || 'none'"
            />
          </g>
        </template>
      </g>

      <!-- Missing tooth X overlay -->
      <g
        v-if="generalCondition === 'missing'"
        class="missing-indicator"
        pointer-events="none"
      >
        <line
          x1="8"
          y1="8"
          x2="42"
          y2="42"
          stroke="#6B7280"
          stroke-width="2.5"
          stroke-linecap="round"
        />
        <line
          x1="42"
          y1="8"
          x2="8"
          y2="42"
          stroke="#6B7280"
          stroke-width="2.5"
          stroke-linecap="round"
        />
      </g>

      <!-- Extraction indicated marker -->
      <g
        v-if="generalCondition === 'extraction_indicated'"
        class="extraction-indicator"
        pointer-events="none"
      >
        <line
          x1="10"
          y1="10"
          x2="40"
          y2="40"
          stroke="#DC2626"
          stroke-width="2"
          stroke-dasharray="5,3"
          stroke-linecap="round"
        />
        <line
          x1="40"
          y1="10"
          x2="10"
          y2="40"
          stroke="#DC2626"
          stroke-width="2"
          stroke-dasharray="5,3"
          stroke-linecap="round"
        />
      </g>

      <!-- Preview overlay for pending treatment -->
      <g
        v-if="showingPreview"
        class="preview-overlay"
        opacity="0.5"
        pointer-events="none"
      >
        <path
          :d="occlusalPaths.outline"
          :fill="TREATMENT_COLORS[pendingTreatment!.type] || '#3B82F6'"
          stroke="var(--odontogram-selected)"
          stroke-width="2"
        />
      </g>

      <!-- Selection highlight -->
      <path
        v-if="selected"
        :d="occlusalPaths.outline"
        fill="none"
        stroke="var(--odontogram-selected)"
        stroke-width="2.5"
        class="selection-ring"
        pointer-events="none"
      />

    </svg>

    <!-- Tooth number label -->
    <div
      class="tooth-number"
      :class="{ selected: selected }"
    >
      {{ toothNumber }}
    </div>
  </div>
</template>

<style scoped>
.tooth-dual-view-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  transition: transform 0.15s ease, filter 0.15s ease;
  position: relative;
}

.tooth-dual-view-wrapper:hover {
  transform: translateY(-1px);
}

.tooth-dual-view-wrapper.readonly {
  cursor: default;
}

.tooth-dual-view-wrapper.readonly:hover {
  transform: none;
}

.tooth-dual-view-wrapper.transparent {
  opacity: 0.4;
}

.tooth-dual-view-wrapper.has-preview {
  filter: drop-shadow(0 0 4px rgba(59, 130, 246, 0.5));
}

.tooth-dual-view-wrapper.highlighted {
  filter: drop-shadow(0 0 6px rgba(245, 158, 11, 0.6));
  animation: highlight-pulse 1s ease-in-out infinite;
}

/* Tooth SVG styling using CSS variables */
.tooth-crown,
.tooth-occlusal {
  fill: var(--odontogram-fill);
  stroke: var(--odontogram-outline);
  transition: fill 0.15s ease, stroke 0.15s ease;
}

.tooth-root {
  fill: var(--odontogram-root-fill);
  stroke: var(--odontogram-outline);
  transition: fill 0.15s ease, stroke 0.15s ease;
}

.tooth-highlight {
  stroke: var(--odontogram-detail);
  transition: stroke 0.15s ease;
}

.position-indicators {
  position: absolute;
  top: 0;
  right: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
  z-index: 10;
}

.indicator-displaced,
.indicator-rotated {
  display: block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  border: 1.5px solid white;
  box-shadow: 0 1px 2px rgba(0,0,0,0.2);
}

.indicator-displaced {
  background: #F59E0B;
}

.indicator-rotated {
  background: #8B5CF6;
}

@keyframes highlight-pulse {
  0%, 100% {
    filter: drop-shadow(0 0 6px rgba(245, 158, 11, 0.6));
  }
  50% {
    filter: drop-shadow(0 0 10px rgba(245, 158, 11, 0.8));
  }
}

.tooth-number {
  font-size: 10px;
  color: var(--color-gray-600);
  font-weight: 600;
  user-select: none;
  text-align: center;
  margin-top: 2px;
  transition: color 0.15s ease;
}

.tooth-number.selected {
  color: var(--odontogram-selected);
}

:root.dark .tooth-number {
  color: var(--color-gray-400);
}

.surface {
  transition: opacity 0.15s ease;
  pointer-events: all;
}

.surface.clickable:hover {
  opacity: 0.85;
}

/* Lateral view container - fixed height for alignment across all teeth */
.lateral-view-container {
  display: flex;
  justify-content: center;
  width: 100%;
  height: 100px; /* Fixed height for consistent crown alignment */
}

/* Upper teeth: align SVG to bottom so crowns line up */
.lateral-view-container.upper {
  align-items: flex-end;
}

/* Lower teeth: align SVG to top so crowns line up (after scaleY flip) */
.lateral-view-container.lower {
  align-items: flex-start;
}

.lateral-view {
  display: block;
  flex-shrink: 0;
}

.occlusal-view {
  display: block;
  pointer-events: all;
}

/* For UPPER teeth: lateral first (order 1), occlusal second (order 2) */
/* For LOWER teeth: occlusal first (order 1), lateral second (order 2) */
.tooth-dual-view-wrapper.is-upper .lateral-view-container {
  order: 1;
}

.tooth-dual-view-wrapper.is-upper .occlusal-view {
  order: 2;
}

.tooth-dual-view-wrapper.is-lower .lateral-view-container {
  order: 2;
}

.tooth-dual-view-wrapper.is-lower .occlusal-view {
  order: 1;
}

.tooth-dual-view-wrapper.is-lower .tooth-number {
  order: 3;
}

.tooth-dual-view-wrapper.is-upper .tooth-number {
  order: 3;
}

.treatment-overlays,
.treatment-overlays-lateral {
  pointer-events: none;
}

.selection-ring {
  animation: pulse-ring 1.5s ease-in-out infinite;
}

@keyframes pulse-ring {
  0%, 100% {
    stroke-opacity: 1;
  }
  50% {
    stroke-opacity: 0.6;
  }
}

.preview-overlay {
  pointer-events: none;
  animation: preview-pulse 1s ease-in-out infinite;
}

@keyframes preview-pulse {
  0%, 100% {
    opacity: 0.4;
  }
  50% {
    opacity: 0.6;
  }
}

.crown-treatment path,
.crown-overlay path {
  filter: drop-shadow(0 1px 2px rgba(180, 83, 9, 0.3));
}

.implant-treatment path {
  filter: drop-shadow(0 1px 1px rgba(0,0,0,0.2));
}
</style>
