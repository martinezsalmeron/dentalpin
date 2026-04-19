<script setup lang="ts">
/**
 * DataField — consistent label + value read-only display for detail views.
 *
 * Either pass `value` as a prop or put content in the default slot.
 */
interface Props {
  label: string
  value?: string | number | null
  /** Fallback when value is empty */
  placeholder?: string
  /** Render value as whitespace-preserving paragraph (notes, descriptions) */
  multiline?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: '—',
  multiline: false
})

const display = computed(() => {
  if (props.value === null || props.value === undefined || props.value === '') {
    return props.placeholder
  }
  return String(props.value)
})
</script>

<template>
  <div>
    <dt class="text-caption text-subtle">
      {{ label }}
    </dt>
    <dd
      class="text-body text-default"
      :class="multiline ? 'whitespace-pre-wrap' : ''"
    >
      <slot>{{ display }}</slot>
    </dd>
  </div>
</template>
