<script setup lang="ts">
import type { Treatment, TreatmentStatus } from '~/types'
import { TREATMENT_COLORS, STATUS_STYLES } from './ToothSVGPaths'

const props = defineProps<{
  treatments: Treatment[]
  toothNumber: number
  loading?: boolean
  readonly?: boolean
}>()

const emit = defineEmits<{
  addTreatment: []
  performTreatment: [treatment: Treatment]
  deleteTreatment: [treatment: Treatment]
  selectTreatment: [treatment: Treatment]
}>()

const { t } = useI18n()

// Group treatments by status
const groupedTreatments = computed(() => {
  const groups: Record<TreatmentStatus, Treatment[]> = {
    planned: [],
    performed: [],
    preexisting: []
  }
  for (const treatment of props.treatments) {
    groups[treatment.status]?.push(treatment)
  }
  return groups
})

function getTreatmentLabel(type: string): string {
  return t(`odontogram.treatments.types.${type}`, type)
}

function getStatusLabel(status: TreatmentStatus): string {
  return t(`odontogram.status.${status}`, status)
}

function getStatusColor(status: TreatmentStatus): string {
  const colorMap: Record<TreatmentStatus, string> = {
    preexisting: 'neutral',
    planned: 'warning',
    performed: 'success'
  }
  return colorMap[status] || 'neutral'
}

function getTreatmentColor(type: string): string {
  return TREATMENT_COLORS[type] || '#9CA3AF'
}

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString()
}
</script>

<template>
  <div class="treatment-panel">
    <div class="flex items-center justify-between mb-3">
      <h4 class="text-sm font-semibold flex items-center gap-2">
        {{ t('odontogram.treatments.title') }}
        <UBadge color="neutral" variant="subtle" size="xs">
          {{ toothNumber }}
        </UBadge>
      </h4>
      <UButton
        v-if="!readonly"
        icon="i-lucide-plus"
        size="xs"
        variant="soft"
        @click="emit('addTreatment')"
      >
        {{ t('odontogram.treatments.addTreatment') }}
      </UButton>
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="flex justify-center py-4">
      <UIcon name="i-lucide-loader-2" class="w-5 h-5 animate-spin text-gray-400" />
    </div>

    <!-- Empty state -->
    <div
      v-else-if="treatments.length === 0"
      class="text-center py-6 text-gray-500 text-sm"
    >
      {{ t('odontogram.treatments.noTreatments') }}
    </div>

    <!-- Treatment list by status -->
    <div v-else class="space-y-4">
      <!-- Planned treatments (show first, most actionable) -->
      <div v-if="groupedTreatments.planned.length > 0">
        <div class="text-xs font-medium text-amber-600 mb-2 flex items-center gap-1">
          <UIcon name="i-lucide-clock" class="w-3 h-3" />
          {{ getStatusLabel('planned') }}
        </div>
        <div class="space-y-2">
          <div
            v-for="treatment in groupedTreatments.planned"
            :key="treatment.id"
            class="treatment-item treatment-planned"
            @click="emit('selectTreatment', treatment)"
          >
            <div class="flex items-center gap-2">
              <div
                class="w-3 h-3 rounded-full"
                :style="{ backgroundColor: getTreatmentColor(treatment.treatment_type) }"
              />
              <span class="text-sm font-medium">{{ getTreatmentLabel(treatment.treatment_type) }}</span>
              <UBadge
                v-if="treatment.surfaces?.length"
                color="neutral"
                variant="subtle"
                size="xs"
              >
                {{ treatment.surfaces.join('-') }}
              </UBadge>
            </div>
            <div class="flex items-center gap-1 mt-1">
              <UButton
                v-if="!readonly"
                icon="i-lucide-check"
                size="xs"
                color="success"
                variant="soft"
                @click.stop="emit('performTreatment', treatment)"
              >
                {{ t('odontogram.treatments.markPerformed') }}
              </UButton>
              <UButton
                v-if="!readonly"
                icon="i-lucide-trash-2"
                size="xs"
                color="error"
                variant="ghost"
                @click.stop="emit('deleteTreatment', treatment)"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- Performed treatments -->
      <div v-if="groupedTreatments.performed.length > 0">
        <div class="text-xs font-medium text-green-600 mb-2 flex items-center gap-1">
          <UIcon name="i-lucide-check-circle" class="w-3 h-3" />
          {{ getStatusLabel('performed') }}
        </div>
        <div class="space-y-2">
          <div
            v-for="treatment in groupedTreatments.performed"
            :key="treatment.id"
            class="treatment-item treatment-performed"
            @click="emit('selectTreatment', treatment)"
          >
            <div class="flex items-center gap-2">
              <div
                class="w-3 h-3 rounded-full"
                :style="{ backgroundColor: getTreatmentColor(treatment.treatment_type) }"
              />
              <span class="text-sm">{{ getTreatmentLabel(treatment.treatment_type) }}</span>
              <UBadge
                v-if="treatment.surfaces?.length"
                color="neutral"
                variant="subtle"
                size="xs"
              >
                {{ treatment.surfaces.join('-') }}
              </UBadge>
            </div>
            <div class="text-xs text-gray-500 mt-1">
              {{ formatDate(treatment.performed_at || treatment.recorded_at) }}
              <span v-if="treatment.performed_by_name"> - {{ treatment.performed_by_name }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Preexisting treatments -->
      <div v-if="groupedTreatments.preexisting.length > 0">
        <div class="text-xs font-medium text-gray-500 mb-2 flex items-center gap-1">
          <UIcon name="i-lucide-history" class="w-3 h-3" />
          {{ getStatusLabel('preexisting') }}
        </div>
        <div class="space-y-2">
          <div
            v-for="treatment in groupedTreatments.preexisting"
            :key="treatment.id"
            class="treatment-item treatment-preexisting"
            @click="emit('selectTreatment', treatment)"
          >
            <div class="flex items-center gap-2">
              <div
                class="w-3 h-3 rounded-full opacity-60"
                :style="{ backgroundColor: getTreatmentColor(treatment.treatment_type) }"
              />
              <span class="text-sm text-gray-600">{{ getTreatmentLabel(treatment.treatment_type) }}</span>
              <UBadge
                v-if="treatment.surfaces?.length"
                color="neutral"
                variant="subtle"
                size="xs"
              >
                {{ treatment.surfaces.join('-') }}
              </UBadge>
            </div>
            <div v-if="treatment.notes" class="text-xs text-gray-400 mt-1 truncate">
              {{ treatment.notes }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.treatment-panel {
  background-color: white;
  border-radius: 0.5rem;
  border: 1px solid #e5e7eb;
  padding: 1rem;
}

:root.dark .treatment-panel {
  background-color: #111827;
  border-color: #374151;
}

.treatment-item {
  padding: 0.5rem;
  border-radius: 0.375rem;
  cursor: pointer;
  transition: background-color 0.15s;
}

.treatment-item:hover {
  background-color: #f9fafb;
}

:root.dark .treatment-item:hover {
  background-color: #1f2937;
}

.treatment-planned {
  border-left: 2px solid #fbbf24;
  padding-left: 0.75rem;
}

.treatment-performed {
  border-left: 2px solid #4ade80;
  padding-left: 0.75rem;
}

.treatment-preexisting {
  border-left: 2px solid #d1d5db;
  padding-left: 0.75rem;
  opacity: 0.8;
}
</style>
