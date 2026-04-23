<script setup lang="ts">
defineProps<{ ctx?: unknown }>()

const { t } = useI18n()
const { todayAppointments, todayLoaded, fetchToday } = useHomeAgenda()

const pending = computed(() => !todayLoaded.value)

onMounted(() => {
  if (!todayLoaded.value) fetchToday()
})
onActivated(() => {
  fetchToday()
})

const counts = computed(() => {
  const c = { total: 0, completed: 0, inProgress: 0, upcoming: 0, cancelled: 0, noShow: 0 }
  const now = Date.now()
  for (const a of todayAppointments.value) {
    c.total += 1
    if (a.status === 'completed') c.completed += 1
    else if (a.status === 'cancelled') c.cancelled += 1
    else if (a.status === 'no_show') c.noShow += 1
    else if (a.status === 'checked_in' || a.status === 'in_treatment') c.inProgress += 1
    else if (new Date(a.start_time).getTime() >= now) c.upcoming += 1
  }
  return c
})
</script>

<template>
  <div class="rounded-token-lg bg-surface ring-1 ring-[var(--color-border)] px-4 py-3 shadow-[var(--shadow-sm)]">
    <div class="flex items-center justify-between mb-1">
      <p class="text-caption text-subtle">
        {{ t('dashboard.todayKpi.title') }}
      </p>
      <UIcon
        name="i-lucide-calendar"
        class="w-4 h-4 text-subtle"
      />
    </div>

    <USkeleton
      v-if="pending"
      class="h-8 w-16 mb-2"
    />
    <p
      v-else
      class="text-display text-default tnum"
    >
      {{ counts.total }}
    </p>

    <div
      v-if="!pending && counts.total > 0"
      class="flex flex-wrap items-center gap-x-3 gap-y-1 text-caption text-muted mt-1"
    >
      <span
        v-if="counts.completed"
        class="flex items-center gap-1"
      >
        <span class="w-1.5 h-1.5 rounded-full bg-[var(--color-success-accent)]" />
        <span class="tnum">{{ counts.completed }}</span>
        {{ t('dashboard.todayKpi.completed') }}
      </span>
      <span
        v-if="counts.inProgress"
        class="flex items-center gap-1"
      >
        <span class="w-1.5 h-1.5 rounded-full bg-[var(--color-primary)]" />
        <span class="tnum">{{ counts.inProgress }}</span>
        {{ t('dashboard.todayKpi.inProgress') }}
      </span>
      <span
        v-if="counts.upcoming"
        class="flex items-center gap-1"
      >
        <span class="w-1.5 h-1.5 rounded-full bg-[var(--color-info-accent)]" />
        <span class="tnum">{{ counts.upcoming }}</span>
        {{ t('dashboard.todayKpi.upcoming') }}
      </span>
      <span
        v-if="counts.cancelled"
        class="flex items-center gap-1"
      >
        <span class="w-1.5 h-1.5 rounded-full bg-[var(--color-danger-accent)]" />
        <span class="tnum">{{ counts.cancelled }}</span>
        {{ t('dashboard.todayKpi.cancelled') }}
      </span>
      <span
        v-if="counts.noShow"
        class="flex items-center gap-1"
      >
        <span class="w-1.5 h-1.5 rounded-full bg-[var(--color-warning-accent)]" />
        <span class="tnum">{{ counts.noShow }}</span>
        {{ t('dashboard.todayKpi.noShow') }}
      </span>
    </div>
    <p
      v-else-if="!pending"
      class="text-caption text-subtle mt-1"
    >
      {{ t('dashboard.todayKpi.empty') }}
    </p>
  </div>
</template>
