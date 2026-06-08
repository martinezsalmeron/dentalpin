<script setup lang="ts">
// The chat surface: scrolling transcript + composer. Used inside the
// global slide-over and on the standalone /copilot page.
const { t } = useI18n()
const { messages, busy, phase, send, confirm } = useCopilot()

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
    <div
      ref="listEl"
      class="flex-1 space-y-3 overflow-y-auto p-1"
    >
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
  </div>
</template>
