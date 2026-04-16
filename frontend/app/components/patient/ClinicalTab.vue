<script setup lang="ts">
import type { TreatmentPlan, TreatmentPlanDetail as TreatmentPlanDetailType } from '~/types'
import { PERMISSIONS } from '~/config/permissions'

const props = defineProps<{
  patientId: string
  readonly?: boolean
}>()

const { t } = useI18n()
const { can } = usePermissions()
const router = useRouter()
const route = useRoute()

// Treatment plans composable
const {
  plans,
  loading: plansLoading,
  fetchPatientPlans,
  fetchPlan,
  updatePlanStatus,
  generateBudget,
  completeItem,
  removeItem
} = useTreatmentPlans()

// Fetch plans on mount
onMounted(() => {
  fetchPatientPlans(props.patientId)
})

// Active plan (first active plan)
const activePlan = computed(() => plans.value.find(p => p.status === 'active') || null)

// Other plans (non-active, non-archived)
const otherPlans = computed(() => plans.value.filter(p => p.status !== 'active' && p.status !== 'archived'))

// Has any plans
const hasPlans = computed(() => plans.value.length > 0)

// Plan detail modal
const showPlanDetail = ref(false)
const selectedPlanDetail = ref<TreatmentPlanDetailType | null>(null)
const loadingPlanDetail = ref(false)

async function handleViewPlan(plan: TreatmentPlan) {
  showPlanDetail.value = true
  loadingPlanDetail.value = true
  selectedPlanDetail.value = null

  const detail = await fetchPlan(plan.id)
  selectedPlanDetail.value = detail
  loadingPlanDetail.value = false
}

async function handleActivatePlan(plan: TreatmentPlan) {
  await updatePlanStatus(plan.id, { status: 'active' })
  await fetchPatientPlans(props.patientId)
}

async function handleGenerateBudget(plan: TreatmentPlan) {
  const result = await generateBudget(plan.id)
  if (result) {
    router.push(`/budgets/${result.budget_id}?from=patient&patientId=${props.patientId}`)
  }
}

function handleScheduleAppointment(plan: TreatmentPlan) {
  router.push(`/appointments?patient_id=${props.patientId}&plan_id=${plan.id}`)
}

// Create/Edit plan modal
const showPlanModal = ref(false)
const editingPlan = ref<TreatmentPlan | null>(null)

function handleEditPlan() {
  if (selectedPlanDetail.value) {
    // Convert TreatmentPlanDetail to TreatmentPlan for modal
    editingPlan.value = selectedPlanDetail.value as TreatmentPlan
    showPlanDetail.value = false
    showPlanModal.value = true
  }
}

function handleCreatePlan() {
  editingPlan.value = null
  showPlanModal.value = true
}

async function handlePlanSaved() {
  showPlanModal.value = false
  editingPlan.value = null
  await fetchPatientPlans(props.patientId)
}

// Detail modal event handlers
async function handleDetailStatusChange(status: string) {
  if (selectedPlanDetail.value) {
    await updatePlanStatus(selectedPlanDetail.value.id, { status })
    // Refresh detail
    const detail = await fetchPlan(selectedPlanDetail.value.id)
    selectedPlanDetail.value = detail
    // Refresh list
    await fetchPatientPlans(props.patientId)
  }
}

async function handleDetailGenerateBudget() {
  if (selectedPlanDetail.value) {
    const result = await generateBudget(selectedPlanDetail.value.id)
    if (result) {
      showPlanDetail.value = false
      router.push(`/budgets/${result.budget_id}?from=patient&patientId=${props.patientId}`)
    }
  }
}

async function handleItemComplete(itemId: string) {
  if (selectedPlanDetail.value) {
    await completeItem(selectedPlanDetail.value.id, itemId)
    // Refresh detail
    const detail = await fetchPlan(selectedPlanDetail.value.id)
    selectedPlanDetail.value = detail
  }
}

async function handleItemRemove(itemId: string) {
  if (selectedPlanDetail.value) {
    await removeItem(selectedPlanDetail.value.id, itemId)
    // Refresh detail
    const detail = await fetchPlan(selectedPlanDetail.value.id)
    selectedPlanDetail.value = detail
  }
}

// Watch for action=createPlan query param (from sidebar widget)
watch(
  () => route.query.action,
  (action) => {
    if (action === 'createPlan' && can(PERMISSIONS.treatmentPlans.write)) {
      handleCreatePlan()
      // Clear query param after opening modal
      router.replace({ query: { ...route.query, action: undefined } })
    }
  },
  { immediate: true }
)
</script>

<template>
  <div class="clinical-tab space-y-6">
    <!-- Odontogram Section -->
    <UCard>
      <template #header>
        <div class="flex items-center justify-between">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
            {{ t('patientDetail.tabs.clinical') }}
          </h3>
        </div>
      </template>

      <OdontogramChart
        :patient-id="patientId"
        :readonly="readonly"
      />
    </UCard>

    <!-- Treatment Plans Section -->
    <UCard v-if="can(PERMISSIONS.treatmentPlans.read)">
      <template #header>
        <div class="flex items-center justify-between">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
            {{ t('treatmentPlans.title') }}
          </h3>
          <UButton
            v-if="can(PERMISSIONS.treatmentPlans.write)"
            size="sm"
            icon="i-lucide-plus"
            @click="handleCreatePlan"
          >
            {{ t('treatmentPlans.new') }}
          </UButton>
        </div>
      </template>

      <!-- Loading state -->
      <div
        v-if="plansLoading"
        class="space-y-4"
      >
        <USkeleton
          v-for="i in 2"
          :key="i"
          class="h-32 w-full"
        />
      </div>

      <!-- Empty state -->
      <div
        v-else-if="!hasPlans"
        class="text-center py-8"
      >
        <UIcon
          name="i-lucide-clipboard-list"
          class="w-12 h-12 text-gray-400 mx-auto mb-4"
        />
        <p class="text-gray-500 dark:text-gray-400 mb-4">
          {{ t('treatmentPlans.noPlans') }}
        </p>
        <p class="text-sm text-gray-400 dark:text-gray-500 mb-4">
          {{ t('treatmentPlans.noPlansHint') }}
        </p>
        <UButton
          v-if="can(PERMISSIONS.treatmentPlans.write)"
          icon="i-lucide-plus"
          @click="handleCreatePlan"
        >
          {{ t('treatmentPlans.createFirst') }}
        </UButton>
      </div>

      <!-- Plans grid -->
      <div
        v-else
        class="space-y-4"
      >
        <!-- Active plan (highlighted) -->
        <div
          v-if="activePlan"
          class="mb-4"
        >
          <h4 class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">
            {{ t('treatmentPlans.activePlan') }}
          </h4>
          <TreatmentPlanMiniCard
            :plan="activePlan"
            :is-active="true"
            @view="handleViewPlan"
            @activate="handleActivatePlan"
            @schedule="handleScheduleAppointment"
            @generate-budget="handleGenerateBudget"
          />
        </div>

        <!-- Other plans -->
        <div v-if="otherPlans.length > 0">
          <h4 class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">
            {{ t('treatmentPlans.otherPlans') }}
          </h4>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <TreatmentPlanMiniCard
              v-for="plan in otherPlans"
              :key="plan.id"
              :plan="plan"
              @view="handleViewPlan"
              @activate="handleActivatePlan"
              @schedule="handleScheduleAppointment"
              @generate-budget="handleGenerateBudget"
            />
          </div>
        </div>
      </div>
    </UCard>

    <!-- Plan Detail Modal -->
    <UModal
      v-model:open="showPlanDetail"
      :ui="{ width: 'max-w-4xl' }"
    >
      <template #header>
        <div class="flex items-center justify-between w-full">
          <h2 class="text-lg font-semibold">
            {{ selectedPlanDetail?.title || selectedPlanDetail?.plan_number || t('treatmentPlans.title') }}
          </h2>
          <UButton
            variant="ghost"
            color="neutral"
            icon="i-lucide-x"
            @click="showPlanDetail = false"
          />
        </div>
      </template>

      <template #body>
        <div
          v-if="loadingPlanDetail"
          class="flex items-center justify-center py-12"
        >
          <UIcon
            name="i-lucide-loader-2"
            class="w-8 h-8 animate-spin text-gray-400"
          />
        </div>
        <TreatmentPlanDetail
          v-else-if="selectedPlanDetail"
          :plan="selectedPlanDetail"
          @edit="handleEditPlan"
          @status-change="handleDetailStatusChange"
          @generate-budget="handleDetailGenerateBudget"
          @item-complete="handleItemComplete"
          @item-remove="handleItemRemove"
        />
      </template>
    </UModal>

    <!-- Create/Edit Plan Modal -->
    <TreatmentPlanModal
      v-model="showPlanModal"
      :patient-id="patientId"
      :plan="editingPlan"
      @saved="handlePlanSaved"
    />
  </div>
</template>
