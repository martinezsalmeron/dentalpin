<script setup lang="ts">
/**
 * "Cobro" multi-select chip injected into the /budgets toolbar.
 *
 * Plugged into the ``budget.list.filter`` slot. The page owns the
 * value (string[]) and relays changes through ``ctx.onChange``.
 */
interface Ctx {
  value: string[]
  onChange: (value: string[]) => void
}

interface Props {
  ctx: Ctx
}

const props = defineProps<Props>()
const { t } = useI18n()

const items = computed(() => [
  { label: t('payments.list.budgetStatus.paid'), value: 'paid' },
  { label: t('payments.list.budgetStatus.partial'), value: 'partial' },
  { label: t('payments.list.budgetStatus.unpaid'), value: 'unpaid' }
])

function onUpdate(value: string[]) {
  props.ctx.onChange(value)
}
</script>

<template>
  <FilterChipMulti
    :model-value="ctx.value"
    :items="items"
    :label="t('payments.list.filter.paymentStatus')"
    icon="i-lucide-wallet"
    @update:model-value="onUpdate"
  />
</template>
