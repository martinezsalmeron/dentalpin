<script setup lang="ts">
/**
 * ToothQuadrant - Renders a row of teeth for one quadrant
 *
 * Eliminates code duplication - used 4 times in OdontogramChart
 * (upperRight, upperLeft, lowerRight, lowerLeft)
 */

import type { Surface, ToothTreatmentView, TreatmentStatus, TreatmentType } from '~~/app/types'

const props = withDefaults(defineProps<{
  /** List of tooth numbers in this quadrant */
  teeth: readonly number[]
  /** Function to get tooth data (condition, displaced, rotated) */
  getToothData: (toothNumber: number) => {
    generalCondition: string
    isDisplaced: boolean
    isRotated: boolean
  }
  /** Per-tooth flattened Treatment views for this tooth. */
  getTreatments: (toothNumber: number) => ToothTreatmentView[]
  /** Whether chart is read-only */
  readonly: boolean
  /** Currently selected tooth number */
  selectedTooth: number | null
  /** Show lateral view */
  showLateral: boolean
  /** Currently hovered tooth */
  hoveredTooth: number | null
  /** Highlighted teeth (from summary) */
  highlightedTeeth: number[]
  /** Pending treatment for preview */
  pendingTreatment: { type: TreatmentType, status: TreatmentStatus } | null
  /** Optional: return the treatment_group_id of any group the tooth participates in. */
  getGroupId?: (toothNumber: number) => string | null
  /** Status of the group for styling (planned -> dashed, existing -> solid). */
  getGroupStatus?: (toothNumber: number) => 'existing' | 'planned' | null
  /** Optional: return the clinical_type of the group (e.g. 'bridge', 'splint'). */
  getGroupType?: (toothNumber: number) => string | null
  /** Teeth currently in an in-progress multi-tooth selection (range/free). */
  multiSelectedTeeth?: number[]
}>(), {
  getGroupId: () => () => null,
  getGroupStatus: () => () => null,
  getGroupType: () => () => null,
  multiSelectedTeeth: () => []
})

const emit = defineEmits<{
  surfaceClick: [toothNumber: number, surface: Surface]
  toothClick: [toothNumber: number]
  toothContextMenu: [toothNumber: number, event: MouseEvent]
  toothHover: [toothNumber: number | null]
  editTreatment: [treatment: ToothTreatmentView]
}>()

function isHighlighted(toothNumber: number): boolean {
  return props.highlightedTeeth.includes(toothNumber)
}

function isInMultiSelection(toothNumber: number): boolean {
  return props.multiSelectedTeeth.includes(toothNumber)
}

/**
 * Returns the shared group id between this tooth and the next tooth in the row, or null.
 * Used to render a connector bar between adjacent teeth that belong to the same group.
 */
function connectorGroupId(index: number): string | null {
  if (!props.getGroupId) return null
  const current = props.teeth[index]
  const next = props.teeth[index + 1]
  if (current === undefined || next === undefined) return null
  const currentGroup = props.getGroupId(current)
  const nextGroup = props.getGroupId(next)
  return currentGroup && currentGroup === nextGroup ? currentGroup : null
}

function connectorStatus(index: number): 'existing' | 'planned' | null {
  const current = props.teeth[index]
  if (current === undefined || !props.getGroupStatus) return null
  return props.getGroupStatus(current)
}

function connectorType(index: number): string | null {
  const current = props.teeth[index]
  if (current === undefined || !props.getGroupType) return null
  return props.getGroupType(current)
}

function isUpperTooth(toothNumber: number): boolean {
  // FDI: 11-28 = permanent upper, 51-65 = deciduous upper
  const q = Math.floor(toothNumber / 10)
  return q === 1 || q === 2 || q === 5 || q === 6
}
</script>

<template>
  <div class="tooth-row">
    <template
      v-for="(toothNum, idx) in teeth"
      :key="toothNum"
    >
      <UPopover
        :open-delay="300"
        :close-delay="100"
        :ui="{ width: 'min-w-48 max-w-72' }"
      >
        <div
          class="tooth-cell"
          :class="[
            { 'tooth-cell-dual': showLateral },
            getGroupId(toothNum) && getGroupType(toothNum) !== 'bridge' ? 'in-group' : '',
            isInMultiSelection(toothNum) ? 'in-multi-selection' : ''
          ]"
        >
          <ToothDualView
            :tooth-number="toothNum"
            :general-condition="getToothData(toothNum).generalCondition"
            :treatments="getTreatments(toothNum)"
            :readonly="readonly"
            :selected="selectedTooth === toothNum"
            :show-lateral="showLateral"
            :is-displaced="getToothData(toothNum).isDisplaced"
            :is-rotated="getToothData(toothNum).isRotated"
            :is-hovered="hoveredTooth === toothNum"
            :is-highlighted="isHighlighted(toothNum)"
            :pending-treatment="hoveredTooth === toothNum ? pendingTreatment : null"
            @surface-click="(s: Surface) => emit('surfaceClick', toothNum, s)"
            @tooth-click="emit('toothClick', toothNum)"
            @contextmenu="(e: MouseEvent) => emit('toothContextMenu', toothNum, e)"
            @mouseenter="emit('toothHover', toothNum)"
            @mouseleave="emit('toothHover', null)"
          />
        </div>

        <template #content>
          <ToothTooltip
            :tooth-number="toothNum"
            :treatments="getTreatments(toothNum)"
            @edit-treatment="(t: ToothTreatmentView) => emit('editTreatment', t)"
          />
        </template>
      </UPopover>

      <!-- Inline connector for non-bridge groups (splint, multi-crown...). -->
      <div
        v-if="connectorGroupId(idx) && connectorType(idx) !== 'bridge'"
        class="group-connector"
        :class="['status-' + (connectorStatus(idx) ?? 'planned')]"
      />
    </template>

    <!-- Bridge connectors: absolute overlays so they don't push teeth apart.
         Centered on the gap between cell[idx] and cell[idx+1]; left in px is
         deterministic from cell width + flex gap. -->
    <template
      v-for="(toothNum, idx) in teeth"
      :key="'br-' + toothNum"
    >
      <div
        v-if="connectorGroupId(idx) && connectorType(idx) === 'bridge' && toothNum !== undefined"
        class="bridge-connector"
        :class="[
          'status-' + (connectorStatus(idx) ?? 'planned'),
          isUpperTooth(toothNum) ? 'upper' : 'lower'
        ]"
        :style="{ left: (idx * 62 + 61) + 'px' }"
      />
    </template>
  </div>
</template>

<style scoped>
.tooth-row {
  display: flex;
  gap: 2px;
  align-items: center;
  position: relative;
}

.tooth-cell {
  width: 60px;
  height: 75px;
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
}

.tooth-cell-dual {
  height: 160px;
}

/* Subtle underline for any tooth that belongs to a group */
.tooth-cell.in-group::after {
  content: '';
  position: absolute;
  left: 10%;
  right: 10%;
  bottom: 2px;
  height: 2px;
  border-radius: 2px;
  background: #3B82F6;
  opacity: 0.6;
}

/* Tooth currently inside an in-progress multi-tooth selection */
.tooth-cell.in-multi-selection {
  outline: 2px solid #3B82F6;
  outline-offset: 2px;
  border-radius: 6px;
  animation: multi-tooth-pulse 1.2s ease-in-out infinite;
}

@keyframes multi-tooth-pulse {
  0%, 100% {
    outline-color: #3B82F6;
  }
  50% {
    outline-color: #60A5FA;
  }
}

/* Connector bar between two adjacent teeth of the same group */
.group-connector {
  width: 8px;
  height: 4px;
  border-radius: 2px;
  align-self: end;
  margin-bottom: 2px;
  background: #3B82F6;
  position: relative;
}

.group-connector.status-planned {
  background: repeating-linear-gradient(
    90deg,
    #3B82F6 0,
    #3B82F6 3px,
    transparent 3px,
    transparent 6px
  );
}

.group-connector.status-existing {
  background: #3B82F6;
}

/* Bridge connector: absolute overlay at crown level. Zero flex footprint so
   adjacent teeth stay at their original positions (no horizontal shift vs a
   non-bridge tooth row). */
.bridge-connector {
  position: absolute;
  transform: translateX(-50%);
  width: 56px;
  height: 12px;
  border-radius: 2px;
  background: #F59E0B;
  pointer-events: none;
  z-index: 1;
}

/* Upper crowns: rectangle sits just above the row's bottom half. */
.bridge-connector.upper {
  bottom: 62px;
}

/* Lower crowns: slightly lower than upper to match the flipped crown position. */
.bridge-connector.lower {
  bottom: 72px;
}

.bridge-connector.status-planned {
  background: repeating-linear-gradient(
    90deg,
    #F59E0B 0,
    #F59E0B 4px,
    transparent 4px,
    transparent 8px
  );
}

.bridge-connector.status-existing {
  background: #F59E0B;
}
</style>
