<script setup lang="ts">
import type {
  BillingSummary,
  NumberingGap,
  OverdueInvoice,
  PaymentMethodSummary,
  ProfessionalBillingSummary,
  VatSummaryItem
} from '~/types'

const { t, locale } = useI18n()
const router = useRouter()
const {
  fetchSummary,
  fetchOverdue,
  fetchByPaymentMethod,
  fetchByProfessional,
  fetchVatSummary,
  fetchGaps,
  formatCurrency,
  getPaymentMethodLabel
} = useInvoices()

// State
const isLoading = ref(false)
const summary = ref<BillingSummary | null>(null)
const overdueInvoices = ref<OverdueInvoice[]>([])
const paymentMethods = ref<PaymentMethodSummary[]>([])
const professionals = ref<ProfessionalBillingSummary[]>([])
const vatSummary = ref<VatSummaryItem[]>([])
const numberingGaps = ref<NumberingGap[]>([])

// Date range
const today = new Date()
const firstDayOfMonth = new Date(today.getFullYear(), today.getMonth(), 1)
const dateFrom = ref(firstDayOfMonth.toISOString().split('T')[0])
const dateTo = ref(today.toISOString().split('T')[0])

// Quick date range options
const dateRangeOptions = computed(() => [
  { label: t('invoice.reports.thisMonth'), value: 'month' },
  { label: t('invoice.reports.thisQuarter'), value: 'quarter' },
  { label: t('invoice.reports.thisYear'), value: 'year' },
  { label: t('invoice.reports.lastMonth'), value: 'last_month' },
  { label: t('invoice.reports.lastQuarter'), value: 'last_quarter' },
  { label: t('invoice.reports.lastYear'), value: 'last_year' }
])
const selectedRange = ref('month')

watch(selectedRange, (range) => {
  const now = new Date()
  let from: Date
  let to: Date

  switch (range) {
    case 'month':
      from = new Date(now.getFullYear(), now.getMonth(), 1)
      to = now
      break
    case 'quarter': {
      const quarter = Math.floor(now.getMonth() / 3)
      from = new Date(now.getFullYear(), quarter * 3, 1)
      to = now
      break
    }
    case 'year':
      from = new Date(now.getFullYear(), 0, 1)
      to = now
      break
    case 'last_month':
      from = new Date(now.getFullYear(), now.getMonth() - 1, 1)
      to = new Date(now.getFullYear(), now.getMonth(), 0)
      break
    case 'last_quarter': {
      const lastQuarter = Math.floor(now.getMonth() / 3) - 1
      const year = lastQuarter < 0 ? now.getFullYear() - 1 : now.getFullYear()
      const q = lastQuarter < 0 ? 3 : lastQuarter
      from = new Date(year, q * 3, 1)
      to = new Date(year, q * 3 + 3, 0)
      break
    }
    case 'last_year':
      from = new Date(now.getFullYear() - 1, 0, 1)
      to = new Date(now.getFullYear() - 1, 11, 31)
      break
    default:
      return
  }

  dateFrom.value = from.toISOString().split('T')[0]
  dateTo.value = to.toISOString().split('T')[0]
})

// Load all report data
async function loadReports() {
  isLoading.value = true

  try {
    const [
      summaryData,
      overdueData,
      paymentMethodsData,
      professionalsData,
      vatData,
      gapsData
    ] = await Promise.all([
      fetchSummary(dateFrom.value, dateTo.value),
      fetchOverdue(),
      fetchByPaymentMethod(dateFrom.value, dateTo.value),
      fetchByProfessional(dateFrom.value, dateTo.value),
      fetchVatSummary(dateFrom.value, dateTo.value),
      fetchGaps()
    ])

    summary.value = summaryData
    overdueInvoices.value = overdueData
    paymentMethods.value = paymentMethodsData
    professionals.value = professionalsData
    vatSummary.value = vatData
    numberingGaps.value = gapsData
  } catch (e) {
    console.error('Failed to load reports:', e)
  } finally {
    isLoading.value = false
  }
}

// Reload when dates change
watch([dateFrom, dateTo], () => {
  loadReports()
})

onMounted(() => {
  loadReports()
})

// Format date
function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString(locale.value, {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

// Get payment method icon
function getPaymentMethodIcon(method: string): string {
  const icons: Record<string, string> = {
    cash: 'i-lucide-banknote',
    card: 'i-lucide-credit-card',
    bank_transfer: 'i-lucide-building-2',
    direct_debit: 'i-lucide-repeat',
    other: 'i-lucide-circle'
  }
  return icons[method] || 'i-lucide-circle'
}

// Navigate to invoice
function goToInvoice(id: string) {
  router.push(`/invoices/${id}`)
}

function goBack() {
  router.push('/invoices')
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-4">
        <UButton
          variant="ghost"
          color="neutral"
          icon="i-lucide-arrow-left"
          @click="goBack"
        />
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
          {{ t('invoice.reports.title') }}
        </h1>
      </div>
    </div>

    <!-- Date Range Filters -->
    <UCard>
      <div class="flex flex-wrap items-end gap-4">
        <UFormField :label="t('invoice.reports.period')">
          <USelectMenu
            v-model="selectedRange"
            :items="dateRangeOptions"
            value-key="value"
            class="w-48"
          />
        </UFormField>

        <UFormField :label="t('invoice.reports.from')">
          <UInput
            v-model="dateFrom"
            type="date"
          />
        </UFormField>

        <UFormField :label="t('invoice.reports.to')">
          <UInput
            v-model="dateTo"
            type="date"
          />
        </UFormField>

        <UButton
          :loading="isLoading"
          @click="loadReports"
        >
          {{ t('invoice.reports.refresh') }}
        </UButton>
      </div>
    </UCard>

    <!-- Loading state -->
    <div
      v-if="isLoading"
      class="flex justify-center py-12"
    >
      <UIcon
        name="i-lucide-loader-2"
        class="h-8 w-8 animate-spin text-primary-500"
      />
    </div>

    <template v-else>
      <!-- Summary Cards -->
      <div
        v-if="summary"
        class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4"
      >
        <UCard>
          <div class="text-center">
            <p class="text-sm text-gray-500 dark:text-gray-400">
              {{ t('invoice.reports.totalInvoiced') }}
            </p>
            <p class="text-2xl font-bold text-gray-900 dark:text-white">
              {{ formatCurrency(summary.total_invoiced) }}
            </p>
            <p class="text-sm text-gray-500">
              {{ summary.invoice_count }} {{ t('invoice.reports.invoices') }}
            </p>
          </div>
        </UCard>

        <UCard>
          <div class="text-center">
            <p class="text-sm text-gray-500 dark:text-gray-400">
              {{ t('invoice.reports.totalCollected') }}
            </p>
            <p class="text-2xl font-bold text-green-600">
              {{ formatCurrency(summary.total_paid) }}
            </p>
            <p class="text-sm text-gray-500">
              {{ summary.paid_count }} {{ t('invoice.reports.paid') }}
            </p>
          </div>
        </UCard>

        <UCard>
          <div class="text-center">
            <p class="text-sm text-gray-500 dark:text-gray-400">
              {{ t('invoice.reports.pending') }}
            </p>
            <p class="text-2xl font-bold text-amber-600">
              {{ formatCurrency(summary.total_pending) }}
            </p>
          </div>
        </UCard>

        <UCard>
          <div class="text-center">
            <p class="text-sm text-gray-500 dark:text-gray-400">
              {{ t('invoice.reports.overdue') }}
            </p>
            <p
              class="text-2xl font-bold"
              :class="summary.overdue_count > 0 ? 'text-red-600' : 'text-gray-900 dark:text-white'"
            >
              {{ summary.overdue_count }}
            </p>
            <p class="text-sm text-gray-500">
              {{ t('invoice.reports.invoices') }}
            </p>
          </div>
        </UCard>
      </div>

      <!-- Numbering Gaps Alert -->
      <UAlert
        v-if="numberingGaps.length > 0"
        color="warning"
        icon="i-lucide-alert-triangle"
        :title="t('invoice.reports.gapsDetected')"
      >
        <template #description>
          <div class="space-y-1">
            <div
              v-for="gap in numberingGaps"
              :key="`${gap.series_prefix}-${gap.year}`"
              class="text-sm"
            >
              {{ gap.series_prefix }}-{{ gap.year }}:
              {{ t('invoice.reports.missingNumbers') }}
              <span class="font-mono">{{ gap.missing_numbers.join(', ') }}</span>
            </div>
          </div>
        </template>
      </UAlert>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Payment Methods -->
        <UCard>
          <template #header>
            <h3 class="font-semibold text-gray-900 dark:text-white">
              {{ t('invoice.reports.byPaymentMethod') }}
            </h3>
          </template>

          <div
            v-if="paymentMethods.length > 0"
            class="space-y-3"
          >
            <div
              v-for="pm in paymentMethods"
              :key="pm.payment_method"
              class="flex items-center justify-between"
            >
              <div class="flex items-center gap-2">
                <UIcon
                  :name="getPaymentMethodIcon(pm.payment_method)"
                  class="h-5 w-5 text-gray-400"
                />
                <span class="text-gray-700 dark:text-gray-300">
                  {{ getPaymentMethodLabel(pm.payment_method) }}
                </span>
              </div>
              <div class="text-right">
                <p class="font-semibold text-gray-900 dark:text-white">
                  {{ formatCurrency(pm.total_amount) }}
                </p>
                <p class="text-xs text-gray-500">
                  {{ pm.payment_count }} {{ t('invoice.reports.payments') }}
                </p>
              </div>
            </div>
          </div>
          <p
            v-else
            class="text-gray-500 text-center py-4"
          >
            {{ t('invoice.reports.noData') }}
          </p>
        </UCard>

        <!-- VAT Summary -->
        <UCard>
          <template #header>
            <h3 class="font-semibold text-gray-900 dark:text-white">
              {{ t('invoice.reports.vatSummary') }}
            </h3>
          </template>

          <div
            v-if="vatSummary.length > 0"
            class="overflow-x-auto"
          >
            <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead>
                <tr>
                  <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                    {{ t('invoice.reports.vatType') }}
                  </th>
                  <th class="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase">
                    {{ t('invoice.reports.base') }}
                  </th>
                  <th class="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase">
                    {{ t('invoice.reports.tax') }}
                  </th>
                  <th class="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase">
                    {{ t('invoice.total') }}
                  </th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
                <tr
                  v-for="vat in vatSummary"
                  :key="vat.vat_type_id || 'exempt'"
                >
                  <td class="px-3 py-2 text-sm text-gray-700 dark:text-gray-300">
                    {{ vat.vat_name }} ({{ vat.vat_rate }}%)
                  </td>
                  <td class="px-3 py-2 text-sm text-right text-gray-700 dark:text-gray-300">
                    {{ formatCurrency(vat.base_amount) }}
                  </td>
                  <td class="px-3 py-2 text-sm text-right text-gray-700 dark:text-gray-300">
                    {{ formatCurrency(vat.tax_amount) }}
                  </td>
                  <td class="px-3 py-2 text-sm text-right font-medium text-gray-900 dark:text-white">
                    {{ formatCurrency(vat.total_amount) }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <p
            v-else
            class="text-gray-500 text-center py-4"
          >
            {{ t('invoice.reports.noData') }}
          </p>
        </UCard>

        <!-- Billing by Professional -->
        <UCard>
          <template #header>
            <h3 class="font-semibold text-gray-900 dark:text-white">
              {{ t('invoice.reports.byProfessional') }}
            </h3>
          </template>

          <div
            v-if="professionals.length > 0"
            class="space-y-3"
          >
            <div
              v-for="prof in professionals"
              :key="prof.professional_id"
              class="flex items-center justify-between"
            >
              <div class="flex items-center gap-2">
                <UAvatar
                  :alt="prof.professional_name"
                  size="sm"
                />
                <span class="text-gray-700 dark:text-gray-300">
                  {{ prof.professional_name }}
                </span>
              </div>
              <div class="text-right">
                <p class="font-semibold text-gray-900 dark:text-white">
                  {{ formatCurrency(prof.total_invoiced) }}
                </p>
                <p class="text-xs text-gray-500">
                  {{ prof.invoice_count }} {{ t('invoice.reports.invoices') }}
                </p>
              </div>
            </div>
          </div>
          <p
            v-else
            class="text-gray-500 text-center py-4"
          >
            {{ t('invoice.reports.noData') }}
          </p>
        </UCard>

        <!-- Overdue Invoices -->
        <UCard>
          <template #header>
            <div class="flex items-center justify-between">
              <h3 class="font-semibold text-gray-900 dark:text-white">
                {{ t('invoice.reports.overdueInvoices') }}
              </h3>
              <UBadge
                v-if="overdueInvoices.length > 0"
                color="error"
              >
                {{ overdueInvoices.length }}
              </UBadge>
            </div>
          </template>

          <div
            v-if="overdueInvoices.length > 0"
            class="divide-y divide-gray-200 dark:divide-gray-700 max-h-80 overflow-y-auto"
          >
            <div
              v-for="inv in overdueInvoices"
              :key="inv.id"
              class="py-3 hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer"
              @click="goToInvoice(inv.id)"
            >
              <div class="flex justify-between items-start">
                <div>
                  <p class="font-medium text-gray-900 dark:text-white">
                    {{ inv.invoice_number }}
                  </p>
                  <p class="text-sm text-gray-500">
                    {{ inv.patient_name }}
                  </p>
                </div>
                <div class="text-right">
                  <p class="font-semibold text-red-600">
                    {{ formatCurrency(inv.balance_due) }}
                  </p>
                  <p class="text-xs text-red-500">
                    {{ inv.days_overdue }} {{ t('invoice.reports.daysOverdue') }}
                  </p>
                </div>
              </div>
              <p class="text-xs text-gray-400 mt-1">
                {{ t('invoice.dueDate') }}: {{ formatDate(inv.due_date) }}
              </p>
            </div>
          </div>
          <div
            v-else
            class="text-center py-8"
          >
            <UIcon
              name="i-lucide-check-circle"
              class="h-12 w-12 text-green-500 mx-auto mb-2"
            />
            <p class="text-gray-500">
              {{ t('invoice.reports.noOverdue') }}
            </p>
          </div>
        </UCard>
      </div>
    </template>
  </div>
</template>
