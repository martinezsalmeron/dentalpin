<script setup lang="ts">
/**
 * Purpose-built "Cobrar presupuesto" modal.
 *
 * Optimised for receptionists: amount-first input, visual method
 * picker, auto-derived allocation breakdown. The user never sees
 * ``target_type`` jargon — when the amount exceeds the pending
 * balance the excess automatically lands on the patient's on-account
 * credit, and the modal narrates it in plain language.
 *
 * The generic, allocations-aware ``PaymentCreateModal`` still powers
 * the ``/payments`` page where flexibility matters more than ergonomics.
 */

import type { PaymentMethod, PaymentRecord, PaymentAllocationCreate } from '~~/app/types'

const props = withDefaults(defineProps<{
  open: boolean
  budgetId: string
  patientId: string
  budgetNumber?: string
  patientName?: string
  pendingAmount: number
}>(), {
  budgetNumber: undefined,
  patientName: undefined
})

const emit = defineEmits<{
  (e: 'update:open', value: boolean): void
  (e: 'created', payment: PaymentRecord): void
}>()

const { t } = useI18n()
const { create } = usePayments()
const { format: formatCurrency } = useCurrency()
const toast = useToast()

interface MethodOption {
  value: PaymentMethod
  icon: string
}

const METHODS: MethodOption[] = [
  { value: 'cash', icon: 'i-lucide-banknote' },
  { value: 'card', icon: 'i-lucide-credit-card' },
  { value: 'bank_transfer', icon: 'i-lucide-landmark' },
  { value: 'direct_debit', icon: 'i-lucide-repeat' },
  { value: 'insurance', icon: 'i-lucide-shield' },
  { value: 'other', icon: 'i-lucide-more-horizontal' }
]

const todayIso = () => new Date().toISOString().slice(0, 10)

const buildInitial = () => ({
  amount: Math.max(0, Number(props.pendingAmount || 0)),
  method: 'cash' as PaymentMethod,
  payment_date: todayIso(),
  reference: '',
  notes: ''
})

const form = ref(buildInitial())
const showDetails = ref(false)
const isSubmitting = ref(false)
const errorMsg = ref<string | null>(null)

watch(() => props.open, (isOpen) => {
  if (isOpen) {
    form.value = buildInitial()
    showDetails.value = false
    errorMsg.value = null
  }
})

// --- Computed --------------------------------------------------------------

const pending = computed(() => Math.max(0, Number(props.pendingAmount || 0)))
const amount = computed(() => Number(form.value.amount || 0))
const isValid = computed(() => amount.value > 0)

const toBudget = computed(() => Math.min(amount.value, pending.value))
const toOnAccount = computed(() => Math.max(0, amount.value - pending.value))

const newPending = computed(() => Math.max(0, pending.value - toBudget.value))
const willClose = computed(() => pending.value > 0 && newPending.value === 0)

const isToday = computed(() => form.value.payment_date === todayIso())

// --- Formatters ------------------------------------------------------------

function fmt(value: number | string) {
  return formatCurrency(Number(value || 0))
}

// --- Actions ---------------------------------------------------------------

function setAmount(v: number) {
  form.value.amount = Number(v.toFixed(2))
}

function setToday() {
  form.value.payment_date = todayIso()
}

function buildAllocations(): PaymentAllocationCreate[] {
  const allocs: PaymentAllocationCreate[] = []
  if (toBudget.value > 0) {
    allocs.push({
      target_type: 'budget',
      target_id: props.budgetId,
      amount: toBudget.value
    })
  }
  if (toOnAccount.value > 0) {
    allocs.push({
      target_type: 'on_account',
      amount: toOnAccount.value
    })
  }
  return allocs
}

async function submit() {
  errorMsg.value = null
  if (!isValid.value) return

  isSubmitting.value = true
  try {
    const created = await create({
      patient_id: props.patientId,
      amount: amount.value,
      method: form.value.method,
      payment_date: form.value.payment_date,
      reference: form.value.reference?.trim() || undefined,
      notes: form.value.notes?.trim() || undefined,
      allocations: buildAllocations()
    })
    if (created) {
      toast.add({
        title: t('payments.budgetCollect.success'),
        description: fmt(amount.value),
        color: 'success'
      })
      emit('created', created)
      emit('update:open', false)
    } else {
      errorMsg.value = t('payments.budgetCollect.errorGeneric')
    }
  } catch (e) {
    errorMsg.value = (e as Error)?.message || t('payments.budgetCollect.errorGeneric')
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <UModal
    :open="open"
    :title="t('payments.budgetCollect.title') + (budgetNumber ? ` · ${budgetNumber}` : '')"
    :description="patientName"
    :ui="{
      content: 'max-h-[90vh] flex flex-col',
      body: 'overflow-y-auto'
    }"
    @update:open="emit('update:open', $event)"
  >
    <template #body>
      <div class="space-y-5">
        <!-- Amount -->
        <section class="space-y-2">
          <label class="block text-sm font-medium text-default">
            {{ t('payments.budgetCollect.amountLabel') }}
          </label>
          <div class="relative">
            <span
              class="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-xl text-subtle"
            >
              {{ fmt(0).replace(/[\d.,]/g, '').trim() }}
            </span>
            <input
              v-model.number="form.amount"
              type="number"
              inputmode="decimal"
              step="0.01"
              min="0"
              class="w-full rounded-md border border-default bg-elevated py-3 pl-10 pr-3 text-2xl font-semibold text-default focus:border-primary-accent focus:outline-none focus:ring-1 focus:ring-primary-accent"
            >
          </div>
          <div class="flex flex-wrap gap-2">
            <UButton
              v-if="pending > 0"
              size="xs"
              variant="soft"
              :color="amount === pending ? 'primary' : 'neutral'"
              @click="setAmount(pending)"
            >
              {{ t('payments.budgetCollect.quickFull') }} · {{ fmt(pending) }}
            </UButton>
            <UButton
              v-if="pending > 0"
              size="xs"
              variant="soft"
              color="neutral"
              @click="setAmount(pending / 2)"
            >
              50% · {{ fmt(pending / 2) }}
            </UButton>
            <UButton
              v-if="pending > 0"
              size="xs"
              variant="soft"
              color="neutral"
              @click="setAmount(pending / 4)"
            >
              25% · {{ fmt(pending / 4) }}
            </UButton>
          </div>
        </section>

        <!-- Method -->
        <section class="space-y-2">
          <label class="block text-sm font-medium text-default">
            {{ t('payments.budgetCollect.methodLabel') }}
          </label>
          <div class="grid grid-cols-3 gap-2">
            <button
              v-for="m in METHODS"
              :key="m.value"
              type="button"
              class="flex flex-col items-center gap-1 rounded-md border px-2 py-3 text-xs transition-all focus:outline-none focus:ring-1 focus:ring-primary-accent"
              :class="form.method === m.value
                ? 'border-primary-accent bg-primary-50 text-primary-accent dark:bg-primary-950'
                : 'border-default bg-elevated text-default hover:border-primary-accent'"
              @click="form.method = m.value"
            >
              <UIcon :name="m.icon" class="h-5 w-5" />
              <span>{{ t(`payments.methods.${m.value}`) }}</span>
            </button>
          </div>
        </section>

        <!-- Date -->
        <section class="space-y-2">
          <label class="block text-sm font-medium text-default">
            {{ t('payments.budgetCollect.dateLabel') }}
          </label>
          <div class="flex items-center gap-2">
            <UInput v-model="form.payment_date" type="date" class="flex-1" />
            <UButton
              v-if="!isToday"
              size="xs"
              variant="soft"
              color="neutral"
              @click="setToday"
            >
              {{ t('payments.budgetCollect.today') }}
            </UButton>
          </div>
        </section>

        <!-- Allocation summary (auto-derived, plain language) -->
        <section
          v-if="amount > 0"
          class="rounded-md border-l-4 px-3 py-2 text-sm"
          :class="toOnAccount > 0
            ? 'border-amber-400 bg-amber-50 text-amber-900 dark:bg-amber-950 dark:text-amber-100'
            : willClose
              ? 'border-green-500 bg-green-50 text-green-900 dark:bg-green-950 dark:text-green-100'
              : 'border-info-accent bg-info-50 text-info-900 dark:bg-info-950 dark:text-info-100'"
        >
          <p v-if="pending === 0">
            {{ t('payments.budgetCollect.noteBudgetSettled') }}
            <strong>{{ fmt(amount) }}</strong>
            {{ t('payments.budgetCollect.noteToOnAccount') }}
          </p>
          <p v-else-if="toOnAccount > 0">
            <strong>{{ fmt(toBudget) }}</strong>
            {{ t('payments.budgetCollect.noteToBudget') }}
            <strong>{{ fmt(toOnAccount) }}</strong>
            {{ t('payments.budgetCollect.noteExcessToOnAccount') }}
          </p>
          <p v-else-if="willClose">
            {{ t('payments.budgetCollect.noteFullySettled') }}
          </p>
          <p v-else>
            <strong>{{ fmt(amount) }}</strong>
            {{ t('payments.budgetCollect.noteAppliedToBudget') }}
            {{ t('payments.budgetCollect.notePendingAfter') }}
            <strong>{{ fmt(newPending) }}</strong>.
          </p>
        </section>

        <!-- Optional details -->
        <section>
          <button
            type="button"
            class="flex items-center gap-1 text-sm text-subtle hover:text-default"
            @click="showDetails = !showDetails"
          >
            <UIcon
              :name="showDetails ? 'i-lucide-chevron-down' : 'i-lucide-chevron-right'"
              class="h-4 w-4"
            />
            {{ t('payments.budgetCollect.optionalDetails') }}
          </button>
          <div v-if="showDetails" class="mt-3 space-y-3">
            <UFormField :label="t('payments.budgetCollect.referenceLabel')">
              <UInput
                v-model="form.reference"
                :placeholder="t('payments.budgetCollect.referencePlaceholder')"
              />
            </UFormField>
            <UFormField :label="t('payments.budgetCollect.notesLabel')">
              <UInput v-model="form.notes" />
            </UFormField>
          </div>
        </section>

        <p v-if="errorMsg" class="text-sm text-red-600">{{ errorMsg }}</p>
      </div>
    </template>

    <template #footer>
      <div class="flex w-full flex-col-reverse gap-2 sm:flex-row sm:justify-end">
        <UButton
          variant="ghost"
          color="neutral"
          :disabled="isSubmitting"
          @click="emit('update:open', false)"
        >
          {{ t('payments.budgetCollect.cancel') }}
        </UButton>
        <UButton
          color="primary"
          size="lg"
          :loading="isSubmitting"
          :disabled="!isValid || isSubmitting"
          @click="submit"
        >
          <UIcon name="i-lucide-wallet" class="mr-1 h-4 w-4" />
          {{ t('payments.budgetCollect.submit') }} {{ fmt(amount) }}
        </UButton>
      </div>
    </template>
  </UModal>
</template>
