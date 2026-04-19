<script setup lang="ts">
interface Props {
  /** Amount in major units (e.g. euros). Accepts null/undefined → renders placeholder */
  value: number | null | undefined
  /** ISO 4217 code */
  currency?: string
  /** BCP 47 locale */
  locale?: string
  /** Render negative values in `--color-danger-text` */
  signed?: boolean
  /** Bold weight (e.g. for total rows) */
  strong?: boolean
  /** Fallback string when value is null/undefined */
  placeholder?: string
}

const props = withDefaults(defineProps<Props>(), {
  currency: 'EUR',
  locale: 'es-ES',
  signed: false,
  strong: false,
  placeholder: '—'
})

const formatted = computed(() => {
  if (props.value === null || props.value === undefined || Number.isNaN(props.value)) {
    return props.placeholder
  }
  return new Intl.NumberFormat(props.locale, {
    style: 'currency',
    currency: props.currency
  }).format(props.value)
})

const isNegative = computed(() =>
  props.signed && typeof props.value === 'number' && props.value < 0
)
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
