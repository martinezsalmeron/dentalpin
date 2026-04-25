<script setup lang="ts">
/**
 * Placeholder for settings pages whose backing UI hasn't shipped yet.
 * Used by the registry for catalog, vat-types, invoice-series and
 * notifications entries until each gets a proper editor.
 */
interface Props {
  icon: string
  title: string
  description?: string
}

defineProps<Props>()
const { t } = useI18n()
</script>

<template>
  <SectionCard
    :icon="icon"
    :title="title"
  >
    <div class="flex items-start gap-3">
      <UIcon
        name="i-lucide-clock"
        class="w-5 h-5 text-(--color-warning-accent) shrink-0 mt-0.5"
      />
      <div class="min-w-0">
        <p class="text-body text-default">
          {{ t('settings.comingSoon.title') }}
        </p>
        <p
          v-if="description"
          class="mt-1 text-caption text-muted"
        >
          {{ description }}
        </p>
        <p class="mt-2 text-caption text-subtle">
          {{ t('settings.comingSoon.subtitle') }}
        </p>
      </div>
    </div>
  </SectionCard>
</template>
