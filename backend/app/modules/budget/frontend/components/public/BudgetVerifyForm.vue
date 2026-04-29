<script setup lang="ts">
/**
 * BudgetVerifyForm — collects the knowledge factor and submits it to
 * ``/verify`` on the public budget endpoint. Renders the appropriate
 * input for the method requested by ``/meta`` (ADR 0006):
 *
 * - phone_last4 → 4-digit numeric input
 * - dob         → date input (ISO yyyy-mm-dd)
 * - manual_code → 4-6 digit numeric input (provided verbally by reception)
 *
 * Surfaces the error state returned by the composable so the parent page
 * can show inline messages (invalid, locked, rate-limited).
 */

import type { PublicAuthMethod, VerifyError } from '../../composables/usePublicBudget'

const props = defineProps<{
  method: PublicAuthMethod
  verifying: boolean
  error: VerifyError | null
}>()

const emit = defineEmits<{
  submit: [payload: { method: PublicAuthMethod; value: string }]
}>()

const { t } = useI18n()

const value = ref('')

const labelKey = computed(() => {
  switch (props.method) {
    case 'phone_last4':
      return 'budget.public.verify.phone_last4_label'
    case 'dob':
      return 'budget.public.verify.dob_label'
    case 'manual_code':
      return 'budget.public.verify.manual_code_label'
    default:
      return 'budget.public.verify.phone_last4_label'
  }
})

const placeholder = computed(() => {
  switch (props.method) {
    case 'phone_last4':
      return '1234'
    case 'manual_code':
      return '123456'
    case 'dob':
      return ''
    default:
      return ''
  }
})

const inputType = computed(() => (props.method === 'dob' ? 'date' : 'text'))
const inputMode = computed(() =>
  props.method === 'phone_last4' || props.method === 'manual_code' ? 'numeric' : undefined
)
const maxLength = computed(() => {
  if (props.method === 'phone_last4') return 4
  if (props.method === 'manual_code') return 6
  return undefined
})

const errorMessage = computed(() => {
  switch (props.error) {
    case 'invalid':
      return t('budget.public.verify.invalid')
    case 'locked':
      return t('budget.public.verify.locked')
    case 'rate_limited':
      return t('budget.public.verify.rate_limited')
    case 'method_mismatch':
      return t('budget.public.verify.invalid')
    case 'expired':
      return t('budget.public.expired')
    case 'unknown':
      return t('budget.public.verify.invalid')
    default:
      return null
  }
})

const isValid = computed(() => {
  if (props.method === 'phone_last4') return /^\d{4}$/.test(value.value)
  if (props.method === 'manual_code') return /^\d{4,6}$/.test(value.value)
  if (props.method === 'dob') return /^\d{4}-\d{2}-\d{2}$/.test(value.value)
  return value.value.length > 0
})

function submit() {
  if (!isValid.value || props.verifying) return
  emit('submit', { method: props.method, value: value.value })
}
</script>

<template>
  <UCard class="max-w-md mx-auto">
    <template #header>
      <h2 class="text-lg font-semibold">
        {{ t('budget.public.verify.title') }}
      </h2>
    </template>

    <form class="space-y-4" @submit.prevent="submit">
      <p class="text-sm text-[var(--ui-text-muted)]">
        {{ t('budget.public.verify.intro') }}
      </p>

      <UFormField :label="t(labelKey)" required>
        <UInput
          v-model="value"
          autofocus
          :type="inputType"
          :inputmode="inputMode"
          :placeholder="placeholder"
          :maxlength="maxLength"
          size="lg"
        />
      </UFormField>

      <UAlert
        v-if="errorMessage"
        color="error"
        variant="soft"
        :description="errorMessage"
      />

      <UButton
        type="submit"
        color="primary"
        size="lg"
        block
        :loading="verifying"
        :disabled="!isValid || verifying"
      >
        {{ t('budget.public.verify.submit') }}
      </UButton>
    </form>
  </UCard>
</template>
