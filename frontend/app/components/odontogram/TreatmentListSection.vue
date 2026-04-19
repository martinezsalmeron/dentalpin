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
  <div class="treatment-list-section border border-default rounded-lg overflow-hidden">
    <!-- Header (clickable to collapse/expand) -->
    <button
      class="w-full flex items-center justify-between px-4 py-3 bg-surface-muted hover:bg-surface-muted transition-colors"
      @click="isExpanded = !isExpanded"
    >
      <div class="flex items-center gap-2">
        <UIcon
          name="i-lucide-list"
          class="w-5 h-5 text-subtle"
        />
        <span class="font-medium text-muted">
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
        class="w-5 h-5 text-subtle transition-transform"
      />
    </button>

    <!-- Content -->
    <div
      v-if="isExpanded"
      class="p-4 bg-surface"
    >
      <div
        v-if="sortedTreatments.length === 0"
        class="text-center py-4 text-subtle"
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
          class="flex items-center gap-3 p-2 rounded-lg hover:bg-surface-muted transition-colors"
        >
          <!-- Color indicator -->
          <span
            class="w-3 h-3 rounded-full flex-shrink-0 border border-default"
            :style="{ backgroundColor: getTreatmentColor(treatment.treatment_type) }"
          />

          <!-- Treatment info -->
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2">
              <span class="font-medium text-default">
                {{ treatment.tooth_number }}
              </span>
              <span class="text-muted truncate">
                {{ getToothFullName(treatment.tooth_number) }}
              </span>
            </div>
            <div class="flex items-center gap-2 text-sm">
              <span class="text-muted">
                {{ getTreatmentDisplayName(treatment, locale, t) }}
              </span>
              <span
                v-if="treatment.surfaces && treatment.surfaces.length > 0"
                class="text-subtle"
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
            <span class="text-caption text-subtle">
              {{ formatDate(treatment.performed_at || treatment.recorded_at) }}
            </span>
          </div>
        </li>
      </ul>
    </div>
  </div>
</template>
