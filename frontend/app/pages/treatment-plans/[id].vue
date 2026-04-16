<script setup lang="ts">
import type { TreatmentCatalogItem } from '~/types'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const toast = useToast()

const {
  currentPlan,
  loading,
  fetchPlan,
  updatePlanStatus,
  addItem,
  completeItem,
  removeItem,
  generateBudget
} = useTreatmentPlans()

const planId = computed(() => route.params.id as string)
const comesFromPatient = computed(() => route.query.from === 'patient' && route.query.patientId)
const backLabel = computed(() => comesFromPatient.value ? t('actions.back') : t('treatmentPlans.title'))

// Modal states
const showEditModal = ref(false)
const showAddItemModal = ref(false)
const selectedTreatments = ref<TreatmentCatalogItem[]>([])

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

// Actions
async function handleStatusChange(status: string) {
  await updatePlanStatus(planId.value, { status })
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
    // Optionally navigate to budget
    router.push(`/budgets/${result.budget_id}`)
  }
}

async function handleItemComplete(itemId: string) {
  await completeItem(planId.value, itemId, { completed_without_appointment: true })
}

async function handleItemRemove(itemId: string) {
  if (!confirm(t('treatmentPlans.items.remove') + '?')) return
  await removeItem(planId.value, itemId)
}

function handleItemAdd() {
  selectedTreatments.value = []
  showAddItemModal.value = true
}

async function handleAddTreatments() {
  if (selectedTreatments.value.length === 0) return

  const nextOrder = currentPlan.value?.items.length || 0

  for (let i = 0; i < selectedTreatments.value.length; i++) {
    const treatment = selectedTreatments.value[i]
    await addItem(planId.value, {
      catalog_item_id: treatment.id,
      is_global: true,
      sequence_order: nextOrder + i + 1
    })
  }

  showAddItemModal.value = false
  selectedTreatments.value = []
  await fetchPlan(planId.value)

  toast.add({
    title: t('common.success'),
    description: t('treatmentPlans.messages.itemsAdded'),
    color: 'success'
  })
}

function handleEdit() {
  showEditModal.value = true
}

async function handlePlanSaved() {
  showEditModal.value = false
  await fetchPlan(planId.value)
}

function goBack() {
  // If navigated from patient page, return there
  if (route.query.from === 'patient' && route.query.patientId) {
    router.push(`/patients/${route.query.patientId}`)
  } else {
    router.push('/treatment-plans')
  }
}
</script>

<template>
  <div class="space-y-6">
    <!-- Back button -->
    <div>
      <UButton
        variant="ghost"
        color="neutral"
        icon="i-lucide-arrow-left"
        @click="goBack"
      >
        {{ backLabel }}
      </UButton>
    </div>

    <!-- Loading state -->
    <div
      v-if="loading && !currentPlan"
      class="space-y-4"
    >
      <USkeleton class="h-12 w-1/3" />
      <USkeleton class="h-32 w-full" />
      <USkeleton class="h-64 w-full" />
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
        @click="goBack"
      >
        {{ backLabel }}
      </UButton>
    </UCard>

    <!-- Plan detail -->
    <TreatmentPlanDetail
      v-else
      :plan="currentPlan"
      @edit="handleEdit"
      @status-change="handleStatusChange"
      @generate-budget="handleGenerateBudget"
      @item-add="handleItemAdd"
      @item-complete="handleItemComplete"
      @item-remove="handleItemRemove"
    />

    <!-- Edit modal -->
    <TreatmentPlanModal
      v-if="currentPlan"
      v-model="showEditModal"
      :plan="currentPlan"
      :patient-id="currentPlan.patient_id"
      @saved="handlePlanSaved"
    />

    <!-- Add treatments modal -->
    <UModal
      v-model:open="showAddItemModal"
      :ui="{ width: 'sm:max-w-2xl', body: 'min-h-[60vh]' }"
    >
      <template #header>
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
          {{ t('treatmentPlans.items.add') }}
        </h3>
      </template>

      <template #body>
        <TreatmentMultiSelector v-model="selectedTreatments" />
      </template>

      <template #footer>
        <div class="flex justify-end gap-2">
          <UButton
            color="neutral"
            variant="ghost"
            @click="showAddItemModal = false"
          >
            {{ t('actions.cancel') }}
          </UButton>
          <UButton
            color="primary"
            :disabled="selectedTreatments.length === 0"
            :loading="loading"
            @click="handleAddTreatments"
          >
            {{ selectedTreatments.length === 0
              ? t('treatmentPlans.items.add')
              : t('treatmentPlans.items.addSelected', { count: selectedTreatments.length }, selectedTreatments.length)
            }}
          </UButton>
        </div>
      </template>
    </UModal>
  </div>
</template>
