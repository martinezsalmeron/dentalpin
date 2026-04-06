<script setup lang="ts">
import type { OdontogramHistoryEntry } from '~/types'
import { TREATMENT_COLORS } from './ToothSVGPaths'

defineProps<{
  history: OdontogramHistoryEntry[]
  loading?: boolean
  treatmentColors?: Record<string, string>
}>()

const { t, d } = useI18n()

function getConditionLabel(condition?: string): string {
  if (!condition) return '-'
  // Try treatment type first, then condition
  const treatmentLabel = t(`odontogram.treatments.types.${condition}`, '')
  if (treatmentLabel) return treatmentLabel
  return t(`odontogram.conditions.${condition}`, condition)
}

function getConditionColor(condition?: string): string {
  if (!condition) return '#E5E7EB'
  return TREATMENT_COLORS[condition] || '#E5E7EB'
}

function getChangeTypeLabel(changeType: string): string {
  return t(`odontogram.history.changeTypes.${changeType}`, changeType)
}

function formatDate(dateStr: string): string {
  return d(new Date(dateStr), 'long')
}
</script>

<template>
  <div class="odontogram-history">
    <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
      {{ t('odontogram.history.title') }}
    </h4>

    <div
      v-if="loading"
      class="flex items-center justify-center py-8"
    >
      <UIcon
        name="i-lucide-loader-2"
        class="w-6 h-6 animate-spin text-gray-400"
      />
    </div>

    <div
      v-else-if="history.length === 0"
      class="text-center py-8 text-gray-500"
    >
      {{ t('odontogram.history.noChanges') }}
    </div>

    <div
      v-else
      class="space-y-3 max-h-96 overflow-y-auto"
    >
      <div
        v-for="entry in history"
        :key="entry.id"
        class="flex gap-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg"
      >
        <!-- Timeline indicator -->
        <div class="flex flex-col items-center">
          <div class="w-2 h-2 rounded-full bg-primary-500" />
          <div class="w-0.5 flex-1 bg-gray-200 dark:bg-gray-700 mt-1" />
        </div>

        <!-- Content -->
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2 text-sm">
            <span class="font-medium text-gray-900 dark:text-gray-100">
              {{ t('odontogram.tooth') }} {{ entry.tooth_number }}
            </span>
            <span
              v-if="entry.surface"
              class="text-gray-500"
            >
              ({{ entry.surface }})
            </span>
            <UBadge
              :label="getChangeTypeLabel(entry.change_type)"
              size="xs"
              color="neutral"
              variant="subtle"
            />
          </div>

          <!-- Condition/Treatment change -->
          <div
            v-if="entry.old_condition || entry.new_condition"
            class="flex items-center gap-2 mt-1 text-sm"
          >
            <span
              v-if="entry.old_condition"
              class="flex items-center gap-1"
            >
              <span
                class="w-3 h-3 rounded border border-gray-300"
                :style="{ backgroundColor: getConditionColor(entry.old_condition) }"
              />
              <span class="text-gray-500">{{ getConditionLabel(entry.old_condition) }}</span>
            </span>
            <UIcon
              name="i-lucide-arrow-right"
              class="w-4 h-4 text-gray-400"
            />
            <span
              v-if="entry.new_condition"
              class="flex items-center gap-1"
            >
              <span
                class="w-3 h-3 rounded border border-gray-300"
                :style="{ backgroundColor: getConditionColor(entry.new_condition) }"
              />
              <span class="text-gray-700 dark:text-gray-300">{{ getConditionLabel(entry.new_condition) }}</span>
            </span>
          </div>

          <!-- Notes -->
          <p
            v-if="entry.notes"
            class="text-sm text-gray-600 dark:text-gray-400 mt-1"
          >
            {{ entry.notes }}
          </p>

          <!-- Metadata -->
          <div class="flex items-center gap-2 mt-2 text-xs text-gray-400">
            <span>{{ entry.changed_by_name || entry.changed_by }}</span>
            <span>&bull;</span>
            <span>{{ formatDate(entry.changed_at) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
