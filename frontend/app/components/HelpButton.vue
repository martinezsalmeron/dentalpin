<script setup lang="ts">
/**
 * Contextual help button for the app shell.
 *
 * Click → right-side slideover that iframes the matching help fragment
 * from the public documentation portal (`<docsUrl>/<lang>/help/<slug>.html`).
 * The fragment is rendered separately by VitePress' `buildEnd` hook
 * (see `docs/portal/.vitepress/help.ts`) and served by nginx with CORS
 * + frame-embedding allowed for the `/help/` path.
 *
 * Hidden when `NUXT_PUBLIC_DOCS_URL` is empty (e.g. in dev without a
 * portal running).
 */
import { ref } from 'vue'

const { t } = useI18n()
const { helpUrl, fullManualUrl, isAvailable } = useHelp()

const open = ref(false)
const loadFailed = ref(false)
const loading = ref(true)

function onIframeLoad() {
  loading.value = false
}

function onIframeError() {
  loading.value = false
  loadFailed.value = true
}

function handleOpen(value: boolean) {
  open.value = value
  if (value) {
    loadFailed.value = false
    loading.value = true
  }
}
</script>

<template>
  <UButton
    v-if="isAvailable"
    variant="ghost"
    color="neutral"
    size="sm"
    icon="i-lucide-circle-help"
    :aria-label="t('help.openHelp', 'Open help')"
    @click="handleOpen(true)"
  >
    <span class="hidden sm:inline">{{ t('help.label', 'Help') }}</span>
  </UButton>

  <USlideover
    :open="open"
    side="right"
    :title="t('help.drawerTitle', 'Help for this page')"
    :ui="{ content: 'w-[480px] max-w-[95vw] bg-surface' }"
    @update:open="handleOpen"
  >
    <template #content>
      <div class="flex flex-col h-full">
        <header class="flex items-center justify-between px-4 h-14 border-b border-default">
          <div class="flex items-center gap-2 min-w-0">
            <UIcon
              name="i-lucide-circle-help"
              class="w-4 h-4 text-subtle shrink-0"
            />
            <span class="text-h3 text-default truncate">
              {{ t('help.drawerTitle', 'Help for this page') }}
            </span>
          </div>
          <UButton
            variant="ghost"
            color="neutral"
            size="sm"
            icon="i-lucide-x"
            :aria-label="t('actions.close', 'Close')"
            @click="handleOpen(false)"
          />
        </header>

        <div class="relative flex-1 min-h-0 overflow-hidden">
          <div
            v-if="loading"
            class="absolute inset-0 flex items-center justify-center bg-surface"
          >
            <UIcon
              name="i-lucide-loader"
              class="w-6 h-6 text-muted animate-spin"
            />
          </div>

          <div
            v-if="loadFailed"
            class="absolute inset-0 flex flex-col items-center justify-center text-center px-6 gap-2 bg-surface"
          >
            <UIcon
              name="i-lucide-circle-alert"
              class="w-6 h-6 text-warning"
            />
            <p class="text-default">
              {{ t('help.unavailable', 'No contextual help available for this page yet.') }}
            </p>
          </div>

          <iframe
            v-show="!loadFailed"
            :src="helpUrl"
            class="w-full h-full border-0"
            :title="t('help.drawerTitle', 'Help for this page')"
            sandbox="allow-popups allow-popups-to-escape-sandbox"
            referrerpolicy="no-referrer"
            @load="onIframeLoad"
            @error="onIframeError"
          />
        </div>

        <footer class="flex items-center justify-end gap-2 px-4 h-12 border-t border-default">
          <UButton
            v-if="fullManualUrl"
            variant="link"
            color="primary"
            size="sm"
            icon="i-lucide-external-link"
            :to="fullManualUrl"
            target="_blank"
          >
            {{ t('help.openFullManual', 'Open full manual') }}
          </UButton>
        </footer>
      </div>
    </template>
  </USlideover>
</template>
