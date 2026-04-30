<script setup lang="ts">
/**
 * AdministrationTab - Main administration tab with two modes
 *
 * Modes:
 * - budgets: View and manage patient budgets
 * - billing: View invoices and billing summary
 */

import type { AdministrationMode } from './AdministrationModeToggle.vue'
import type { BudgetListItem, PaginatedResponse } from '~~/app/types'
import { PERMISSIONS } from '~~/app/config/permissions'

interface Props {
  patientId: string
}

const props = defineProps<Props>()
const { t, locale } = useI18n()
const { can } = usePermissions()
const api = useApi()
const router = useRouter()
const route = useRoute()

// Current mode (default to budgets)
const currentMode = ref<AdministrationMode>('budgets')

// Budgets list (paginated)
const budgets = ref<BudgetListItem[]>([])
const budgetsTotal = ref(0)
const budgetsLoading = ref(false)
const budgetsPage = ref(1)
const budgetsPageSize = 20
const budgetsTotalPages = computed(() => Math.ceil(budgetsTotal.value / budgetsPageSize))

async function loadBudgets() {
  if (!can(PERMISSIONS.budget.read)) return
  budgetsLoading.value = true
  try {
    const params = new URLSearchParams({
      patient_id: props.patientId,
      page: String(budgetsPage.value),
      page_size: String(budgetsPageSize)
    })
    const response = await api.get<PaginatedResponse<BudgetListItem>>(
      `/api/v1/budget/budgets?${params.toString()}`
    )
    budgets.value = response.data
    budgetsTotal.value = response.total
  } catch {
    budgets.value = []
    budgetsTotal.value = 0
  } finally {
    budgetsLoading.value = false
  }
}

watch(budgetsPage, loadBudgets)
watch(() => props.patientId, () => {
  budgetsPage.value = 1
  loadBudgets()
})

onMounted(loadBudgets)

// Sync mode with URL query param
watch(currentMode, (mode) => {
  router.replace({
    query: {
      ...route.query,
      adminMode: mode
    }
  })
})

// Initialize from URL on mount
onMounted(() => {
  const queryMode = route.query.adminMode as AdministrationMode
  if (queryMode && ['budgets', 'billing', 'documents'].includes(queryMode)) {
    currentMode.value = queryMode
  }
})

// Format date
function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString(locale.value, {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  })
}

// Format currency — clinic-wide via useCurrency.
const { format: formatCurrency } = useCurrency()
</script>

<template>
  <div class="administration-tab space-y-4">
    <!-- Mode Toggle -->
    <AdministrationModeToggle v-model="currentMode" />

    <!-- Budgets Mode -->
    <div v-if="currentMode === 'budgets' && can(PERMISSIONS.budget.read)">
      <SectionHeader
        icon="i-lucide-file-text"
        class="mb-4"
      >
        <span class="truncate">{{ t('patientDetail.tabs.budgets') }}</span>
        <UBadge
          v-if="budgetsTotal > 0"
          color="neutral"
          size="xs"
          variant="subtle"
        >
          {{ budgetsTotal }}
        </UBadge>
        <template
          v-if="can(PERMISSIONS.budget.write)"
          #action
        >
          <UButton
            size="sm"
            icon="i-lucide-plus"
            color="primary"
            :to="`/budgets/new?patient_id=${patientId}&from=patient`"
          >
            {{ t('patientDetail.createBudget') }}
          </UButton>
        </template>
      </SectionHeader>

      <!-- Loading -->
      <div
        v-if="budgetsLoading"
        class="space-y-3"
      >
        <USkeleton
          v-for="i in 3"
          :key="i"
          class="h-12 w-full"
        />
      </div>

      <!-- Empty state -->
      <UCard
        v-else-if="budgets.length === 0"
        class="text-center py-8"
      >
        <UIcon
          name="i-lucide-file-text"
          class="w-12 h-12 text-subtle mx-auto mb-3"
        />
        <p class="text-muted mb-4">
          {{ t('patientDetail.noBudgets') }}
        </p>
        <UButton
          v-if="can(PERMISSIONS.budget.write)"
          :to="`/budgets/new?patient_id=${patientId}&from=patient`"
          icon="i-lucide-plus"
        >
          {{ t('patientDetail.createBudget') }}
        </UButton>
      </UCard>

      <!-- Budget list -->
      <UCard v-else>
        <ul class="divide-y divide-[var(--color-border-subtle)]">
          <li
            v-for="budget in budgets"
            :key="budget.id"
            class="py-3 first:pt-0 last:pb-0"
          >
            <NuxtLink
              :to="`/budgets/${budget.id}?from=patient&patientId=${patientId}`"
              class="flex items-center justify-between hover:bg-surface-muted -mx-4 px-4 py-2 rounded-lg transition-colors"
            >
              <div>
                <div class="flex items-center gap-3">
                  <span class="font-medium text-default">
                    {{ budget.budget_number }}
                  </span>
                  <UBadge
                    color="neutral"
                    size="xs"
                    variant="subtle"
                  >
                    v{{ budget.version }}
                  </UBadge>
                  <BudgetStatusBadge :status="budget.status" />
                </div>
                <div class="flex items-center gap-2 mt-1">
                  <span class="text-sm text-muted">
                    {{ formatDate(budget.created_at) }}
                  </span>
                  <span
                    v-if="budget.treatment_plan_id"
                    class="text-caption text-subtle flex items-center gap-1"
                  >
                    <UIcon
                      name="i-lucide-link"
                      class="w-3 h-3"
                    />
                    {{ t('budget.linkedToPlan') }}
                  </span>
                </div>
              </div>
              <div class="flex items-center gap-4">
                <span class="font-semibold text-default">
                  {{ formatCurrency(budget.total) }}
                </span>
                <UIcon
                  name="i-lucide-chevron-right"
                  class="w-5 h-5 text-subtle"
                />
              </div>
            </NuxtLink>
          </li>
        </ul>

        <PaginationBar
          v-model:page="budgetsPage"
          :total-pages="budgetsTotalPages"
          :total="budgetsTotal"
          :page-size="budgetsPageSize"
        />

        <!-- View all link -->
        <div class="pt-3 border-t border-default mt-3">
          <NuxtLink
            :to="`/budgets?patient_id=${patientId}`"
            class="text-caption text-primary-accent hover:underline inline-flex items-center gap-1"
          >
            {{ t('patientDetail.viewAllBudgets') }}
            <UIcon
              name="i-lucide-arrow-right"
              class="w-4 h-4"
            />
          </NuxtLink>
        </div>
      </UCard>
    </div>

    <!-- Billing Mode -->
    <div v-else-if="currentMode === 'billing' && can(PERMISSIONS.billing.read)">
      <PatientBillingSummary :patient-id="patientId" />
    </div>

    <!-- Documents Mode -->
    <div v-else-if="currentMode === 'documents' && can(PERMISSIONS.documents.read)">
      <DocumentGallery :patient-id="patientId" />
    </div>
  </div>
</template>
