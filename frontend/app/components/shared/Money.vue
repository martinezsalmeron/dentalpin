<script setup lang="ts">
interface Props {
  /** Amount in major units (e.g. euros). Accepts null/undefined → renders placeholder */
  value: number | string | null | undefined
  /** Render negative values in `--color-danger-text` */
  signed?: boolean
  /** Bold weight (e.g. for total rows) */
  strong?: boolean
  /** Fallback string when value is null/undefined */
  placeholder?: string
}

const props = withDefaults(defineProps<Props>(), {
  signed: false,
  strong: false,
  placeholder: '—'
})

const { format } = useCurrency()

const formatted = computed(() => format(props.value) || props.placeholder)

const isNegative = computed(() => {
  if (!props.signed) return false
  const n = typeof props.value === 'string' ? Number(props.value) : props.value
  return typeof n === 'number' && !Number.isNaN(n) && n < 0
})
</script>

<template>
  <span
    class="tnum"
    :class="[
      strong ? 'font-semibold' : '',
      isNegative ? 'text-[var(--color-danger-text)]' : 'text-default'
    ]"
  >
    {{ formatted }}
  </span>
</template>
