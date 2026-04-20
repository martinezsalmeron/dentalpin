<script setup lang="ts">
/**
 * ClinicalModeToggle — segmented control over clinical tab modes.
 * Chronological order: history → diagnosis → plans → appointments.
 */
export type ClinicalMode = 'history' | 'diagnosis' | 'plans' | 'appointments'

defineProps<{
  modelValue: ClinicalMode
}>()

const emit = defineEmits<{
  'update:modelValue': [mode: ClinicalMode]
}>()

const { t } = useI18n()

const options = computed(() => [
  { value: 'history', label: t('clinical.modes.history'), icon: 'i-lucide-history' },
  { value: 'diagnosis', label: t('clinical.modes.diagnosis'), icon: 'i-lucide-stethoscope' },
  { value: 'plans', label: t('clinical.modes.plans'), icon: 'i-lucide-clipboard-list' },
  { value: 'appointments', label: t('clinical.modes.appointments'), icon: 'i-lucide-calendar' }
])
</script>

<template>
  <SegmentedControl
    :model-value="modelValue"
    :options="options"
    @update:model-value="(v) => emit('update:modelValue', v as ClinicalMode)"
  />
</template>
