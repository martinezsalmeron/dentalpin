<script setup lang="ts">
/**
 * Renders the per-row debt badge on the /patients list.
 *
 * Plugged into the ``patients.list.row.financial`` slot from the
 * patients module — patients never imports anything from payments;
 * the contract is the slot name + the ``ctx`` shape.
 *
 * Off-books safe: ``summary.debt`` comes from
 * ``earned − net_paid`` (payments-axis only), never from invoices.
 */
import type { PatientPaymentSummary } from '../composables/usePayments'

interface Ctx {
  patient_id: string
  summary: PatientPaymentSummary | null
  currency?: string
}

interface Props {
  ctx: Ctx
}

const props = defineProps<Props>()
const { t } = useI18n()
const { format } = useCurrency()

const summary = computed(() => props.ctx.summary)
const hasDebt = computed(() => Number(summary.value?.debt ?? 0) > 0)
const hasCredit = computed(() => Number(summary.value?.on_account_balance ?? 0) > 0)
</script>

<template>
  <span
    v-if="summary && hasDebt"
    class="inline-flex items-center gap-1 text-caption font-medium text-[var(--color-danger)] tnum"
    :title="t('payments.list.row.debtTooltip')"
  >
    <UIcon
      name="i-lucide-alert-circle"
      class="w-3.5 h-3.5"
    />
    {{ format(summary.debt) }}
  </span>
  <span
    v-else-if="summary && hasCredit"
    class="inline-flex items-center gap-1 text-caption text-[var(--color-info,_var(--color-primary))] tnum"
    :title="t('payments.list.row.creditTooltip')"
  >
    <UIcon
      name="i-lucide-piggy-bank"
      class="w-3.5 h-3.5"
    />
    {{ format(summary.on_account_balance) }}
  </span>
</template>
