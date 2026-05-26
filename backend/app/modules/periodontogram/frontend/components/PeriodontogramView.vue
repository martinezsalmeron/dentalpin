<script setup lang="ts">
/**
 * Entry point rendered by the `patient.diagnosis.subtabs` slot.
 *
 * PR-5 lights up the SEPA chart for both drafts and closed snapshots.
 * Timeline navigation between closed snapshots and autosave plumbing
 * arrive in PR-6.
 */

import { onMounted, ref, watch } from 'vue'
import { usePeriodontogram } from '../composables/usePeriodontogram'

const props = defineProps<{
  patientId: string
  readonly?: boolean
}>()

const { t } = useI18n()
const starting = ref(false)

const {
  timeline,
  currentSnapshot,
  isLoading,
  error,
  hasDraft,
  closedCount,
  isEmpty,
  fetchTimeline,
  fetchDraft,
  fetchSnapshot,
  startDraft
} = usePeriodontogram(() => props.patientId)

async function refreshAll() {
  await fetchTimeline()
  if (hasDraft.value && timeline.value?.draft) {
    await fetchSnapshot(timeline.value.draft.id)
  } else if (timeline.value && timeline.value.dates.length > 0) {
    // Show the most recent closed snapshot as the default view.
    const last = timeline.value.dates[timeline.value.dates.length - 1]
    await fetchSnapshot(last.snapshot_id)
  } else {
    currentSnapshot.value = null
  }
}

onMounted(refreshAll)
watch(() => props.patientId, refreshAll)

async function handleStart() {
  starting.value = true
  try {
    await startDraft()
    if (timeline.value?.draft) {
      await fetchSnapshot(timeline.value.draft.id)
    }
  } finally {
    starting.value = false
  }
}

async function handleRefresh() {
  if (currentSnapshot.value) {
    await fetchSnapshot(currentSnapshot.value.id)
  }
  await fetchTimeline()
}
</script>

<template>
  <div class="periodontogram-view space-y-4">
    <div
      v-if="isLoading && !currentSnapshot"
      class="flex items-center gap-2 text-sm text-gray-500"
    >
      <UIcon name="i-lucide-loader-2" class="animate-spin" />
      <span>{{ t('periodontogram.loading') }}</span>
    </div>

    <UAlert
      v-else-if="error"
      color="error"
      variant="soft"
      icon="i-lucide-alert-triangle"
      :title="t('periodontogram.errors.loadFailed')"
    />

    <PerioEmptyState
      v-else-if="isEmpty"
      :loading="starting"
      @start="handleStart"
    />

    <template v-else-if="currentSnapshot">
      <PeriodontogramChart
        :snapshot="currentSnapshot"
        :readonly="readonly"
        @refresh="handleRefresh"
      />

      <!-- Quick action for snapshots in closed-only state. -->
      <UCard v-if="!hasDraft">
        <div class="flex items-center justify-between">
          <span class="text-sm text-gray-600">
            {{ closedCount }} sesiones cerradas
          </span>
          <UButton
            size="sm"
            icon="i-lucide-plus"
            :loading="starting"
            :disabled="readonly"
            @click="handleStart"
          >
            {{ t('periodontogram.session.openDraft') }}
          </UButton>
        </div>
      </UCard>
    </template>
  </div>
</template>
