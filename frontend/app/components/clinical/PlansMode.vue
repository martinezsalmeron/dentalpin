<script setup lang="ts">
/**
 * PlansMode - Manage treatment plans for a patient
 *
 * Features:
 * - List view of all plans (grouped by status)
 * - Detail view of single plan with odontogram
 * - Create new plan modal
 * - Transitions from diagnosis mode (initialPlanId)
 */

import type { TreatmentPlan, TreatmentPlanDetail } from '~/types'

const props = defineProps<{
  patientId: string
  initialPlanId?: string | null
  readonly?: boolean
}>()

const emit = defineEmits<{
  'plan-activated': [plan: TreatmentPlan]
  'budget-generated': [planId: string]
  'view-change': [view: 'list' | 'detail']
}>()

const router = useRouter()

// ============================================================================
// Composables
// ============================================================================

const {
  plans,
  loading,
  fetchPatientPlans,
  fetchPlan,
  updatePlanStatus,
  generateBudget
} = useTreatmentPlans()

// ============================================================================
// State
// ============================================================================

// Current view: 'list' or 'detail'
const view = ref<'list' | 'detail'>('list')
const selectedPlan = ref<TreatmentPlanDetail | null>(null)
const showCreateModal = ref(false)

// Emit view changes to parent
watch(view, (newView) => {
  emit('view-change', newView)
}, { immediate: true })

// ============================================================================
// Methods
// ============================================================================

async function openPlanDetail(planId: string) {
  const plan = await fetchPlan(planId)
  if (plan) {
    selectedPlan.value = plan
    view.value = 'detail'
  }
}

function backToList() {
  view.value = 'list'
  selectedPlan.value = null
  // Refresh list after changes
  fetchPatientPlans(props.patientId)
}

async function handleActivatePlan(plan: TreatmentPlan) {
  const updated = await updatePlanStatus(plan.id, { status: 'active' })
  if (updated) {
    emit('plan-activated', updated)
    fetchPatientPlans(props.patientId)
  }
}

async function handleGenerateBudget(plan: TreatmentPlan) {
  const result = await generateBudget(plan.id)
  if (result) {
    emit('budget-generated', plan.id)
    // Navigate to budget
    router.push(`/budgets/${result.budget_id}`)
  }
}

function handlePlanCreated(plan: TreatmentPlan) {
  showCreateModal.value = false
  // Open the newly created plan
  openPlanDetail(plan.id)
}

async function handlePlanUpdated() {
  // Refresh the detail view with updated data
  if (selectedPlan.value) {
    const updated = await fetchPlan(selectedPlan.value.id)
    if (updated) {
      selectedPlan.value = updated
    }
  }
}

// ============================================================================
// Lifecycle
// ============================================================================

onMounted(async () => {
  await fetchPatientPlans(props.patientId)

  // If initialPlanId provided, open that plan directly
  if (props.initialPlanId) {
    openPlanDetail(props.initialPlanId)
  }
})

// Watch for initialPlanId changes (e.g., from diagnosis mode)
watch(() => props.initialPlanId, (newId) => {
  if (newId) {
    openPlanDetail(newId)
  }
})
</script>

<template>
  <div>
    <!-- List View -->
    <PlansListView
      v-if="view === 'list'"
      :plans="plans"
      :patient-id="patientId"
      :loading="loading"
      @view-plan="openPlanDetail"
      @create-plan="showCreateModal = true"
      @activate-plan="handleActivatePlan"
      @generate-budget="handleGenerateBudget"
    />

    <!-- Detail View -->
    <PlanDetailView
      v-else-if="selectedPlan"
      :plan="selectedPlan"
      :patient-id="patientId"
      :readonly="readonly"
      @back="backToList"
      @updated="handlePlanUpdated"
      @activate="fetchPatientPlans(patientId)"
      @generate-budget="fetchPatientPlans(patientId)"
    />

    <!-- Create Plan Modal -->
    <TreatmentPlanModal
      v-model="showCreateModal"
      :patient-id="patientId"
      @saved="handlePlanCreated"
    />
  </div>
</template>
