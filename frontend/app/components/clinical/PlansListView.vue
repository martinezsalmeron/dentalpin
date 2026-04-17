<script setup lang="ts">
/**
 * PlansListView - Display list of treatment plans for a patient
 *
 * Uses TreatmentPlanMiniCard for each plan.
 * Provides actions: view, activate, generate budget.
 */

import type { TreatmentPlan } from '~/types'

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
  <div class="space-y-4">
    <!-- Header with create button -->
    <div class="flex items-center justify-between">
      <h3 class="font-medium flex items-center gap-2">
        <UIcon
          name="i-lucide-clipboard-list"
          class="w-5 h-5"
        />
        {{ t('clinical.plans.title') }}
      </h3>
      <UButton
        color="primary"
        size="sm"
        icon="i-lucide-plus"
        @click="emit('create-plan')"
      >
        {{ t('clinical.plans.create') }}
      </UButton>
    </div>

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

    <!-- Empty state -->
    <UCard v-else-if="!hasPlans">
      <div class="text-center py-8 text-gray-500 dark:text-gray-400">
        <UIcon
          name="i-lucide-clipboard"
          class="w-12 h-12 mx-auto mb-3 opacity-50"
        />
        <p class="text-lg font-medium mb-1">
          {{ t('clinical.plans.empty') }}
        </p>
        <p class="text-sm mb-4">
          {{ t('clinical.plans.emptyDescription') }}
        </p>
        <UButton
          color="primary"
          icon="i-lucide-plus"
          @click="emit('create-plan')"
        >
          {{ t('clinical.plans.createFirst') }}
        </UButton>
      </div>
    </UCard>

    <!-- Plans list -->
    <template v-else>
      <!-- Active plans -->
      <div
        v-if="activePlans.length > 0"
        class="space-y-3"
      >
        <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 flex items-center gap-2">
          <UIcon
            name="i-lucide-play-circle"
            class="w-4 h-4 text-green-500"
          />
          {{ t('clinical.plans.active') }}
        </h4>
        <div class="grid gap-3">
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
        class="space-y-3"
      >
        <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 flex items-center gap-2">
          <UIcon
            name="i-lucide-pencil"
            class="w-4 h-4 text-amber-500"
          />
          {{ t('clinical.plans.drafts') }}
        </h4>
        <div class="grid gap-3">
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
          <div class="grid gap-3 pt-2">
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
