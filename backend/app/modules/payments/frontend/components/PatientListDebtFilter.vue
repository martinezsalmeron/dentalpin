<script setup lang="ts">
/**
 * Filter chip "Con deuda" injected into the /patients page toolbar.
 *
 * Plugged into the ``patients.list.filter`` slot from the patients
 * module. The page owns the filter value; the slot just renders the
 * chip + relays toggle events back via ``ctx.onChange``.
 */
interface Ctx {
  /** Current toggle value (null = inactive, true = active). */
  value: boolean | null
  onChange: (value: boolean | null) => void
}

interface Props {
  ctx: Ctx
}

const props = defineProps<Props>()
const { t } = useI18n()

function onUpdate(v: boolean | null) {
  props.ctx.onChange(v)
}
</script>

<template>
  <FilterToggle
    :model-value="ctx.value"
    :label="t('payments.list.filter.withDebt')"
    icon="i-lucide-alert-circle"
    @update:model-value="onUpdate"
  />
</template>
