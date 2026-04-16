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
    class="cursor-pointer hover:border-primary-500 transition-colors"
    @click="emit('click')"
  >
    <div class="flex items-start justify-between">
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2 mb-1">
          <span class="text-sm font-mono text-gray-500">
            {{ plan.plan_number }}
          </span>
          <TreatmentPlanStatusBadge
            :status="plan.status"
            size="xs"
          />
        </div>

        <h3
          v-if="plan.title"
          class="font-medium text-gray-900 truncate"
        >
          {{ plan.title }}
        </h3>
        <h3
          v-else
          class="font-medium text-gray-500 italic truncate"
        >
          {{ t('treatmentPlans.untitled') }}
        </h3>

        <div class="mt-2 text-sm text-gray-500">
          {{ t('treatmentPlans.itemCount', { count: itemCount }) }}
        </div>

        <div class="mt-1 text-xs text-gray-400">
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
          color="gray"
          variant="ghost"
          icon="i-lucide-more-vertical"
          size="sm"
          @click.stop
        />
      </UDropdown>
    </div>
  </UCard>
</template>
