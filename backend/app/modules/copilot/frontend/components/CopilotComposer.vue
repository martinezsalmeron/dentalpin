<script setup lang="ts">
const model = defineModel<string>({ required: true })
defineProps<{ busy: boolean }>()
const emit = defineEmits<{ submit: [] }>()
const { t } = useI18n()

function onKeydown(e: KeyboardEvent) {
  // Enter sends; Shift+Enter inserts a newline.
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    emit('submit')
  }
}
</script>

<template>
  <div class="border-t border-default pt-2">
    <div class="flex items-end gap-2">
      <UTextarea
        v-model="model"
        :rows="1"
        autoresize
        :placeholder="t('copilot.placeholder')"
        class="flex-1"
        :disabled="busy"
        @keydown="onKeydown"
      />
      <UButton
        icon="i-lucide-send"
        color="primary"
        :loading="busy"
        :disabled="!model.trim()"
        :aria-label="t('copilot.send')"
        @click="emit('submit')"
      />
    </div>
    <p class="mt-1.5 flex items-center justify-center gap-1 text-center text-xs text-muted">
      <UIcon name="i-lucide-shield-check" />
      {{ t('copilot.trust') }}
    </p>
  </div>
</template>
