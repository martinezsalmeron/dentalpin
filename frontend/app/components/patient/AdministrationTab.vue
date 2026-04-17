<script setup lang="ts">
/**
 * AdministrationTab - Main administration tab with two modes
 *
 * Modes:
 * - budgets: View and manage patient budgets
 * - billing: View invoices and billing summary
 */

import type { AdministrationMode } from './AdministrationModeToggle.vue'
import type { BudgetListItem } from '~/types'
import { PERMISSIONS } from '~/config/permissions'

interface Props {
  patientId: string
  budgets: BudgetListItem[]
  budgetsLoading?: boolean
}

defineProps<Props>()
const { t, locale } = useI18n()
const { can } = usePermissions()
const router = useRouter()
const route = useRoute()

// Current mode (default to budgets)
const currentMode = ref<AdministrationMode>('budgets')

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

// Format currency
function formatCurrency(amount: number, currency: string = 'EUR'): string {
  return new Intl.NumberFormat(locale.value, {
    style: 'currency',
    currency
  }).format(amount)
}
</script>

<template>
  <div class="administration-tab space-y-4">
    <!-- Mode Toggle -->
    <AdministrationModeToggle v-model="currentMode" />

    <!-- Budgets Mode -->
    <div v-if="currentMode === 'budgets' && can(PERMISSIONS.budget.read)">
      <!-- Header with create button -->
      <div class="flex items-center justify-between mb-4">
        <h3 class="font-medium flex items-center gap-2">
          <UIcon
            name="i-lucide-file-text"
            class="w-5 h-5"
          />
          {{ t('patientDetail.tabs.budgets') }}
          <UBadge
            v-if="budgets.length > 0"
            color="neutral"
            size="xs"
            variant="subtle"
          >
            {{ budgets.length }}
          </UBadge>
        </h3>
        <UButton
          v-if="can(PERMISSIONS.budget.write)"
          size="sm"
          icon="i-lucide-plus"
          color="primary"
          :to="`/budgets/new?patient_id=${patientId}&from=patient`"
        >
          {{ t('patientDetail.createBudget') }}
        </UButton>
      </div>

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
          class="w-12 h-12 text-gray-400 mx-auto mb-3"
        />
        <p class="text-gray-500 dark:text-gray-400 mb-4">
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
        <ul class="divide-y divide-gray-200 dark:divide-gray-800">
          <li
            v-for="budget in budgets"
            :key="budget.id"
            class="py-3 first:pt-0 last:pb-0"
          >
            <NuxtLink
              :to="`/budgets/${budget.id}?from=patient&patientId=${patientId}`"
              class="flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-800 -mx-4 px-4 py-2 rounded-lg transition-colors"
            >
              <div>
                <div class="flex items-center gap-3">
                  <span class="font-medium text-gray-900 dark:text-white">
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
                  <span class="text-sm text-gray-500 dark:text-gray-400">
                    {{ formatDate(budget.created_at) }}
                  </span>
                  <span
                    v-if="budget.treatment_plan_id"
                    class="text-xs text-gray-400 flex items-center gap-1"
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
                <span class="font-semibold text-gray-900 dark:text-white">
                  {{ formatCurrency(budget.total, budget.currency) }}
                </span>
                <UIcon
                  name="i-lucide-chevron-right"
                  class="w-5 h-5 text-gray-400"
                />
              </div>
            </NuxtLink>
          </li>
        </ul>

        <!-- View all link -->
        <div class="pt-3 border-t border-gray-200 dark:border-gray-700 mt-3">
          <NuxtLink
            :to="`/budgets?patient_id=${patientId}`"
            class="text-sm text-primary-500 hover:text-primary-600 font-medium inline-flex items-center gap-1"
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
