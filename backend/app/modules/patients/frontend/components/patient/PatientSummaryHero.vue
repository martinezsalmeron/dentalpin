<script setup lang="ts">
import type { PatientExtended, PatientAlert, TreatmentPlan, Appointment } from '~~/app/types'

interface Props {
  patient: PatientExtended
  activePlan?: TreatmentPlan | null
  nextAppointment?: Appointment | null
  loadingPlan?: boolean
  loadingAppointment?: boolean
}

const props = defineProps<Props>()

const { t } = useI18n()

const age = computed(() => {
  if (!props.patient.date_of_birth) return null
  const today = new Date()
  const birth = new Date(props.patient.date_of_birth)
  let years = today.getFullYear() - birth.getFullYear()
  const m = today.getMonth() - birth.getMonth()
  if (m < 0 || (m === 0 && today.getDate() < birth.getDate())) years--
  return years
})

const initials = computed(() => {
  const first = props.patient.first_name?.[0] || ''
  const last = props.patient.last_name?.[0] || ''
  return (first + last).toUpperCase()
})

const statusColor = computed(() =>
  props.patient.status === 'active' ? 'success' : 'neutral'
)

const genderLabel = computed(() => {
  const g = props.patient.gender
  if (!g) return null
  const map: Record<string, string> = {
    male: t('patients.gender.male'),
    female: t('patients.gender.female'),
    other: t('patients.gender.other'),
    prefer_not_say: t('patients.gender.preferNotSay')
  }
  return map[g] ?? null
})

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

const alerts = computed(() => props.patient.active_alerts ?? [])
const hasCriticalAlerts = computed(() =>
  alerts.value.some(a => a.severity === 'critical' || a.severity === 'high')
)
</script>

<template>
  <section
    class="patient-summary-hero space-y-3"
    aria-label="Resumen del paciente"
  >
    <!-- Identity card -->
    <UCard :ui="{ body: 'p-3' }">
      <div class="flex flex-col items-center gap-3 text-center">
        <!-- Avatar -->
        <UAvatar
          v-if="patient.photo_url"
          :src="patient.photo_url"
          :alt="`${patient.first_name} ${patient.last_name}`"
          size="xl"
          class="shrink-0"
        />
        <UAvatar
          v-else
          :text="initials"
          size="xl"
          class="shrink-0"
        />

        <!-- Identity column -->
        <div class="flex-1 min-w-0 w-full space-y-2">
          <div class="flex flex-wrap items-center justify-center gap-1.5">
            <UBadge
              :color="statusColor"
              size="sm"
              variant="subtle"
            >
              {{ patient.status === 'active' ? t('patients.status.active') : t('patients.status.archived') }}
            </UBadge>
            <UBadge
              v-if="age != null"
              color="neutral"
              variant="soft"
              size="sm"
            >
              <UIcon
                name="i-lucide-cake"
                class="w-3.5 h-3.5 mr-1"
              />
              {{ age }} {{ t('patients.years') }}
            </UBadge>
            <UBadge
              v-if="genderLabel"
              color="neutral"
              variant="soft"
              size="sm"
            >
              {{ genderLabel }}
            </UBadge>
            <UBadge
              v-if="patient.national_id"
              color="neutral"
              variant="soft"
              size="sm"
              class="tnum"
            >
              <UIcon
                name="i-lucide-id-card"
                class="w-3.5 h-3.5 mr-1"
              />
              {{ patient.national_id_type?.toUpperCase() }} {{ patient.national_id }}
            </UBadge>
          </div>

          <!-- Contact strip -->
          <div class="flex flex-col items-center gap-1 text-sm">
            <a
              v-if="patient.phone"
              :href="`tel:${patient.phone}`"
              class="inline-flex items-center gap-1.5 text-primary-accent hover:underline"
            >
              <UIcon
                name="i-lucide-phone"
                class="w-4 h-4 text-subtle"
              />
              <span class="tnum">{{ patient.phone }}</span>
            </a>
            <a
              v-if="patient.email"
              :href="`mailto:${patient.email}`"
              class="inline-flex items-center gap-1.5 text-primary-accent hover:underline truncate max-w-[18rem]"
            >
              <UIcon
                name="i-lucide-mail"
                class="w-4 h-4 text-subtle shrink-0"
              />
              <span class="truncate">{{ patient.email }}</span>
            </a>
            <span
              v-if="!patient.phone && !patient.email"
              class="text-caption text-subtle"
            >
              {{ t('patients.noContactInfo', 'Sin datos de contacto') }}
            </span>
          </div>
        </div>
      </div>
    </UCard>

    <!-- Action slot for sibling modules (e.g. recalls "Set recall"). -->
    <ModuleSlot
      name="patient.summary.actions"
      :ctx="{ patient }"
    />

    <!-- Clinical alerts banner -->
    <div
      v-if="alerts.length > 0"
      :class="[
        hasCriticalAlerts ? 'alert-surface-danger' : 'alert-surface-warning',
        'rounded-token-md px-3 py-2'
      ]"
      role="alert"
    >
      <div class="flex items-center gap-1.5 mb-1.5">
        <UIcon
          :name="hasCriticalAlerts ? 'i-lucide-alert-triangle' : 'i-lucide-info'"
          class="w-4 h-4"
          :style="{ color: hasCriticalAlerts ? 'var(--color-danger-accent)' : 'var(--color-warning-accent)' }"
        />
        <span class="text-caption uppercase tracking-wide font-medium">
          {{ t('patients.alerts.label') }}
        </span>
      </div>
      <div class="flex flex-col gap-1.5">
        <template
          v-for="(alert, index) in alerts"
          :key="index"
        >
          <UTooltip
            v-if="alert.details"
            :text="alert.details"
          >
            <UBadge
              :color="getSeverityColor(alert.severity)"
              size="sm"
              variant="subtle"
              class="w-full justify-start items-start text-left"
            >
              <UIcon
                :name="getAlertIcon(alert.type)"
                class="w-3.5 h-3.5 mr-1 shrink-0 mt-0.5"
              />
              <span class="whitespace-normal break-words">{{ alert.title }}</span>
            </UBadge>
          </UTooltip>
          <UBadge
            v-else
            :color="getSeverityColor(alert.severity)"
            size="sm"
            variant="subtle"
            class="w-full justify-start items-start text-left"
          >
            <UIcon
              :name="getAlertIcon(alert.type)"
              class="w-3.5 h-3.5 mr-1 shrink-0 mt-0.5"
            />
            <span class="whitespace-normal break-words">{{ alert.title }}</span>
          </UBadge>
        </template>
      </div>
    </div>

    <!-- Plan + Appointment widgets -->
    <div class="space-y-3">
      <ActivePlanWidget
        :plan="activePlan"
        :patient-id="patient.id"
        :loading="loadingPlan"
      />
      <NextAppointmentWidget
        :appointment="nextAppointment"
        :patient-id="patient.id"
        :loading="loadingAppointment"
      />
    </div>

    <!-- Emergency contact (if exists) -->
    <UCard
      v-if="patient.emergency_contact"
      :ui="{ body: 'p-3' }"
    >
      <div class="flex items-center gap-2 text-caption uppercase tracking-wide text-subtle mb-1.5">
        <UIcon
          name="i-lucide-phone-call"
          class="w-4 h-4"
        />
        {{ t('patients.emergencyContact.title') }}
      </div>
      <div class="space-y-0.5 text-sm">
        <p class="text-default font-medium">
          {{ patient.emergency_contact.name }}
        </p>
        <p
          v-if="patient.emergency_contact.relationship"
          class="text-subtle text-caption"
        >
          {{ patient.emergency_contact.relationship }}
        </p>
        <a
          :href="`tel:${patient.emergency_contact.phone}`"
          class="text-primary-accent hover:underline tnum inline-flex items-center gap-1"
        >
          <UIcon
            name="i-lucide-phone"
            class="w-3.5 h-3.5"
          />
          {{ patient.emergency_contact.phone }}
        </a>
      </div>
    </UCard>

    <!-- Sidebar slot extension point (preserved for community modules) -->
    <ModuleSlot
      name="patient.detail.sidebar"
      :ctx="{ patient }"
    />
  </section>
</template>
