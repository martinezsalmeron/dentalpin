<script setup lang="ts">
import type { Payment, PaymentMethod } from '~/types'

const route = useRoute()
const router = useRouter()
const { t, locale } = useI18n()
const toast = useToast()
const { can } = usePermissions()
const {
  currentInvoice,
  isLoading,
  fetchInvoice,
  issueInvoice,
  voidInvoice,
  recordPayment,
  voidPayment,
  canEdit: _canEdit,
  canIssue,
  canRecordPayment,
  canVoid,
  canCreateCreditNote,
  getPaymentMethodLabel,
  formatCurrency
} = useInvoices()

const invoiceId = computed(() => route.params.id as string)

// Modal states
const showPaymentModal = ref(false)
const showCreditNoteModal = ref(false)
const isProcessing = ref(false)

// Payment form
const paymentForm = ref({
  amount: 0,
  payment_method: 'cash' as PaymentMethod,
  payment_date: new Date().toISOString().split('T')[0],
  reference: '',
  notes: ''
})

// Credit note form
const creditNoteForm = ref({
  reason: '',
  items: [] as { invoice_item_id: string, quantity?: number }[]
})

// Payment method options
const paymentMethodOptions = [
  { label: 'Efectivo', value: 'cash' },
  { label: 'Tarjeta', value: 'card' },
  { label: 'Transferencia', value: 'bank_transfer' },
  { label: 'Domiciliaci\u00f3n', value: 'direct_debit' },
  { label: 'Otro', value: 'other' }
]

// Load invoice
onMounted(async () => {
  await fetchInvoice(invoiceId.value)
})

// Format date
function formatDate(dateStr: string | undefined): string {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString(locale.value)
}

// Check if overdue
function isOverdue(): boolean {
  if (!currentInvoice.value?.due_date) return false
  if (!['issued', 'partial'].includes(currentInvoice.value.status)) return false
  return new Date(currentInvoice.value.due_date) < new Date()
}

// Get status badge color
function getStatusBadgeColor(status: string): string {
  const colors: Record<string, string> = {
    draft: 'gray',
    issued: 'blue',
    partial: 'amber',
    paid: 'green',
    cancelled: 'red',
    voided: 'neutral'
  }
  return colors[status] || 'gray'
}

// Actions
async function handleIssue() {
  if (!currentInvoice.value) return
  if (!confirm(t('invoice.confirmations.issue'))) return

  isProcessing.value = true
  try {
    await issueInvoice(invoiceId.value)
    toast.add({
      title: t('common.success'),
      description: t('invoice.messages.issued'),
      color: 'success'
    })
    await fetchInvoice(invoiceId.value)
  } catch {
    toast.add({
      title: t('common.error'),
      description: t('invoice.errors.issue'),
      color: 'error'
    })
  } finally {
    isProcessing.value = false
  }
}

async function handleVoid() {
  if (!currentInvoice.value) return
  if (!confirm(t('invoice.confirmations.void'))) return

  isProcessing.value = true
  try {
    await voidInvoice(invoiceId.value)
    toast.add({
      title: t('common.success'),
      description: t('invoice.messages.voided'),
      color: 'success'
    })
    await fetchInvoice(invoiceId.value)
  } catch {
    toast.add({
      title: t('common.error'),
      description: t('invoice.errors.void'),
      color: 'error'
    })
  } finally {
    isProcessing.value = false
  }
}

function openPaymentModal() {
  if (!currentInvoice.value) return
  paymentForm.value = {
    amount: currentInvoice.value.balance_due,
    payment_method: 'cash',
    payment_date: new Date().toISOString().split('T')[0],
    reference: '',
    notes: ''
  }
  showPaymentModal.value = true
}

async function handleRecordPayment() {
  if (!currentInvoice.value) return

  isProcessing.value = true
  try {
    await recordPayment(invoiceId.value, {
      amount: paymentForm.value.amount,
      payment_method: paymentForm.value.payment_method,
      payment_date: paymentForm.value.payment_date,
      reference: paymentForm.value.reference || undefined,
      notes: paymentForm.value.notes || undefined
    })
    toast.add({
      title: t('common.success'),
      description: t('invoice.messages.paymentRecorded'),
      color: 'success'
    })
    showPaymentModal.value = false
    await fetchInvoice(invoiceId.value)
  } catch {
    toast.add({
      title: t('common.error'),
      description: t('invoice.errors.payment'),
      color: 'error'
    })
  } finally {
    isProcessing.value = false
  }
}

async function handleVoidPayment(payment: Payment) {
  const reason = prompt(t('invoice.prompts.voidPaymentReason'))
  if (!reason) return

  isProcessing.value = true
  try {
    await voidPayment(payment.id, { reason })
    toast.add({
      title: t('common.success'),
      description: t('invoice.messages.paymentVoided'),
      color: 'success'
    })
    await fetchInvoice(invoiceId.value)
  } catch {
    toast.add({
      title: t('common.error'),
      description: t('invoice.errors.voidPayment'),
      color: 'error'
    })
  } finally {
    isProcessing.value = false
  }
}

function openCreditNoteModal() {
  creditNoteForm.value = {
    reason: '',
    items: []
  }
  showCreditNoteModal.value = true
}

async function handleCreateCreditNote() {
  if (!currentInvoice.value) return
  if (!creditNoteForm.value.reason) {
    toast.add({
      title: t('common.error'),
      description: t('invoice.errors.creditNoteReasonRequired'),
      color: 'error'
    })
    return
  }

  isProcessing.value = true
  try {
    const { createCreditNote } = useInvoices()
    const creditNote = await createCreditNote(invoiceId.value, {
      reason: creditNoteForm.value.reason,
      items: creditNoteForm.value.items.length > 0 ? creditNoteForm.value.items : undefined
    })
    toast.add({
      title: t('common.success'),
      description: t('invoice.messages.creditNoteCreated'),
      color: 'success'
    })
    showCreditNoteModal.value = false
    // Navigate to the new credit note
    router.push(`/invoices/${creditNote.id}`)
  } catch {
    toast.add({
      title: t('common.error'),
      description: t('invoice.errors.creditNote'),
      color: 'error'
    })
  } finally {
    isProcessing.value = false
  }
}

function goBack() {
  router.push('/invoices')
}

function goToEdit() {
  router.push(`/invoices/${invoiceId.value}/edit`)
}

function goToBudget() {
  if (currentInvoice.value?.budget_id) {
    router.push(`/budgets/${currentInvoice.value.budget_id}`)
  }
}

function goToCreditNoteFor() {
  if (currentInvoice.value?.credit_note_for_id) {
    router.push(`/invoices/${currentInvoice.value.credit_note_for_id}`)
  }
}
</script>

<template>
  <div class="space-y-6">
    <!-- Loading state -->
    <div
      v-if="isLoading && !currentInvoice"
      class="space-y-4"
    >
      <USkeleton class="h-8 w-48" />
      <USkeleton class="h-64 w-full" />
    </div>

    <!-- Invoice not found -->
    <div
      v-else-if="!currentInvoice"
      class="text-center py-12"
    >
      <UIcon
        name="i-lucide-file-x"
        class="w-12 h-12 text-gray-400 mx-auto mb-4"
      />
      <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">
        {{ t('invoice.notFound') }}
      </h3>
      <UButton @click="goBack">
        {{ t('common.back') }}
      </UButton>
    </div>

    <!-- Invoice content -->
    <template v-else>
      <!-- Header -->
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-4">
          <UButton
            variant="ghost"
            color="neutral"
            icon="i-lucide-arrow-left"
            @click="goBack"
          />
          <div>
            <h1 class="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-3">
              {{ currentInvoice.invoice_number }}
              <UBadge
                :color="getStatusBadgeColor(currentInvoice.status)"
                variant="subtle"
              >
                {{ t(`invoice.status.${currentInvoice.status}`) }}
              </UBadge>
              <UBadge
                v-if="isOverdue()"
                color="red"
                variant="solid"
              >
                {{ t('invoice.overdue') }}
              </UBadge>
            </h1>
            <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
              {{ currentInvoice.patient?.first_name }} {{ currentInvoice.patient?.last_name }}
            </p>
          </div>
        </div>

        <!-- Actions -->
        <div class="flex items-center gap-2">
          <UButton
            v-if="canEdit(currentInvoice) && can('billing.write')"
            variant="outline"
            icon="i-lucide-pencil"
            @click="goToEdit"
          >
            {{ t('common.edit') }}
          </UButton>
          <UButton
            v-if="canIssue(currentInvoice) && can('billing.write')"
            color="primary"
            icon="i-lucide-send"
            :loading="isProcessing"
            @click="handleIssue"
          >
            {{ t('invoice.actions.issue') }}
          </UButton>
          <UButton
            v-if="canRecordPayment(currentInvoice) && can('billing.write')"
            color="success"
            icon="i-lucide-credit-card"
            @click="openPaymentModal"
          >
            {{ t('invoice.actions.recordPayment') }}
          </UButton>
          <UButton
            v-if="canCreateCreditNote(currentInvoice) && can('billing.write')"
            variant="outline"
            color="warning"
            icon="i-lucide-file-minus"
            @click="openCreditNoteModal"
          >
            {{ t('invoice.actions.createCreditNote') }}
          </UButton>
          <UButton
            v-if="canVoid(currentInvoice) && can('billing.admin')"
            variant="outline"
            color="error"
            icon="i-lucide-ban"
            :loading="isProcessing"
            @click="handleVoid"
          >
            {{ t('invoice.actions.void') }}
          </UButton>
        </div>
      </div>

      <!-- Main content grid -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Left column - Invoice details -->
        <div class="lg:col-span-2 space-y-6">
          <!-- Invoice info card -->
          <UCard>
            <template #header>
              <h3 class="font-semibold text-gray-900 dark:text-white">
                {{ t('invoice.details') }}
              </h3>
            </template>

            <div class="grid grid-cols-2 gap-4">
              <div>
                <dt class="text-sm text-gray-500 dark:text-gray-400">
                  {{ t('invoice.issueDate') }}
                </dt>
                <dd class="font-medium text-gray-900 dark:text-white">
                  {{ formatDate(currentInvoice.issue_date) }}
                </dd>
              </div>
              <div>
                <dt class="text-sm text-gray-500 dark:text-gray-400">
                  {{ t('invoice.dueDate') }}
                </dt>
                <dd
                  class="font-medium"
                  :class="isOverdue() ? 'text-red-600' : 'text-gray-900 dark:text-white'"
                >
                  {{ formatDate(currentInvoice.due_date) }}
                </dd>
              </div>
              <div>
                <dt class="text-sm text-gray-500 dark:text-gray-400">
                  {{ t('invoice.billingName') }}
                </dt>
                <dd class="font-medium text-gray-900 dark:text-white">
                  {{ currentInvoice.billing_name }}
                </dd>
              </div>
              <div v-if="currentInvoice.billing_tax_id">
                <dt class="text-sm text-gray-500 dark:text-gray-400">
                  {{ t('invoice.taxId') }}
                </dt>
                <dd class="font-medium text-gray-900 dark:text-white">
                  {{ currentInvoice.billing_tax_id }}
                </dd>
              </div>
              <div v-if="currentInvoice.budget">
                <dt class="text-sm text-gray-500 dark:text-gray-400">
                  {{ t('invoice.linkedBudget') }}
                </dt>
                <dd>
                  <UButton
                    variant="link"
                    size="sm"
                    class="p-0"
                    @click="goToBudget"
                  >
                    {{ currentInvoice.budget.budget_number }}
                  </UButton>
                </dd>
              </div>
              <div v-if="currentInvoice.credit_note_for">
                <dt class="text-sm text-gray-500 dark:text-gray-400">
                  {{ t('invoice.creditNoteFor') }}
                </dt>
                <dd>
                  <UButton
                    variant="link"
                    size="sm"
                    class="p-0"
                    @click="goToCreditNoteFor"
                  >
                    {{ currentInvoice.credit_note_for.invoice_number }}
                  </UButton>
                </dd>
              </div>
            </div>
          </UCard>

          <!-- Items card -->
          <UCard>
            <template #header>
              <h3 class="font-semibold text-gray-900 dark:text-white">
                {{ t('invoice.items') }}
              </h3>
            </template>

            <div class="divide-y divide-gray-200 dark:divide-gray-800">
              <div
                v-for="item in currentInvoice.items"
                :key="item.id"
                class="py-3 first:pt-0 last:pb-0"
              >
                <div class="flex justify-between items-start">
                  <div class="flex-1">
                    <p class="font-medium text-gray-900 dark:text-white">
                      {{ item.description }}
                    </p>
                    <p
                      v-if="item.internal_code"
                      class="text-sm text-gray-500"
                    >
                      {{ item.internal_code }}
                    </p>
                    <p
                      v-if="item.tooth_number"
                      class="text-sm text-gray-500"
                    >
                      {{ t('invoice.tooth') }} {{ item.tooth_number }}
                      <span v-if="item.surfaces?.length">
                        ({{ item.surfaces.join(', ') }})
                      </span>
                    </p>
                  </div>
                  <div class="text-right">
                    <p class="text-sm text-gray-500">
                      {{ item.quantity }} x {{ formatCurrency(item.unit_price, currentInvoice.currency) }}
                    </p>
                    <p
                      v-if="item.line_discount > 0"
                      class="text-sm text-green-600"
                    >
                      -{{ formatCurrency(item.line_discount, currentInvoice.currency) }}
                    </p>
                    <p class="font-semibold text-gray-900 dark:text-white">
                      {{ formatCurrency(item.line_total, currentInvoice.currency) }}
                    </p>
                    <p class="text-xs text-gray-400">
                      {{ t('invoice.vat') }} {{ item.vat_rate }}%
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </UCard>

          <!-- Payments card -->
          <UCard v-if="currentInvoice.payments && currentInvoice.payments.length > 0">
            <template #header>
              <h3 class="font-semibold text-gray-900 dark:text-white">
                {{ t('invoice.payments') }}
              </h3>
            </template>

            <div class="divide-y divide-gray-200 dark:divide-gray-800">
              <div
                v-for="payment in currentInvoice.payments"
                :key="payment.id"
                class="py-3 first:pt-0 last:pb-0 flex items-center justify-between"
                :class="{ 'opacity-50 line-through': payment.is_voided }"
              >
                <div>
                  <p class="font-medium text-gray-900 dark:text-white">
                    {{ formatCurrency(payment.amount, currentInvoice.currency) }}
                  </p>
                  <p class="text-sm text-gray-500">
                    {{ getPaymentMethodLabel(payment.payment_method) }} - {{ formatDate(payment.payment_date) }}
                  </p>
                  <p
                    v-if="payment.reference"
                    class="text-xs text-gray-400"
                  >
                    {{ payment.reference }}
                  </p>
                  <p
                    v-if="payment.is_voided"
                    class="text-xs text-red-600"
                  >
                    {{ t('invoice.paymentVoided') }}: {{ payment.void_reason }}
                  </p>
                </div>
                <UButton
                  v-if="!payment.is_voided && can('billing.admin')"
                  variant="ghost"
                  color="error"
                  icon="i-lucide-x"
                  size="sm"
                  :title="t('invoice.actions.voidPayment')"
                  @click="handleVoidPayment(payment)"
                />
              </div>
            </div>
          </UCard>
        </div>

        <!-- Right column - Summary -->
        <div class="space-y-6">
          <!-- Totals card -->
          <UCard>
            <template #header>
              <h3 class="font-semibold text-gray-900 dark:text-white">
                {{ t('invoice.summary') }}
              </h3>
            </template>

            <div class="space-y-3">
              <div class="flex justify-between">
                <span class="text-gray-500">{{ t('invoice.subtotal') }}</span>
                <span class="font-medium">{{ formatCurrency(currentInvoice.subtotal, currentInvoice.currency) }}</span>
              </div>
              <div
                v-if="currentInvoice.total_discount > 0"
                class="flex justify-between text-green-600"
              >
                <span>{{ t('invoice.discount') }}</span>
                <span>-{{ formatCurrency(currentInvoice.total_discount, currentInvoice.currency) }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-500">{{ t('invoice.tax') }}</span>
                <span class="font-medium">{{ formatCurrency(currentInvoice.total_tax, currentInvoice.currency) }}</span>
              </div>
              <div class="flex justify-between pt-3 border-t border-gray-200 dark:border-gray-700">
                <span class="font-semibold text-gray-900 dark:text-white">{{ t('invoice.total') }}</span>
                <span class="font-bold text-lg text-gray-900 dark:text-white">
                  {{ formatCurrency(currentInvoice.total, currentInvoice.currency) }}
                </span>
              </div>
              <div
                v-if="currentInvoice.status !== 'draft'"
                class="flex justify-between"
              >
                <span class="text-gray-500">{{ t('invoice.paid') }}</span>
                <span class="font-medium text-green-600">
                  {{ formatCurrency(currentInvoice.total_paid, currentInvoice.currency) }}
                </span>
              </div>
              <div
                v-if="currentInvoice.status !== 'draft' && currentInvoice.balance_due > 0"
                class="flex justify-between pt-2 border-t border-gray-200 dark:border-gray-700"
              >
                <span class="font-semibold text-amber-600">{{ t('invoice.balanceDue') }}</span>
                <span class="font-bold text-amber-600">
                  {{ formatCurrency(currentInvoice.balance_due, currentInvoice.currency) }}
                </span>
              </div>
            </div>
          </UCard>

          <!-- Notes card -->
          <UCard v-if="currentInvoice.public_notes || currentInvoice.internal_notes">
            <template #header>
              <h3 class="font-semibold text-gray-900 dark:text-white">
                {{ t('invoice.notes') }}
              </h3>
            </template>

            <div class="space-y-4">
              <div v-if="currentInvoice.public_notes">
                <dt class="text-sm text-gray-500 dark:text-gray-400 mb-1">
                  {{ t('invoice.publicNotes') }}
                </dt>
                <dd class="text-gray-900 dark:text-white whitespace-pre-wrap">
                  {{ currentInvoice.public_notes }}
                </dd>
              </div>
              <div v-if="currentInvoice.internal_notes">
                <dt class="text-sm text-gray-500 dark:text-gray-400 mb-1">
                  {{ t('invoice.internalNotes') }}
                </dt>
                <dd class="text-gray-900 dark:text-white whitespace-pre-wrap">
                  {{ currentInvoice.internal_notes }}
                </dd>
              </div>
            </div>
          </UCard>
        </div>
      </div>
    </template>

    <!-- Payment Modal -->
    <UModal
      v-model:open="showPaymentModal"
      :title="t('invoice.recordPayment')"
    >
      <template #body>
        <div class="space-y-4 p-4">
          <UFormField :label="t('invoice.paymentAmount')">
            <UInput
              v-model.number="paymentForm.amount"
              type="number"
              :min="0.01"
              :max="currentInvoice?.balance_due"
              step="0.01"
            />
          </UFormField>

          <UFormField :label="t('invoice.paymentMethod')">
            <USelectMenu
              v-model="paymentForm.payment_method"
              :items="paymentMethodOptions"
            />
          </UFormField>

          <UFormField :label="t('invoice.paymentDate')">
            <UInput
              v-model="paymentForm.payment_date"
              type="date"
            />
          </UFormField>

          <UFormField :label="t('invoice.paymentReference')">
            <UInput
              v-model="paymentForm.reference"
              :placeholder="t('invoice.paymentReferencePlaceholder')"
            />
          </UFormField>

          <UFormField :label="t('invoice.paymentNotes')">
            <UTextarea
              v-model="paymentForm.notes"
              :rows="2"
            />
          </UFormField>
        </div>
      </template>
      <template #footer>
        <div class="flex justify-end gap-2">
          <UButton
            variant="ghost"
            color="neutral"
            @click="showPaymentModal = false"
          >
            {{ t('common.cancel') }}
          </UButton>
          <UButton
            color="primary"
            :loading="isProcessing"
            @click="handleRecordPayment"
          >
            {{ t('invoice.actions.recordPayment') }}
          </UButton>
        </div>
      </template>
    </UModal>

    <!-- Credit Note Modal -->
    <UModal
      v-model:open="showCreditNoteModal"
      :title="t('invoice.createCreditNote')"
    >
      <template #body>
        <div class="space-y-4 p-4">
          <UFormField :label="t('invoice.creditNoteReason')">
            <UTextarea
              v-model="creditNoteForm.reason"
              :rows="3"
              :placeholder="t('invoice.creditNoteReasonPlaceholder')"
            />
          </UFormField>

          <p class="text-sm text-gray-500">
            {{ t('invoice.creditNoteInfo') }}
          </p>
        </div>
      </template>
      <template #footer>
        <div class="flex justify-end gap-2">
          <UButton
            variant="ghost"
            color="neutral"
            @click="showCreditNoteModal = false"
          >
            {{ t('common.cancel') }}
          </UButton>
          <UButton
            color="warning"
            :loading="isProcessing"
            @click="handleCreateCreditNote"
          >
            {{ t('invoice.actions.createCreditNote') }}
          </UButton>
        </div>
      </template>
    </UModal>
  </div>
</template>
