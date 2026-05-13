<script setup lang="ts">
import type { PaymentMethod, PaymentRecord } from '~~/app/types'

definePageMeta({ middleware: 'auth' })

const { t } = useI18n()
const { can } = usePermissions()
const { payments, total, isLoading, list, refund } = usePayments()

const filters = ref({
  date_from: '' as string | undefined,
  date_to: '' as string | undefined,
  method: '' as string | undefined,
  patient_id: '' as string | undefined
})

const showCreate = ref(false)
const showRefund = ref(false)
const refundTarget = ref<PaymentRecord | null>(null)

const PAYMENT_METHODS: PaymentMethod[] = [
  'cash', 'card', 'bank_transfer', 'direct_debit', 'insurance', 'other'
]

const formatCurrency = (amount: number | string, currency = 'EUR') =>
  new Intl.NumberFormat(undefined, { style: 'currency', currency }).format(Number(amount))

const refresh = () => list({
  date_from: filters.value.date_from || undefined,
  date_to: filters.value.date_to || undefined,
  method: filters.value.method || undefined,
  patient_id: filters.value.patient_id || undefined,
  page: 1,
  page_size: 50
})

onMounted(() => { refresh() })
watch(filters, () => { refresh() }, { deep: true })

function handleCreated() {
  refresh()
}

// --- Refund form ----------------------------------------------------------

const refundForm = ref({
  amount: 0,
  method: 'cash' as PaymentMethod,
  reason_code: 'overpaid' as const,
  reason_note: ''
})

const openRefund = (p: PaymentRecord) => {
  refundTarget.value = p
  refundForm.value = {
    amount: p.net_amount,
    method: p.method,
    reason_code: 'overpaid',
    reason_note: ''
  }
  showRefund.value = true
}

const submitRefund = async () => {
  if (!refundTarget.value) return
  await refund(refundTarget.value.id, { ...refundForm.value })
  showRefund.value = false
  refundTarget.value = null
  refresh()
}
</script>

<template>
  <div class="space-y-4 p-4 md:p-6">
    <div class="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
      <div>
        <h1 class="text-2xl font-semibold">{{ t('payments.list.title') }}</h1>
        <p class="text-sm text-neutral-500">{{ t('payments.list.subtitle') }}</p>
      </div>
      <UButton
        v-if="can('payments.record.write')"
        icon="i-lucide-plus"
        size="lg"
        @click="showCreate = true"
      >
        {{ t('payments.list.new') }}
      </UButton>
    </div>

    <div class="grid grid-cols-1 gap-3 md:grid-cols-4">
      <UFormField :label="t('payments.list.filterDateFrom')">
        <UInput v-model="filters.date_from" type="date" />
      </UFormField>
      <UFormField :label="t('payments.list.filterDateTo')">
        <UInput v-model="filters.date_to" type="date" />
      </UFormField>
      <UFormField :label="t('payments.list.filterMethod')">
        <USelect
          v-model="filters.method"
          :items="PAYMENT_METHODS.map(m => ({ label: t(`payments.methods.${m}`), value: m }))"
          placeholder="—"
        />
      </UFormField>
      <UFormField :label="t('payments.list.filterPatient')">
        <UInput v-model="filters.patient_id" placeholder="patient_id" />
      </UFormField>
    </div>

    <UCard v-if="!isLoading && payments.length === 0">
      <p class="text-center text-neutral-500">{{ t('payments.list.empty') }}</p>
    </UCard>

    <UCard v-for="p in payments" :key="p.id" class="hover:bg-neutral-50">
      <div class="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <div>
          <div class="font-medium">
            {{ p.patient ? `${p.patient.first_name} ${p.patient.last_name}` : '—' }}
          </div>
          <div class="text-sm text-neutral-500">
            {{ p.payment_date }} · {{ t(`payments.methods.${p.method}`) }} · {{ p.reference || '—' }}
          </div>
          <div class="mt-1 flex flex-wrap gap-1">
            <UBadge
              v-for="a in p.allocations"
              :key="a.id"
              color="neutral"
              variant="subtle"
            >
              {{ a.target_type === 'budget' ? t('payments.new.allocationToBudget') : t('payments.new.allocationOnAccount') }}
              · {{ formatCurrency(a.amount, p.currency) }}
            </UBadge>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <div class="text-right">
            <div class="text-lg font-semibold">{{ formatCurrency(p.amount, p.currency) }}</div>
            <div v-if="Number(p.refunded_total) > 0" class="text-xs text-red-600">
              − {{ formatCurrency(p.refunded_total, p.currency) }} {{ t('payments.detail.refundedTotal') }}
            </div>
          </div>
          <UButton
            v-if="can('payments.record.refund') && Number(p.net_amount) > 0"
            variant="soft"
            color="warning"
            size="sm"
            icon="i-lucide-rotate-ccw"
            @click="openRefund(p)"
          >
            {{ t('payments.detail.refund') }}
          </UButton>
        </div>
      </div>
    </UCard>

    <div class="text-center text-xs text-neutral-500">
      {{ payments.length }} / {{ total }}
    </div>

    <PaymentCreateModal
      v-model:open="showCreate"
      @created="handleCreated"
    />

    <UModal v-model:open="showRefund" :title="t('payments.refund.title')">
      <template #body>
        <div class="space-y-3">
          <UFormField :label="t('payments.refund.amount')">
            <UInput v-model.number="refundForm.amount" type="number" step="0.01" />
          </UFormField>
          <UFormField :label="t('payments.refund.method')">
            <USelect
              v-model="refundForm.method"
              :items="PAYMENT_METHODS.map(m => ({ label: t(`payments.methods.${m}`), value: m }))"
            />
          </UFormField>
          <UFormField :label="t('payments.refund.reason')">
            <USelect
              v-model="refundForm.reason_code"
              :items="[
                { label: t('payments.refund.reasonCodes.duplicate'), value: 'duplicate' },
                { label: t('payments.refund.reasonCodes.overpaid'), value: 'overpaid' },
                { label: t('payments.refund.reasonCodes.treatment_cancelled'), value: 'treatment_cancelled' },
                { label: t('payments.refund.reasonCodes.dispute'), value: 'dispute' },
                { label: t('payments.refund.reasonCodes.other'), value: 'other' }
              ]"
            />
          </UFormField>
          <UFormField :label="t('payments.refund.note')">
            <UInput v-model="refundForm.reason_note" />
          </UFormField>
        </div>
      </template>
      <template #footer>
        <div class="flex justify-end gap-2">
          <UButton variant="ghost" @click="showRefund = false">{{ t('payments.new.cancel') }}</UButton>
          <UButton color="warning" @click="submitRefund">{{ t('payments.refund.submit') }}</UButton>
        </div>
      </template>
    </UModal>
  </div>
</template>
