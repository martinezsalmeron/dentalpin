<script setup lang="ts">
import type { TreatmentPlan, TreatmentPlanStatus } from '~/types'

const { t, locale } = useI18n()
const router = useRouter()
const toast = useToast()
const { can } = usePermissions()
const {
  plans,
  total,
  loading,
  fetchPlans,
  deletePlan
} = useTreatmentPlans()

// Search and filter state
const searchQuery = ref('')
const selectedStatuses = ref<TreatmentPlanStatus[]>([])
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
  { label: t('treatmentPlans.status.draft'), value: 'draft' as TreatmentPlanStatus },
  { label: t('treatmentPlans.status.active'), value: 'active' as TreatmentPlanStatus },
  { label: t('treatmentPlans.status.completed'), value: 'completed' as TreatmentPlanStatus },
  { label: t('treatmentPlans.status.archived'), value: 'archived' as TreatmentPlanStatus },
  { label: t('treatmentPlans.status.cancelled'), value: 'cancelled' as TreatmentPlanStatus }
])

// Load plans
async function loadPlans() {
  await fetchPlans({
    page: currentPage.value,
    page_size: pageSize,
    search: debouncedSearch.value || undefined,
    status: selectedStatuses.value.length > 0 ? selectedStatuses.value : undefined
  })
}

// Initial load
onMounted(() => {
  loadPlans()
})

// Reload when filters change
watch([currentPage, debouncedSearch, selectedStatuses], () => {
  loadPlans()
})

const totalPages = computed(() => Math.ceil(total.value / pageSize))

// Actions
function goToPlan(plan: TreatmentPlan) {
  router.push(`/treatment-plans/${plan.id}`)
}

function createPlan() {
  router.push('/treatment-plans/new')
}

async function handleDelete(plan: TreatmentPlan, event: Event) {
  event.stopPropagation()
  if (!confirm(t('treatmentPlans.confirmations.delete'))) return

  try {
    await deletePlan(plan.id)
    toast.add({
      title: t('common.success'),
      description: t('treatmentPlans.messages.deleted'),
      color: 'success'
    })
  } catch {
    toast.add({
      title: t('common.error'),
      description: t('treatmentPlans.errors.delete'),
      color: 'error'
    })
  }
}

// Format date
function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString(locale.value)
}

// Get patient name
function getPatientName(plan: TreatmentPlan): string {
  if (!plan.patient) return '-'
  return `${plan.patient.last_name}, ${plan.patient.first_name}`
}

// Get item count
function getItemCount(plan: TreatmentPlan): number {
  return plan.item_count || 0
}
</script>

<template>
  <div class="space-y-6">
    <!-- Page header -->
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
        {{ t('treatmentPlans.title') }}
      </h1>
      <UButton
        v-if="can('treatment_plan.plans.write')"
        icon="i-lucide-plus"
        @click="createPlan"
      >
        {{ t('treatmentPlans.new') }}
      </UButton>
    </div>

    <!-- Filters -->
    <div class="flex flex-wrap gap-4">
      <UInput
        v-model="searchQuery"
        :placeholder="t('treatmentPlans.searchPlaceholder')"
        icon="i-lucide-search"
        class="max-w-sm"
      />

      <USelectMenu
        v-model="selectedStatuses"
        :items="statusOptions"
        multiple
        :placeholder="t('treatmentPlans.filters.allStatuses')"
        class="w-64"
      />
    </div>

    <!-- Plans list -->
    <UCard>
      <!-- Loading state -->
      <div
        v-if="loading"
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
        v-else-if="plans.length === 0"
        class="text-center py-12"
      >
        <UIcon
          name="i-lucide-clipboard-list"
          class="w-12 h-12 text-gray-400 mx-auto mb-4"
        />
        <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">
          {{ debouncedSearch || selectedStatuses.length > 0 ? t('treatmentPlans.noItems') : t('treatmentPlans.empty') }}
        </h3>
        <UButton
          v-if="!debouncedSearch && selectedStatuses.length === 0 && can('treatment_plan.plans.write')"
          icon="i-lucide-plus"
          @click="createPlan"
        >
          {{ t('treatmentPlans.emptyAction') }}
        </UButton>
      </div>

      <!-- Plans table -->
      <div
        v-else
        class="divide-y divide-gray-200 dark:divide-gray-800"
      >
        <div
          v-for="plan in plans"
          :key="plan.id"
          class="flex items-center py-4 px-2 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors rounded-lg -mx-2"
          @click="goToPlan(plan)"
        >
          <!-- Plan info -->
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-3">
              <span class="font-medium text-gray-900 dark:text-white">
                {{ plan.plan_number }}
              </span>
              <TreatmentPlanStatusBadge :status="plan.status" />
            </div>
            <div class="text-sm text-gray-600 dark:text-gray-300 mt-1">
              {{ plan.title || t('treatmentPlans.untitled') }}
            </div>
            <div class="text-sm text-gray-500 dark:text-gray-400 mt-1">
              {{ getPatientName(plan) }}
            </div>
          </div>

          <!-- Item count -->
          <div class="hidden sm:block text-sm text-gray-500 dark:text-gray-400 w-32 text-center">
            {{ t('treatmentPlans.itemCount', { count: getItemCount(plan) }, getItemCount(plan)) }}
          </div>

          <!-- Date -->
          <div class="hidden sm:block text-sm text-gray-500 dark:text-gray-400 w-28 text-right">
            {{ formatDate(plan.created_at) }}
          </div>

          <!-- Actions -->
          <div class="flex items-center gap-2 ml-4">
            <UButton
              v-if="can('treatment_plan.plans.write') && plan.status === 'draft'"
              variant="ghost"
              color="error"
              icon="i-lucide-trash-2"
              size="sm"
              :title="t('treatmentPlans.delete')"
              @click="handleDelete(plan, $event)"
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
