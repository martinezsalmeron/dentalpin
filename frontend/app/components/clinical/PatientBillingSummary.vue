<script setup lang="ts">
import type { PatientBillingSummary, InvoiceListItem, Payment } from '~/types'
import { PERMISSIONS } from '~/config/permissions'

const props = defineProps<{
  patientId: string
}>()

const { t, locale } = useI18n()
const { can } = usePermissions()
const { fetchPatientSummary, fetchInvoices, fetchPayments, getPaymentMethodLabel } = useInvoices()

// State
const summary = ref<PatientBillingSummary | null>(null)
const invoices = ref<InvoiceListItem[]>([])
const isLoading = ref(true)
const expandedInvoices = ref<Set<string>>(new Set())
const invoicePayments = ref<Map<string, Payment[]>>(new Map())
const loadingPayments = ref<Set<string>>(new Set())

// Fetch data
async function loadData() {
  isLoading.value = true
  try {
    const [summaryData, invoicesData] = await Promise.all([
      fetchPatientSummary(props.patientId),
      fetchInvoices({ patient_id: props.patientId, page_size: 100 })
    ])
    summary.value = summaryData
    invoices.value = invoicesData
  } finally {
    isLoading.value = false
  }
}

// Toggle invoice expansion and load payments
async function toggleInvoice(invoiceId: string) {
  if (expandedInvoices.value.has(invoiceId)) {
    expandedInvoices.value.delete(invoiceId)
  } else {
    expandedInvoices.value.add(invoiceId)
    // Load payments if not already loaded
    if (!invoicePayments.value.has(invoiceId)) {
      loadingPayments.value.add(invoiceId)
      try {
        const payments = await fetchPayments(invoiceId)
        invoicePayments.value.set(invoiceId, payments)
      } finally {
        loadingPayments.value.delete(invoiceId)
      }
    }
  }
}

// Format currency
function formatCurrency(amount: number, currency: string = 'EUR'): string {
  return new Intl.NumberFormat(locale.value, {
    style: 'currency',
    currency
  }).format(amount)
}

// Format date
function formatDate(dateStr: string | undefined): string {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString(locale.value, {
    day: '2-digit',
    month: '2-digit',
    year: '2-digit'
  })
}

// Status badge color
type BadgeColor = 'success' | 'warning' | 'neutral' | 'error' | 'info' | 'primary' | 'secondary'

function getInvoiceStatusColor(status: string): BadgeColor {
  switch (status) {
    case 'draft': return 'neutral'
    case 'issued': return 'info'
    case 'partial': return 'warning'
    case 'paid': return 'success'
    case 'cancelled':
    case 'voided': return 'error'
    default: return 'neutral'
  }
}

// Load data on mount
onMounted(loadData)

// Watch for patient changes
watch(() => props.patientId, loadData)
</script>

<template>
  <div class="space-y-6">
    <!-- Loading state -->
    <div v-if="isLoading">
      <div class="grid grid-cols-3 gap-4 mb-6">
        <USkeleton
          v-for="i in 6"
          :key="i"
          class="h-[72px] rounded-lg"
        />
      </div>
      <USkeleton class="h-8 w-32 mb-4" />
      <USkeleton class="h-12 w-full mb-2" />
      <USkeleton class="h-12 w-full mb-2" />
      <USkeleton class="h-12 w-full" />
    </div>

    <template v-else>
      <!-- Summary metrics - 3x2 grid -->
      <div
        v-if="summary"
        class="grid grid-cols-3 gap-4"
      >
        <!-- Row 1: Budget metrics -->
        <div class="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
          <p class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">
            {{ t('patientBilling.totalBudgeted') }}
          </p>
          <p class="text-2xl font-bold text-gray-900 dark:text-white mt-1">
            {{ formatCurrency(summary.total_budgeted, summary.currency) }}
          </p>
        </div>

        <div class="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 border border-blue-200 dark:border-blue-800">
          <p class="text-xs font-medium text-blue-600 dark:text-blue-400 uppercase tracking-wide">
            {{ t('patientBilling.workInProgress') }}
          </p>
          <p class="text-2xl font-bold text-blue-700 dark:text-blue-300 mt-1">
            {{ formatCurrency(summary.work_in_progress, summary.currency) }}
          </p>
        </div>

        <div class="bg-emerald-50 dark:bg-emerald-900/20 rounded-lg p-4 border border-emerald-200 dark:border-emerald-800">
          <p class="text-xs font-medium text-emerald-600 dark:text-emerald-400 uppercase tracking-wide">
            {{ t('patientBilling.workCompleted') }}
          </p>
          <p class="text-2xl font-bold text-emerald-700 dark:text-emerald-300 mt-1">
            {{ formatCurrency(summary.work_completed, summary.currency) }}
          </p>
        </div>

        <!-- Row 2: Invoice metrics -->
        <div class="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
          <p class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">
            {{ t('patientBilling.totalInvoiced') }}
          </p>
          <p class="text-2xl font-bold text-gray-900 dark:text-white mt-1">
            {{ formatCurrency(summary.total_invoiced, summary.currency) }}
          </p>
        </div>

        <div class="bg-emerald-50 dark:bg-emerald-900/20 rounded-lg p-4 border border-emerald-200 dark:border-emerald-800">
          <p class="text-xs font-medium text-emerald-600 dark:text-emerald-400 uppercase tracking-wide">
            {{ t('patientBilling.totalPaid') }}
          </p>
          <p class="text-2xl font-bold text-emerald-700 dark:text-emerald-300 mt-1">
            {{ formatCurrency(summary.total_paid, summary.currency) }}
          </p>
        </div>

        <div
          :class="[
            'rounded-lg p-4 border',
            summary.balance_pending > 0
              ? 'bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800'
              : 'bg-gray-50 dark:bg-gray-800/50 border-gray-200 dark:border-gray-700'
          ]"
        >
          <p
            :class="[
              'text-xs font-medium uppercase tracking-wide',
              summary.balance_pending > 0
                ? 'text-amber-600 dark:text-amber-400'
                : 'text-gray-500 dark:text-gray-400'
            ]"
          >
            {{ t('patientBilling.balancePending') }}
          </p>
          <p
            :class="[
              'text-2xl font-bold mt-1',
              summary.balance_pending > 0
                ? 'text-amber-700 dark:text-amber-300'
                : 'text-gray-900 dark:text-white'
            ]"
          >
            {{ formatCurrency(summary.balance_pending, summary.currency) }}
          </p>
        </div>
      </div>

      <!-- Invoices section -->
      <div>
        <!-- Header -->
        <div class="flex items-center justify-between mb-4 pb-4 border-b border-gray-200 dark:border-gray-700">
          <h3 class="text-base font-semibold text-gray-900 dark:text-white">
            {{ t('patientBilling.invoices') }}
          </h3>
          <UButton
            v-if="can(PERMISSIONS.billing.write)"
            :to="`/invoices/new?patient_id=${patientId}`"
            icon="i-lucide-plus"
            size="sm"
          >
            {{ t('patientBilling.createInvoice') }}
          </UButton>
        </div>

        <!-- Empty state -->
        <div
          v-if="invoices.length === 0"
          class="text-center py-12 bg-gray-50 dark:bg-gray-800/30 rounded-lg"
        >
          <UIcon
            name="i-lucide-receipt"
            class="w-10 h-10 text-gray-400 mx-auto mb-3"
          />
          <p class="text-sm text-gray-500 dark:text-gray-400 mb-4">
            {{ t('patientBilling.noInvoices') }}
          </p>
          <UButton
            v-if="can(PERMISSIONS.billing.write)"
            :to="`/invoices/new?patient_id=${patientId}`"
            icon="i-lucide-plus"
            size="sm"
            variant="outline"
          >
            {{ t('patientBilling.createInvoice') }}
          </UButton>
        </div>

        <!-- Invoices table -->
        <div
          v-else
          class="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden"
        >
          <table class="w-full">
            <thead class="bg-gray-50 dark:bg-gray-800/50">
              <tr>
                <th class="w-8 px-3 py-2" />
                <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  {{ t('invoice.invoiceNumber') }}
                </th>
                <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  {{ t('common.date') }}
                </th>
                <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  {{ t('invoice.status.title') || t('common.status') }}
                </th>
                <th class="px-3 py-2 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  {{ t('invoice.total') }}
                </th>
                <th class="px-3 py-2 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  {{ t('invoice.balance') }}
                </th>
                <th class="w-16 px-3 py-2" />
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
              <template
                v-for="invoice in invoices"
                :key="invoice.id"
              >
                <!-- Invoice row -->
                <tr
                  class="hover:bg-gray-50 dark:hover:bg-gray-800/30 cursor-pointer transition-colors"
                  @click="toggleInvoice(invoice.id)"
                >
                  <td class="px-3 py-3">
                    <UIcon
                      :name="expandedInvoices.has(invoice.id) ? 'i-lucide-chevron-down' : 'i-lucide-chevron-right'"
                      class="w-4 h-4 text-gray-400"
                    />
                  </td>
                  <td class="px-3 py-3">
                    <span class="font-medium text-gray-900 dark:text-white">
                      {{ invoice.invoice_number || t('invoice.draftNoNumber') }}
                    </span>
                  </td>
                  <td class="px-3 py-3 text-sm text-gray-600 dark:text-gray-300">
                    {{ formatDate(invoice.issue_date || invoice.created_at) }}
                  </td>
                  <td class="px-3 py-3">
                    <UBadge
                      :color="getInvoiceStatusColor(invoice.status)"
                      variant="subtle"
                      size="xs"
                    >
                      {{ t(`invoice.status.${invoice.status}`) }}
                    </UBadge>
                  </td>
                  <td class="px-3 py-3 text-right font-medium text-gray-900 dark:text-white">
                    {{ formatCurrency(invoice.total, invoice.currency) }}
                  </td>
                  <td class="px-3 py-3 text-right">
                    <span
                      :class="invoice.balance_due > 0 ? 'text-amber-600 dark:text-amber-400 font-medium' : 'text-gray-500 dark:text-gray-400'"
                    >
                      {{ formatCurrency(invoice.balance_due, invoice.currency) }}
                    </span>
                  </td>
                  <td class="px-3 py-3 text-right">
                    <NuxtLink
                      :to="`/invoices/${invoice.id}`"
                      class="text-primary-600 dark:text-primary-400 hover:underline text-sm"
                      @click.stop
                    >
                      {{ t('invoice.view') }}
                    </NuxtLink>
                  </td>
                </tr>

                <!-- Expanded payments row -->
                <tr v-if="expandedInvoices.has(invoice.id)">
                  <td
                    colspan="7"
                    class="bg-gray-50 dark:bg-gray-800/30 px-4 py-3"
                  >
                    <!-- Loading payments -->
                    <div
                      v-if="loadingPayments.has(invoice.id)"
                      class="flex items-center gap-2 text-sm text-gray-500 pl-6"
                    >
                      <UIcon
                        name="i-lucide-loader-2"
                        class="w-4 h-4 animate-spin"
                      />
                      {{ t('common.loading') }}
                    </div>

                    <!-- No payments -->
                    <div
                      v-else-if="!invoicePayments.get(invoice.id)?.length"
                      class="text-sm text-gray-500 dark:text-gray-400 pl-6"
                    >
                      {{ t('invoice.payments.noPayments') }}
                    </div>

                    <!-- Payments list -->
                    <div
                      v-else
                      class="pl-6 space-y-2"
                    >
                      <p class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase mb-2">
                        {{ t('invoice.payments.title') }}
                      </p>
                      <div
                        v-for="payment in invoicePayments.get(invoice.id)"
                        :key="payment.id"
                        class="flex items-center gap-4 text-sm"
                        :class="{ 'opacity-50': payment.is_voided }"
                      >
                        <span class="text-gray-500 dark:text-gray-400 w-20">
                          {{ formatDate(payment.payment_date) }}
                        </span>
                        <span class="text-gray-700 dark:text-gray-300 w-28">
                          {{ getPaymentMethodLabel(payment.payment_method) }}
                        </span>
                        <span
                          class="font-medium"
                          :class="payment.is_voided ? 'line-through text-gray-400' : 'text-gray-900 dark:text-white'"
                        >
                          {{ formatCurrency(payment.amount, invoice.currency) }}
                        </span>
                        <UBadge
                          v-if="payment.is_voided"
                          color="error"
                          variant="subtle"
                          size="xs"
                        >
                          {{ t('invoice.payments.voided') }}
                        </UBadge>
                      </div>
                    </div>
                  </td>
                </tr>
              </template>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </div>
</template>
