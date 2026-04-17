<script setup lang="ts">
/**
 * ClinicalModeToggle - Toggle between clinical tab modes
 *
 * Four modes ordered chronologically:
 * - history: View past odontogram states (read-only)
 * - diagnosis: Record current conditions
 * - plans: Create and manage treatment plans
 * - appointments: View and manage patient appointments
 */

export type ClinicalMode = 'history' | 'diagnosis' | 'plans' | 'appointments'

defineProps<{
  modelValue: ClinicalMode
}>()

const emit = defineEmits<{
  'update:modelValue': [mode: ClinicalMode]
}>()

const { t } = useI18n()

const modes: Array<{ value: ClinicalMode, labelKey: string, icon: string }> = [
  { value: 'history', labelKey: 'clinical.modes.history', icon: 'i-lucide-history' },
  { value: 'diagnosis', labelKey: 'clinical.modes.diagnosis', icon: 'i-lucide-stethoscope' },
  { value: 'plans', labelKey: 'clinical.modes.plans', icon: 'i-lucide-clipboard-list' },
  { value: 'appointments', labelKey: 'clinical.modes.appointments', icon: 'i-lucide-calendar' }
]

function selectMode(mode: ClinicalMode) {
  emit('update:modelValue', mode)
}
</script>

<template>
  <div class="flex gap-1 p-1 bg-gray-100 dark:bg-gray-800 rounded-lg">
    <UButton
      v-for="mode in modes"
      :key="mode.value"
      :variant="modelValue === mode.value ? 'solid' : 'ghost'"
      :color="modelValue === mode.value ? 'primary' : 'gray'"
      :icon="mode.icon"
      size="sm"
      @click="selectMode(mode.value)"
    >
      <span class="hidden sm:inline">{{ t(mode.labelKey) }}</span>
    </UButton>
  </div>
</template>
