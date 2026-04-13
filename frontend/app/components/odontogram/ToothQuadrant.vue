<script setup lang="ts">
/**
 * ToothQuadrant - Renders a row of teeth for one quadrant
 *
 * Eliminates code duplication - used 4 times in OdontogramChart
 * (upperRight, upperLeft, lowerRight, lowerLeft)
 */

import type { Surface, Treatment, TreatmentStatus, TreatmentType } from '~/types'

const props = defineProps<{
  /** List of tooth numbers in this quadrant */
  teeth: readonly number[]
  /** Function to get tooth data (condition, displaced, rotated) */
  getToothData: (toothNumber: number) => {
    generalCondition: string
    isDisplaced: boolean
    isRotated: boolean
  }
  /** Function to get treatments for a tooth */
  getTreatments: (toothNumber: number) => Treatment[]
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
}>()

const emit = defineEmits<{
  surfaceClick: [toothNumber: number, surface: Surface]
  toothClick: [toothNumber: number]
  toothContextMenu: [toothNumber: number, event: MouseEvent]
  toothHover: [toothNumber: number | null]
  editTreatment: [treatment: Treatment]
}>()

function isHighlighted(toothNumber: number): boolean {
  return props.highlightedTeeth.includes(toothNumber)
}
</script>

<template>
  <div class="flex gap-0.5">
    <UPopover
      v-for="toothNum in teeth"
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
          @edit-treatment="(t: Treatment) => emit('editTreatment', t)"
        />
      </template>
    </UPopover>
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
</style>
