<script setup lang="ts">
import { TREATMENT_COLORS, STATUS_STYLES } from './ToothSVGPaths'
import type { TreatmentStatus, TreatmentType } from '~/types'

const { t } = useI18n()

// Common treatments to show in legend
const treatmentTypes: TreatmentType[] = [
  'filling',
  'caries',
  'crown',
  'root_canal',
  'extraction',
  'implant',
  'sealant'
]

// Status types
const statusTypes: Array<{ key: TreatmentStatus, borderStyle: string }> = [
  { key: 'preexisting', borderStyle: 'none' },
  { key: 'planned', borderStyle: 'dashed' },
  { key: 'performed', borderStyle: 'solid' }
]

function getTreatmentLabel(treatment: TreatmentType): string {
  return t(`odontogram.treatments.types.${treatment}`, treatment)
}

function getStatusLabel(status: TreatmentStatus): string {
  return t(`odontogram.status.${status}`, status)
}
</script>

<template>
  <div class="odontogram-legend">
    <!-- Treatments -->
    <div class="legend-section">
      <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
        {{ t('odontogram.treatments.title') }}
      </h4>
      <div class="flex flex-wrap gap-3">
        <div
          v-for="treatment in treatmentTypes"
          :key="treatment"
          class="flex items-center gap-1.5"
        >
          <span
            class="w-4 h-4 rounded"
            :style="{ backgroundColor: TREATMENT_COLORS[treatment] }"
          />
          <span class="text-xs text-gray-600 dark:text-gray-400">
            {{ getTreatmentLabel(treatment) }}
          </span>
        </div>
      </div>
    </div>

    <!-- Status Indicators -->
    <div class="legend-section mt-3">
      <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
        {{ t('odontogram.statusLegend') }}
      </h4>
      <div class="flex flex-wrap gap-4">
        <div
          v-for="status in statusTypes"
          :key="status.key"
          class="flex items-center gap-1.5"
        >
          <span
            class="w-4 h-4 rounded"
            :style="{
              backgroundColor: '#E5E7EB',
              border: status.key === 'preexisting'
                ? 'none'
                : `2px ${status.borderStyle} ${STATUS_STYLES[status.key].border}`
            }"
          />
          <span class="text-xs text-gray-600 dark:text-gray-400">
            {{ getStatusLabel(status.key) }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.odontogram-legend {
  padding: 0.75rem;
  background: var(--color-gray-50);
  border-radius: 0.5rem;
}

:root.dark .odontogram-legend {
  background: var(--color-gray-800);
}

.legend-section + .legend-section {
  border-top: 1px solid var(--color-gray-200);
  padding-top: 0.75rem;
}

:root.dark .legend-section + .legend-section {
  border-color: var(--color-gray-700);
}
</style>
