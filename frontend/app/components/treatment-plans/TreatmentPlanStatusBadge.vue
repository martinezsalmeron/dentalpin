<script setup lang="ts">
import type { TreatmentPlanStatus } from '~/types'

const props = defineProps<{
  status: TreatmentPlanStatus
  size?: 'xs' | 'sm' | 'md'
}>()

const { t } = useI18n()

const colorMap: Record<TreatmentPlanStatus, string> = {
  draft: 'gray',
  active: 'blue',
  completed: 'green',
  archived: 'neutral',
  cancelled: 'red'
}

const color = computed(() => colorMap[props.status] || 'gray')
const label = computed(() => t(`treatmentPlans.status.${props.status}`))
</script>

<template>
  <UBadge
    :color="color"
    :size="size || 'sm'"
    variant="subtle"
  >
    {{ label }}
  </UBadge>
</template>
