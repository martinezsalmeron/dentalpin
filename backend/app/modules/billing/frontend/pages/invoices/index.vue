<script setup lang="ts">
import type { InvoiceListItem, InvoiceStatus } from '~~/app/types'
import { roleToUiColor, type SemanticRole } from '~~/app/config/severity'

// Invoice status → semantic role (local mapping; `voided` is invoice-specific)
const INVOICE_STATUS_ROLE: Record<InvoiceStatus, SemanticRole> = {
  draft: 'neutral',
  issued: 'info',
  partial: 'warning',
  paid: 'success',
  cancelled: 'danger',
  voided: 'neutral'
}

function getStatusBadgeColor(status: InvoiceStatus) {
  return roleToUiColor(INVOICE_STATUS_ROLE[status] || 'neutral')
}

const { t, locale } = useI18n()
const router = useRouter()
const toast = useToast()
const { can } = usePermissions()
const { currentClinic } = useClinic()
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
// Generic compliance severity filter — owned and rendered by the
// active compliance module via the ``invoice.list.toolbar.filters``
// slot. Billing only knows about the param shape.
const complianceSeverity = ref<string[]>([])
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
    overdue: showOverdue.value || undefined,
    compliance_severity: complianceSeverity.value.length > 0 ? complianceSeverity.value : undefined
  })
}

// Initial load
onMounted(() => {
  loadInvoices()
})

// Reload when filters change
watch([currentPage, debouncedSearch, selectedStatuses, showOverdue, complianceSeverity], () => {
  loadInvoices()
})

function applyComplianceSeverity(next: string[]) {
  complianceSeverity.value = next
  currentPage.value = 1
}

const totalPages = computed(() => Math.ceil(total.value / pageSize))

// Actions
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
</script>

<template>
  <div>
    <PageHeader :title="t('invoice.title')">
      <template #actions>
        <UButton
          v-if="can('billing.write')"
          color="primary"
          variant="solid"
          icon="i-lucide-plus"
          @click="createInvoice"
        >
          {{ t('invoice.new') }}
        </UButton>
      </template>
    </PageHeader>

    <!-- Filters -->
    <div class="flex flex-wrap items-center gap-[var(--density-gap,0.75rem)] mb-[var(--density-gap,1rem)]">
      <UInput
        v-model="searchQuery"
        :placeholder="t('invoice.searchPlaceholder')"
        icon="i-lucide-search"
        class="max-w-sm"
      />
      <USelectMenu
        v-model="selectedStatuses"
        :items="statusOptions"
        value-key="value"
        multiple
        :placeholder="t('invoice.filters.allStatuses')"
        class="w-64"
      />
      <UCheckbox
        v-model="showOverdue"
        :label="t('invoice.filters.overdueOnly')"
      />
      <!--
        Compliance modules (verifactu-ES, factur-x-FR…) inject extra
        toolbar filters here. Billing knows nothing about them — it
        just owns the ``compliance_severity`` query param shape.
      -->
      <ModuleSlot
        name="invoice.list.toolbar.filters"
        :ctx="{ severity: complianceSeverity, onChange: applyComplianceSeverity, clinic: currentClinic }"
      />
    </div>

    <UCard>
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

      <EmptyState
        v-else-if="invoices.length === 0"
        icon="i-lucide-receipt"
        :title="debouncedSearch || selectedStatuses.length > 0 || showOverdue ? t('invoice.noItems') : t('invoice.empty')"
      >
        <template
          v-if="!debouncedSearch && selectedStatuses.length === 0 && !showOverdue && can('billing.write')"
          #actions
        >
          <UButton
            color="primary"
            variant="solid"
            icon="i-lucide-plus"
            @click="createInvoice"
          >
            {{ t('invoice.emptyAction') }}
          </UButton>
        </template>
      </EmptyState>

      <div
        v-else
        class="divide-y divide-[var(--color-border-subtle)]"
      >
        <ListRow
          v-for="invoice in invoices"
          :key="invoice.id"
          :to="`/invoices/${invoice.id}`"
        >
          <template #title>
            <span class="tnum">{{ invoice.invoice_number || t('invoice.draftNoNumber') }}</span>
            <UBadge
              :color="getStatusBadgeColor(invoice.status)"
              variant="subtle"
              size="xs"
            >
              {{ t(`invoice.status.${invoice.status}`) }}
            </UBadge>
            <StatusBadge
              v-if="isOverdue(invoice)"
              role="danger"
              :label="t('invoice.overdue')"
              size="xs"
              dot
            />
            <!--
              Compliance badge slot (verifactu, factur-x…). Returns
              nothing when the invoice has no compliance_data for the
              active country — keeps non-ES clinics' rows untouched.
            -->
            <ModuleSlot
              name="invoice.list.row.meta"
              :ctx="{ invoice, clinic: currentClinic }"
            />
          </template>
          <template #subtitle>
            {{ getPatientName(invoice) }}
          </template>
          <template #meta>
            <span class="hidden sm:inline text-caption text-subtle tnum">
              {{ formatDate(invoice.issue_date) }}
            </span>
            <span
              class="hidden md:inline text-caption tnum"
              :class="isOverdue(invoice) ? 'text-danger font-medium' : 'text-subtle'"
            >
              {{ formatDate(invoice.due_date) }}
            </span>
            <div class="text-right">
              <Money
                :value="invoice.total"
                strong
              />
              <div
                v-if="invoice.balance_due > 0 && invoice.status !== 'draft'"
                class="text-caption text-warning tnum"
              >
                {{ t('invoice.balance') }}: {{ formatCurrency(invoice.balance_due) }}
              </div>
            </div>
          </template>
          <template
            v-if="invoice.status === 'draft' && can('billing.admin')"
            #actions
          >
            <UButton
              variant="ghost"
              color="error"
              icon="i-lucide-trash-2"
              size="xs"
              :aria-label="t('invoice.delete')"
              :title="t('invoice.delete')"
              @click="handleDelete(invoice, $event)"
            />
          </template>
        </ListRow>
      </div>

      <div
        v-if="totalPages > 1"
        class="flex items-center justify-between pt-4 mt-4 border-t border-subtle"
      >
        <span class="text-caption text-subtle tnum">
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
