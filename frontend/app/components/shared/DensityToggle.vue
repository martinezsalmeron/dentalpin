<script setup lang="ts">
const { t } = useI18n()
const { density, toggle } = useDensity()

const icon = computed(() =>
  density.value === 'compact' ? 'i-lucide-rows-2' : 'i-lucide-rows-4'
)

const label = computed(() =>
  density.value === 'compact'
    ? t('density.switchToComfortable', 'Vista cómoda')
    : t('density.switchToCompact', 'Vista compacta')
)
</script>

<template>
  <UButton
    variant="ghost"
    color="neutral"
    size="sm"
    :icon="icon"
    :aria-label="label"
    :title="label"
    @click="toggle"
  />
</template>
