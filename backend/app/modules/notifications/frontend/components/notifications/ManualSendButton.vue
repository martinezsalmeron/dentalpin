<script setup lang="ts">
/**
 * ManualSendButton - Button for manually sending notification emails.
 *
 * This component only renders when:
 * 1. The notification type is enabled at clinic level
 * 2. auto_send is disabled (manual mode)
 * 3. The recipient has an email address
 */

import type { ManualSendRequest } from '~~/app/types'

const props = defineProps<{
  /** Type of notification to send */
  notificationType: string
  /** Recipient's email address */
  recipientEmail?: string
  /** Patient ID (for patient notifications) */
  patientId?: string
  /** Appointment ID (for appointment notifications) */
  appointmentId?: string
  /** Budget ID (for budget notifications) */
  budgetId?: string
  /** Additional context for the template */
  customContext?: Record<string, unknown>
  /** Button size */
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'
  /** Button variant */
  variant?: 'solid' | 'outline' | 'ghost' | 'soft' | 'subtle' | 'link'
  /** Custom label (overrides default) */
  label?: string
}>()

const emit = defineEmits<{
  (e: 'sent'): void
  (e: 'error', message: string): void
}>()

const { t } = useI18n()
const { shouldShowManualSend, sendNotification, fetchSettings, settings } = useNotificationSettings()

const isSending = ref(false)

// Fetch settings on mount if not already loaded
onMounted(async () => {
  if (!settings.value) {
    await fetchSettings()
  }
})

// Check if button should be shown
const shouldShow = computed(() => {
  // Must have recipient email
  if (!props.recipientEmail) return false

  // Check clinic settings
  return shouldShowManualSend(props.notificationType)
})

// Get button label
const buttonLabel = computed(() => {
  if (props.label) return props.label

  const typeLabels: Record<string, string> = {
    appointment_confirmation: t('notifications.sendConfirmation'),
    appointment_reminder: t('notifications.sendReminder'),
    appointment_cancelled: t('notifications.sendCancellation'),
    budget_sent: t('notifications.sendBudget'),
    budget_accepted: t('notifications.sendAcceptance'),
    welcome: t('notifications.sendWelcome')
  }

  return typeLabels[props.notificationType] || t('notifications.sendEmail')
})

// Send notification
async function handleSend() {
  isSending.value = true

  const request: ManualSendRequest = {
    notification_type: props.notificationType,
    patient_id: props.patientId,
    appointment_id: props.appointmentId,
    budget_id: props.budgetId,
    custom_context: props.customContext
  }

  const success = await sendNotification(request)

  isSending.value = false

  if (success) {
    emit('sent')
  } else {
    emit('error', t('notifications.errors.send_failed'))
  }
}
</script>

<template>
  <UButton
    v-if="shouldShow"
    icon="i-lucide-send"
    :size="size || 'sm'"
    :variant="variant || 'outline'"
    :loading="isSending"
    @click="handleSend"
  >
    {{ buttonLabel }}
  </UButton>
</template>
