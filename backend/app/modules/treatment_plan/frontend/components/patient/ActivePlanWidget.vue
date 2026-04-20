<script setup lang="ts">
import type { TreatmentPlan } from '~~/app/types'

interface Props {
  plan: TreatmentPlan | null
  patientId: string
  loading?: boolean
}

const props = defineProps<Props>()
const { t } = useI18n()

const progress = computed(() => {
  if (!props.plan) return 0
  const total = props.plan.item_count || 0
  const completed = props.plan.completed_count || 0
  if (total === 0) return 0
  return Math.round((completed / total) * 100)
})

const completedCount = computed(() => props.plan?.completed_count || 0)
const totalCount = computed(() => props.plan?.item_count || 0)
</script>

<template>
  <div class="active-plan-widget">
    <!-- Loading state -->
    <template v-if="loading">
      <div class="widget-header">
        <UIcon
          name="i-lucide-target"
          class="w-4 h-4 text-subtle"
        />
        <span class="text-caption text-muted uppercase tracking-wide">
          {{ t('patientDetail.activePlan') }}
        </span>
      </div>
      <USkeleton class="h-4 w-3/4 mb-2" />
      <USkeleton class="h-2 w-full mb-2" />
      <USkeleton class="h-3 w-1/2" />
    </template>

    <!-- Has active plan -->
    <template v-else-if="plan">
      <div class="widget-header">
        <UIcon
          name="i-lucide-target"
          class="w-4 h-4 text-primary-accent"
        />
        <span class="text-caption text-muted uppercase tracking-wide">
          {{ t('patientDetail.activePlan') }}
        </span>
      </div>

      <p class="text-ui text-default mb-2 line-clamp-2">
        {{ plan.title || plan.plan_number }}
      </p>

      <!-- Progress bar -->
      <div class="mb-2">
        <div class="flex justify-between items-center mb-1">
          <span class="text-caption text-subtle tnum">{{ completedCount }}/{{ totalCount }} {{ t('treatmentPlans.treatments') }}</span>
          <span class="text-caption text-primary-accent tnum">{{ progress }}%</span>
        </div>
        <div class="w-full bg-surface-sunken rounded-full h-1.5 overflow-hidden">
          <div
            class="h-full rounded-full transition-[width] duration-300"
            :style="{ width: `${progress}%`, backgroundColor: 'var(--color-primary)' }"
          />
        </div>
      </div>

      <NuxtLink
        :to="`/treatment-plans/${plan.id}?from=patient&patientId=${patientId}`"
        class="text-caption text-primary-accent hover:underline inline-flex items-center gap-1"
      >
        {{ t('patientDetail.viewPlan') }}
        <UIcon
          name="i-lucide-arrow-right"
          class="w-3 h-3"
        />
      </NuxtLink>
    </template>

    <!-- No active plan -->
    <template v-else>
      <div class="widget-header">
        <UIcon
          name="i-lucide-target"
          class="w-4 h-4 text-subtle"
        />
        <span class="text-caption text-muted uppercase tracking-wide">
          {{ t('patientDetail.activePlan') }}
        </span>
      </div>

      <p class="text-body text-muted mb-2">
        {{ t('patientDetail.noActivePlan') }}
      </p>

      <NuxtLink
        :to="`/patients/${patientId}?tab=clinical&action=createPlan`"
        class="text-caption text-primary-accent hover:underline inline-flex items-center gap-1"
      >
        <UIcon
          name="i-lucide-plus"
          class="w-3 h-3"
        />
        {{ t('patientDetail.createPlan') }}
      </NuxtLink>
    </template>
  </div>
</template>

<style scoped>
.active-plan-widget {
  padding: 0.75rem;
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  background-color: var(--color-surface-muted);
}

.widget-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}
</style>
