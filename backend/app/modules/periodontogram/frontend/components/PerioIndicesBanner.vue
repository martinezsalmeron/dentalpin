<script setup lang="ts">
/**
 * Compact banner showing the four canonical SEPA indices for a
 * snapshot. Closed snapshots reuse the frozen `indices` blob, drafts
 * fall back to the on-the-fly bundle served by `/indices`.
 */
import type { PerioIndices, PerioSnapshotSummary } from '../types'

defineProps<{
  indices: PerioIndices | null
  snapshot: PerioSnapshotSummary | null
}>()

const { t, locale } = useI18n()

function formatDate(iso: string | null | undefined): string {
  if (!iso) return ''
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
  <UCard>
    <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div class="flex items-center gap-3">
        <UBadge
          v-if="snapshot?.status === 'draft'"
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
        <span v-if="snapshot?.closed_at" class="text-sm text-gray-600">
          {{ t('periodontogram.session.recordedAt', { date: formatDate(snapshot.closed_at) }) }}
        </span>
        <span v-else-if="snapshot?.recorded_at" class="text-sm text-gray-600">
          {{ t('periodontogram.session.recordedAt', { date: formatDate(snapshot.recorded_at) }) }}
        </span>
      </div>

      <div
        v-if="indices"
        class="grid grid-cols-2 gap-4 text-sm sm:grid-cols-4"
      >
        <div>
          <div class="text-[10px] uppercase tracking-wide text-gray-500">
            {{ t('periodontogram.indices.bop') }}
          </div>
          <div class="font-mono text-lg font-semibold tabular-nums">
            {{ indices.bop_pct.toFixed(1) }}%
          </div>
        </div>
        <div>
          <div class="text-[10px] uppercase tracking-wide text-gray-500">
            {{ t('periodontogram.indices.pi') }}
          </div>
          <div class="font-mono text-lg font-semibold tabular-nums">
            {{ indices.pi_pct.toFixed(1) }}%
          </div>
        </div>
        <div>
          <div class="text-[10px] uppercase tracking-wide text-gray-500">
            {{ t('periodontogram.indices.calMean') }}
          </div>
          <div class="font-mono text-lg font-semibold tabular-nums">
            {{ indices.cal_mean_mm.toFixed(1) }}mm
          </div>
        </div>
        <div>
          <div class="text-[10px] uppercase tracking-wide text-gray-500">
            {{ t('periodontogram.indices.deepPockets') }}
          </div>
          <div class="font-mono text-lg font-semibold tabular-nums">
            {{ indices.deep_pockets_count }}
          </div>
        </div>
      </div>
    </div>
  </UCard>
</template>
