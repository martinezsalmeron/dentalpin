<script setup lang="ts">
/**
 * Slot entry into ``budget.detail.sidebar``.
 *
 * Receives the host's ``{ budget }`` context and renders the payments
 * view of that budget: cobrado / pendiente totals, the allocation
 * rows that target the budget, and a "Cobrar" action that pre-fills
 * the create-payment modal.
 *
 * The card lives in the ``payments`` module so the ``budget`` module
 * never imports payments code — they only share the ``ModuleSlot``
 * contract.
 */

import type { PaymentAllocation } from '~~/app/types'

interface BudgetCtx {
  budget: {
    id: string
    patient_id: string
    budget_number?: string
    total: number | string
    status: string
  } | null
}

const props = defineProps<{ ctx: BudgetCtx }>()

const { t } = useI18n()
const { can } = usePermissions()
const { fetchBudgetAllocations } = usePayments()

const allocations = ref<PaymentAllocation[]>([])
const isLoading = ref(false)
const showCreate = ref(false)

const budgetTotal = computed(() => Number(props.ctx?.budget?.total ?? 0))

const collected = computed(() =>
  allocations.value.reduce((sum, a) => sum + Number(a.amount || 0), 0)
)

const pending = computed(() => Math.max(0, budgetTotal.value - collected.value))

async function refresh() {
  if (!props.ctx?.budget?.id) return
  isLoading.value = true
  try {
    allocations.value = await fetchBudgetAllocations(props.ctx.budget.id)
  } finally {
    isLoading.value = false
  }
}

onMounted(refresh)
watch(() => props.ctx?.budget?.id, refresh)

function handleCreated() {
  refresh()
}

const formatCurrency = (amount: number | string) =>
  new Intl.NumberFormat(undefined, { style: 'currency', currency: 'EUR' }).format(Number(amount))
</script>

<template>
  <UCard v-if="ctx?.budget">
    <template #header>
      <div class="flex items-center justify-between">
        <h3 class="font-semibold text-default">
          {{ t('payments.budgetCard.title') }}
        </h3>
        <UButton
          v-if="can('payments.record.write')"
          size="xs"
          icon="i-lucide-wallet"
          @click="showCreate = true"
        >
          {{ t('payments.budgetCard.collect') }}
        </UButton>
      </div>
    </template>

    <div class="space-y-3">
      <div class="grid grid-cols-3 gap-2 text-center">
        <div class="rounded border p-2">
          <div class="text-xs text-neutral-500">{{ t('payments.budgetCard.budgetTotal') }}</div>
          <div class="font-semibold">{{ formatCurrency(budgetTotal) }}</div>
        </div>
        <div class="rounded border p-2">
          <div class="text-xs text-neutral-500">{{ t('payments.budgetCard.collected') }}</div>
          <div class="font-semibold text-green-700">{{ formatCurrency(collected) }}</div>
        </div>
        <div class="rounded border p-2">
          <div class="text-xs text-neutral-500">{{ t('payments.budgetCard.pending') }}</div>
          <div
            class="font-semibold"
            :class="pending > 0 ? 'text-amber-700' : 'text-neutral-500'"
          >
            {{ formatCurrency(pending) }}
          </div>
        </div>
      </div>

      <div v-if="!isLoading && allocations.length === 0" class="text-sm text-neutral-500">
        {{ t('payments.budgetCard.empty') }}
      </div>

      <ul v-else class="divide-y divide-[var(--color-border-subtle)]">
        <li
          v-for="a in allocations"
          :key="a.id"
          class="flex items-center justify-between py-2 text-sm first:pt-0 last:pb-0"
        >
          <span class="text-neutral-600">
            {{ new Date(a.created_at).toLocaleDateString() }}
          </span>
          <span class="font-medium">{{ formatCurrency(a.amount) }}</span>
        </li>
      </ul>
    </div>

    <PaymentCreateModal
      v-model:open="showCreate"
      :default-patient-id="ctx.budget.patient_id"
      :default-budget-id="ctx.budget.id"
      :default-amount="pending"
      :budget-label="ctx.budget.budget_number"
      @created="handleCreated"
    />
  </UCard>
</template>
