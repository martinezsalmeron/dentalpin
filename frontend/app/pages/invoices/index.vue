<script setup lang="ts">
import type { InvoiceListItem, InvoiceStatus } from '~/types'

const { t, locale } = useI18n()
const router = useRouter()
const toast = useToast()
const { can } = usePermissions()
const {
  invoices,
  total,
  isLoading,
  fetchInvoices,
  deleteInvoice,
  formatCurrency
} = useInvoices()

// Search and filter state
const searchQuery = ref('')
const selectedStatuses = ref<InvoiceStatus[]>([])
const showOverdue = ref(false)
const currentPage = ref(1)
const pageSize = 20

// Debounced search
const debouncedSearch = ref('')
let searchTimeout: ReturnType<typeof setTimeout> | null = null

watch(searchQuery, (val) => {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    debouncedSearch.value = val
    currentPage.value = 1
  }, 300)
})

// Status filter options
const statusOptions = computed(() => [
  { label: t('invoice.status.draft'), value: 'draft' as InvoiceStatus },
  { label: t('invoice.status.issued'), value: 'issued' as InvoiceStatus },
  { label: t('invoice.status.partial'), value: 'partial' as InvoiceStatus },
  { label: t('invoice.status.paid'), value: 'paid' as InvoiceStatus },
  { label: t('invoice.status.cancelled'), value: 'cancelled' as InvoiceStatus },
  { label: t('invoice.status.voided'), value: 'voided' as InvoiceStatus }
])

// Load invoices
async function loadInvoices() {
  await fetchInvoices({
    page: currentPage.value,
    page_size: pageSize,
    search: debouncedSearch.value || undefined,
    status: selectedStatuses.value.length > 0 ? selectedStatuses.value : undefined,
    overdue: showOverdue.value || undefined
  })
}

// Initial load
onMounted(() => {
  loadInvoices()
})

// Reload when filters change
watch([currentPage, debouncedSearch, selectedStatuses, showOverdue], () => {
  loadInvoices()
})

const totalPages = computed(() => Math.ceil(total.value / pageSize))

// Actions
function goToInvoice(invoice: InvoiceListItem) {
  router.push(`/invoices/${invoice.id}`)
}

function createInvoice() {
  router.push('/invoices/new')
}

async function handleDelete(invoice: InvoiceListItem, event: Event) {
  event.stopPropagation()
  if (invoice.status !== 'draft') {
    toast.add({
      title: t('common.error'),
      description: t('invoice.errors.canOnlyDeleteDraft'),
      color: 'error'
    })
    return
  }
  if (!confirm(t('invoice.confirmations.delete'))) return

  try {
    await deleteInvoice(invoice.id)
    toast.add({
      title: t('common.success'),
      description: t('invoice.messages.deleted'),
      color: 'success'
    })
  } catch {
    toast.add({
      title: t('common.error'),
      description: t('invoice.errors.delete'),
      color: 'error'
    })
  }
}

// Format date
function formatDate(dateStr: string | undefined): string {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString(locale.value)
}

// Get patient name
function getPatientName(invoice: InvoiceListItem): string {
  if (!invoice.patient) return '-'
  return `${invoice.patient.last_name}, ${invoice.patient.first_name}`
}

// Check if overdue
function isOverdue(invoice: InvoiceListItem): boolean {
  if (!invoice.due_date) return false
  if (!['issued', 'partial'].includes(invoice.status)) return false
  return new Date(invoice.due_date) < new Date()
}

// Get status badge color
function getStatusBadgeColor(status: InvoiceStatus): string {
  const colors: Record<InvoiceStatus, string> = {
    draft: 'gray',
    issued: 'blue',
    partial: 'amber',
    paid: 'green',
    cancelled: 'red',
    voided: 'neutral'
  }
  return colors[status] || 'gray'
}
</script>

<template>
  <div class="space-y-6">
    <!-- Page header -->
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
        {{ t('invoice.title') }}
      </h1>
      <UButton
        v-if="can('billing.write')"
        icon="i-lucide-plus"
        @click="createInvoice"
      >
        {{ t('invoice.new') }}
      </UButton>
    </div>

    <!-- Filters -->
    <div class="flex flex-wrap gap-4">
      <UInput
        v-model="searchQuery"
        :placeholder="t('invoice.searchPlaceholder')"
        icon="i-lucide-search"
        class="max-w-sm"
      />

      <USelectMenu
        v-model="selectedStatuses"
        :items="statusOptions"
        multiple
        :placeholder="t('invoice.filters.allStatuses')"
        class="w-64"
      />

      <UCheckbox
        v-model="showOverdue"
        :label="t('invoice.filters.overdueOnly')"
      />
    </div>

    <!-- Invoice list -->
    <UCard>
      <!-- Loading state -->
      <div
        v-if="isLoading"
        class="space-y-3"
      >
        <USkeleton
          v-for="i in 5"
          :key="i"
          class="h-16 w-full"
        />
      </div>

      <!-- Empty state -->
      <div
        v-else-if="invoices.length === 0"
        class="text-center py-12"
      >
        <UIcon
          name="i-lucide-receipt"
          class="w-12 h-12 text-gray-400 mx-auto mb-4"
        />
        <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">
          {{ debouncedSearch || selectedStatuses.length > 0 || showOverdue ? t('invoice.noItems') : t('invoice.empty') }}
        </h3>
        <UButton
          v-if="!debouncedSearch && selectedStatuses.length === 0 && !showOverdue && can('billing.write')"
          icon="i-lucide-plus"
          @click="createInvoice"
        >
          {{ t('invoice.emptyAction') }}
        </UButton>
      </div>

      <!-- Invoice table -->
      <div
        v-else
        class="divide-y divide-gray-200 dark:divide-gray-800"
      >
        <div
          v-for="invoice in invoices"
          :key="invoice.id"
          class="flex items-center py-4 px-2 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors rounded-lg -mx-2"
          @click="goToInvoice(invoice)"
        >
          <!-- Invoice info -->
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-3">
              <span class="font-medium text-gray-900 dark:text-white">
                {{ invoice.invoice_number }}
              </span>
              <UBadge
                :color="getStatusBadgeColor(invoice.status)"
                variant="subtle"
                size="xs"
              >
                {{ t(`invoice.status.${invoice.status}`) }}
              </UBadge>
              <UBadge
                v-if="isOverdue(invoice)"
                color="red"
                variant="solid"
                size="xs"
              >
                {{ t('invoice.overdue') }}
              </UBadge>
            </div>
            <div class="text-sm text-gray-500 dark:text-gray-400 mt-1">
              {{ getPatientName(invoice) }}
            </div>
          </div>

          <!-- Issue date -->
          <div class="hidden sm:block text-sm text-gray-500 dark:text-gray-400 w-28 text-right">
            {{ formatDate(invoice.issue_date) }}
          </div>

          <!-- Due date -->
          <div
            class="hidden md:block text-sm w-28 text-right"
            :class="isOverdue(invoice) ? 'text-red-600 font-medium' : 'text-gray-500 dark:text-gray-400'"
          >
            {{ formatDate(invoice.due_date) }}
          </div>

          <!-- Total / Balance -->
          <div class="text-right w-32">
            <div class="font-semibold text-gray-900 dark:text-white">
              {{ formatCurrency(invoice.total, invoice.currency) }}
            </div>
            <div
              v-if="invoice.balance_due > 0 && invoice.status !== 'draft'"
              class="text-xs text-amber-600"
            >
              {{ t('invoice.balance') }}: {{ formatCurrency(invoice.balance_due, invoice.currency) }}
            </div>
          </div>

          <!-- Actions -->
          <div class="flex items-center gap-2 ml-4">
            <UButton
              v-if="invoice.status === 'draft' && can('billing.admin')"
              variant="ghost"
              color="error"
              icon="i-lucide-trash-2"
              size="sm"
              :title="t('invoice.delete')"
              @click="handleDelete(invoice, $event)"
            />
            <UIcon
              name="i-lucide-chevron-right"
              class="w-5 h-5 text-gray-400"
            />
          </div>
        </div>
      </div>

      <!-- Pagination -->
      <div
        v-if="totalPages > 1"
        class="flex items-center justify-between pt-4 border-t border-gray-200 dark:border-gray-800"
      >
        <span class="text-sm text-gray-500 dark:text-gray-400">
          {{ t('common.page', { current: currentPage, total: totalPages }) }}
        </span>
        <div class="flex gap-2">
          <UButton
            variant="outline"
            color="neutral"
            size="sm"
            :disabled="currentPage <= 1"
            @click="currentPage--"
          >
            {{ t('common.previous') }}
          </UButton>
          <UButton
            variant="outline"
            color="neutral"
            size="sm"
            :disabled="currentPage >= totalPages"
            @click="currentPage++"
          >
            {{ t('common.next') }}
          </UButton>
        </div>
      </div>
    </UCard>
  </div>
</template>
