<script setup lang="ts">
defineProps<{ ctx?: unknown }>()

const { t } = useI18n()
const { todayAppointments, todayLoaded, fetchToday } = useHomeAgenda()

const pending = computed(() => !todayLoaded.value)
let intervalId: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  if (!todayLoaded.value) fetchToday()
  intervalId = setInterval(fetchToday, 60_000)
})
onBeforeUnmount(() => {
  if (intervalId) clearInterval(intervalId)
})

const counts = computed(() => {
  let inTreatment = 0
  let waiting = 0
  for (const a of todayAppointments.value) {
    if (a.status === 'in_treatment') inTreatment += 1
    else if (a.status === 'checked_in') waiting += 1
  }
  return { inTreatment, waiting, total: inTreatment + waiting }
})

const isEmpty = computed(() => !pending.value && counts.value.total === 0)
</script>

<template>
  <div
    class="rounded-token-lg px-4 py-3"
    :class="isEmpty
      ? 'bg-surface ring-1 ring-[var(--color-border)] shadow-[var(--shadow-sm)]'
      : 'alert-surface-info'"
  >
    <div class="flex items-center justify-between mb-1">
      <p
        class="text-caption"
        :class="isEmpty ? 'text-subtle' : 'opacity-75'"
      >
        {{ t('dashboard.inClinic.title') }}
      </p>
      <UIcon
        name="i-lucide-activity"
        class="w-4 h-4"
        :class="isEmpty ? 'text-subtle' : 'opacity-75'"
      />
    </div>

    <USkeleton
      v-if="pending"
      class="h-8 w-16 mb-2"
    />
    <p
      v-else
      class="text-display tnum"
      :class="isEmpty ? 'text-default' : ''"
    >
      {{ counts.total }}
    </p>

    <div
      v-if="!pending && !isEmpty"
      class="flex flex-wrap items-center gap-x-3 text-caption mt-1 opacity-75"
    >
      <span v-if="counts.inTreatment">
        {{ t('dashboard.inClinic.inTreatment', { n: counts.inTreatment }) }}
      </span>
      <span v-if="counts.waiting">
        {{ t('dashboard.inClinic.waiting', { n: counts.waiting }) }}
      </span>
    </div>
    <p
      v-else-if="!pending"
      class="text-caption text-subtle mt-1"
    >
      {{ t('dashboard.inClinic.empty') }}
    </p>
  </div>
</template>
