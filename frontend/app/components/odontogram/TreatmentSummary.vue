<script setup lang="ts">
import type { Treatment, TreatmentStatus, TreatmentType } from '~/types'
import { TREATMENT_COLORS, STATUS_STYLES } from './ToothSVGPaths'

const props = defineProps<{
  treatments: Treatment[]
}>()

const emit = defineEmits<{
  highlightTeeth: [teeth: number[]]
  clearHighlight: []
  filterStatus: [status: TreatmentStatus | null]
}>()

const { t } = useI18n()

// Active status filter
const activeStatusFilter = ref<TreatmentStatus | null>(null)

// Group treatments by type
const treatmentsByType = computed(() => {
  const grouped: Record<string, { count: number, teeth: number[], treatments: Treatment[] }> = {}

  for (const treatment of props.treatments) {
    if (!grouped[treatment.treatment_type]) {
      grouped[treatment.treatment_type] = { count: 0, teeth: [], treatments: [] }
    }
    grouped[treatment.treatment_type].count++
    if (!grouped[treatment.treatment_type].teeth.includes(treatment.tooth_number)) {
      grouped[treatment.treatment_type].teeth.push(treatment.tooth_number)
    }
    grouped[treatment.treatment_type].treatments.push(treatment)
  }

  // Sort by count descending
  return Object.entries(grouped)
    .sort(([, a], [, b]) => b.count - a.count)
    .map(([type, data]) => ({
      type: type as TreatmentType,
      ...data
    }))
})

// Group treatments by status
const treatmentsByStatus = computed(() => {
  const grouped: Record<TreatmentStatus, number> = {
    planned: 0,
    performed: 0,
    preexisting: 0
  }

  for (const treatment of props.treatments) {
    grouped[treatment.status]++
  }

  return grouped
})

// Total count
const totalTreatments = computed(() => props.treatments.length)

// Filtered treatments
const filteredTreatments = computed(() => {
  if (!activeStatusFilter.value) return props.treatments
  return props.treatments.filter(t => t.status === activeStatusFilter.value)
})

// Unique teeth count
const uniqueTeethCount = computed(() => {
  const teeth = new Set<number>()
  for (const treatment of filteredTreatments.value) {
    teeth.add(treatment.tooth_number)
  }
  return teeth.size
})

function toggleStatusFilter(status: TreatmentStatus) {
  if (activeStatusFilter.value === status) {
    activeStatusFilter.value = null
  } else {
    activeStatusFilter.value = status
  }
  emit('filterStatus', activeStatusFilter.value)
}

function highlightTreatmentTeeth(type: TreatmentType) {
  const entry = treatmentsByType.value.find(e => e.type === type)
  if (entry) {
    emit('highlightTeeth', entry.teeth)
  }
}

function clearHighlight() {
  emit('clearHighlight')
}

function getTreatmentLabel(type: string): string {
  return t(`odontogram.treatments.types.${type}`, type)
}
</script>

<template>
  <div class="treatment-summary">
    <!-- Header -->
    <div class="summary-header">
      <h4 class="text-sm font-semibold text-gray-700 dark:text-gray-300">
        {{ t('odontogram.treatments.title') }}
      </h4>
      <span class="text-xs text-gray-500">
        {{ totalTreatments }} total
      </span>
    </div>

    <!-- Status filters -->
    <div class="status-filters">
      <button
        v-for="(count, status) in treatmentsByStatus"
        :key="status"
        type="button"
        class="status-badge"
        :class="{
          active: activeStatusFilter === status,
          planned: status === 'planned',
          performed: status === 'performed',
          preexisting: status === 'preexisting'
        }"
        @click="toggleStatusFilter(status)"
      >
        <span
          class="status-dot"
          :style="{ backgroundColor: STATUS_STYLES[status].border }"
        />
        <span class="status-count">{{ count }}</span>
        <span class="status-label">{{ t(`odontogram.status.${status}`) }}</span>
      </button>
    </div>

    <!-- Divider -->
    <div class="divider" />

    <!-- Treatments by type -->
    <div class="treatments-list">
      <div
        v-for="entry in treatmentsByType"
        :key="entry.type"
        class="treatment-row"
        @mouseenter="highlightTreatmentTeeth(entry.type)"
        @mouseleave="clearHighlight"
      >
        <div class="treatment-info">
          <span
            class="treatment-dot"
            :style="{ backgroundColor: TREATMENT_COLORS[entry.type] || '#9CA3AF' }"
          />
          <span class="treatment-name">{{ getTreatmentLabel(entry.type) }}</span>
        </div>
        <div class="treatment-stats">
          <span class="treatment-count">{{ entry.count }}</span>
          <span class="teeth-count">{{ entry.teeth.length }} {{ t('odontogram.tooth').toLowerCase() }}{{ entry.teeth.length > 1 ? 's' : '' }}</span>
        </div>
      </div>

      <!-- Empty state -->
      <div
        v-if="treatmentsByType.length === 0"
        class="empty-state"
      >
        <UIcon
          name="i-lucide-clipboard-list"
          class="w-8 h-8 text-gray-300"
        />
        <span class="text-sm text-gray-400">{{ t('odontogram.treatments.noTreatments') }}</span>
      </div>
    </div>

    <!-- Footer stats -->
    <div
      v-if="totalTreatments > 0"
      class="summary-footer"
    >
      <div class="stat">
        <span class="stat-value">{{ uniqueTeethCount }}</span>
        <span class="stat-label">{{ t('odontogram.tooth') }}{{ uniqueTeethCount > 1 ? 's' : '' }}</span>
      </div>
      <div class="stat">
        <span class="stat-value">{{ treatmentsByStatus.planned }}</span>
        <span class="stat-label">{{ t('odontogram.status.planned') }}</span>
      </div>
      <div class="stat">
        <span class="stat-value">{{ treatmentsByStatus.performed }}</span>
        <span class="stat-label">{{ t('odontogram.status.performed') }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.treatment-summary {
  background: white;
  border: 1px solid #E5E7EB;
  border-radius: 12px;
  padding: 16px;
}

:root.dark .treatment-summary {
  background: #1F2937;
  border-color: #374151;
}

.summary-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

/* Status filters */
.status-filters {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.status-badge {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  background: #F4F4F5;
  border: 1px solid transparent;
  transition: all 0.15s ease;
}

:root.dark .status-badge {
  background: #27272A;
}

.status-badge:hover {
  background: #E4E4E7;
}

:root.dark .status-badge:hover {
  background: #3F3F46;
}

.status-badge.active {
  border-color: currentColor;
}

.status-badge.active.planned {
  background: #FEF2F2;
  color: #DC2626;
}

.status-badge.active.performed {
  background: #F0FDF4;
  color: #16A34A;
}

.status-badge.active.preexisting {
  background: #F4F4F5;
  color: #52525B;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-count {
  font-weight: 600;
}

.status-label {
  color: #6B7280;
}

/* Divider */
.divider {
  height: 1px;
  background: #E5E7EB;
  margin: 12px 0;
}

:root.dark .divider {
  background: #374151;
}

/* Treatments list */
.treatments-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 200px;
  overflow-y: auto;
}

.treatment-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 10px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.15s ease;
}

.treatment-row:hover {
  background: #F4F4F5;
}

:root.dark .treatment-row:hover {
  background: #27272A;
}

.treatment-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.treatment-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.treatment-name {
  font-size: 13px;
  font-weight: 500;
  color: #374151;
}

:root.dark .treatment-name {
  color: #E5E7EB;
}

.treatment-stats {
  display: flex;
  align-items: center;
  gap: 8px;
}

.treatment-count {
  font-size: 14px;
  font-weight: 600;
  color: #374151;
}

:root.dark .treatment-count {
  color: #E5E7EB;
}

.teeth-count {
  font-size: 11px;
  color: #9CA3AF;
}

/* Empty state */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 24px;
}

/* Footer stats */
.summary-footer {
  display: flex;
  justify-content: space-around;
  padding-top: 12px;
  margin-top: 12px;
  border-top: 1px solid #E5E7EB;
}

:root.dark .summary-footer {
  border-color: #374151;
}

.stat {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-value {
  font-size: 18px;
  font-weight: 700;
  color: #374151;
}

:root.dark .stat-value {
  color: #E5E7EB;
}

.stat-label {
  font-size: 10px;
  text-transform: uppercase;
  color: #9CA3AF;
  letter-spacing: 0.05em;
}
</style>
