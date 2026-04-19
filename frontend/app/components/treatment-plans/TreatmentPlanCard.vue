<script setup lang="ts">
import type { TreatmentPlan } from '~/types'

const props = defineProps<{
  plan: TreatmentPlan
}>()

const emit = defineEmits<{
  click: []
  edit: []
  delete: []
}>()

const { t, d } = useI18n()

const itemCount = computed(() => {
  const plan = props.plan as TreatmentPlan & { items?: unknown[] }
  return plan.items?.length || 0
})
</script>

<template>
  <UCard
    class="cursor-pointer hover:border-[var(--color-primary)] transition-colors"
    @click="emit('click')"
  >
    <div class="flex items-start justify-between">
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2 mb-1">
          <span class="text-sm font-mono text-subtle">
            {{ plan.plan_number }}
          </span>
          <TreatmentPlanStatusBadge
            :status="plan.status"
            size="xs"
          />
        </div>

        <h3
          v-if="plan.title"
          class="font-medium text-default truncate"
        >
          {{ plan.title }}
        </h3>
        <h3
          v-else
          class="font-medium text-subtle italic truncate"
        >
          {{ t('treatmentPlans.untitled') }}
        </h3>

        <div class="mt-2 text-caption text-subtle">
          {{ t('treatmentPlans.itemCount', { count: itemCount }) }}
        </div>

        <div class="mt-1 text-caption text-subtle">
          {{ d(new Date(plan.created_at), 'short') }}
        </div>
      </div>

      <UDropdown
        :items="[
          [{
            label: t('actions.edit'),
            icon: 'i-lucide-pencil',
            click: () => emit('edit')
          }],
          [{
            label: t('actions.delete'),
            icon: 'i-lucide-trash-2',
            click: () => emit('delete')
          }]
        ]"
        @click.stop
      >
        <UButton
          color="neutral"
          variant="ghost"
          icon="i-lucide-more-vertical"
          size="sm"
          @click.stop
        />
      </UDropdown>
    </div>
  </UCard>
</template>
