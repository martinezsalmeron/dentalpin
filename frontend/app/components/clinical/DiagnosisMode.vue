<script setup lang="ts">
/**
 * DiagnosisMode - Record current patient conditions
 *
 * Features:
 * - Odontogram in diagnosis mode (only diagnostic categories)
 * - List of recorded conditions with hover linking
 * - Contextual CTA to create/continue treatment plan
 */

const props = defineProps<{
  patientId: string
  readonly?: boolean
}>()

const emit = defineEmits<{
  'create-plan': []
  'continue-plan': [planId: string]
}>()

const { t } = useI18n()

// ============================================================================
// Composables
// ============================================================================

const { treatments, fetchTreatments, loading: odontogramLoading } = useOdontogram()
const { plans, fetchPatientPlans, loading: plansLoading } = useTreatmentPlans()

// ============================================================================
// State
// ============================================================================

// Hover linking between odontogram and conditions list
const hoveredTeeth = ref<number[]>([])

// ============================================================================
// Computed
// ============================================================================

// Filter only diagnostic conditions (status = 'existing')
const conditions = computed(() =>
  treatments.value.filter(t => t.status === 'existing')
)

// Draft plans for contextual CTA
const draftPlans = computed(() =>
  plans.value.filter(p => p.status === 'draft')
)

// Combined loading state
const loading = computed(() => odontogramLoading.value || plansLoading.value)

// Collapsible state for conditions block
const conditionsCollapsed = ref(false)

// ============================================================================
// Lifecycle
// ============================================================================

onMounted(async () => {
  await Promise.all([
    fetchTreatments(props.patientId),
    fetchPatientPlans(props.patientId)
  ])
})

// ============================================================================
// Handlers
// ============================================================================

function handleToothHover(toothNumber: number | null) {
  hoveredTeeth.value = toothNumber ? [toothNumber] : []
}

function handleConditionHover(toothNumber: number | null) {
  hoveredTeeth.value = toothNumber ? [toothNumber] : []
}

async function handleTreatmentsChanged() {
  await fetchTreatments(props.patientId)
}
</script>

<template>
  <div class="space-y-4">
    <!-- Loading state -->
    <div
      v-if="loading"
      class="flex items-center justify-center py-8"
    >
      <UIcon
        name="i-lucide-loader-2"
        class="w-8 h-8 animate-spin text-primary-500"
      />
    </div>

    <template v-else>
      <!-- Odontogram with diagnosis mode -->
      <UCard>
        <template #header>
          <div class="flex items-center gap-2">
            <UIcon
              name="i-lucide-stethoscope"
              class="w-5 h-5 text-primary-500"
            />
            <span class="font-medium">{{ t('clinical.diagnosis.registerConditions') }}</span>
          </div>
        </template>

        <OdontogramChart
          :patient-id="patientId"
          mode="diagnosis"
          :highlighted-teeth-prop="hoveredTeeth"
          @tooth-hover="handleToothHover"
          @treatments-changed="handleTreatmentsChanged"
        />
      </UCard>

      <!-- Registered conditions list -->
      <UCard>
        <template #header>
          <button
            type="button"
            class="w-full flex items-center justify-between gap-2 text-left"
            :aria-expanded="!conditionsCollapsed"
            @click="conditionsCollapsed = !conditionsCollapsed"
          >
            <div class="flex items-center gap-2">
              <UIcon
                :name="conditionsCollapsed ? 'i-lucide-chevron-right' : 'i-lucide-chevron-down'"
                class="w-4 h-4 text-gray-500 transition-transform"
              />
              <UIcon
                name="i-lucide-clipboard-list"
                class="w-5 h-5"
              />
              <span class="font-medium">{{ t('clinical.diagnosis.registeredConditions') }}</span>
            </div>
            <UBadge
              v-if="conditions.length > 0"
              color="gray"
              variant="subtle"
            >
              {{ conditions.length }}
            </UBadge>
          </button>
        </template>

        <ConditionsList
          v-if="!conditionsCollapsed"
          :conditions="conditions"
          :highlighted-teeth="hoveredTeeth"
          @tooth-hover="handleConditionHover"
        />
      </UCard>

      <!-- Contextual CTA -->
      <DiagnosisCTA
        v-if="!readonly && conditions.length > 0"
        :draft-plans="draftPlans"
        @create="emit('create-plan')"
        @continue="emit('continue-plan', $event)"
      />
    </template>
  </div>
</template>
