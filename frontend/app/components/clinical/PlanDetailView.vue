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
  'cancelled': []
}>()

const { t } = useI18n()
const toast = useToast()

const {
  completeItem,
  removeItem,
  reorderItems,
  updatePlanStatus,
  unlockPlan,
  fetchPlan,
  loading
} = useTreatmentPlans()

// ============================================================================
// Confirmation modal (draft → active)
// ============================================================================

const showActivateModal = ref(false)

// ============================================================================
// Lock state — a plan with a non-cancelled budget is locked for editing.
// Modifying it would silently invalidate the budget already shown to the
// patient, so mutations go through an explicit unlock flow that cancels the
// budget (preserving traceability).
// ============================================================================

const isLocked = computed(() => {
  if (!props.plan.budget_id) return false
  const status = props.plan.budget?.status
  return status !== 'cancelled'
})

const effectiveReadonly = computed(() => props.readonly || isLocked.value)

const showUnlockModal = ref(false)

function openUnlockModal() {
  showUnlockModal.value = true
}

function cancelUnlock() {
  showUnlockModal.value = false
}

async function confirmUnlock() {
  showUnlockModal.value = false
  const result = await unlockPlan(props.plan.id)
  if (result) {
    // Refresh the plan so UI reflects the cancelled budget and unlocked state.
    await fetchPlan(props.plan.id)
    emit('updated')
  }
}

// ============================================================================
// Cancel plan — terminal transition from draft/active. Locked plans must
// unlock first (explicit two-step: prevents silent budget orphaning).
// ============================================================================

const showCancelModal = ref(false)

const canCancelPlan = computed(() =>
  !props.readonly
  && !isLocked.value
  && (props.plan.status === 'draft' || props.plan.status === 'active')
)

function openCancelModal() {
  showCancelModal.value = true
}

function cancelCancel() {
  showCancelModal.value = false
}

async function confirmCancelPlan() {
  showCancelModal.value = false
  const updated = await updatePlanStatus(props.plan.id, { status: 'cancelled' })
  if (updated) {
    emit('cancelled')
  }
}

// ============================================================================
// Visual feedback: pulse right-column card when first item lands on a draft plan
// ============================================================================

const listPulse = ref(false)
watch(
  () => props.plan.items.length,
  (next, prev) => {
    // Only celebrate the first treatment on a draft plan to keep feedback focused.
    if (prev === 0 && next > 0 && props.plan.status === 'draft') {
      toast.add({
        title: t('clinical.plans.addedToPlan'),
        color: 'success',
        icon: 'i-lucide-check-circle'
      })
      listPulse.value = true
      setTimeout(() => {
        listPulse.value = false
      }, 900)
    }
  }
)

// ============================================================================
// Hover linking state
// ============================================================================

const hoveredToothNumber = ref<number | null>(null)
const hoveredItemId = ref<string | null>(null)
/** Treatment id currently under hover in the globals strip (chart → list). */
const hoveredGlobalTreatmentId = ref<string | null>(null)

function itemTeeth(item: { treatment?: { teeth?: Array<{ tooth_number: number }> } }): number[] {
  return (item.treatment?.teeth ?? []).map(t => t.tooth_number)
}

function itemGlobalTreatmentId(item: { treatment?: { id: string, scope?: string } | null }): string | null {
  const scope = item.treatment?.scope
  if (scope === 'global_mouth' || scope === 'global_arch') {
    return item.treatment?.id ?? null
  }
  return null
}

// Items of the hovered tooth (any of whose members touches that tooth).
const highlightedItems = computed(() => {
  const fromTooth = hoveredToothNumber.value
    ? props.plan.items
        .filter(item => itemTeeth(item).includes(hoveredToothNumber.value!))
        .map(item => item.id)
    : []
  const fromGlobal = hoveredGlobalTreatmentId.value
    ? props.plan.items
        .filter(item => item.treatment?.id === hoveredGlobalTreatmentId.value)
        .map(item => item.id)
    : []
  return [...fromTooth, ...fromGlobal]
})

// Teeth of the hovered item (from Treatment.teeth[]).
const highlightedTeeth = computed(() => {
  if (!hoveredItemId.value) return []
  const item = props.plan.items.find(i => i.id === hoveredItemId.value)
  return item ? itemTeeth(item) : []
})

// Global treatment ids to highlight in the strip when hovering a list item.
const highlightedGlobalIds = computed(() => {
  if (!hoveredItemId.value) return []
  const item = props.plan.items.find(i => i.id === hoveredItemId.value)
  if (!item) return []
  const globalId = itemGlobalTreatmentId(item)
  return globalId ? [globalId] : []
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
// Progress stepper — maps plan status to a 3-step user journey.
// ============================================================================

type StepState = 'current' | 'complete' | 'upcoming'

interface Step {
  key: 'plan' | 'confirm' | 'billing'
  label: string
  icon: string
  state: StepState
}

const steps = computed<Step[]>(() => {
  const status = props.plan.status
  // Completed / archived / cancelled collapse to "all done" for this chart.
  const allDone = status === 'completed'
  const isDraft = status === 'draft'
  const isActive = status === 'active'

  return [
    {
      key: 'plan',
      label: t('clinical.plans.steps.plan'),
      icon: 'i-lucide-clipboard-list',
      state: isDraft ? 'current' : 'complete'
    },
    {
      key: 'confirm',
      label: t('clinical.plans.steps.confirm'),
      icon: 'i-lucide-check-circle-2',
      state: isDraft ? 'upcoming' : (isActive ? 'complete' : (allDone ? 'complete' : 'upcoming'))
    },
    {
      key: 'billing',
      label: t('clinical.plans.steps.billingScheduling'),
      icon: 'i-lucide-file-plus',
      state: isActive ? 'current' : (allDone ? 'complete' : 'upcoming')
    }
  ]
})

const isDraft = computed(() => props.plan.status === 'draft')
const canConfirm = computed(() => isDraft.value && pendingCount.value > 0)

// ============================================================================
// Actions
// ============================================================================

const odontogramRef = ref<{ refetchTreatments: () => Promise<void> } | null>(null)

async function handleCompleteItem(itemId: string) {
  await completeItem(props.plan.id, itemId)
  await odontogramRef.value?.refetchTreatments()
  emit('updated')
}

async function handleRemoveItem(itemId: string) {
  await removeItem(props.plan.id, itemId)
  await odontogramRef.value?.refetchTreatments()
  emit('updated')
}

async function handleReorder(itemIds: string[]) {
  await reorderItems(props.plan.id, itemIds)
  emit('updated')
}

function openActivateModal() {
  showActivateModal.value = true
}

async function confirmActivate() {
  showActivateModal.value = false
  await updatePlanStatus(props.plan.id, { status: 'active' })
  emit('updated')
  emit('activate')
}

function cancelActivate() {
  showActivateModal.value = false
}

function handleGenerateBudget() {
  emit('generate-budget')
}
</script>

<template>
  <div class="space-y-4">
    <!-- Header: title + stepper + actions -->
    <div class="plan-header">
      <div class="plan-header-title">
        <h2 class="text-lg font-semibold">
          {{ plan.title || plan.plan_number }}
        </h2>
        <NuxtLink
          v-if="standalone && plan.patient"
          :to="`/patients/${patientId}`"
          class="inline-flex items-center gap-1 text-sm text-primary-600 dark:text-primary-400 hover:underline mt-0.5"
        >
          <UIcon
            name="i-lucide-user"
            class="w-3.5 h-3.5"
          />
          {{ plan.patient.first_name }} {{ plan.patient.last_name }}
        </NuxtLink>
      </div>

      <!-- Progress stepper -->
      <ol class="plan-stepper">
        <li
          v-for="(step, idx) in steps"
          :key="step.key"
          class="plan-step"
          :class="`plan-step-${step.state}`"
        >
          <span class="plan-step-marker">
            <UIcon
              v-if="step.state === 'complete'"
              name="i-lucide-check"
              class="w-3.5 h-3.5"
            />
            <span v-else>{{ idx + 1 }}</span>
          </span>
          <span class="plan-step-label">{{ step.label }}</span>
          <span
            v-if="idx < steps.length - 1"
            class="plan-step-connector"
          />
        </li>
      </ol>

      <!-- Action buttons: ghost/disabled for draft, live for active/completed. -->
      <div
        v-if="!readonly"
        class="plan-header-actions"
      >
        <UButton
          v-if="isLocked"
          variant="soft"
          size="sm"
          color="warning"
          icon="i-lucide-unlock"
          :loading="loading"
          @click="openUnlockModal"
        >
          {{ t('clinical.plans.modifyPlan') }}
        </UButton>
        <UButton
          v-if="canCancelPlan"
          variant="ghost"
          size="sm"
          color="error"
          icon="i-lucide-ban"
          :loading="loading"
          @click="openCancelModal"
        >
          {{ t('clinical.plans.cancelPlan') }}
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
          v-else-if="isDraft"
          variant="soft"
          size="sm"
          icon="i-lucide-file-plus"
          color="neutral"
          disabled
          :title="t('clinical.plans.ghostHint')"
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
        <UButton
          v-else-if="isDraft"
          variant="soft"
          size="sm"
          icon="i-lucide-calendar-plus"
          color="neutral"
          disabled
          :title="t('clinical.plans.ghostHint')"
        >
          {{ t('treatmentPlans.scheduleAppointment') }}
        </UButton>
      </div>
    </div>

    <!-- Locked banner — shown whenever plan has a live budget attached. -->
    <div
      v-if="isLocked"
      class="plan-locked-banner"
    >
      <UIcon
        name="i-lucide-lock"
        class="w-4 h-4 shrink-0"
      />
      <div class="plan-locked-text">
        <div class="plan-locked-title">
          {{ t('clinical.plans.locked.title') }}
        </div>
        <div class="plan-locked-subtitle">
          {{ t('clinical.plans.locked.subtitle', { number: plan.budget?.budget_number || '' }) }}
        </div>
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
          ref="odontogramRef"
          :patient-id="patientId"
          :mode="effectiveReadonly ? 'view-only' : 'planning'"
          :plan-id="plan.id"
          :plan-title="plan.title || plan.plan_number"
          :highlighted-teeth-prop="highlightedTeeth"
          :highlighted-global-ids="highlightedGlobalIds"
          @tooth-hover="hoveredToothNumber = $event"
          @global-hover="hoveredGlobalTreatmentId = $event"
          @treatments-changed="emit('updated')"
        />
      </UCard>

      <!-- Right column: Treatment list (narrower). Pulses briefly when first item lands. -->
      <UCard
        class="lg:col-span-2 plan-list-card"
        :class="{ 'plan-list-pulse': listPulse }"
      >
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
          :readonly="effectiveReadonly"
          :plan-status="plan.status"
          @item-hover="hoveredItemId = $event"
          @item-complete="handleCompleteItem"
          @item-remove="handleRemoveItem"
          @reorder="handleReorder"
        />

        <!-- Sticky confirm-plan CTA: only in draft, adapts to whether items exist. -->
        <template
          v-if="!readonly && isDraft"
          #footer
        >
          <div class="confirm-cta">
            <div
              v-if="!canConfirm"
              class="confirm-cta-empty"
            >
              <UIcon
                name="i-lucide-info"
                class="w-4 h-4"
              />
              <span>{{ t('clinical.plans.confirmCta.empty') }}</span>
            </div>
            <template v-else>
              <div class="confirm-cta-text">
                <div class="confirm-cta-title">
                  {{ t('clinical.plans.confirmCta.titleWithItems') }}
                </div>
                <div class="confirm-cta-subtitle">
                  {{ t('clinical.plans.confirmCta.subtitleWithItems') }}
                </div>
              </div>
              <UButton
                color="primary"
                size="lg"
                block
                icon="i-lucide-check-circle-2"
                :loading="loading"
                @click="openActivateModal"
              >
                {{ t('treatmentPlans.actions.confirm') }}
              </UButton>
            </template>
          </div>
        </template>
      </UCard>
    </div>

    <!-- Cancel plan confirmation modal -->
    <UModal v-model:open="showCancelModal">
      <template #content>
        <UCard>
          <template #header>
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center">
                <UIcon
                  name="i-lucide-ban"
                  class="w-5 h-5 text-red-600 dark:text-red-400"
                />
              </div>
              <h3 class="font-semibold text-gray-900 dark:text-white">
                {{ t('treatmentPlans.confirmations.cancelTitle') }}
              </h3>
            </div>
          </template>

          <p class="text-sm text-gray-700 dark:text-gray-300">
            {{ t('treatmentPlans.confirmations.cancelDescription') }}
          </p>

          <template #footer>
            <div class="flex justify-end gap-2">
              <UButton
                color="neutral"
                variant="ghost"
                @click="cancelCancel"
              >
                {{ t('actions.cancel') }}
              </UButton>
              <UButton
                color="error"
                icon="i-lucide-ban"
                :loading="loading"
                @click="confirmCancelPlan"
              >
                {{ t('treatmentPlans.actions.cancelPlan') }}
              </UButton>
            </div>
          </template>
        </UCard>
      </template>
    </UModal>

    <!-- Unlock confirmation modal — lists concrete consequences of modifying -->
    <UModal v-model:open="showUnlockModal">
      <template #content>
        <UCard>
          <template #header>
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-full bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center">
                <UIcon
                  name="i-lucide-alert-triangle"
                  class="w-5 h-5 text-amber-600 dark:text-amber-400"
                />
              </div>
              <h3 class="font-semibold text-gray-900 dark:text-white">
                {{ t('treatmentPlans.confirmations.unlockTitle') }}
              </h3>
            </div>
          </template>

          <div class="space-y-3">
            <p class="text-sm text-gray-700 dark:text-gray-300">
              {{ t('treatmentPlans.confirmations.unlockIntro', { number: plan.budget?.budget_number || '' }) }}
            </p>
            <ul class="unlock-consequences">
              <li>
                <UIcon
                  name="i-lucide-x-circle"
                  class="w-4 h-4 text-red-500 shrink-0"
                />
                <span>{{ t('treatmentPlans.confirmations.unlockConsequence1') }}</span>
              </li>
              <li>
                <UIcon
                  name="i-lucide-edit-3"
                  class="w-4 h-4 text-amber-500 shrink-0"
                />
                <span>{{ t('treatmentPlans.confirmations.unlockConsequence2') }}</span>
              </li>
              <li>
                <UIcon
                  name="i-lucide-file-plus"
                  class="w-4 h-4 text-blue-500 shrink-0"
                />
                <span>{{ t('treatmentPlans.confirmations.unlockConsequence3') }}</span>
              </li>
              <li>
                <UIcon
                  name="i-lucide-history"
                  class="w-4 h-4 text-gray-500 shrink-0"
                />
                <span>{{ t('treatmentPlans.confirmations.unlockConsequence4') }}</span>
              </li>
            </ul>
          </div>

          <template #footer>
            <div class="flex justify-end gap-2">
              <UButton
                color="neutral"
                variant="ghost"
                @click="cancelUnlock"
              >
                {{ t('actions.cancel') }}
              </UButton>
              <UButton
                color="warning"
                icon="i-lucide-unlock"
                :loading="loading"
                @click="confirmUnlock"
              >
                {{ t('treatmentPlans.actions.unlockConfirm') }}
              </UButton>
            </div>
          </template>
        </UCard>
      </template>
    </UModal>

    <!-- Activation confirmation modal -->
    <UModal v-model:open="showActivateModal">
      <template #content>
        <UCard>
          <template #header>
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-full bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center">
                <UIcon
                  name="i-lucide-check-circle-2"
                  class="w-5 h-5 text-primary-600 dark:text-primary-400"
                />
              </div>
              <h3 class="font-semibold text-gray-900 dark:text-white">
                {{ t('treatmentPlans.confirmations.activateTitle') }}
              </h3>
            </div>
          </template>

          <p class="text-sm text-gray-600 dark:text-gray-300">
            {{ t('treatmentPlans.confirmations.activateDescription') }}
          </p>

          <template #footer>
            <div class="flex justify-end gap-2">
              <UButton
                color="neutral"
                variant="ghost"
                @click="cancelActivate"
              >
                {{ t('actions.cancel') }}
              </UButton>
              <UButton
                color="primary"
                icon="i-lucide-check-circle-2"
                :loading="loading"
                @click="confirmActivate"
              >
                {{ t('treatmentPlans.actions.confirm') }}
              </UButton>
            </div>
          </template>
        </UCard>
      </template>
    </UModal>
  </div>
</template>

<style scoped>
.plan-header {
  display: grid;
  grid-template-columns: 1fr auto auto;
  align-items: center;
  gap: 16px;
}

@media (max-width: 900px) {
  .plan-header {
    grid-template-columns: 1fr;
  }
}

.plan-header-title {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.plan-header-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

/* Stepper */
.plan-stepper {
  display: flex;
  align-items: center;
  gap: 8px;
  list-style: none;
  padding: 0;
  margin: 0;
}

.plan-step {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #9CA3AF;
  position: relative;
}

.plan-step-marker {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 600;
  border: 1.5px solid currentColor;
  background: transparent;
  flex-shrink: 0;
}

.plan-step-label {
  font-weight: 500;
  white-space: nowrap;
}

.plan-step-connector {
  width: 20px;
  height: 1.5px;
  background: currentColor;
  opacity: 0.4;
}

.plan-step-current {
  color: #2563EB;
}

.plan-step-current .plan-step-marker {
  background: #2563EB;
  color: white;
  border-color: #2563EB;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.2);
}

.plan-step-complete {
  color: #16A34A;
}

.plan-step-complete .plan-step-marker {
  background: #16A34A;
  color: white;
  border-color: #16A34A;
}

.plan-step-upcoming {
  color: #9CA3AF;
}

:root.dark .plan-step-current {
  color: #60A5FA;
}

:root.dark .plan-step-current .plan-step-marker {
  background: #2563EB;
  border-color: #3B82F6;
}

:root.dark .plan-step-complete {
  color: #4ADE80;
}

/* Confirm CTA footer */
.confirm-cta {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.confirm-cta-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.confirm-cta-title {
  font-weight: 600;
  font-size: 14px;
  color: #1E40AF;
}

:root.dark .confirm-cta-title {
  color: #BFDBFE;
}

.confirm-cta-subtitle {
  font-size: 12px;
  color: #475569;
  line-height: 1.35;
}

:root.dark .confirm-cta-subtitle {
  color: #94A3B8;
}

.confirm-cta-empty {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  font-size: 13px;
  color: #64748B;
  background: #F1F5F9;
  border-radius: 8px;
}

:root.dark .confirm-cta-empty {
  background: rgba(100, 116, 139, 0.15);
  color: #CBD5E1;
}

/* First-item pulse on list card */
.plan-list-card {
  transition: box-shadow 0.3s ease;
}

.plan-list-pulse {
  animation: plan-list-pulse 0.9s ease-out;
}

@keyframes plan-list-pulse {
  0%   { box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.55); }
  50%  { box-shadow: 0 0 0 8px rgba(34, 197, 94, 0.18); }
  100% { box-shadow: 0 0 0 0 rgba(34, 197, 94, 0); }
}

/* Locked banner */
.plan-locked-banner {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 14px;
  background: #FEF3C7;
  border: 1px solid #FCD34D;
  border-radius: 8px;
  color: #92400E;
  font-size: 13px;
  line-height: 1.4;
}

:root.dark .plan-locked-banner {
  background: rgba(251, 191, 36, 0.12);
  border-color: rgba(251, 191, 36, 0.35);
  color: #FCD34D;
}

.plan-locked-title {
  font-weight: 600;
}

.plan-locked-subtitle {
  font-size: 12px;
  opacity: 0.85;
}

/* Unlock consequences list */
.unlock-consequences {
  display: flex;
  flex-direction: column;
  gap: 8px;
  list-style: none;
  padding: 10px 12px;
  margin: 0;
  background: #F8FAFC;
  border-radius: 8px;
  border: 1px solid #E2E8F0;
}

:root.dark .unlock-consequences {
  background: rgba(148, 163, 184, 0.08);
  border-color: rgba(148, 163, 184, 0.2);
}

.unlock-consequences li {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 13px;
  line-height: 1.4;
  color: #334155;
}

:root.dark .unlock-consequences li {
  color: #CBD5E1;
}
</style>
