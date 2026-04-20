<script setup lang="ts">
/**
 * PlansListView - Display list of treatment plans for a patient
 *
 * Uses TreatmentPlanMiniCard for each plan.
 * Provides actions: view, activate, generate budget.
 */

import type { TreatmentPlan } from '~~/app/types'

const props = defineProps<{
  plans: TreatmentPlan[]
  patientId: string
  loading?: boolean
}>()

const emit = defineEmits<{
  'view-plan': [planId: string]
  'create-plan': []
  'activate-plan': [plan: TreatmentPlan]
  'generate-budget': [plan: TreatmentPlan]
  'schedule': [plan: TreatmentPlan]
}>()

const { t } = useI18n()

// Group plans by status for display order
const activePlans = computed(() =>
  props.plans.filter(p => p.status === 'active')
)

const draftPlans = computed(() =>
  props.plans.filter(p => p.status === 'draft')
)

const completedPlans = computed(() =>
  props.plans.filter(p => p.status === 'completed')
)

const hasPlans = computed(() => props.plans.length > 0)
</script>

<template>
  <div class="space-y-[var(--density-gap,1rem)]">
    <SectionHeader
      icon="i-lucide-clipboard-list"
      :title="t('clinical.plans.title')"
    >
      <template #action>
        <UButton
          color="primary"
          size="sm"
          icon="i-lucide-plus"
          @click="emit('create-plan')"
        >
          {{ t('clinical.plans.create') }}
        </UButton>
      </template>
    </SectionHeader>

    <!-- Loading state -->
    <div
      v-if="loading"
      class="flex items-center justify-center py-8"
    >
      <UIcon
        name="i-lucide-loader-2"
        class="w-8 h-8 animate-spin text-primary-accent"
      />
    </div>

    <!-- Empty state -->
    <UCard v-else-if="!hasPlans">
      <EmptyState
        icon="i-lucide-clipboard"
        :title="t('clinical.plans.empty')"
        :description="t('clinical.plans.emptyDescription')"
      >
        <template #actions>
          <UButton
            color="primary"
            variant="soft"
            icon="i-lucide-plus"
            @click="emit('create-plan')"
          >
            {{ t('clinical.plans.createFirst') }}
          </UButton>
        </template>
      </EmptyState>
    </UCard>

    <!-- Plans list -->
    <template v-else>
      <!-- Active plans -->
      <div
        v-if="activePlans.length > 0"
        class="space-y-[var(--density-gap,0.75rem)]"
      >
        <h4 class="text-caption text-muted uppercase tracking-wide flex items-center gap-2">
          <UIcon
            name="i-lucide-play-circle"
            class="w-4 h-4 text-success-accent"
          />
          {{ t('clinical.plans.active') }}
        </h4>
        <div class="grid gap-[var(--density-gap,0.75rem)]">
          <TreatmentPlanMiniCard
            v-for="plan in activePlans"
            :key="plan.id"
            :plan="plan"
            is-active
            @view="emit('view-plan', plan.id)"
            @activate="emit('activate-plan', plan)"
            @generate-budget="emit('generate-budget', plan)"
            @schedule="emit('schedule', plan)"
          />
        </div>
      </div>

      <!-- Draft plans -->
      <div
        v-if="draftPlans.length > 0"
        class="space-y-[var(--density-gap,0.75rem)]"
      >
        <h4 class="text-caption text-muted uppercase tracking-wide flex items-center gap-2">
          <UIcon
            name="i-lucide-pencil"
            class="w-4 h-4 text-warning-accent"
          />
          {{ t('clinical.plans.drafts') }}
        </h4>
        <div class="grid gap-[var(--density-gap,0.75rem)]">
          <TreatmentPlanMiniCard
            v-for="plan in draftPlans"
            :key="plan.id"
            :plan="plan"
            @view="emit('view-plan', plan.id)"
            @activate="emit('activate-plan', plan)"
            @schedule="emit('schedule', plan)"
          />
        </div>
      </div>

      <!-- Completed plans (collapsible) -->
      <UAccordion
        v-if="completedPlans.length > 0"
        :items="[{
          label: `${t('clinical.plans.completed')} (${completedPlans.length})`,
          slot: 'completed'
        }]"
        class="mt-4"
      >
        <template #completed>
          <div class="grid gap-[var(--density-gap,0.75rem)] pt-2">
            <TreatmentPlanMiniCard
              v-for="plan in completedPlans"
              :key="plan.id"
              :plan="plan"
              @view="emit('view-plan', plan.id)"
              @generate-budget="emit('generate-budget', plan)"
              @schedule="emit('schedule', plan)"
            />
          </div>
        </template>
      </UAccordion>
    </template>
  </div>
</template>
