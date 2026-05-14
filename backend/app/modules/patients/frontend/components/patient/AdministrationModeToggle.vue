<script setup lang="ts">
/**
 * AdministrationModeToggle — segmented control over administration tab modes.
 *
 * The `payments` mode is contributed by the `payments` module via the
 * `patient.detail.administracion.payments` slot. The pill only appears
 * when the slot has at least one provider that the current user can see
 * — i.e. the module is installed AND the user has `payments.record.read`.
 * No direct dependency from `patients` to `payments`: we only probe the
 * slot registry.
 */
import { useModuleSlots } from '~~/app/composables/useModuleSlots'

export type AdministrationMode = 'budgets' | 'billing' | 'payments' | 'documents'

defineProps<{
  modelValue: AdministrationMode
}>()

const emit = defineEmits<{
  'update:modelValue': [mode: AdministrationMode]
}>()

const { t } = useI18n()
const { resolve } = useModuleSlots()

const paymentsAvailable = computed(() =>
  resolve('patient.detail.administracion.payments', {}).length > 0
)

const options = computed(() => {
  const base = [
    { value: 'budgets', label: t('patientDetail.tabs.budgets'), icon: 'i-lucide-file-text' },
    { value: 'billing', label: t('patientDetail.tabs.billing'), icon: 'i-lucide-receipt' }
  ]
  if (paymentsAvailable.value) {
    base.push({ value: 'payments', label: t('patientDetail.tabs.payments'), icon: 'i-lucide-wallet' })
  }
  base.push({ value: 'documents', label: t('patientDetail.tabs.documents'), icon: 'i-lucide-files' })
  return base
})
</script>

<template>
  <SegmentedControl
    :model-value="modelValue"
    :options="options"
    @update:model-value="(v) => emit('update:modelValue', v as AdministrationMode)"
  />
</template>
