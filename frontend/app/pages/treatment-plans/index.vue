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
  <div>
    <PageHeader :title="t('treatmentPlans.title')">
      <template #actions>
        <UButton
          v-if="can('treatment_plan.plans.write')"
          color="primary"
          variant="solid"
          icon="i-lucide-plus"
          @click="createPlan"
        >
          {{ t('treatmentPlans.new') }}
        </UButton>
      </template>
    </PageHeader>

    <div class="flex flex-wrap gap-[var(--density-gap,0.75rem)] mb-[var(--density-gap,1rem)]">
      <UInput
        v-model="searchQuery"
        :placeholder="t('treatmentPlans.searchPlaceholder')"
        icon="i-lucide-search"
        class="max-w-sm"
      />
      <USelectMenu
        v-model="selectedStatuses"
        :items="statusOptions"
        value-key="value"
        multiple
        :placeholder="t('treatmentPlans.filters.allStatuses')"
        class="w-64"
      />
    </div>

    <UCard>
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

      <EmptyState
        v-else-if="plans.length === 0"
        icon="i-lucide-clipboard-list"
        :title="debouncedSearch || selectedStatuses.length > 0 ? t('treatmentPlans.noItems') : t('treatmentPlans.empty')"
      >
        <template
          v-if="!debouncedSearch && selectedStatuses.length === 0 && can('treatment_plan.plans.write')"
          #actions
        >
          <UButton
            color="primary"
            variant="solid"
            icon="i-lucide-plus"
            @click="createPlan"
          >
            {{ t('treatmentPlans.emptyAction') }}
          </UButton>
        </template>
      </EmptyState>

      <div
        v-else
        class="divide-y divide-[var(--color-border-subtle)]"
      >
        <ListRow
          v-for="plan in plans"
          :key="plan.id"
          :to="`/treatment-plans/${plan.id}`"
        >
          <template #title>
            <span class="tnum">{{ plan.plan_number }}</span>
            <TreatmentPlanStatusBadge :status="plan.status" />
            <span class="text-default truncate">
              {{ plan.title || t('treatmentPlans.untitled') }}
            </span>
          </template>
          <template #subtitle>
            {{ getPatientName(plan) }}
          </template>
          <template #meta>
            <span class="hidden sm:inline text-caption text-subtle tnum">
              {{ t('treatmentPlans.itemCount', { count: getItemCount(plan) }, getItemCount(plan)) }}
            </span>
            <span class="hidden sm:inline text-caption text-subtle tnum">
              {{ formatDate(plan.created_at) }}
            </span>
          </template>
          <template
            v-if="can('treatment_plan.plans.write') && plan.status === 'draft'"
            #actions
          >
            <UButton
              variant="ghost"
              color="error"
              icon="i-lucide-trash-2"
              size="xs"
              :aria-label="t('treatmentPlans.delete')"
              :title="t('treatmentPlans.delete')"
              @click="handleDelete(plan, $event)"
            />
          </template>
        </ListRow>
      </div>

      <PaginationBar
        v-model:page="currentPage"
        :total-pages="totalPages"
      />
    </UCard>
  </div>
</template>
