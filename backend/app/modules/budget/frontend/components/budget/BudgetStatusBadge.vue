<script setup lang="ts">
import type { BudgetStatus } from '~~/app/types'
import { BUDGET_STATUS_ROLE } from '~~/app/config/severity'

const props = defineProps<{
  status: BudgetStatus
  size?: 'xs' | 'sm' | 'md'
}>()

const { t } = useI18n()
const role = computed(() => BUDGET_STATUS_ROLE[props.status] ?? 'neutral')
const label = computed(() => t(`budget.status.${props.status}`))
</script>

<template>
  <StatusBadge
    :role="role"
    :label="label"
    :size="size ?? 'sm'"
  />
</template>
