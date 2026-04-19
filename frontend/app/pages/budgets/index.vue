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

// Status filter options (simplified)
const statusOptions = computed(() => [
  { label: t('budget.status.draft'), value: 'draft' as BudgetStatus },
  { label: t('budget.status.accepted'), value: 'accepted' as BudgetStatus },
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
  <div>
    <PageHeader :title="t('budget.title')">
      <template #actions>
        <UButton
          v-if="can('budget.write')"
          color="primary"
          variant="solid"
          icon="i-lucide-plus"
          @click="createBudget"
        >
          {{ t('budget.new') }}
        </UButton>
      </template>
    </PageHeader>

    <!-- Filters -->
    <div class="flex flex-wrap gap-3 mb-4">
      <UInput
        v-model="searchQuery"
        :placeholder="t('budget.searchPlaceholder')"
        icon="i-lucide-search"
        class="max-w-sm"
      />
      <USelectMenu
        v-model="selectedStatuses"
        :items="statusOptions"
        value-key="value"
        multiple
        :placeholder="t('budget.filters.allStatuses')"
        class="w-64"
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
        v-else-if="budgets.length === 0"
        icon="i-lucide-file-text"
        :title="debouncedSearch || selectedStatuses.length > 0 ? t('budget.noItems') : t('budget.empty')"
      >
        <template
          v-if="!debouncedSearch && selectedStatuses.length === 0 && can('budget.write')"
          #actions
        >
          <UButton
            color="primary"
            variant="solid"
            icon="i-lucide-plus"
            @click="createBudget"
          >
            {{ t('budget.emptyAction') }}
          </UButton>
        </template>
      </EmptyState>

      <div
        v-else
        class="divide-y divide-[var(--color-border-subtle)]"
      >
        <div
          v-for="budget in budgets"
          :key="budget.id"
          class="flex items-center gap-3 py-3 px-2 -mx-2 cursor-pointer hover:bg-surface-muted rounded-token-md transition-colors"
          @click="goToBudget(budget)"
        >
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-3">
              <span class="text-ui text-default tnum">
                {{ budget.budget_number }}
              </span>
              <span class="text-caption text-subtle tnum">
                v{{ budget.version }}
              </span>
              <BudgetStatusBadge :status="budget.status" />
            </div>
            <div class="text-caption text-muted mt-1 truncate">
              {{ getPatientName(budget) }}
            </div>
          </div>

          <div class="hidden sm:block text-caption text-subtle tnum w-32 text-right">
            {{ formatDate(budget.created_at) }}
          </div>

          <div class="w-28 text-right">
            <Money
              :value="budget.total"
              :currency="budget.currency"
              strong
            />
          </div>

          <div class="flex items-center gap-1">
            <UButton
              variant="ghost"
              color="neutral"
              icon="i-lucide-download"
              size="xs"
              :aria-label="t('budget.actions.downloadPdf')"
              :title="t('budget.actions.downloadPdf')"
              @click="handleDownloadPDF(budget, $event)"
            />
            <UButton
              v-if="can('budget.admin')"
              variant="ghost"
              color="error"
              icon="i-lucide-trash-2"
              size="xs"
              :aria-label="t('budget.delete')"
              :title="t('budget.delete')"
              @click="handleDelete(budget, $event)"
            />
            <UIcon
              name="i-lucide-chevron-right"
              class="w-4 h-4 text-subtle"
            />
          </div>
        </div>
      </div>

      <PaginationBar
        v-model:page="currentPage"
        :total-pages="totalPages"
      />
    </UCard>
  </div>
</template>
