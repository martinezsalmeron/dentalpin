<script setup lang="ts">
/**
 * ConditionsList - Display diagnosed conditions (status='existing')
 *
 * Shows treatments with existing status grouped by tooth.
 * Supports hover linking with odontogram.
 */

import type { Treatment } from '~/types'

const props = defineProps<{
  conditions: Treatment[]
  highlightedTeeth?: number[]
}>()

const emit = defineEmits<{
  'tooth-hover': [toothNumber: number | null]
}>()

const { t } = useI18n()

// Group conditions by tooth
const groupedByTooth = computed(() => {
  const groups = new Map<number, Treatment[]>()

  for (const condition of props.conditions) {
    if (condition.tooth_number) {
      const existing = groups.get(condition.tooth_number) || []
      existing.push(condition)
      groups.set(condition.tooth_number, existing)
    }
  }

  // Sort by tooth number
  return Array.from(groups.entries())
    .sort(([a], [b]) => a - b)
    .map(([toothNumber, treatments]) => ({ toothNumber, treatments }))
})

// General conditions (no specific tooth)
const generalConditions = computed(() =>
  props.conditions.filter(c => !c.tooth_number)
)

function getTreatmentLabel(treatment: Treatment): string {
  const key = `odontogram.treatments.types.${treatment.treatment_type}`
  const translated = t(key, treatment.treatment_type)
  return translated !== key ? translated : treatment.treatment_type
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
  <div class="space-y-3">
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

    <!-- Conditions by tooth -->
    <div
      v-for="group in groupedByTooth"
      :key="group.toothNumber"
      class="p-3 rounded-lg border transition-colors"
      :class="{
        'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-300 dark:border-yellow-700': isHighlighted(group.toothNumber),
        'bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700': !isHighlighted(group.toothNumber)
      }"
      @mouseenter="emit('tooth-hover', group.toothNumber)"
      @mouseleave="emit('tooth-hover', null)"
    >
      <div class="flex items-center gap-2 mb-2">
        <UIcon
          name="i-lucide-circle-dot"
          class="w-4 h-4 text-gray-500"
        />
        <span class="font-medium">{{ t('clinical.tooth') }} {{ group.toothNumber }}</span>
      </div>
      <ul class="ml-6 space-y-1">
        <li
          v-for="condition in group.treatments"
          :key="condition.id"
          class="flex items-center gap-2 text-sm"
        >
          <span>{{ getTreatmentLabel(condition) }}</span>
          <span
            v-if="condition.surfaces?.length"
            class="text-gray-500 dark:text-gray-400"
          >
            {{ formatSurfaces(condition.surfaces) }}
          </span>
        </li>
      </ul>
    </div>

    <!-- General conditions (no tooth) -->
    <div
      v-if="generalConditions.length > 0"
      class="p-3 rounded-lg bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800"
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
