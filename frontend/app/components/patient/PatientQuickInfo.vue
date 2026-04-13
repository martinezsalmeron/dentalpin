<script setup lang="ts">
import type { PatientExtended, PatientAlert } from '~/types'

interface Props {
  patient: PatientExtended
}

const props = defineProps<Props>()

const { t } = useI18n()

// Calculate age from date of birth
const age = computed(() => {
  if (!props.patient.date_of_birth) return null
  const today = new Date()
  const birth = new Date(props.patient.date_of_birth)
  let years = today.getFullYear() - birth.getFullYear()
  const monthDiff = today.getMonth() - birth.getMonth()
  if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
    years--
  }
  return years
})

// Get initials for avatar fallback
const initials = computed(() => {
  const first = props.patient.first_name?.[0] || ''
  const last = props.patient.last_name?.[0] || ''
  return (first + last).toUpperCase()
})

// Format phone for display
const formattedPhone = computed(() => {
  const phone = props.patient.phone
  if (!phone) return null
  return phone
})

// Status color
const statusColor = computed(() => {
  return props.patient.status === 'active' ? 'success' : 'neutral'
})

// Alert helpers
function getAlertIcon(type: PatientAlert['type']): string {
  const icons: Record<PatientAlert['type'], string> = {
    allergy: 'i-lucide-alert-triangle',
    pregnancy: 'i-lucide-baby',
    lactating: 'i-lucide-heart',
    anticoagulant: 'i-lucide-droplet',
    anesthesia_reaction: 'i-lucide-syringe',
    systemic_disease: 'i-lucide-activity'
  }
  return icons[type] || 'i-lucide-alert-circle'
}

function getSeverityColor(severity: PatientAlert['severity']): string {
  const colors: Record<PatientAlert['severity'], string> = {
    critical: 'error',
    high: 'warning',
    medium: 'info',
    low: 'neutral'
  }
  return colors[severity] || 'neutral'
}

const hasCriticalAlerts = computed(() =>
  props.patient.active_alerts?.some(a => a.severity === 'critical' || a.severity === 'high')
)
</script>

<template>
  <div class="p-4">
    <!-- Photo/Avatar -->
    <div class="flex flex-col items-center mb-4">
      <UAvatar
        v-if="patient.photo_url"
        :src="patient.photo_url"
        :alt="`${patient.first_name} ${patient.last_name}`"
        size="3xl"
        class="mb-2"
      />
      <UAvatar
        v-else
        :text="initials"
        size="3xl"
        class="mb-2"
      />

      <h2 class="text-lg font-semibold text-center">
        {{ patient.first_name }} {{ patient.last_name }}
      </h2>

      <div class="flex items-center gap-2 mt-1">
        <UBadge
          :color="statusColor"
          size="sm"
          variant="subtle"
        >
          {{ patient.status === 'active' ? t('patients.status.active') : t('patients.status.archived') }}
        </UBadge>
      </div>
    </div>

    <!-- Clinical Alerts Section -->
    <div
      v-if="patient.active_alerts?.length > 0"
      class="mb-4 p-3 rounded-lg border-l-3 bg-gray-50 dark:bg-gray-800/50"
      :class="hasCriticalAlerts ? 'border-l-red-400 dark:border-l-red-500' : 'border-l-amber-400 dark:border-l-amber-500'"
    >
      <!-- Section header -->
      <div class="flex items-center gap-2 mb-2">
        <UIcon
          :name="hasCriticalAlerts ? 'i-lucide-alert-triangle' : 'i-lucide-info'"
          class="w-4 h-4 text-gray-500 dark:text-gray-400"
        />
        <span class="font-medium text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide">
          {{ t('patients.alerts.label') }}
        </span>
      </div>
      <!-- Alert badges -->
      <div class="flex flex-col gap-2">
        <template
          v-for="(alert, index) in patient.active_alerts"
          :key="index"
        >
          <UTooltip
            v-if="alert.details"
            :text="alert.details"
          >
            <UBadge
              :color="getSeverityColor(alert.severity)"
              size="md"
              variant="subtle"
              class="w-full justify-start items-start text-left"
            >
              <UIcon
                :name="getAlertIcon(alert.type)"
                class="w-4 h-4 mr-2 shrink-0 mt-0.5"
              />
              <span class="whitespace-normal break-words">{{ alert.title }}</span>
            </UBadge>
          </UTooltip>
          <UBadge
            v-else
            :color="getSeverityColor(alert.severity)"
            size="md"
            variant="subtle"
            class="w-full justify-start items-start text-left"
          >
            <UIcon
              :name="getAlertIcon(alert.type)"
              class="w-4 h-4 mr-2 shrink-0 mt-0.5"
            />
            <span class="whitespace-normal break-words">{{ alert.title }}</span>
          </UBadge>
        </template>
      </div>
    </div>

    <!-- Quick Stats -->
    <div class="space-y-3 text-sm">
      <!-- Age -->
      <div
        v-if="age"
        class="flex items-center gap-2"
      >
        <UIcon
          name="i-lucide-cake"
          class="w-4 h-4 text-gray-400"
        />
        <span>{{ age }} {{ t('patients.years') }}</span>
      </div>

      <!-- Phone -->
      <div
        v-if="formattedPhone"
        class="flex items-center gap-2"
      >
        <UIcon
          name="i-lucide-phone"
          class="w-4 h-4 text-gray-400"
        />
        <a
          :href="`tel:${patient.phone}`"
          class="text-primary-500 hover:underline"
        >
          {{ formattedPhone }}
        </a>
      </div>

      <!-- Email -->
      <div
        v-if="patient.email"
        class="flex items-center gap-2"
      >
        <UIcon
          name="i-lucide-mail"
          class="w-4 h-4 text-gray-400"
        />
        <a
          :href="`mailto:${patient.email}`"
          class="text-primary-500 hover:underline truncate"
        >
          {{ patient.email }}
        </a>
      </div>

      <!-- National ID -->
      <div
        v-if="patient.national_id"
        class="flex items-center gap-2"
      >
        <UIcon
          name="i-lucide-id-card"
          class="w-4 h-4 text-gray-400"
        />
        <span>{{ patient.national_id_type?.toUpperCase() }}: {{ patient.national_id }}</span>
      </div>

      <!-- Emergency Contact -->
      <div
        v-if="patient.emergency_contact"
        class="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700"
      >
        <div class="flex items-center gap-2 mb-2 text-gray-500">
          <UIcon
            name="i-lucide-phone-call"
            class="w-4 h-4"
          />
          <span class="font-medium">{{ t('patients.emergencyContact.title') }}</span>
        </div>
        <div class="pl-6 space-y-1">
          <p class="font-medium">
            {{ patient.emergency_contact.name }}
          </p>
          <p
            v-if="patient.emergency_contact.relationship"
            class="text-gray-500"
          >
            {{ patient.emergency_contact.relationship }}
          </p>
          <a
            :href="`tel:${patient.emergency_contact.phone}`"
            class="text-primary-500 hover:underline"
          >
            {{ patient.emergency_contact.phone }}
          </a>
        </div>
      </div>
    </div>
  </div>
</template>
