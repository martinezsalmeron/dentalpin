<script setup lang="ts">
import { onMounted, ref } from 'vue'
import type { RecallDashboardStats } from '../composables/useRecalls'

const { t } = useI18n()
const recallsApi = useRecalls()

const stats = ref<RecallDashboardStats | null>(null)
const isLoading = ref(false)

async function load() {
  isLoading.value = true
  try {
    const res = await recallsApi.dashboardStats()
    stats.value = res.data
  } catch {
    stats.value = null
  } finally {
    isLoading.value = false
  }
}

onMounted(load)

const conversionPct = computed(() =>
  stats.value ? Math.round(stats.value.conversion_rate * 100) : 0
)
</script>

<template>
  <UCard
    v-if="stats || isLoading"
    :ui="{ body: 'p-3' }"
  >
    <template #header>
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <UIcon
            name="i-lucide-bell"
            class="w-4 h-4 text-default"
          />
          <span class="font-medium">{{ t('recalls.dashboard.title') }}</span>
        </div>
        <NuxtLink
          to="/recalls"
          class="text-primary-accent hover:underline text-caption"
        >
          {{ t('recalls.callList') }} →
        </NuxtLink>
      </div>
    </template>

    <USkeleton
      v-if="isLoading || !stats"
      class="h-16 w-full"
    />

    <div
      v-else
      class="grid grid-cols-2 gap-2 sm:grid-cols-4 text-center"
    >
      <div>
        <div class="text-h2 text-default tnum">
          {{ stats.due_this_week }}
        </div>
        <div class="text-caption text-subtle">
          {{ t('recalls.counters.due_this_week') }}
        </div>
      </div>
      <div>
        <div class="text-h2 text-default tnum">
          {{ stats.overdue }}
        </div>
        <div class="text-caption text-subtle">
          {{ t('recalls.counters.overdue') }}
        </div>
      </div>
      <div>
        <div class="text-h2 text-default tnum">
          {{ stats.scheduled_this_month }}
        </div>
        <div class="text-caption text-subtle">
          {{ t('recalls.counters.scheduled_this_month') }}
        </div>
      </div>
      <div>
        <div class="text-h2 text-default tnum">
          {{ conversionPct }}%
        </div>
        <div class="text-caption text-subtle">
          {{ t('recalls.counters.conversion_rate') }}
        </div>
      </div>
    </div>
  </UCard>
</template>
