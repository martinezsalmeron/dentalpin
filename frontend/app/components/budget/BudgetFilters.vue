<script setup lang="ts">
import type { BudgetStatus } from '~/types'

const props = defineProps<{
  modelValue: {
    search: string
    statuses: BudgetStatus[]
    dateFrom: string
    dateTo: string
  }
}>()

const emit = defineEmits<{
  'update:modelValue': [value: typeof props.modelValue]
}>()

const { t } = useI18n()

// Local state for binding
const localFilters = reactive({
  search: props.modelValue.search,
  statuses: props.modelValue.statuses,
  dateFrom: props.modelValue.dateFrom,
  dateTo: props.modelValue.dateTo
})

// Watch for external changes
watch(() => props.modelValue, (newVal) => {
  localFilters.search = newVal.search
  localFilters.statuses = newVal.statuses
  localFilters.dateFrom = newVal.dateFrom
  localFilters.dateTo = newVal.dateTo
}, { deep: true })

// Emit changes
watch(localFilters, (newVal) => {
  emit('update:modelValue', { ...newVal })
}, { deep: true })

// Status filter options
const statusOptions = computed(() => [
  { label: t('budget.status.draft'), value: 'draft' as BudgetStatus },
  { label: t('budget.status.sent'), value: 'sent' as BudgetStatus },
  { label: t('budget.status.accepted'), value: 'accepted' as BudgetStatus },
  { label: t('budget.status.completed'), value: 'completed' as BudgetStatus },
  { label: t('budget.status.rejected'), value: 'rejected' as BudgetStatus },
  { label: t('budget.status.expired'), value: 'expired' as BudgetStatus },
  { label: t('budget.status.cancelled'), value: 'cancelled' as BudgetStatus }
])

// Show advanced filters
const showAdvanced = ref(false)

// Clear all filters
function clearFilters() {
  localFilters.search = ''
  localFilters.statuses = []
  localFilters.dateFrom = ''
  localFilters.dateTo = ''
}

// Check if any filters are active
const hasActiveFilters = computed(() => {
  return localFilters.search
    || localFilters.statuses.length > 0
    || localFilters.dateFrom
    || localFilters.dateTo
})
</script>

<template>
  <div class="space-y-4">
    <!-- Main filters row -->
    <div class="flex flex-wrap items-center gap-4">
      <!-- Search -->
      <UInput
        v-model="localFilters.search"
        :placeholder="t('budget.searchPlaceholder')"
        icon="i-lucide-search"
        class="max-w-sm"
      />

      <!-- Status filter -->
      <USelectMenu
        v-model="localFilters.statuses"
        :items="statusOptions"
        multiple
        :placeholder="t('budget.filters.allStatuses')"
        class="w-64"
      />

      <!-- Toggle advanced filters -->
      <UButton
        variant="ghost"
        color="neutral"
        size="sm"
        :icon="showAdvanced ? 'i-lucide-chevron-up' : 'i-lucide-chevron-down'"
        @click="showAdvanced = !showAdvanced"
      >
        {{ t('budget.filters.advanced') }}
      </UButton>

      <!-- Clear filters -->
      <UButton
        v-if="hasActiveFilters"
        variant="ghost"
        color="neutral"
        size="sm"
        icon="i-lucide-x"
        @click="clearFilters"
      >
        {{ t('budget.filters.clear') }}
      </UButton>
    </div>

    <!-- Advanced filters -->
    <div
      v-if="showAdvanced"
      class="flex flex-wrap items-center gap-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg"
    >
      <UFormField :label="t('budget.filters.dateFrom')">
        <UInput
          v-model="localFilters.dateFrom"
          type="date"
        />
      </UFormField>

      <UFormField :label="t('budget.filters.dateTo')">
        <UInput
          v-model="localFilters.dateTo"
          type="date"
        />
      </UFormField>
    </div>
  </div>
</template>
