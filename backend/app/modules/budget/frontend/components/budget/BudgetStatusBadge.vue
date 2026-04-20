<script setup lang="ts">
import type { BudgetStatus } from '~~/app/types'

const props = defineProps<{
  status: BudgetStatus
  size?: 'xs' | 'sm' | 'md'
}>()

const { t } = useI18n()

const colorMap: Record<BudgetStatus, string> = {
  draft: 'gray',
  sent: 'blue',
  accepted: 'green',
  completed: 'emerald',
  rejected: 'red',
  expired: 'orange',
  cancelled: 'neutral'
}

const color = computed(() => colorMap[props.status] || 'gray')
const label = computed(() => t(`budget.status.${props.status}`))
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
