<script setup lang="ts">
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

// Section collapse states
const budgetsExpanded = ref(true)
const billingExpanded = ref(true)
</script>

<template>
  <div class="administration-tab space-y-6">
    <!-- Budgets Section -->
    <UCard v-if="can(PERMISSIONS.budget.read)">
      <template #header>
        <button
          type="button"
          class="flex items-center justify-between w-full"
          @click="budgetsExpanded = !budgetsExpanded"
        >
          <div class="flex items-center gap-2">
            <UIcon
              name="i-lucide-file-text"
              class="w-5 h-5 text-gray-500"
            />
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
              {{ t('patientDetail.tabs.budgets') }}
            </h3>
            <UBadge
              v-if="budgets.length > 0"
              color="neutral"
              size="xs"
              variant="subtle"
            >
              {{ budgets.length }}
            </UBadge>
          </div>
          <div class="flex items-center gap-2">
            <UButton
              v-if="can(PERMISSIONS.budget.write)"
              size="xs"
              icon="i-lucide-plus"
              variant="soft"
              :to="`/budgets/new?patient_id=${patientId}&from=patient`"
              @click.stop
            >
              {{ t('patientDetail.createBudget') }}
            </UButton>
            <UIcon
              :name="budgetsExpanded ? 'i-lucide-chevron-up' : 'i-lucide-chevron-down'"
              class="w-5 h-5 text-gray-400"
            />
          </div>
        </button>
      </template>

      <Transition
        enter-active-class="transition-all duration-200 ease-out"
        enter-from-class="opacity-0 max-h-0"
        enter-to-class="opacity-100"
        leave-active-class="transition-all duration-200 ease-in"
        leave-from-class="opacity-100"
        leave-to-class="opacity-0 max-h-0"
      >
        <div v-show="budgetsExpanded">
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
          <div
            v-else-if="budgets.length === 0"
            class="text-center py-8"
          >
            <UIcon
              name="i-lucide-file-text"
              class="w-10 h-10 text-gray-400 mx-auto mb-3"
            />
            <p class="text-gray-500 dark:text-gray-400 mb-4">
              {{ t('patientDetail.noBudgets') }}
            </p>
            <UButton
              v-if="can(PERMISSIONS.budget.write)"
              :to="`/budgets/new?patient_id=${patientId}&from=patient`"
              icon="i-lucide-plus"
              size="sm"
            >
              {{ t('patientDetail.createBudget') }}
            </UButton>
          </div>

          <!-- Budget list -->
          <ul
            v-else
            class="divide-y divide-gray-200 dark:divide-gray-800"
          >
            <li
              v-for="budget in budgets"
              :key="budget.id"
              class="py-3"
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
          <div
            v-if="budgets.length > 0"
            class="pt-3 border-t border-gray-200 dark:border-gray-700 mt-3"
          >
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
        </div>
      </Transition>
    </UCard>

    <!-- Billing Section -->
    <UCard v-if="can(PERMISSIONS.billing.read)">
      <template #header>
        <button
          type="button"
          class="flex items-center justify-between w-full"
          @click="billingExpanded = !billingExpanded"
        >
          <div class="flex items-center gap-2">
            <UIcon
              name="i-lucide-receipt"
              class="w-5 h-5 text-gray-500"
            />
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
              {{ t('patientDetail.tabs.billing') }}
            </h3>
          </div>
          <UIcon
            :name="billingExpanded ? 'i-lucide-chevron-up' : 'i-lucide-chevron-down'"
            class="w-5 h-5 text-gray-400"
          />
        </button>
      </template>

      <Transition
        enter-active-class="transition-all duration-200 ease-out"
        enter-from-class="opacity-0 max-h-0"
        enter-to-class="opacity-100"
        leave-active-class="transition-all duration-200 ease-in"
        leave-from-class="opacity-100"
        leave-to-class="opacity-0 max-h-0"
      >
        <div v-show="billingExpanded">
          <PatientBillingSummary :patient-id="patientId" />
        </div>
      </Transition>
    </UCard>
  </div>
</template>
