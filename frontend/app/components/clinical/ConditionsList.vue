<script setup lang="ts">
/**
 * ConditionsList - Display diagnosed conditions (status='existing')
 *
 * Shows treatments with existing status grouped by tooth.
 * Supports hover linking with odontogram.
 */

import type { ToothTreatmentView, Treatment } from '~/types'
import { getTreatmentDisplayName, viewForTooth } from '~/utils/treatmentView'

const props = defineProps<{
  conditions: Treatment[]
  highlightedTeeth?: number[]
}>()

const emit = defineEmits<{
  'tooth-hover': [toothNumber: number | null]
}>()

const { t, locale } = useI18n()

// Flatten Treatment[] into per-tooth views and group by tooth number.
const groupedByTooth = computed(() => {
  const groups = new Map<number, ToothTreatmentView[]>()
  for (const treatment of props.conditions) {
    for (const tooth of treatment.teeth) {
      const v = viewForTooth(treatment, tooth.tooth_number)
      if (!v) continue
      const existing = groups.get(v.tooth_number) || []
      existing.push(v)
      groups.set(v.tooth_number, existing)
    }
  }
  return Array.from(groups.entries())
    .sort(([a], [b]) => a - b)
    .map(([toothNumber, treatments]) => ({ toothNumber, treatments }))
})

const generalConditions = computed<ToothTreatmentView[]>(() => [])

function getTreatmentLabel(treatment: ToothTreatmentView): string {
  return getTreatmentDisplayName(treatment, locale.value, t)
}

function formatSurfaces(surfaces: string[] | undefined): string {
  if (!surfaces || surfaces.length === 0) return ''
  return `(${surfaces.join(', ')})`
}

function isHighlighted(toothNumber: number): boolean {
  return props.highlightedTeeth?.includes(toothNumber) ?? false
}
</script>

<template>
  <div>
    <!-- No conditions -->
    <div
      v-if="conditions.length === 0"
      class="text-center py-6 text-gray-500 dark:text-gray-400"
    >
      <UIcon
        name="i-lucide-clipboard-check"
        class="w-10 h-10 mx-auto mb-2 opacity-50"
      />
      <p class="font-medium">
        {{ t('clinical.diagnosis.noConditions') }}
      </p>
      <p class="text-sm">
        {{ t('clinical.diagnosis.startDiagnosis') }}
      </p>
    </div>

    <!-- Conditions by tooth: one compact row per tooth -->
    <ul
      v-else
      class="divide-y divide-gray-100 dark:divide-gray-800"
    >
      <li
        v-for="group in groupedByTooth"
        :key="group.toothNumber"
        class="flex items-center gap-3 py-2 px-2 rounded-md transition-colors cursor-default"
        :class="{
          'bg-yellow-50 dark:bg-yellow-900/20': isHighlighted(group.toothNumber),
          'hover:bg-gray-50 dark:hover:bg-gray-800/60': !isHighlighted(group.toothNumber)
        }"
        @mouseenter="emit('tooth-hover', group.toothNumber)"
        @mouseleave="emit('tooth-hover', null)"
      >
        <span
          class="inline-flex items-center justify-center min-w-[2.25rem] h-7 px-2 rounded text-xs font-semibold tabular-nums bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200"
        >
          {{ group.toothNumber }}
        </span>
        <div class="flex flex-wrap items-center gap-x-2 gap-y-1 text-sm flex-1 min-w-0">
          <template
            v-for="(condition, idx) in group.treatments"
            :key="condition.id"
          >
            <span class="flex items-baseline gap-1">
              <span>{{ getTreatmentLabel(condition) }}</span>
              <span
                v-if="condition.surfaces?.length"
                class="text-xs text-gray-500 dark:text-gray-400 tabular-nums"
              >
                {{ formatSurfaces(condition.surfaces) }}
              </span>
            </span>
            <span
              v-if="idx < group.treatments.length - 1"
              class="text-gray-300 dark:text-gray-600"
            >·</span>
          </template>
        </div>
      </li>
    </ul>

    <!-- General conditions (no tooth) -->
    <div
      v-if="generalConditions.length > 0"
      class="mt-3 p-3 rounded-lg bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800"
    >
      <div class="flex items-center gap-2 mb-2">
        <UIcon
          name="i-lucide-user"
          class="w-4 h-4 text-blue-500"
        />
        <span class="font-medium">{{ t('clinical.diagnosis.generalConditions') }}</span>
      </div>
      <ul class="ml-6 space-y-1">
        <li
          v-for="condition in generalConditions"
          :key="condition.id"
          class="text-sm"
        >
          {{ getTreatmentLabel(condition) }}
        </li>
      </ul>
    </div>
  </div>
</template>
