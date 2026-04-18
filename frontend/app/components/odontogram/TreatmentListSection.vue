<script setup lang="ts">
import type { Treatment } from '~/types'
import { getToothNameKey, getToothPositionKeys, TREATMENT_COLORS } from '~/config/odontogramConstants'
import { getTreatmentDisplayName, viewForTooth } from '~/utils/treatmentView'

const props = defineProps<{
  treatments: Treatment[]
}>()

const { t, locale } = useI18n()

const isExpanded = ref(false)

// Flatten Treatment[] into per-tooth rows and sort by performed_at / recorded_at desc.
const sortedTreatments = computed(() => {
  const rows = []
  for (const treatment of props.treatments) {
    for (const tooth of treatment.teeth) {
      const v = viewForTooth(treatment, tooth.tooth_number)
      if (v) rows.push(v)
    }
  }
  return rows.sort((a, b) => {
    const dateA = new Date(a.performed_at || a.recorded_at).getTime()
    const dateB = new Date(b.performed_at || b.recorded_at).getTime()
    return dateB - dateA
  })
})

function getToothFullName(toothNumber: number): string {
  const nameKey = getToothNameKey(toothNumber)
  const positionKeys = getToothPositionKeys(toothNumber)
  const name = t(nameKey)
  const position = `${t(positionKeys.horizontal)} ${t(positionKeys.vertical)}`
  return `${name} ${position}`
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  const day = date.getDate().toString().padStart(2, '0')
  const month = (date.getMonth() + 1).toString().padStart(2, '0')
  const year = date.getFullYear()
  return `${day}/${month}/${year}`
}

function getTreatmentColor(treatmentType: string): string {
  return TREATMENT_COLORS[treatmentType] || '#9CA3AF'
}

function getStatusBadgeColor(status: string): 'success' | 'warning' | 'neutral' {
  switch (status) {
    case 'planned':
      return 'warning'
    default:
      return 'neutral'
  }
}
</script>

<template>
  <div class="treatment-list-section border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
    <!-- Header (clickable to collapse/expand) -->
    <button
      class="w-full flex items-center justify-between px-4 py-3 bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-750 transition-colors"
      @click="isExpanded = !isExpanded"
    >
      <div class="flex items-center gap-2">
        <UIcon
          name="i-lucide-list"
          class="w-5 h-5 text-gray-500"
        />
        <span class="font-medium text-gray-700 dark:text-gray-300">
          {{ t('odontogram.treatmentList.title') }}
        </span>
        <UBadge
          v-if="treatments.length > 0"
          :label="String(treatments.length)"
          size="xs"
          color="neutral"
          variant="subtle"
        />
      </div>
      <UIcon
        :name="isExpanded ? 'i-lucide-chevron-up' : 'i-lucide-chevron-down'"
        class="w-5 h-5 text-gray-400 transition-transform"
      />
    </button>

    <!-- Content -->
    <div
      v-if="isExpanded"
      class="p-4 bg-white dark:bg-gray-900"
    >
      <div
        v-if="sortedTreatments.length === 0"
        class="text-center py-4 text-gray-500"
      >
        {{ t('odontogram.treatmentList.noTreatments') }}
      </div>

      <ul
        v-else
        class="space-y-2 max-h-64 overflow-y-auto"
      >
        <li
          v-for="treatment in sortedTreatments"
          :key="treatment.id"
          class="flex items-center gap-3 p-2 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
        >
          <!-- Color indicator -->
          <span
            class="w-3 h-3 rounded-full flex-shrink-0 border border-gray-200 dark:border-gray-600"
            :style="{ backgroundColor: getTreatmentColor(treatment.treatment_type) }"
          />

          <!-- Treatment info -->
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2">
              <span class="font-medium text-gray-900 dark:text-gray-100">
                {{ treatment.tooth_number }}
              </span>
              <span class="text-gray-600 dark:text-gray-400 truncate">
                {{ getToothFullName(treatment.tooth_number) }}
              </span>
            </div>
            <div class="flex items-center gap-2 text-sm">
              <span class="text-gray-700 dark:text-gray-300">
                {{ getTreatmentDisplayName(treatment, locale, t) }}
              </span>
              <span
                v-if="treatment.surfaces && treatment.surfaces.length > 0"
                class="text-gray-500"
              >
                ({{ treatment.surfaces.join(', ') }})
              </span>
            </div>
          </div>

          <!-- Status badge and date -->
          <div class="flex items-center gap-2 flex-shrink-0">
            <UBadge
              :label="t(`odontogram.treatments.status.${treatment.status}`)"
              size="xs"
              :color="getStatusBadgeColor(treatment.status)"
              variant="subtle"
            />
            <span class="text-xs text-gray-400">
              {{ formatDate(treatment.performed_at || treatment.recorded_at) }}
            </span>
          </div>
        </li>
      </ul>
    </div>
  </div>
</template>
