<script setup lang="ts">
import type { OdontogramHistoryEntry, ToothTreatmentView, Treatment } from '~~/app/types'
import { viewForTooth } from '~~/app/utils/treatmentView'
import { getToothNameKey, getToothPositionKeys, TREATMENT_COLORS } from '~~/app/config/odontogramConstants'

const props = defineProps<{
  history: OdontogramHistoryEntry[]
  treatments: Treatment[]
  loading?: boolean
}>()

const emit = defineEmits<{
  'update:expanded': [value: boolean]
}>()

const { t } = useI18n()

const isExpanded = ref(false) // Collapsed by default

// Unified timeline entry type
interface TimelineEntry {
  id: string
  type: 'history' | 'treatment'
  toothNumber: number
  date: Date
  // For history entries
  historyEntry?: OdontogramHistoryEntry
  // For treatment entries (per-tooth flattened view).
  treatment?: ToothTreatmentView
}

// Filter out"created" history entries that just show initial"healthy" state
// These are auto-generated when a tooth record is created and aren't meaningful changes
function isInitialToothCreation(entry: OdontogramHistoryEntry): boolean {
  return entry.change_type === 'created'
    && !entry.old_condition
    && (entry.new_condition === 'healthy' || !entry.new_condition)
}

// Combine history and treatments into a unified timeline
const unifiedTimeline = computed<TimelineEntry[]>(() => {
  const entries: TimelineEntry[] = []

  // Add history entries (filtering out initial tooth creations)
  for (const entry of props.history) {
    // Skip entries that are just the initial tooth record creation with"healthy"
    if (isInitialToothCreation(entry)) {
      continue
    }

    entries.push({
      id: `history-${entry.id}`,
      type: 'history',
      toothNumber: entry.tooth_number,
      date: new Date(entry.changed_at),
      historyEntry: entry
    })
  }

  // Add treatment entries — one per Treatment × tooth member.
  for (const treatment of props.treatments) {
    for (const tooth of treatment.teeth) {
      const v = viewForTooth(treatment, tooth.tooth_number)
      if (!v) continue
      entries.push({
        id: `treatment-${v.id}`,
        type: 'treatment',
        toothNumber: v.tooth_number,
        date: new Date(v.performed_at || v.recorded_at),
        treatment: v
      })
    }
  }

  // Sort by date (most recent first)
  return entries.sort((a, b) => b.date.getTime() - a.date.getTime())
})

// Total count for the badge
const totalEntries = computed(() => unifiedTimeline.value.length)

function toggleExpanded() {
  isExpanded.value = !isExpanded.value
  emit('update:expanded', isExpanded.value)
}

function getToothFullName(toothNumber: number): string {
  const nameKey = getToothNameKey(toothNumber)
  const positionKeys = getToothPositionKeys(toothNumber)
  const name = t(nameKey)
  const position = `${t(positionKeys.horizontal)} ${t(positionKeys.vertical)}`
  return `${name} ${position}`
}

function getConditionLabel(condition?: string): string {
  if (!condition) return '-'
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

function getTreatmentStatusColor(status: string): string {
  switch (status) {
    case 'planned':
      return 'text-warning-accent'
    default:
      return 'text-muted'
  }
}

function formatDateTime(dateStr: string | Date): string {
  const date = typeof dateStr === 'string' ? new Date(dateStr) : dateStr
  const day = date.getDate().toString().padStart(2, '0')
  const month = (date.getMonth() + 1).toString().padStart(2, '0')
  const year = date.getFullYear()
  const hours = date.getHours().toString().padStart(2, '0')
  const minutes = date.getMinutes().toString().padStart(2, '0')
  return `${day}/${month}/${year} ${hours}:${minutes}`
}
</script>

<template>
  <div class="change-history-section border border-default rounded-lg overflow-hidden">
    <!-- Header (clickable to collapse/expand) -->
    <button
      class="w-full flex items-center justify-between px-4 py-3 bg-surface-muted hover:bg-surface-muted transition-colors"
      @click="toggleExpanded"
    >
      <div class="flex items-center gap-2">
        <UIcon
          name="i-lucide-history"
          class="w-5 h-5 text-subtle"
        />
        <span class="font-medium text-muted">
          {{ t('odontogram.changeHistory.title') }}
        </span>
        <UBadge
          v-if="totalEntries > 0"
          :label="String(totalEntries)"
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
      <!-- Loading state -->
      <div
        v-if="loading"
        class="flex items-center justify-center py-8"
      >
        <UIcon
          name="i-lucide-loader-2"
          class="w-6 h-6 animate-spin text-subtle"
        />
      </div>

      <!-- Empty state -->
      <div
        v-else-if="totalEntries === 0"
        class="text-center py-4 text-subtle"
      >
        {{ t('odontogram.changeHistory.noChanges') }}
      </div>

      <!-- Unified Timeline -->
      <div
        v-else
        class="space-y-3 max-h-72 overflow-y-auto"
      >
        <div
          v-for="entry in unifiedTimeline"
          :key="entry.id"
          class="flex gap-3 p-3 bg-surface-muted rounded-lg"
        >
          <!-- Timeline indicator -->
          <div class="flex flex-col items-center">
            <div
              class="w-2 h-2 rounded-full"
              :class="entry.type === 'treatment' ? 'bg-[var(--color-success-accent)]' : 'bg-[var(--color-primary)]'"
            />
            <div class="w-0.5 flex-1 bg-surface-sunken mt-1" />
          </div>

          <!-- Content for TREATMENT entries -->
          <div
            v-if="entry.type === 'treatment' && entry.treatment"
            class="flex-1 min-w-0"
          >
            <!-- Tooth info -->
            <div class="flex items-center gap-2 text-sm flex-wrap">
              <span class="font-medium text-default">
                {{ entry.toothNumber }}
              </span>
              <span class="text-muted">
                {{ getToothFullName(entry.toothNumber) }}
              </span>
              <span
                v-if="entry.treatment.surfaces && entry.treatment.surfaces.length > 0"
                class="text-subtle"
              >
                ({{ entry.treatment.surfaces.join(', ') }})
              </span>
              <UBadge
                :label="t('odontogram.changeHistory.treatmentAdded')"
                size="xs"
                color="success"
                variant="subtle"
              />
            </div>

            <!-- Treatment info -->
            <div class="flex items-center gap-2 mt-1 text-sm">
              <span
                class="w-3 h-3 rounded border border-default"
                :style="{ backgroundColor: getConditionColor(entry.treatment.treatment_type) }"
              />
              <span class="text-muted font-medium">
                {{ t(`odontogram.treatments.types.${entry.treatment.treatment_type}`) }}
              </span>
              <span :class="getTreatmentStatusColor(entry.treatment.status)">
                ({{ t(`odontogram.treatments.status.${entry.treatment.status}`) }})
              </span>
            </div>

            <!-- Notes -->
            <p
              v-if="entry.treatment.notes"
              class="text-sm text-muted mt-1"
            >
              {{ entry.treatment.notes }}
            </p>

            <!-- Timestamp -->
            <div class="flex items-center gap-2 mt-2 text-caption text-subtle">
              <UIcon
                name="i-lucide-calendar"
                class="w-3 h-3"
              />
              <span>{{ formatDateTime(entry.date) }}</span>
              <span
                v-if="entry.treatment.performed_by_name"
                class="flex items-center gap-1"
              >
                <span>&bull;</span>
                <UIcon
                  name="i-lucide-user"
                  class="w-3 h-3"
                />
                {{ entry.treatment.performed_by_name }}
              </span>
            </div>
          </div>

          <!-- Content for HISTORY entries -->
          <div
            v-else-if="entry.type === 'history' && entry.historyEntry"
            class="flex-1 min-w-0"
          >
            <!-- Tooth info and change type -->
            <div class="flex items-center gap-2 text-sm flex-wrap">
              <span class="font-medium text-default">
                {{ entry.toothNumber }}
              </span>
              <span class="text-muted">
                {{ getToothFullName(entry.toothNumber) }}
              </span>
              <span
                v-if="entry.historyEntry.surface"
                class="text-subtle"
              >
                ({{ entry.historyEntry.surface }})
              </span>
              <UBadge
                :label="getChangeTypeLabel(entry.historyEntry.change_type)"
                size="xs"
                color="neutral"
                variant="subtle"
              />
            </div>

            <!-- Condition change -->
            <div
              v-if="entry.historyEntry.old_condition || entry.historyEntry.new_condition"
              class="flex items-center gap-2 mt-1 text-sm flex-wrap"
            >
              <!-- Old condition -->
              <span
                v-if="entry.historyEntry.old_condition"
                class="flex items-center gap-1"
              >
                <span
                  class="w-3 h-3 rounded border border-default"
                  :style="{ backgroundColor: getConditionColor(entry.historyEntry.old_condition) }"
                />
                <span class="text-subtle">{{ getConditionLabel(entry.historyEntry.old_condition) }}</span>
              </span>

              <!-- Arrow -->
              <UIcon
                v-if="entry.historyEntry.old_condition && entry.historyEntry.new_condition"
                name="i-lucide-arrow-right"
                class="w-4 h-4 text-subtle"
              />

              <!-- New condition -->
              <span
                v-if="entry.historyEntry.new_condition"
                class="flex items-center gap-1"
              >
                <span
                  class="w-3 h-3 rounded border border-default"
                  :style="{ backgroundColor: getConditionColor(entry.historyEntry.new_condition) }"
                />
                <span class="text-muted">{{ getConditionLabel(entry.historyEntry.new_condition) }}</span>
              </span>
            </div>

            <!-- Notes -->
            <p
              v-if="entry.historyEntry.notes"
              class="text-sm text-muted mt-1"
            >
              {{ entry.historyEntry.notes }}
            </p>

            <!-- User and timestamp -->
            <div class="flex items-center gap-2 mt-2 text-caption text-subtle">
              <UIcon
                name="i-lucide-user"
                class="w-3 h-3"
              />
              <span>{{ entry.historyEntry.changed_by_name || entry.historyEntry.changed_by }}</span>
              <span>&bull;</span>
              <span>{{ formatDateTime(entry.historyEntry.changed_at) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
