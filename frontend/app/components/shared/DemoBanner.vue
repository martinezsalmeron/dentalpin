<script setup lang="ts">
const { t } = useI18n()
const { public: { demoMode } } = useRuntimeConfig()

const STORAGE_KEY = 'demo:bannerDismissed'
const isDismissed = ref(true)

onMounted(() => {
  if (!demoMode) return
  isDismissed.value = localStorage.getItem(STORAGE_KEY) === 'true'
})

function dismiss() {
  isDismissed.value = true
  if (import.meta.client) {
    localStorage.setItem(STORAGE_KEY, 'true')
  }
}
</script>

<template>
  <div
    v-if="demoMode && !isDismissed"
    class="alert-surface-warning alert-critical-warning flex items-center gap-2 px-4 py-2 text-body"
    role="status"
  >
    <UIcon
      name="i-lucide-triangle-alert"
      class="w-4 h-4 shrink-0"
      :style="{ color: 'var(--color-warning-accent)' }"
    />
    <span class="flex-1">
      {{ t('demo.bannerMessage') }}
    </span>
    <button
      type="button"
      class="shrink-0 inline-flex items-center justify-center w-6 h-6 rounded-token-sm hover:bg-surface transition-colors"
      :aria-label="t('demo.bannerDismiss')"
      @click="dismiss"
    >
      <UIcon
        name="i-lucide-x"
        class="w-4 h-4"
      />
    </button>
  </div>
</template>
