<script setup lang="ts">
// Proactive nudges (ADR 0014 §Deferred). Contextual banners at the top
// of the drawer — e.g. a cancellation freed a slot, fill it from recalls.
// The backend stores kind + payload only; text and the chat prompt are
// rendered here so they stay locale-correct.
import type { ApiResponse } from '~~/app/types'

interface Nudge {
  id: string
  kind: string
  payload: Record<string, unknown>
  created_at: string
  expires_at: string
}

const { t, locale } = useI18n()
const api = useApi()
const emit = defineEmits<{ act: [prompt: string] }>()

const nudges = ref<Nudge[]>([])

async function load() {
  try {
    const res = await api.get<ApiResponse<Nudge[]>>('/api/v1/copilot/nudges')
    nudges.value = res.data
  } catch {
    nudges.value = []
  }
}

onMounted(load)
defineExpose({ refresh: load })

function timeOf(n: Nudge): string {
  const raw = n.payload?.start_time as string | undefined
  if (!raw) return ''
  return new Date(raw).toLocaleTimeString(locale.value, { hour: '2-digit', minute: '2-digit' })
}

function textOf(n: Nudge): string {
  if (n.kind === 'appointment_cancelled') {
    return t('copilot.nudge.appointmentCancelled.text', { time: timeOf(n) })
  }
  return n.kind
}

function promptOf(n: Nudge): string {
  if (n.kind === 'appointment_cancelled') {
    return t('copilot.nudge.appointmentCancelled.prompt', { time: timeOf(n) })
  }
  return ''
}

async function dismiss(n: Nudge) {
  nudges.value = nudges.value.filter(x => x.id !== n.id)
  try {
    await api.post(`/api/v1/copilot/nudges/${n.id}/dismiss`, {})
  } catch {
    // optimistic; a failed dismiss just reappears on next load
  }
}

async function act(n: Nudge) {
  const prompt = promptOf(n)
  await dismiss(n)
  if (prompt) emit('act', prompt)
}
</script>

<template>
  <div
    v-if="nudges.length"
    class="flex flex-col gap-2 px-1 pb-2"
  >
    <div
      v-for="n in nudges"
      :key="n.id"
      class="flex items-start gap-2 rounded-lg border border-primary/30 bg-primary/5 p-3"
    >
      <UIcon
        name="i-lucide-bell-ring"
        class="mt-0.5 size-4 shrink-0 text-primary"
      />
      <div class="flex-1 text-sm">
        <p>{{ textOf(n) }}</p>
        <UButton
          size="xs"
          variant="link"
          class="px-0"
          @click="act(n)"
        >
          {{ t('copilot.nudge.act') }}
        </UButton>
      </div>
      <UButton
        icon="i-lucide-x"
        color="neutral"
        variant="ghost"
        size="xs"
        :aria-label="t('copilot.nudge.dismiss')"
        @click="dismiss(n)"
      />
    </div>
  </div>
</template>
