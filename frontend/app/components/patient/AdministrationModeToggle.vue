<script setup lang="ts">
/**
 * AdministrationModeToggle - Toggle between administration tab modes
 *
 * Three modes:
 * - budgets: View and manage budgets
 * - billing: View invoices and billing summary
 * - documents: View and manage patient documents
 */

export type AdministrationMode = 'budgets' | 'billing' | 'documents'

defineProps<{
  modelValue: AdministrationMode
}>()

const emit = defineEmits<{
  'update:modelValue': [mode: AdministrationMode]
}>()

const { t } = useI18n()

const modes: Array<{ value: AdministrationMode, labelKey: string, icon: string }> = [
  { value: 'budgets', labelKey: 'patientDetail.tabs.budgets', icon: 'i-lucide-file-text' },
  { value: 'billing', labelKey: 'patientDetail.tabs.billing', icon: 'i-lucide-receipt' },
  { value: 'documents', labelKey: 'patientDetail.tabs.documents', icon: 'i-lucide-files' }
]

function selectMode(mode: AdministrationMode) {
  emit('update:modelValue', mode)
}
</script>

<template>
  <div class="flex gap-1 p-1 bg-gray-100 dark:bg-gray-800 rounded-lg">
    <UButton
      v-for="mode in modes"
      :key="mode.value"
      :variant="modelValue === mode.value ? 'solid' : 'ghost'"
      :color="modelValue === mode.value ? 'primary' : 'neutral'"
      :icon="mode.icon"
      size="sm"
      @click="selectMode(mode.value)"
    >
      <span class="hidden sm:inline">{{ t(mode.labelKey) }}</span>
    </UButton>
  </div>
</template>
