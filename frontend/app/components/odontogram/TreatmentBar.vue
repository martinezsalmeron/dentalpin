<script setup lang="ts">
import type { TreatmentStatus, TreatmentType } from '~/types'
import { TREATMENT_ICONS, isSurfaceTreatment } from './TreatmentIcons'
import {
  TREATMENT_CATEGORIES,
  getAllowedStatusesForTreatment,
  getTreatmentColor
} from '~/config/odontogramConstants'

const props = defineProps<{
  selectedTreatment?: TreatmentType | null
  selectedStatus: TreatmentStatus
  disabled?: boolean
}>()

const emit = defineEmits<{
  'update:selectedTreatment': [treatment: TreatmentType | null]
  'update:selectedStatus': [status: TreatmentStatus]
  'treatmentSelect': [treatment: TreatmentType]
  'cancel': []
}>()

const { t } = useI18n()

// Catalog integration - fetch treatments from catalog with fallback to constants
const treatmentCatalog = useTreatmentCatalog()

// Fetch treatments on mount (will use fallback if catalog is empty)
onMounted(async () => {
  if (!treatmentCatalog.initialized.value) {
    await treatmentCatalog.fetchTreatments()
  }
})

// Active category tab - default to diagnostic treatments
const activeCategory = ref('diagnostico')

// All status options
const allStatusOptions: Array<{ value: TreatmentStatus, labelKey: string, color: string }> = [
  { value: 'existing', labelKey: 'odontogram.status.existing', color: 'gray' },
  { value: 'planned', labelKey: 'odontogram.status.planned', color: 'red' }
]

// Get allowed statuses for a treatment (catalog-aware)
function getEffectiveAllowedStatuses(treatment: string): TreatmentStatus[] {
  // Check if treatment is diagnostic from catalog
  if (treatmentCatalog.treatmentIsDiagnostic(treatment)) {
    return ['existing']
  }
  // Fall back to constants
  return getAllowedStatusesForTreatment(treatment)
}

// Filtered status options based on selected treatment
const statusOptions = computed(() => {
  if (!props.selectedTreatment) {
    return allStatusOptions
  }
  const allowedStatuses = getEffectiveAllowedStatuses(props.selectedTreatment)
  return allStatusOptions.filter(opt => allowedStatuses.includes(opt.value))
})

// Categories from catalog (with fallback to constants)
const categories = computed(() => {
  const catalogCategories = treatmentCatalog.clinicalCategories.value
  if (catalogCategories.length > 0) {
    return catalogCategories
  }
  return TREATMENT_CATEGORIES.map(c => c.key)
})

// Current category treatments - uses catalog if available, fallback to constants
const currentTreatments = computed(() => {
  const catalogTreatments = treatmentCatalog.getTreatmentsForCategory(activeCategory.value)
  if (catalogTreatments.length > 0) {
    // Return treatment types from catalog (for odontogram compatibility)
    return catalogTreatments.map(t => t.odontogram_treatment_type)
  }

  // Fallback to constants
  const category = TREATMENT_CATEGORIES.find(c => c.key === activeCategory.value)
  return category?.treatments || []
})

function selectTreatment(treatment: string) {
  // Check allowed statuses and auto-set if restricted
  const allowedStatuses = getEffectiveAllowedStatuses(treatment)
  if (allowedStatuses.length === 1 && !allowedStatuses.includes(props.selectedStatus)) {
    // Auto-select the only allowed status (e.g., existing for diagnostic)
    emit('update:selectedStatus', allowedStatuses[0])
  } else if (!allowedStatuses.includes(props.selectedStatus)) {
    // Current status not allowed, switch to first allowed
    emit('update:selectedStatus', allowedStatuses[0])
  }

  emit('update:selectedTreatment', treatment as TreatmentType)
  emit('treatmentSelect', treatment as TreatmentType)
}

function selectStatus(status: TreatmentStatus) {
  emit('update:selectedStatus', status)
}

function handleCancel() {
  emit('update:selectedTreatment', null)
  emit('cancel')
}

// Check if a treatment is selected
function isSelected(item: string): boolean {
  return props.selectedTreatment === item
}

// Check if any treatment is selected
const hasActiveMode = computed(() => props.selectedTreatment !== null)

// Get treatment label - tries catalog first, then i18n fallback
function getTreatmentLabel(treatment: string): string {
  // Try to get name from catalog
  const catalogName = treatmentCatalog.getTreatmentName(treatment)
  if (catalogName && catalogName !== treatment) {
    return catalogName
  }
  // Fall back to i18n
  return t(`odontogram.treatments.types.${treatment}`, treatment)
}

// Get category label - catalog aware
function getCategoryLabel(categoryKey: string): string {
  const label = treatmentCatalog.getCategoryLabel(categoryKey)
  // If label looks like an i18n key, translate it
  if (label.startsWith('odontogram.')) {
    return t(label, categoryKey)
  }
  return label
}
</script>

<template>
  <div
    class="treatment-bar"
    :class="{ disabled }"
  >
    <!-- Top row: Status + Categories + Instructions -->
    <div class="top-row">
      <!-- Status Toggle -->
      <div class="status-toggle">
        <button
          v-for="option in statusOptions"
          :key="option.value"
          type="button"
          class="status-btn"
          :class="{
            selected: selectedStatus === option.value,
            [`status-${option.color}`]: true
          }"
          @click="selectStatus(option.value)"
        >
          <span class="status-dot" />
          <span class="status-label">{{ t(option.labelKey) }}</span>
        </button>
      </div>

      <!-- Divider -->
      <div class="divider" />

      <!-- Category Tabs -->
      <div class="category-tabs">
        <button
          v-for="categoryKey in categories"
          :key="categoryKey"
          type="button"
          class="category-tab"
          :class="{ active: activeCategory === categoryKey }"
          @click="activeCategory = categoryKey"
        >
          {{ getCategoryLabel(categoryKey) }}
        </button>
      </div>

      <!-- Spacer -->
      <div class="spacer" />

      <!-- Cancel button (when treatment or position action is selected) -->
      <div
        v-if="hasActiveMode"
        class="cancel-section"
      >
        <UButton
          color="neutral"
          variant="ghost"
          size="sm"
          icon="i-lucide-x"
          @click="handleCancel"
        >
          {{ t('common.cancel') }}
        </UButton>
      </div>

      <!-- Instructions -->
      <div class="instructions">
        <template v-if="hasActiveMode">
          <UIcon
            name="i-lucide-mouse-pointer-click"
            class="w-4 h-4"
          />
          <span>{{ t('odontogram.instructions.clickTooth') }}</span>
        </template>
        <template v-else>
          <UIcon
            name="i-lucide-hand-pointer"
            class="w-4 h-4"
          />
          <span>{{ t('odontogram.instructions.selectTreatment') }}</span>
        </template>
      </div>
    </div>

    <!-- Bottom row: Treatment Icons Grid -->
    <div class="treatment-grid">
      <button
        v-for="treatment in currentTreatments"
        :key="treatment"
        type="button"
        class="treatment-btn"
        :class="{
          'selected': isSelected(treatment),
          'is-surface': isSurfaceTreatment(treatment)
        }"
        :title="getTreatmentLabel(treatment)"
        @click="selectTreatment(treatment)"
      >
        <div
          class="treatment-icon"
          :style="{ color: getTreatmentColor(treatment) }"
        >
          <svg
            viewBox="0 0 24 24"
            width="24"
            height="24"
            v-html="TREATMENT_ICONS[treatment]"
          />
        </div>
        <span class="treatment-label">{{ getTreatmentLabel(treatment) }}</span>
      </button>
    </div>
  </div>
</template>

<style scoped>
.treatment-bar {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 12px 16px;
  background: linear-gradient(to bottom, #FAFAFA, #F4F4F5);
  border: 1px solid #E4E4E7;
  border-radius: 12px;
}

:root.dark .treatment-bar {
  background: linear-gradient(to bottom, #27272A, #18181B);
  border-color: #3F3F46;
}

.treatment-bar.disabled {
  opacity: 0.5;
  pointer-events: none;
}

/* Top row */
.top-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

/* Status Toggle */
.status-toggle {
  display: flex;
  gap: 4px;
  background: #E4E4E7;
  padding: 3px;
  border-radius: 8px;
}

:root.dark .status-toggle {
  background: #3F3F46;
}

.status-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.15s ease;
  background: transparent;
  color: #71717A;
}

.status-btn:hover {
  background: rgba(255, 255, 255, 0.5);
}

:root.dark .status-btn:hover {
  background: rgba(0, 0, 0, 0.2);
}

.status-btn.selected {
  background: white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

:root.dark .status-btn.selected {
  background: #27272A;
}

.status-btn.selected.status-red {
  color: #DC2626;
}

.status-btn.selected.status-green {
  color: #16A34A;
}

.status-btn.selected.status-gray {
  color: #52525B;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: currentColor;
}

.status-label {
  display: none;
}

@media (min-width: 768px) {
  .status-label {
    display: inline;
  }
}

/* Divider */
.divider {
  width: 1px;
  height: 32px;
  background: #E4E4E7;
}

:root.dark .divider {
  background: #3F3F46;
}

/* Category Tabs */
.category-tabs {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.category-tab {
  padding: 6px 12px;
  font-size: 13px;
  font-weight: 500;
  color: #71717A;
  border-radius: 6px;
  transition: all 0.15s ease;
}

.category-tab:hover {
  background: #E4E4E7;
  color: #3F3F46;
}

:root.dark .category-tab:hover {
  background: #3F3F46;
  color: #A1A1AA;
}

.category-tab.active {
  background: #3B82F6;
  color: white;
}

/* Spacer */
.spacer {
  flex: 1;
}

/* Cancel Section */
.cancel-section {
  flex-shrink: 0;
}

/* Instructions */
.instructions {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #71717A;
  flex-shrink: 0;
  padding: 6px 12px;
  background: #F4F4F5;
  border-radius: 6px;
}

:root.dark .instructions {
  background: #27272A;
  color: #A1A1AA;
}

/* Treatment Grid - Second row */
.treatment-grid {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  justify-content: flex-start;
}

.treatment-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 8px 10px;
  border-radius: 8px;
  border: 2px solid transparent;
  background: white;
  transition: all 0.15s ease;
  min-width: 70px;
  max-width: 100px;
}

:root.dark .treatment-btn {
  background: #27272A;
}

.treatment-btn:hover {
  border-color: #93C5FD;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.treatment-btn.selected {
  border-color: #3B82F6;
  background: #EFF6FF;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
}

:root.dark .treatment-btn.selected {
  background: rgba(59, 130, 246, 0.2);
}

.treatment-btn.is-surface::after {
  content: '';
  position: absolute;
  top: 4px;
  right: 4px;
  width: 6px;
  height: 6px;
  background: #06B6D4;
  border-radius: 50%;
}

.treatment-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
}

.treatment-icon svg {
  width: 24px;
  height: 24px;
}

.treatment-label {
  font-size: 10px;
  font-weight: 500;
  color: #52525B;
  text-align: center;
  line-height: 1.3;
  word-wrap: break-word;
  hyphens: auto;
}

:root.dark .treatment-label {
  color: #A1A1AA;
}

/* Responsive */
@media (max-width: 640px) {
  .top-row {
    flex-direction: column;
    align-items: stretch;
  }

  .divider {
    width: 100%;
    height: 1px;
  }

  .category-tabs {
    justify-content: center;
  }

  .spacer {
    display: none;
  }

  .cancel-section,
  .instructions {
    justify-content: center;
  }

  .treatment-grid {
    justify-content: center;
  }
}
</style>
