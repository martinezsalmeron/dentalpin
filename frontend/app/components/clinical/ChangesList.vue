<script setup lang="ts">
/**
 * ChangesList - Display odontogram changes at a specific date
 *
 * Shows treatments added, modified, or completed on the selected date.
 */

import type { Treatment } from '~/types'

const props = defineProps<{
  changes: Treatment[]
}>()

const { t } = useI18n()

// Group changes by type
const groupedChanges = computed(() => {
  const added: Treatment[] = []
  const completed: Treatment[] = []

  for (const change of props.changes) {
    if (change.performed_at) {
      completed.push(change)
    } else {
      added.push(change)
    }
  }

  return { added, completed }
})

function getTreatmentLabel(treatment: Treatment): string {
  // Try i18n first
  const key = `odontogram.treatments.types.${treatment.treatment_type}`
  const translated = t(key, treatment.treatment_type)
  return translated !== key ? translated : treatment.treatment_type
}

function formatToothInfo(treatment: Treatment): string {
  let info = `${t('clinical.tooth')} ${treatment.tooth_number}`
  if (treatment.surfaces && treatment.surfaces.length > 0) {
    info += ` (${treatment.surfaces.join(', ')})`
  }
  return info
}
</script>

<template>
  <div class="space-y-3">
    <!-- No changes -->
    <div
      v-if="changes.length === 0"
      class="text-center py-4 text-gray-500 dark:text-gray-400"
    >
      <UIcon
        name="i-lucide-calendar-x"
        class="w-8 h-8 mx-auto mb-2 opacity-50"
      />
      <p>{{ t('clinical.history.noChanges') }}</p>
    </div>

    <!-- Treatments added -->
    <div v-if="groupedChanges.added.length > 0">
      <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 flex items-center gap-2">
        <UIcon
          name="i-lucide-plus-circle"
          class="w-4 h-4 text-blue-500"
        />
        {{ t('odontogram.changeHistory.treatmentAdded') }}
      </h4>
      <ul class="space-y-2">
        <li
          v-for="change in groupedChanges.added"
          :key="change.id"
          class="flex items-center gap-3 p-2 rounded-lg bg-blue-50 dark:bg-blue-900/20 border border-blue-100 dark:border-blue-800"
        >
          <div class="flex-1">
            <span class="font-medium">{{ getTreatmentLabel(change) }}</span>
            <span class="text-sm text-gray-500 dark:text-gray-400 ml-2">
              {{ formatToothInfo(change) }}
            </span>
          </div>
          <UBadge
            :color="change.status === 'planned' ? 'red' : 'gray'"
            variant="subtle"
            size="xs"
          >
            {{ t(`odontogram.status.${change.status}`) }}
          </UBadge>
        </li>
      </ul>
    </div>

    <!-- Treatments completed -->
    <div v-if="groupedChanges.completed.length > 0">
      <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 flex items-center gap-2">
        <UIcon
          name="i-lucide-check-circle"
          class="w-4 h-4 text-green-500"
        />
        {{ t('common.completed') }}
      </h4>
      <ul class="space-y-2">
        <li
          v-for="change in groupedChanges.completed"
          :key="change.id"
          class="flex items-center gap-3 p-2 rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-100 dark:border-green-800"
        >
          <div class="flex-1">
            <span class="font-medium">{{ getTreatmentLabel(change) }}</span>
            <span class="text-sm text-gray-500 dark:text-gray-400 ml-2">
              {{ formatToothInfo(change) }}
            </span>
          </div>
          <UIcon
            name="i-lucide-check"
            class="w-4 h-4 text-green-500"
          />
        </li>
      </ul>
    </div>
  </div>
</template>
