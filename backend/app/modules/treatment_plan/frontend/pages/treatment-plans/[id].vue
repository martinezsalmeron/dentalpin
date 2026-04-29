<script setup lang="ts">
import ConfirmPlanModal from '~/components/clinical/modals/ConfirmPlanModal.vue'
import ReopenPlanModal from '~/components/clinical/modals/ReopenPlanModal.vue'
import ClosePlanModal from '~/components/clinical/modals/ClosePlanModal.vue'
import ReactivatePlanModal from '~/components/clinical/modals/ReactivatePlanModal.vue'
import ContactLogModal from '~/components/clinical/modals/ContactLogModal.vue'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const toast = useToast()

const {
  currentPlan,
  loading,
  fetchPlan,
  generateBudget,
  confirmPlan,
  reopenPlan,
  closePlan,
  reactivatePlan,
  logContact,
} = useTreatmentPlans()

const planId = computed(() => route.params.id as string)

onMounted(async () => {
  await fetchPlan(planId.value)
})

watch(planId, async (newId) => {
  if (newId) await fetchPlan(newId)
})

const patientId = computed(() => currentPlan.value?.patient_id || '')

async function handleUpdated() {
  await fetchPlan(planId.value)
}

async function handleGenerateBudget() {
  const result = await generateBudget(planId.value)
  if (result?.budget_id) {
    toast.add({
      title: t('common.success'),
      description: t('treatmentPlans.actions.generateBudget'),
      color: 'success'
    })
    router.push(`/budgets/${result.budget_id}`)
  }
}

function handleSchedule() {
  if (patientId.value) {
    router.push(`/appointments?patient_id=${patientId.value}`)
  }
}

function handleCancelled() {
  if (patientId.value) {
    router.push(`/patients/${patientId.value}?tab=clinical&clinicalMode=plans`)
  } else {
    router.push('/treatment-plans')
  }
}

// ----- Workflow modal state ------------------------------------------------

const showConfirmModal = ref(false)
const showReopenModal = ref(false)
const showCloseModal = ref(false)
const showReactivateModal = ref(false)
const showContactLogModal = ref(false)
const transitioning = ref(false)

const planSummary = computed(() => {
  const plan = currentPlan.value
  if (!plan) return { number: null, count: 0, total: null as number | null }
  const total = plan.items.reduce((acc, item) => {
    const price = item.treatment?.price_snapshot
    return acc + (typeof price === 'number' ? price : Number(price) || 0)
  }, 0)
  return {
    number: plan.plan_number,
    count: plan.items.length,
    total,
  }
})

async function onConfirmPlan() {
  transitioning.value = true
  try {
    const result = await confirmPlan(planId.value)
    if (result) {
      showConfirmModal.value = false
      await handleUpdated()
    }
  } finally {
    transitioning.value = false
  }
}

async function onReopenPlan() {
  transitioning.value = true
  try {
    const result = await reopenPlan(planId.value)
    if (result) {
      showReopenModal.value = false
      await handleUpdated()
    }
  } finally {
    transitioning.value = false
  }
}

async function onClosePlan(payload: { closure_reason: string; closure_note?: string }) {
  transitioning.value = true
  try {
    const result = await closePlan(planId.value, payload)
    if (result) {
      showCloseModal.value = false
      handleCancelled()
    }
  } finally {
    transitioning.value = false
  }
}

async function onReactivatePlan() {
  transitioning.value = true
  try {
    const result = await reactivatePlan(planId.value)
    if (result) {
      showReactivateModal.value = false
      await handleUpdated()
    }
  } finally {
    transitioning.value = false
  }
}

async function onLogContact(payload: { channel: string; note?: string }) {
  transitioning.value = true
  try {
    const ok = await logContact(planId.value, payload)
    if (ok) showContactLogModal.value = false
  } finally {
    transitioning.value = false
  }
}
</script>

<template>
  <div class="space-y-6">
    <!-- Loading state -->
    <div
      v-if="loading && !currentPlan"
      class="space-y-4"
    >
      <USkeleton class="h-12 w-1/3" />
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <USkeleton class="h-96" />
        <USkeleton class="h-96" />
      </div>
    </div>

    <!-- Not found -->
    <UCard
      v-else-if="!currentPlan"
      class="text-center py-12"
    >
      <UIcon
        name="i-lucide-file-x"
        class="w-12 h-12 text-subtle mx-auto mb-4"
      />
      <p class="text-subtle">
        {{ t('common.notFound') }}
      </p>
      <UButton
        class="mt-4"
        to="/treatment-plans"
      >
        {{ t('treatmentPlans.title') }}
      </UButton>
    </UCard>

    <!-- Plan detail using unified component -->
    <PlanDetailView
      v-else
      :plan="currentPlan"
      :patient-id="patientId"
      standalone
      @updated="handleUpdated"
      @generate-budget="handleGenerateBudget"
      @schedule="handleSchedule"
      @cancelled="handleCancelled"
      @request-confirm="showConfirmModal = true"
      @request-reopen="showReopenModal = true"
      @request-close="showCloseModal = true"
      @request-reactivate="showReactivateModal = true"
      @request-contact-log="showContactLogModal = true"
    />

    <!-- Workflow modals -->
    <ConfirmPlanModal
      :open="showConfirmModal"
      :plan-number="planSummary.number"
      :item-count="planSummary.count"
      :total-estimated="planSummary.total"
      :loading="transitioning"
      @update:open="(v) => showConfirmModal = v"
      @confirm="onConfirmPlan"
      @cancel="showConfirmModal = false"
    />
    <ReopenPlanModal
      :open="showReopenModal"
      :loading="transitioning"
      @update:open="(v) => showReopenModal = v"
      @confirm="onReopenPlan"
      @cancel="showReopenModal = false"
    />
    <ClosePlanModal
      :open="showCloseModal"
      :loading="transitioning"
      @update:open="(v) => showCloseModal = v"
      @confirm="onClosePlan"
      @cancel="showCloseModal = false"
    />
    <ReactivatePlanModal
      :open="showReactivateModal"
      :loading="transitioning"
      :closed-at="currentPlan?.closed_at ?? null"
      :previous-reason="currentPlan?.closure_reason ?? null"
      @update:open="(v) => showReactivateModal = v"
      @confirm="onReactivatePlan"
      @cancel="showReactivateModal = false"
    />
    <ContactLogModal
      :open="showContactLogModal"
      :loading="transitioning"
      @update:open="(v) => showContactLogModal = v"
      @confirm="onLogContact"
      @cancel="showContactLogModal = false"
    />
  </div>
</template>
