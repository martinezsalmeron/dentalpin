<script setup lang="ts">
import type { Surface, Treatment, TreatmentStatus } from '~/types'
import {
  getOcclusalPath,
  getLateralPath,
  isUpperTooth,
  PATTERN_DEFINITIONS,
  STATUS_STYLES,
  TREATMENT_COLORS,
  TREATMENT_OVERLAYS,
  TOOTH_COLORS,
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
const occlusalPaths = computed(() => getOcclusalPath(props.toothNumber))
const lateralPaths = computed(() => getLateralPath(props.toothNumber))
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
  // Crown uses solid color from TREATMENT_COLORS
  return TREATMENT_COLORS.crown || '#F59E0B'
}

function getImplantFill(_treatment: Treatment): string {
  // Implant uses solid color from TREATMENT_COLORS
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
      'is-lower': !isUpper
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

    <!-- For UPPER teeth: Lateral first (top), then Occlusal (bottom) -->
    <!-- For LOWER teeth: Occlusal first (top), then Lateral (bottom) -->

    <!-- Lateral View - shown FIRST for upper teeth -->
    <svg
      v-if="showLateral"
      width="55"
      height="88"
      viewBox="0 0 50 80"
      class="lateral-view"
      :class="{ upper: isUpper, lower: !isUpper }"
      :style="{
        transform: isUpper ? 'scaleY(-1)' : 'none',
        opacity: toothOpacity
      }"
    >
      <!-- Roots (render first, behind crown) -->
      <g class="roots">
        <!-- Single root -->
        <template v-if="'root' in lateralPaths">
          <!-- Root inner shading -->
          <path
            v-if="'rootInner' in lateralPaths"
            :d="lateralPaths.rootInner"
            :fill="TOOTH_COLORS.fillShade"
            stroke="none"
          />
          <!-- Root outline -->
          <path
            :d="lateralPaths.root"
            :fill="TOOTH_COLORS.fill"
            :stroke="TOOTH_COLORS.outline"
            stroke-width="1.5"
          />
        </template>
        <!-- Multiple roots -->
        <template v-else-if="'roots' in lateralPaths">
          <!-- Roots inner shading -->
          <template v-if="'rootsInner' in lateralPaths">
            <path
              v-for="(rootPath, idx) in lateralPaths.rootsInner"
              :key="`inner-${idx}`"
              :d="rootPath"
              :fill="TOOTH_COLORS.fillShade"
              stroke="none"
            />
          </template>
          <!-- Roots outline -->
          <path
            v-for="(rootPath, idx) in lateralPaths.roots"
            :key="idx"
            :d="rootPath"
            :fill="TOOTH_COLORS.fill"
            :stroke="TOOTH_COLORS.outline"
            stroke-width="1.5"
          />
        </template>
      </g>

      <!-- Crown -->
      <g class="crown">
        <!-- Crown inner shading -->
        <path
          v-if="'crownInner' in lateralPaths"
          :d="lateralPaths.crownInner"
          :fill="TOOTH_COLORS.fillShade"
          stroke="none"
        />
        <!-- Crown shading detail -->
        <path
          v-if="'crownShading' in lateralPaths"
          :d="lateralPaths.crownShading"
          :fill="TOOTH_COLORS.fillShade"
          :stroke="TOOTH_COLORS.outlineLight"
          stroke-width="0.5"
          opacity="0.5"
        />
        <!-- Crown cusps for molars/premolars -->
        <path
          v-if="'crownCusps' in lateralPaths"
          :d="lateralPaths.crownCusps"
          fill="none"
          :stroke="TOOTH_COLORS.outlineLight"
          stroke-width="0.75"
          opacity="0.6"
        />
        <!-- Crown outline -->
        <path
          :d="lateralPaths.crown"
          :fill="TOOTH_COLORS.fill"
          :stroke="TOOTH_COLORS.outline"
          stroke-width="1.5"
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
            <!-- Show a colored overlay on the crown for surface treatments -->
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
            :fill="TOOTH_COLORS.fill"
            :stroke="TOOTH_COLORS.outline"
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
            stroke-width="2.5"
            :stroke-dasharray="STATUS_STYLES[getTreatmentOfType('extraction')!.status].borderDash || 'none'"
            stroke-linecap="round"
          />
          <line
            x1="38"
            y1="5"
            x2="12"
            y2="25"
            stroke="#DC2626"
            stroke-width="2.5"
            :stroke-dasharray="STATUS_STYLES[getTreatmentOfType('extraction')!.status].borderDash || 'none'"
            stroke-linecap="round"
          />
        </g>
      </g>
    </svg>

    <!-- Occlusal View (Top-down) -->
    <svg
      width="55"
      height="55"
      viewBox="0 0 50 50"
      class="occlusal-view"
      :style="{ opacity: toothOpacity }"
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
        :fill="TOOTH_COLORS.fill"
        :stroke="TOOTH_COLORS.outline"
        stroke-width="1.5"
        pointer-events="none"
      />

      <!-- Inner detail (characteristic shape) -->
      <path
        v-if="occlusalPaths.innerDetail"
        :d="occlusalPaths.innerDetail"
        fill="none"
        :stroke="TOOTH_COLORS.outlineLight"
        stroke-width="0.75"
        opacity="0.6"
        pointer-events="none"
      />

      <!-- Cross pattern for molars/premolars -->
      <path
        v-if="occlusalPaths.crossPattern"
        :d="occlusalPaths.crossPattern"
        fill="none"
        :stroke="TOOTH_COLORS.outlineLight"
        stroke-width="0.75"
        opacity="0.5"
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
              <!-- All surface treatments fill with their color -->
              <path
                :d="occlusalPaths.surfaces[surface]"
                :fill="TREATMENT_COLORS[treatment.treatment_type] || '#3B82F6'"
                :stroke="STATUS_STYLES[treatment.status].border || TREATMENT_COLORS[treatment.treatment_type] || 'none'"
                :stroke-width="STATUS_STYLES[treatment.status].borderWidth || 1.5"
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
              :stroke-width="STATUS_STYLES[treatment.status].borderWidth || 1.5"
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
            <!-- Small colored badge in bottom-right corner -->
            <circle
              cx="40"
              cy="40"
              r="8"
              :fill="TREATMENT_COLORS[treatment.treatment_type] || '#6366F1'"
              :fill-opacity="STATUS_STYLES[treatment.status].opacity"
              :stroke="STATUS_STYLES[treatment.status].border || '#FFFFFF'"
              :stroke-width="STATUS_STYLES[treatment.status].borderWidth || 1.5"
              :stroke-dasharray="STATUS_STYLES[treatment.status].borderDash || 'none'"
            />
            <!-- Small icon indicator inside the badge -->
            <text
              x="40"
              y="43"
              text-anchor="middle"
              fill="white"
              font-size="8"
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
            <!-- Fill the tooth with treatment color -->
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
          stroke-width="3"
          stroke-linecap="round"
        />
        <line
          x1="42"
          y1="8"
          x2="8"
          y2="42"
          stroke="#6B7280"
          stroke-width="3"
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
          stroke-width="2.5"
          stroke-dasharray="5,3"
          stroke-linecap="round"
        />
        <line
          x1="40"
          y1="10"
          x2="10"
          y2="40"
          stroke="#DC2626"
          stroke-width="2.5"
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
          stroke="#3B82F6"
          stroke-width="2"
        />
      </g>

      <!-- Selection highlight -->
      <path
        v-if="selected"
        :d="occlusalPaths.outline"
        fill="none"
        stroke="#3B82F6"
        stroke-width="2.5"
        class="selection-ring"
        pointer-events="none"
      />

    </svg>

    <!-- Tooth number label -->
    <div
      class="tooth-number"
      :class="{ 'text-primary-600': selected }"
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
  transition: transform 0.15s ease;
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

.position-indicators {
  position: absolute;
  top: 0;
  right: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
  z-index: 10;
  order: 0; /* Always first, but positioned absolute so it doesn't affect layout */
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
  color: #374151;
  font-weight: 600;
  user-select: none;
  text-align: center;
  margin-top: 2px;
}

.tooth-number.text-primary-600 {
  color: #2563EB;
}

:root.dark .tooth-number {
  color: #D1D5DB;
}

.surface {
  transition: opacity 0.15s ease;
  pointer-events: all;
}

.surface.clickable:hover {
  opacity: 0.85;
}

.lateral-view {
  display: block;
}

.lateral-view.upper {
  transform-origin: center;
}

.occlusal-view {
  display: block;
  pointer-events: all;
}

/* For UPPER teeth: lateral first (order 1), occlusal second (order 2) */
/* For LOWER teeth: occlusal first (order 1), lateral second (order 2) */
.tooth-dual-view-wrapper.is-upper .lateral-view {
  order: 1;
}

.tooth-dual-view-wrapper.is-upper .occlusal-view {
  order: 2;
}

.tooth-dual-view-wrapper.is-lower .lateral-view {
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

:root.dark .tooth-number {
  fill: #E5E7EB;
}
</style>
