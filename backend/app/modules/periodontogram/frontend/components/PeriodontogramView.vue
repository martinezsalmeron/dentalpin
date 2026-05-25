<script setup lang="ts">
/**
 * Entry point rendered by the `patient.diagnosis.subtabs` slot.
 *
 * PR-4 ships a deliberately minimal surface: timeline summary, draft
 * pill, and the empty-state CTA. The chart itself + per-site editing
 * arrive in PR-5 / PR-6 — keeping this PR scoped to "module installs,
 * sub-tab appears, fallback works".
 */

import { onMounted, ref, watch } from 'vue'
import { usePeriodontogram } from '../composables/usePeriodontogram'

const props = defineProps<{
  patientId: string
  readonly?: boolean
}>()

const { t, locale } = useI18n()
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
  startDraft
} = usePeriodontogram(() => props.patientId)

onMounted(async () => {
  await fetchTimeline()
  if (hasDraft.value) {
    await fetchDraft()
  }
})

watch(
  () => props.patientId,
  async () => {
    await fetchTimeline()
    currentSnapshot.value = null
    if (hasDraft.value) {
      await fetchDraft()
    }
  }
)

async function handleStart() {
  starting.value = true
  try {
    await startDraft()
  } finally {
    starting.value = false
  }
}

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString(locale.value, {
      day: '2-digit',
      month: 'short',
      year: 'numeric'
    })
  } catch {
    return iso
  }
}
</script>

<template>
  <div class="periodontogram-view space-y-4">
    <div
      v-if="isLoading"
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

    <template v-else>
      <UCard>
        <div class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div class="flex items-center gap-3">
            <UBadge
              v-if="hasDraft"
              color="warning"
              variant="soft"
            >
              {{ t('periodontogram.session.draftBadge') }}
            </UBadge>
            <UBadge
              v-else
              color="success"
              variant="soft"
            >
              {{ t('periodontogram.session.closedBadge') }}
            </UBadge>
            <span class="text-sm text-gray-600">
              {{ closedCount }} {{ t('periodontogram.session.closedBadge').toLowerCase() }}
            </span>
          </div>
          <div class="flex items-center gap-2">
            <UButton
              v-if="hasDraft && currentSnapshot"
              variant="outline"
              size="sm"
              icon="i-lucide-edit"
              disabled
            >
              {{ t('periodontogram.session.continueDraft') }}
            </UButton>
            <UButton
              v-else
              size="sm"
              icon="i-lucide-plus"
              :loading="starting"
              :disabled="readonly"
              @click="handleStart"
            >
              {{ t('periodontogram.session.openDraft') }}
            </UButton>
          </div>
        </div>
      </UCard>

      <UCard v-if="timeline && timeline.dates.length > 0">
        <ul class="space-y-2 text-sm">
          <li
            v-for="entry in timeline.dates"
            :key="entry.snapshot_id"
            class="flex items-center justify-between rounded border border-gray-100 px-3 py-2"
          >
            <span class="font-medium text-gray-900">{{ formatDate(entry.date) }}</span>
            <span class="text-gray-500">{{ entry.change_count }} sitios</span>
          </li>
        </ul>
      </UCard>
    </template>
  </div>
</template>
