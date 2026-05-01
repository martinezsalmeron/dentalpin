<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import type { Recall } from '../composables/useRecalls'

// Slot entry into `patient.summary.feed`. `<ModuleSlot>` passes the
// slot ctx as a single `ctx` prop.
const props = defineProps<{
  ctx: { patient: { id: string } }
}>()

const { t, locale } = useI18n()
const recallsApi = useRecalls()

const recalls = ref<Recall[]>([])
const isLoading = ref(false)

async function load() {
  const patientId = props.ctx?.patient?.id
  if (!patientId) {
    recalls.value = []
    return
  }
  isLoading.value = true
  try {
    const res = await recallsApi.listForPatient(patientId)
    recalls.value = res.data
  } catch {
    recalls.value = []
  } finally {
    isLoading.value = false
  }
}

onMounted(load)

const nextRecall = computed(() =>
  recalls.value.find(r => ['pending', 'contacted_no_answer', 'contacted_scheduled'].includes(r.status))
)

const recentHistory = computed(() => recalls.value.slice(0, 5))

function formatMonth(iso: string): string {
  const date = new Date(iso)
  return new Intl.DateTimeFormat(locale.value, { year: 'numeric', month: 'long' }).format(date)
}

function statusColour(status: Recall['status']): 'success' | 'info' | 'warning' | 'neutral' | 'error' {
  switch (status) {
    case 'done': return 'success'
    case 'contacted_scheduled': return 'info'
    case 'pending':
    case 'contacted_no_answer': return 'warning'
    case 'cancelled':
    case 'contacted_declined':
    case 'needs_review': return 'neutral'
    default: return 'neutral'
  }
}
</script>

<template>
  <UCard
    v-if="recalls.length > 0 || isLoading"
    :ui="{ body: 'p-3' }"
  >
    <template #header>
      <div class="flex items-center gap-2">
        <UIcon
          name="i-lucide-bell"
          class="w-4 h-4 text-subtle"
        />
        <span class="text-caption uppercase tracking-wide text-subtle">
          {{ t('recalls.history') }}
        </span>
      </div>
    </template>

    <USkeleton
      v-if="isLoading"
      class="h-12 w-full"
    />

    <div
      v-else-if="nextRecall"
      class="mb-2"
    >
      <UBadge
        color="warning"
        variant="subtle"
        size="sm"
      >
        {{ t('recalls.pillNext', {
          month: formatMonth(nextRecall.due_month),
          reason: t(`recalls.reasons.${nextRecall.reason}`)
        }) }}
      </UBadge>
    </div>

    <ul class="divide-y divide-default text-sm">
      <li
        v-for="r in recentHistory"
        :key="r.id"
        class="flex items-center justify-between py-1.5 gap-3"
      >
        <div class="min-w-0 truncate">
          <span class="text-default">{{ formatMonth(r.due_month) }}</span>
          <span class="text-subtle"> · </span>
          <span class="text-subtle">{{ t(`recalls.reasons.${r.reason}`) }}</span>
        </div>
        <UBadge
          :color="statusColour(r.status)"
          variant="soft"
          size="xs"
        >
          {{ t(`recalls.status.${r.status}`) }}
        </UBadge>
      </li>
    </ul>
    <div class="pt-2">
      <NuxtLink
        :to="`/recalls?patient_id=${props.ctx.patient.id}`"
        class="text-primary-accent hover:underline text-caption"
      >
        {{ t('recalls.viewAll') }} →
      </NuxtLink>
    </div>
  </UCard>
</template>
