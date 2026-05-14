<script setup lang="ts">
/**
 * Per-row payment progress on the /budgets list.
 *
 * Plugged into the ``budget.list.row.payments`` slot — the budget
 * module declares the slot and never imports from payments.
 *
 * Visual rules:
 *   - unpaid: chip only (gray). No bar — zero noise when nothing was
 *     collected; the chip already carries the signal.
 *   - partial: thin bar (h-1) + chip (warning) + collected amount.
 *   - paid: full bar (success) + chip "Cobrado". Redundant amount
 *     omitted (the row total is already shown elsewhere).
 *
 * Off-books safe: progress is ``collected / budget.total`` where
 * ``collected`` is the sum of allocations to this budget (payments
 * axis only).
 */
import type { BudgetPaymentSummary } from '../composables/usePayments'

interface Ctx {
  budget_id: string
  summary: BudgetPaymentSummary | null
  total: string | number
  currency?: string
}

interface Props {
  ctx: Ctx
}

const props = defineProps<Props>()
const { t } = useI18n()
const { format } = useCurrency()

const summary = computed(() => props.ctx.summary)
const collected = computed(() => Number(summary.value?.collected ?? 0))
const total = computed(() => Number(props.ctx.total ?? 0))
const percent = computed(() => {
  if (!total.value) return 0
  return Math.min(100, Math.round((collected.value / total.value) * 100))
})

const statusColor = computed<'success' | 'warning' | 'neutral'>(() => {
  switch (summary.value?.payment_status) {
    case 'paid':
      return 'success'
    case 'partial':
      return 'warning'
    default:
      return 'neutral'
  }
})

const statusLabel = computed(() => {
  switch (summary.value?.payment_status) {
    case 'paid':
      return t('payments.list.budgetStatus.paid')
    case 'partial':
      return t('payments.list.budgetStatus.partial')
    case 'unpaid':
      return t('payments.list.budgetStatus.unpaid')
    default:
      return ''
  }
})
</script>

<template>
  <div
    v-if="summary"
    class="flex items-center gap-2"
  >
    <!-- Bar: only when payment exists (partial or paid). -->
    <div
      v-if="summary.payment_status !== 'unpaid'"
      class="w-16 h-1 rounded-full bg-[var(--color-surface-muted)] overflow-hidden shrink-0"
      :title="format(collected)"
    >
      <div
        class="h-full transition-[width]"
        :class="summary.payment_status === 'paid'
          ? 'bg-[var(--color-success)]'
          : 'bg-[var(--color-warning)]'"
        :style="{ width: percent + '%' }"
      />
    </div>

    <UBadge
      :color="statusColor"
      variant="subtle"
      size="xs"
      class="shrink-0"
    >
      {{ statusLabel }}
    </UBadge>

    <!-- Collected amount: only on partial (paid is redundant, unpaid is 0). -->
    <span
      v-if="summary.payment_status === 'partial'"
      class="text-caption text-subtle tnum"
    >
      {{ format(collected) }}
    </span>
  </div>
</template>
