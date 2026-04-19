<script setup lang="ts">
interface Props {
  title: string
  subtitle?: string
}

defineProps<Props>()
</script>

<template>
  <header class="mb-6">
    <div class="flex items-start justify-between gap-4">
      <div class="min-w-0">
        <h1 class="text-display text-default text-pretty">
          {{ title }}
        </h1>
        <p
          v-if="subtitle"
          class="mt-1 text-body text-muted text-pretty"
        >
          {{ subtitle }}
        </p>
      </div>
      <div
        v-if="$slots.actions"
        class="flex items-center gap-2 shrink-0"
      >
        <slot name="actions" />
      </div>
    </div>
    <div
      v-if="$slots.tabs"
      class="mt-4"
    >
      <slot name="tabs" />
    </div>
  </header>
</template>
