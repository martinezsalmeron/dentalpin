<script setup lang="ts">
/**
 * AdministrationModeToggle — segmented control over administration tab modes.
 */
export type AdministrationMode = 'budgets' | 'billing' | 'documents'

defineProps<{
  modelValue: AdministrationMode
}>()

const emit = defineEmits<{
  'update:modelValue': [mode: AdministrationMode]
}>()

const { t } = useI18n()

const options = computed(() => [
  { value: 'budgets', label: t('patientDetail.tabs.budgets'), icon: 'i-lucide-file-text' },
  { value: 'billing', label: t('patientDetail.tabs.billing'), icon: 'i-lucide-receipt' },
  { value: 'documents', label: t('patientDetail.tabs.documents'), icon: 'i-lucide-files' }
])
</script>

<template>
  <SegmentedControl
    :model-value="modelValue"
    :options="options"
    @update:model-value="(v) => emit('update:modelValue', v as AdministrationMode)"
  />
</template>
