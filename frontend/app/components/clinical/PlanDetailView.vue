<script setup lang="ts">
/**
 * PlanDetailView - Expanded view of a treatment plan
 *
 * Features:
 * - Odontogram with plan treatments highlighted
 * - Treatment list with hover linking
 * - Actions: activate, generate budget, add treatments
 * - Two-column layout on larger screens
 */

import type { TreatmentPlanDetail } from '~/types'

const props = withDefaults(defineProps<{
  plan: TreatmentPlanDetail
  patientId: string
  readonly?: boolean
  /** Standalone mode: show patient link */
  standalone?: boolean
}>(), {
  standalone: false
})

const emit = defineEmits<{
  'updated': []
  'activate': []
  'generate-budget': []
  'schedule': []
}>()

const { t } = useI18n()

const {
  completeItem,
  removeItem,
  updatePlanStatus,
  loading
} = useTreatmentPlans()

// ============================================================================
// Hover linking state
// ============================================================================

const hoveredToothNumber = ref<number | null>(null)
const hoveredItemId = ref<string | null>(null)

// Items of the hovered tooth
const highlightedItems = computed(() => {
  if (!hoveredToothNumber.value) return []
  return props.plan.items
    .filter(item => item.tooth_number === hoveredToothNumber.value)
    .map(item => item.id)
})

// Teeth of the hovered item
const highlightedTeeth = computed(() => {
  if (!hoveredItemId.value) return []
  const item = props.plan.items.find(i => i.id === hoveredItemId.value)
  return item?.tooth_number ? [item.tooth_number] : []
})

// ============================================================================
// Computed
// ============================================================================

// Pending items count
const pendingCount = computed(() =>
  props.plan.items.filter(i => i.status === 'pending').length
)

// Can create budget: active or completed plan, without active budget
const canGenerateBudget = computed(() => {
  const validStatus = ['active', 'completed'].includes(props.plan.status)
  const noActiveBudget = !props.plan.budget_id || props.plan.budget?.status === 'cancelled'
  return validStatus && noActiveBudget
})

// ============================================================================
// Actions
// ============================================================================

async function handleCompleteItem(itemId: string) {
  await completeItem(props.plan.id, itemId)
  emit('updated')
}

async function handleRemoveItem(itemId: string) {
  await removeItem(props.plan.id, itemId)
  emit('updated')
}

async function handleActivate() {
  await updatePlanStatus(props.plan.id, { status: 'active' })
  emit('updated')
  emit('activate')
}

function handleGenerateBudget() {
  emit('generate-budget')
}
</script>

<template>
  <div class="space-y-4">
    <!-- Header with actions -->
    <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
      <div>
        <h2 class="text-lg font-semibold">
          {{ plan.title || plan.plan_number }}
        </h2>
        <div class="flex items-center gap-2 mt-0.5">
          <UBadge
            :color="plan.status === 'active' ? 'success' : plan.status === 'draft' ? 'warning' : 'neutral'"
            size="xs"
            variant="subtle"
          >
            {{ t(`treatmentPlans.status.${plan.status}`) }}
          </UBadge>
          <!-- Patient link in standalone mode -->
          <NuxtLink
            v-if="standalone && plan.patient"
            :to="`/patients/${patientId}`"
            class="inline-flex items-center gap-1 text-sm text-primary-600 dark:text-primary-400 hover:underline"
          >
            <UIcon
              name="i-lucide-user"
              class="w-3.5 h-3.5"
            />
            {{ plan.patient.first_name }} {{ plan.patient.last_name }}
          </NuxtLink>
        </div>
      </div>

      <div
        v-if="!readonly"
        class="flex gap-2"
      >
        <UButton
          v-if="plan.status === 'draft' && pendingCount > 0"
          color="primary"
          size="sm"
          :loading="loading"
          @click="handleActivate"
        >
          {{ t('clinical.plans.activate') }}
        </UButton>
        <UButton
          v-if="canGenerateBudget"
          variant="soft"
          size="sm"
          icon="i-lucide-file-plus"
          :loading="loading"
          @click="handleGenerateBudget"
        >
          {{ t('clinical.plans.generateBudget') }}
        </UButton>
        <UButton
          v-if="plan.status === 'active'"
          variant="soft"
          size="sm"
          icon="i-lucide-calendar-plus"
          @click="emit('schedule')"
        >
          {{ t('treatmentPlans.scheduleAppointment') }}
        </UButton>
      </div>
    </div>

    <!-- Two-column layout -->
    <div class="grid grid-cols-1 lg:grid-cols-5 gap-4">
      <!-- Left column: Odontogram (wider) -->
      <UCard class="lg:col-span-3">
        <template #header>
          <div class="flex items-center gap-2">
            <UIcon
              name="i-lucide-scan"
              class="w-5 h-5 text-primary-500"
            />
            <span class="font-medium">{{ t('clinical.plans.odontogram') }}</span>
          </div>
        </template>

        <OdontogramChart
          :patient-id="patientId"
          mode="planning"
          :plan-id="plan.id"
          :highlighted-teeth-prop="highlightedTeeth"
          @tooth-hover="hoveredToothNumber = $event"
        />
      </UCard>

      <!-- Right column: Treatment list (narrower) -->
      <UCard class="lg:col-span-2">
        <template #header>
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <UIcon
                name="i-lucide-list-checks"
                class="w-5 h-5"
              />
              <span class="font-medium">{{ t('clinical.plans.treatments') }}</span>
            </div>
            <UBadge
              v-if="pendingCount > 0"
              color="primary"
              variant="subtle"
            >
              {{ pendingCount }} {{ t('clinical.plans.pending') }}
            </UBadge>
          </div>
        </template>

        <PlanTreatmentList
          :items="plan.items"
          :highlighted-items="highlightedItems"
          :readonly="readonly"
          @item-hover="hoveredItemId = $event"
          @item-complete="handleCompleteItem"
          @item-remove="handleRemoveItem"
        />
      </UCard>
    </div>

    <!-- Treatment bar for adding treatments -->
    <UCard v-if="!readonly && plan.status !== 'completed'">
      <template #header>
        <div class="flex items-center gap-2">
          <UIcon
            name="i-lucide-plus-circle"
            class="w-5 h-5 text-primary-500"
          />
          <span class="font-medium">{{ t('clinical.plans.addTreatment') }}</span>
        </div>
      </template>

      <TreatmentBar
        :patient-id="patientId"
        :selected-plan-id="plan.id"
        mode="planning"
        selected-status="planned"
        @treatment-applied="emit('updated')"
      />
    </UCard>
  </div>
</template>
