<script setup lang="ts">
import type { SettingsCategoryId } from '~/composables/useSettingsRegistry'

definePageMeta({ middleware: 'auth' })

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const registry = useSettingsRegistry()

const categoryId = computed(() => route.params.category as SettingsCategoryId)
const pagePath = computed(() => route.params.page as string)
const category = computed(() => registry.findCategory(categoryId.value))
const entry = computed(() => registry.findPage(categoryId.value, pagePath.value))

// External-link entries (with `to`) shouldn't be mounted here — bounce
// to their target.
watchEffect(() => {
  if (entry.value?.to) router.replace(entry.value.to)
})

const resolvedComponent = shallowRef<unknown>(null)
const loadError = ref(false)

watch(entry, async (e) => {
  resolvedComponent.value = null
  loadError.value = false
  if (!e || e.to) return
  if (!e.component) return
  try {
    const mod = await e.component()
    // Async component default export support.
    resolvedComponent.value = (mod as { default?: unknown }).default ?? mod
  } catch (err) {
    console.error('[settings] failed to load page component', err)
    loadError.value = true
  }
}, { immediate: true })

const pageTitle = computed(() => entry.value ? t(entry.value.labelKey) : t('settings.title'))
const pageDescription = computed(() => entry.value?.descriptionKey ? t(entry.value.descriptionKey) : undefined)
const backTo = computed(() => `/settings/${categoryId.value}`)
const backLabel = computed(() => category.value ? t(category.value.labelKey) : t('settings.title'))
</script>

<template>
  <SettingsLayout
    :active-id="categoryId"
    :title="pageTitle"
    :subtitle="pageDescription"
    :back-to="backTo"
    :back-label="backLabel"
  >
    <!-- Locked: known category gated by permission, or page exists but requires permission user lacks -->
    <div
      v-if="!entry"
      class="rounded-[var(--radius-lg)] ring-1 ring-[var(--color-border)] bg-(--color-surface) p-8"
    >
      <EmptyState
        icon="i-lucide-lock"
        :title="t('settings.locked.title')"
        :description="t('settings.locked.description')"
      >
        <template #actions>
          <UButton
            variant="soft"
            icon="i-lucide-arrow-left"
            :to="backTo"
          >
            {{ backLabel }}
          </UButton>
        </template>
      </EmptyState>
    </div>

    <div
      v-else-if="loadError"
      class="rounded-[var(--radius-lg)] ring-1 ring-[var(--color-border)] bg-(--color-surface) p-8"
    >
      <EmptyState
        icon="i-lucide-x-circle"
        :title="t('common.error')"
        :description="t('settings.loadError.description')"
      >
        <template #actions>
          <UButton
            variant="soft"
            icon="i-lucide-arrow-left"
            :to="backTo"
          >
            {{ backLabel }}
          </UButton>
        </template>
      </EmptyState>
    </div>

    <component
      :is="resolvedComponent"
      v-else-if="resolvedComponent"
    />

    <div
      v-else
      class="space-y-3"
    >
      <USkeleton class="h-32 w-full" />
      <USkeleton class="h-32 w-full" />
    </div>
  </SettingsLayout>
</template>
