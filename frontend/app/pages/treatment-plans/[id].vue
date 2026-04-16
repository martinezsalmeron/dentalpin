<script setup lang="ts">
const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const toast = useToast()

const {
  currentPlan,
  loading,
  fetchPlan,
  generateBudget
} = useTreatmentPlans()

const planId = computed(() => route.params.id as string)

// Load plan on mount
onMounted(async () => {
  await fetchPlan(planId.value)
})

// Watch for route changes
watch(planId, async (newId) => {
  if (newId) {
    await fetchPlan(newId)
  }
})

// Computed
const patientId = computed(() => currentPlan.value?.patient_id || '')

// Back navigation
function handleBack() {
  router.push('/treatment-plans')
}

// Refresh plan after changes
async function handleUpdated() {
  await fetchPlan(planId.value)
}

// Handle budget generation with navigation
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
        class="w-12 h-12 text-gray-400 mx-auto mb-4"
      />
      <p class="text-gray-500">
        {{ t('common.notFound') }}
      </p>
      <UButton
        class="mt-4"
        @click="handleBack"
      >
        {{ t('treatmentPlans.title') }}
      </UButton>
    </UCard>

    <!-- Plan detail using unified component -->
    <PlanDetailView
      v-else
      :plan="currentPlan"
      :patient-id="patientId"
      :back-label="t('treatmentPlans.title')"
      standalone
      @back="handleBack"
      @updated="handleUpdated"
      @generate-budget="handleGenerateBudget"
    />
  </div>
</template>
