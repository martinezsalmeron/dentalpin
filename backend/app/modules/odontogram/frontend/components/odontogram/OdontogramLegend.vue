<script setup lang="ts">
import { TREATMENT_ICONS } from './TreatmentIcons'
import {
  TREATMENT_CATEGORIES,
  getTreatmentColor,
  PLANNED_INDICATOR_COLOR
} from '~~/app/config/odontogramConstants'
import type { TreatmentStatus } from '~~/app/types'

const { t } = useI18n()

// Collapsed by default
const isExpanded = ref(false)

// Status types
const statusTypes: Array<{ key: TreatmentStatus }> = [
  { key: 'existing' },
  { key: 'planned' }
]

function getTreatmentLabel(treatment: string): string {
  return t(`odontogram.treatments.types.${treatment}`, treatment)
}

function getStatusLabel(status: TreatmentStatus): string {
  return t(`odontogram.status.${status}`, status)
}

function getCategoryLabel(labelKey: string): string {
  return t(labelKey)
}

function hasIcon(treatment: string): boolean {
  return !!TREATMENT_ICONS[treatment]
}

function toggleExpanded() {
  isExpanded.value = !isExpanded.value
}
</script>

<template>
  <div class="odontogram-legend">
    <!-- Header (always visible) -->
    <button
      type="button"
      class="legend-header"
      @click="toggleExpanded"
    >
      <div class="header-content">
        <UIcon
          name="i-lucide-info"
          class="w-4 h-4"
        />
        <span class="header-title">{{ t('odontogram.legend', 'Leyenda') }}</span>
      </div>
      <UIcon
        :name="isExpanded ? 'i-lucide-chevron-up' : 'i-lucide-chevron-down'"
        class="w-4 h-4 chevron-icon"
      />
    </button>

    <!-- Collapsible content -->
    <div
      v-show="isExpanded"
      class="legend-content"
    >
      <!-- Status Indicators -->
      <div class="legend-section">
        <h4 class="section-title">
          {{ t('odontogram.statusLegend') }}
        </h4>
        <div class="status-list">
          <div
            v-for="status in statusTypes"
            :key="status.key"
            class="status-item"
          >
            <span
              class="status-indicator"
              :class="{ planned: status.key === 'planned' }"
              :style="{ backgroundColor: '#94A3B8' }"
            >
              <span
                v-if="status.key === 'planned'"
                class="planned-p"
                :style="{ color: PLANNED_INDICATOR_COLOR }"
              >P</span>
            </span>
            <span class="item-label">
              {{ getStatusLabel(status.key) }}
            </span>
          </div>
        </div>
      </div>

      <!-- Treatments by Category -->
      <div
        v-for="category in TREATMENT_CATEGORIES"
        :key="category.key"
        class="legend-section"
      >
        <h4 class="section-title">
          {{ getCategoryLabel(category.labelKey) }}
        </h4>
        <div class="treatment-grid">
          <div
            v-for="treatment in category.treatments"
            :key="treatment"
            class="treatment-item"
          >
            <!-- Icon or color square -->
            <div
              v-if="hasIcon(treatment)"
              class="treatment-icon"
              :style="{ color: getTreatmentColor(treatment) }"
            >
              <svg
                viewBox="0 0 24 24"
                width="20"
                height="20"
                v-html="TREATMENT_ICONS[treatment]"
              />
            </div>
            <span
              v-else
              class="treatment-color"
              :style="{ backgroundColor: getTreatmentColor(treatment) }"
            />
            <span class="item-label">
              {{ getTreatmentLabel(treatment) }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.odontogram-legend {
  background: var(--color-gray-50);
  border-radius: 8px;
  overflow: hidden;
}

:root.dark .odontogram-legend {
  background: var(--color-gray-800);
}

/* Header */
.legend-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 10px 12px;
  background: transparent;
  border: none;
  cursor: pointer;
  transition: background-color 0.15s ease;
}

.legend-header:hover {
  background: var(--color-gray-100);
}

:root.dark .legend-header:hover {
  background: var(--color-gray-700);
}

.header-content {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--color-gray-600);
}

:root.dark .header-content {
  color: var(--color-gray-400);
}

.header-title {
  font-size: 13px;
  font-weight: 500;
}

.chevron-icon {
  color: var(--color-gray-400);
  transition: transform 0.2s ease;
}

:root.dark .chevron-icon {
  color: var(--color-gray-500);
}

/* Content */
.legend-content {
  padding: 0 12px 12px;
  border-top: 1px solid var(--color-gray-200);
}

:root.dark .legend-content {
  border-color: var(--color-gray-700);
}

.legend-section {
  padding: 10px 0;
}

.legend-section:last-child {
  padding-bottom: 0;
}

.legend-section + .legend-section {
  border-top: 1px solid var(--color-gray-200);
}

:root.dark .legend-section + .legend-section {
  border-color: var(--color-gray-700);
}

.section-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-gray-600);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 8px;
}

:root.dark .section-title {
  color: var(--color-gray-400);
}

/* Status list */
.status-list {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.status-indicator {
  width: 16px;
  height: 16px;
  border-radius: 4px;
  flex-shrink: 0;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.status-indicator.planned {
  opacity: 0.7;
}

.planned-p {
  font-size: 11px;
  font-weight: bold;
  font-family: Arial, sans-serif;
  line-height: 1;
}

/* Treatment grid */
.treatment-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 6px 12px;
}

.treatment-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.treatment-icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.treatment-icon svg {
  width: 20px;
  height: 20px;
}

.treatment-color {
  width: 16px;
  height: 16px;
  border-radius: 4px;
  flex-shrink: 0;
}

.item-label {
  font-size: 12px;
  color: var(--color-gray-600);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

:root.dark .item-label {
  color: var(--color-gray-400);
}

/* Responsive */
@media (max-width: 640px) {
  .treatment-grid {
    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  }
}
</style>
