<script setup lang="ts">
// Two-zone surface (IA redesign Fase 2): a [Pendientes | Chat] segmented
// control over the read-only pending feed and the chat transcript +
// composer. Used inside the global slide-over and on the /copilot page.
const { t } = useI18n()
const { messages, busy, phase, send, confirm } = useCopilot()

const view = ref<'chat' | 'pending'>('chat')
const tabItems = computed(() => [
  { label: t('copilot.tabs.pending'), value: 'pending' as const },
  { label: t('copilot.tabs.chat'), value: 'chat' as const }
])

const input = ref('')
const listEl = ref<HTMLElement | null>(null)

async function submit() {
  const text = input.value.trim()
  if (!text || busy.value) return
  input.value = ''
  await send(text)
}

async function onPick(prompt: string) {
  if (busy.value) return
  view.value = 'chat'
  input.value = ''
  await send(prompt)
}

const phaseLabel = computed(() => {
  if (!busy.value) return ''
  if (phase.value === 'writing') return t('copilot.phase.writing')
  if (phase.value === 'working') return t('copilot.phase.working')
  return t('copilot.thinking')
})

watch(
  () => messages.value.length,
  async () => {
    await nextTick()
    if (listEl.value) listEl.value.scrollTop = listEl.value.scrollHeight
  }
)
</script>

<template>
  <div class="flex h-full flex-col">
    <div class="p-1 pb-2">
      <UTabs
        v-model="view"
        :items="tabItems"
        size="sm"
        :content="false"
      />
    </div>

    <CopilotPending v-if="view === 'pending'" />

    <template v-else>
      <div
        ref="listEl"
        class="flex-1 space-y-3 overflow-y-auto p-1"
      >
        <CopilotNudges @act="onPick" />

        <CopilotSuggestions
          v-if="!messages.length"
          @pick="onPick"
        />

        <CopilotMessage
          v-for="(m, i) in messages"
          :key="i"
          :message="m"
          @confirm="confirm"
        />

        <p
          v-if="busy"
          class="flex items-center gap-2 px-2 text-xs text-muted"
        >
          <UIcon
            name="i-lucide-loader-circle"
            class="animate-spin"
          />
          {{ phaseLabel }}
        </p>
      </div>

      <CopilotComposer
        v-model="input"
        :busy="busy"
        @submit="submit"
      />
    </template>
  </div>
</template>
