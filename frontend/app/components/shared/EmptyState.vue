<script setup lang="ts">
interface Props {
  icon?: string
  title: string
  description?: string
}

withDefaults(defineProps<Props>(), {
  icon: 'i-lucide-inbox'
})
</script>

<template>
  <div class="flex flex-col items-center justify-center text-center py-12 px-6">
    <UIcon
      :name="icon"
      class="w-8 h-8 text-subtle mb-4"
    />
    <h3 class="text-h2 text-default mb-1">
      {{ title }}
    </h3>
    <p
      v-if="description"
      class="text-body text-muted max-w-sm"
    >
      {{ description }}
    </p>
    <div
      v-if="$slots.actions"
      class="mt-6 flex items-center gap-2"
    >
      <slot name="actions" />
    </div>
  </div>
</template>
