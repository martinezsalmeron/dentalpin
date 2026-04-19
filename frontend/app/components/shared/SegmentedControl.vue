<script setup lang="ts">
/**
 * SegmentedControl — pill-style segmented buttons (view-mode toggles, tabs).
 *
 * Option shape: { value, label, icon? }. The active segment gets a white
 * surface lift on a muted track.
 */
interface Option {
  value: string
  label: string
  icon?: string
}

interface Props {
  modelValue: string
  options: Option[]
  size?: 'sm' | 'md'
}

const props = withDefaults(defineProps<Props>(), {
  size: 'sm'
})

defineEmits<{
  'update:modelValue': [value: string]
}>()

const padding = computed(() => props.size === 'sm' ? 'px-3 py-1.5' : 'px-4 py-2')
</script>

<template>
  <div
    class="inline-flex items-center gap-0.5 p-0.5 bg-surface-muted rounded-token-md"
    role="tablist"
  >
    <button
      v-for="opt in options"
      :key="opt.value"
      type="button"
      role="tab"
      :aria-selected="modelValue === opt.value"
      class="inline-flex items-center gap-1.5 text-ui rounded-token-sm transition-colors"
      :class="[
        padding,
        modelValue === opt.value
          ? 'bg-surface text-default shadow-token-xs'
          : 'text-muted hover:text-default'
      ]"
      @click="$emit('update:modelValue', opt.value)"
    >
      <UIcon
        v-if="opt.icon"
        :name="opt.icon"
        class="w-4 h-4"
      />
      {{ opt.label }}
    </button>
  </div>
</template>
