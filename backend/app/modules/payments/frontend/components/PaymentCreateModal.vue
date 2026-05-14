<script setup lang="ts">
/**
 * Reusable "record payment" modal.
 *
 * Used as a standalone form in /payments/new, and as the action dialog
 * inside the budget-detail slot. When called from a budget context the
 * patient and the first allocation are locked, but the user can still
 * split the amount across additional on_account / budget targets.
 */

import type {
  PaymentAllocationCreate,
  PaymentMethod,
  PaymentRecord
} from '~~/app/types'

const props = withDefaults(defineProps<{
  open: boolean
  defaultPatientId?: string
  defaultBudgetId?: string
  defaultAmount?: number
  /** Visible label for the locked budget (e.g. ``PRES-2026-0001``). */
  budgetLabel?: string
}>(), {
  defaultPatientId: '',
  defaultBudgetId: undefined,
  defaultAmount: 0,
  budgetLabel: undefined
})

const emit = defineEmits<{
  (e: 'update:open', value: boolean): void
  (e: 'created', payment: PaymentRecord): void
}>()

const { t } = useI18n()
const { create } = usePayments()

const PAYMENT_METHODS: PaymentMethod[] = [
  'cash', 'card', 'bank_transfer', 'direct_debit', 'insurance', 'other'
]

const isBudgetContext = computed(() => Boolean(props.defaultBudgetId))

function buildInitialAllocations(): PaymentAllocationCreate[] {
  if (isBudgetContext.value && props.defaultBudgetId) {
    return [{
      target_type: 'budget',
      target_id: props.defaultBudgetId,
      amount: Number(props.defaultAmount ?? 0)
    }]
  }
  return [{ target_type: 'on_account', target_id: undefined, amount: 0 }]
}

function buildInitialForm() {
  return {
    patient_id: props.defaultPatientId || '',
    amount: Number(props.defaultAmount ?? 0),
    method: 'cash' as PaymentMethod,
    payment_date: new Date().toISOString().slice(0, 10),
    reference: '',
    notes: '',
    allocations: buildInitialAllocations()
  }
}

const form = ref(buildInitialForm())
const formError = ref<string | null>(null)
const isSubmitting = ref(false)

// Reset whenever the modal opens — keeps state from leaking between calls.
watch(() => props.open, (isOpen) => {
  if (isOpen) {
    form.value = buildInitialForm()
    formError.value = null
  }
})

const allocationsSum = computed(() =>
  form.value.allocations.reduce((s, a) => s + Number(a.amount || 0), 0)
)

const allocationsValid = computed(() => {
  const target = Number(form.value.amount)
  return Math.abs(allocationsSum.value - target) <= 0.001
})

function addAllocation() {
  form.value.allocations.push({
    target_type: 'on_account',
    target_id: undefined,
    amount: 0
  })
}

function removeAllocation(idx: number) {
  if (form.value.allocations.length > 1) {
    form.value.allocations.splice(idx, 1)
  }
}

async function submit() {
  formError.value = null
  if (!form.value.patient_id) {
    formError.value = t('payments.new.errSum')
    return
  }
  if (!allocationsValid.value) {
    formError.value = t('payments.new.errSum')
    return
  }

  isSubmitting.value = true
  try {
    const created = await create({
      patient_id: form.value.patient_id,
      amount: Number(form.value.amount),
      method: form.value.method,
      payment_date: form.value.payment_date,
      reference: form.value.reference || undefined,
      notes: form.value.notes || undefined,
      allocations: form.value.allocations.map(a => ({
        target_type: a.target_type,
        target_id: a.target_type === 'budget' ? a.target_id : undefined,
        amount: Number(a.amount)
      }))
    })
    if (created) {
      emit('created', created)
      emit('update:open', false)
    } else {
      formError.value = 'Error'
    }
  } finally {
    isSubmitting.value = false
  }
}

const formatCurrency = (amount: number | string) =>
  new Intl.NumberFormat(undefined, { style: 'currency', currency: 'EUR' }).format(Number(amount))
</script>

<template>
  <UModal
    :open="open"
    :title="t('payments.new.title')"
    @update:open="emit('update:open', $event)"
  >
    <template #body>
      <div class="space-y-3">
        <UFormField
          v-if="!isBudgetContext"
          :label="t('payments.new.patient')"
        >
          <UInput v-model="form.patient_id" placeholder="patient_id (UUID)" />
        </UFormField>

        <UFormField :label="t('payments.new.amount')">
          <UInput v-model.number="form.amount" type="number" step="0.01" />
        </UFormField>

        <UFormField :label="t('payments.new.method')">
          <USelect
            v-model="form.method"
            :items="PAYMENT_METHODS.map(m => ({ label: t(`payments.methods.${m}`), value: m }))"
          />
        </UFormField>

        <UFormField :label="t('payments.new.date')">
          <UInput v-model="form.payment_date" type="date" />
        </UFormField>

        <UFormField :label="t('payments.new.reference')">
          <UInput v-model="form.reference" />
        </UFormField>

        <UFormField :label="t('payments.new.notes')">
          <UInput v-model="form.notes" />
        </UFormField>

        <div>
          <div class="mb-2 flex items-center justify-between">
            <span class="font-medium">{{ t('payments.new.allocations') }}</span>
            <UButton size="xs" variant="ghost" icon="i-lucide-plus" @click="addAllocation">
              {{ t('payments.new.addAllocation') }}
            </UButton>
          </div>
          <div
            v-for="(a, idx) in form.allocations"
            :key="idx"
            class="mb-2 flex items-center gap-2"
          >
            <USelect
              v-model="a.target_type"
              :items="[
                { label: t('payments.new.allocationOnAccount'), value: 'on_account' },
                { label: t('payments.new.allocationToBudget'), value: 'budget' }
              ]"
              class="w-40"
              :disabled="idx === 0 && isBudgetContext"
            />
            <UInput
              v-if="a.target_type === 'budget'"
              v-model="a.target_id"
              :placeholder="budgetLabel || 'budget_id'"
              :disabled="idx === 0 && isBudgetContext"
              class="flex-1"
            />
            <UInput
              v-model.number="a.amount"
              type="number"
              step="0.01"
              class="w-32"
            />
            <UButton
              v-if="form.allocations.length > 1 && !(idx === 0 && isBudgetContext)"
              size="xs"
              variant="ghost"
              icon="i-lucide-x"
              @click="removeAllocation(idx)"
            />
          </div>
          <div class="text-xs" :class="allocationsValid ? 'text-neutral-500' : 'text-red-600'">
            Σ = {{ formatCurrency(allocationsSum) }} / {{ formatCurrency(form.amount) }}
          </div>
        </div>

        <p v-if="formError" class="text-sm text-red-600">{{ formError }}</p>
      </div>
    </template>

    <template #footer>
      <div class="flex justify-end gap-2">
        <UButton variant="ghost" @click="emit('update:open', false)">
          {{ t('payments.new.cancel') }}
        </UButton>
        <UButton
          color="primary"
          :loading="isSubmitting"
          :disabled="!allocationsValid || !form.patient_id"
          @click="submit"
        >
          {{ t('payments.new.submit') }}
        </UButton>
      </div>
    </template>
  </UModal>
</template>
