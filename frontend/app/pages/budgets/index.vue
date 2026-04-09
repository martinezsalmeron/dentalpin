<script setup lang="ts">
import type { BudgetListItem, BudgetStatus } from '~/types'

const { t, locale } = useI18n()
const router = useRouter()
const toast = useToast()
const { can } = usePermissions()
const {
  budgets,
  total,
  isLoading,
  fetchBudgets,
  deleteBudget,
  downloadPDF
} = useBudgets()

// Search and filter state
const searchQuery = ref('')
const selectedStatuses = ref<BudgetStatus[]>([])
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
  { label: t('budget.status.draft'), value: 'draft' as BudgetStatus },
  { label: t('budget.status.sent'), value: 'sent' as BudgetStatus },
  { label: t('budget.status.partially_accepted'), value: 'partially_accepted' as BudgetStatus },
  { label: t('budget.status.accepted'), value: 'accepted' as BudgetStatus },
  { label: t('budget.status.in_progress'), value: 'in_progress' as BudgetStatus },
  { label: t('budget.status.completed'), value: 'completed' as BudgetStatus },
  { label: t('budget.status.rejected'), value: 'rejected' as BudgetStatus },
  { label: t('budget.status.expired'), value: 'expired' as BudgetStatus },
  { label: t('budget.status.cancelled'), value: 'cancelled' as BudgetStatus }
])

// Load budgets
async function loadBudgets() {
  await fetchBudgets({
    page: currentPage.value,
    page_size: pageSize,
    search: debouncedSearch.value || undefined,
    status: selectedStatuses.value.length > 0 ? selectedStatuses.value : undefined
  })
}

// Initial load
onMounted(() => {
  loadBudgets()
})

// Reload when filters change
watch([currentPage, debouncedSearch, selectedStatuses], () => {
  loadBudgets()
})

const totalPages = computed(() => Math.ceil(total.value / pageSize))

// Actions
function goToBudget(budget: BudgetListItem) {
  router.push(`/budgets/${budget.id}`)
}

function createBudget() {
  router.push('/budgets/new')
}

async function handleDownloadPDF(budget: BudgetListItem, event: Event) {
  event.stopPropagation()
  try {
    await downloadPDF(budget.id, locale.value)
  } catch {
    toast.add({
      title: t('common.error'),
      description: t('budget.pdf.downloadError'),
      color: 'error'
    })
  }
}

async function handleDelete(budget: BudgetListItem, event: Event) {
  event.stopPropagation()
  if (!confirm(t('budget.confirmations.delete'))) return

  try {
    await deleteBudget(budget.id)
    toast.add({
      title: t('common.success'),
      description: t('budget.messages.deleted'),
      color: 'success'
    })
  } catch {
    toast.add({
      title: t('common.error'),
      description: t('budget.errors.delete'),
      color: 'error'
    })
  }
}

// Format currency
function formatCurrency(amount: number, currency: string): string {
  return new Intl.NumberFormat(locale.value, {
    style: 'currency',
    currency
  }).format(amount)
}

// Format date
function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString(locale.value)
}

// Get patient name
function getPatientName(budget: BudgetListItem): string {
  if (!budget.patient) return '-'
  return `${budget.patient.last_name}, ${budget.patient.first_name}`
}
</script>

<template>
  <div class="space-y-6">
    <!-- Page header -->
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
        {{ t('budget.title') }}
      </h1>
      <UButton
        v-if="can('budget.write')"
        icon="i-lucide-plus"
        @click="createBudget"
      >
        {{ t('budget.new') }}
      </UButton>
    </div>

    <!-- Filters -->
    <div class="flex flex-wrap gap-4">
      <UInput
        v-model="searchQuery"
        :placeholder="t('budget.searchPlaceholder')"
        icon="i-lucide-search"
        class="max-w-sm"
      />

      <USelectMenu
        v-model="selectedStatuses"
        :items="statusOptions"
        multiple
        :placeholder="t('budget.filters.allStatuses')"
        class="w-64"
      />
    </div>

    <!-- Budget list -->
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
        v-else-if="budgets.length === 0"
        class="text-center py-12"
      >
        <UIcon
          name="i-lucide-file-text"
          class="w-12 h-12 text-gray-400 mx-auto mb-4"
        />
        <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">
          {{ debouncedSearch || selectedStatuses.length > 0 ? t('budget.noItems') : t('budget.empty') }}
        </h3>
        <UButton
          v-if="!debouncedSearch && selectedStatuses.length === 0 && can('budget.write')"
          icon="i-lucide-plus"
          @click="createBudget"
        >
          {{ t('budget.emptyAction') }}
        </UButton>
      </div>

      <!-- Budget table -->
      <div
        v-else
        class="divide-y divide-gray-200 dark:divide-gray-800"
      >
        <div
          v-for="budget in budgets"
          :key="budget.id"
          class="flex items-center py-4 px-2 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors rounded-lg -mx-2"
          @click="goToBudget(budget)"
        >
          <!-- Budget info -->
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-3">
              <span class="font-medium text-gray-900 dark:text-white">
                {{ budget.budget_number }}
              </span>
              <span class="text-sm text-gray-500">
                v{{ budget.version }}
              </span>
              <BudgetStatusBadge :status="budget.status" />
            </div>
            <div class="text-sm text-gray-500 dark:text-gray-400 mt-1">
              {{ getPatientName(budget) }}
            </div>
          </div>

          <!-- Dates -->
          <div class="hidden sm:block text-sm text-gray-500 dark:text-gray-400 w-32 text-right">
            {{ formatDate(budget.created_at) }}
          </div>

          <!-- Total -->
          <div class="font-semibold text-gray-900 dark:text-white w-28 text-right">
            {{ formatCurrency(budget.total, budget.currency) }}
          </div>

          <!-- Actions -->
          <div class="flex items-center gap-2 ml-4">
            <UButton
              variant="ghost"
              color="neutral"
              icon="i-lucide-download"
              size="sm"
              :title="t('budget.actions.downloadPdf')"
              @click="handleDownloadPDF(budget, $event)"
            />
            <UButton
              v-if="can('budget.admin')"
              variant="ghost"
              color="error"
              icon="i-lucide-trash-2"
              size="sm"
              :title="t('budget.delete')"
              @click="handleDelete(budget, $event)"
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
