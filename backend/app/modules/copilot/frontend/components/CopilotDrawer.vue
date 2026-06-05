<script setup lang="ts">
// The chat surface: scrolling transcript + composer. Used inside the
// global slide-over and on the standalone /copilot page.
const { t } = useI18n()
const { messages, busy, send, confirm } = useCopilot()

const input = ref('')
const listEl = ref<HTMLElement | null>(null)

async function submit() {
  const text = input.value.trim()
  if (!text || busy.value) return
  input.value = ''
  await send(text)
}

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
      <p
        v-if="!messages.length"
        class="px-2 py-8 text-center text-sm text-muted"
      >
        {{ t('copilot.empty') }}
      </p>

      <CopilotMessage
        v-for="(m, i) in messages"
        :key="i"
        :message="m"
        @confirm="confirm"
      />

      <p
        v-if="busy"
        class="px-2 text-xs text-muted"
      >
        {{ t('copilot.thinking') }}
      </p>
    </div>

    <CopilotComposer
      v-model="input"
      :busy="busy"
      @submit="submit"
    />
  </div>
</template>
