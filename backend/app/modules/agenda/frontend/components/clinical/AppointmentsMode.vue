<script setup lang="ts">
/**
 * AppointmentsMode - View and manage patient appointments
 */

import type { Appointment, PaginatedResponse } from '~~/app/types'

const props = defineProps<{
  patientId: string
}>()

const { t, locale } = useI18n()
const api = useApi()
const router = useRouter()

// Fetch appointments
const { data: appointmentsData, status } = await useAsyncData(
  `clinical-appointments:${props.patientId}`,
  async () => {
    try {
      return await api.get<PaginatedResponse<Appointment>>(
        `/api/v1/agenda/appointments?patient_id=${props.patientId}`
      )
    } catch {
      return { data: [], total: 0, page: 1, page_size: 20 }
    }
  }
)

const appointments = computed(() => appointmentsData.value?.data || [])

// Format date time
function formatDateTime(dateStr: string): string {
  return new Date(dateStr).toLocaleString(locale.value, {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// Status badge color
type BadgeColor = 'success' | 'warning' | 'neutral' | 'error' | 'info' | 'primary' | 'secondary'

function getStatusColor(appointmentStatus: string): BadgeColor {
  switch (appointmentStatus) {
    case 'scheduled':
      return 'info'
    case 'confirmed':
      return 'success'
    case 'checked_in':
    case 'in_treatment':
      return 'warning'
    case 'completed':
      return 'neutral'
    case 'cancelled':
      return 'error'
    case 'no_show':
      return 'error'
    default:
      return 'neutral'
  }
}

function goToAppointment(appointment: Appointment) {
  const date = appointment.start_time.split('T')[0]
  router.push(`/appointments?highlight=${appointment.id}&date=${date}`)
}
</script>

<template>
  <div class="appointments-mode">
    <!-- Header -->
    <div class="flex items-center justify-between mb-4">
      <h3 class="font-medium flex items-center gap-2">
        <UIcon
          name="i-lucide-calendar"
          class="w-5 h-5"
        />
        {{ t('patientDetail.tabs.appointments') }}
        <UBadge
          v-if="appointments.length > 0"
          color="neutral"
          size="xs"
          variant="subtle"
        >
          {{ appointments.length }}
        </UBadge>
      </h3>
      <UButton
        size="sm"
        icon="i-lucide-plus"
        color="primary"
        :to="`/appointments?patient_id=${patientId}`"
      >
        {{ t('patientDetail.scheduleAppointment') }}
      </UButton>
    </div>

    <!-- Loading -->
    <div
      v-if="status === 'pending'"
      class="space-y-3"
    >
      <USkeleton
        v-for="i in 3"
        :key="i"
        class="h-12 w-full"
      />
    </div>

    <!-- Empty state -->
    <UCard
      v-else-if="appointments.length === 0"
      class="text-center py-8"
    >
      <UIcon
        name="i-lucide-calendar"
        class="w-12 h-12 text-subtle mx-auto mb-3"
      />
      <p class="text-muted mb-4">
        {{ t('patientDetail.noAppointments') }}
      </p>
      <UButton
        :to="`/appointments?patient_id=${patientId}`"
        icon="i-lucide-plus"
      >
        {{ t('patientDetail.scheduleAppointment') }}
      </UButton>
    </UCard>

    <!-- Appointments list -->
    <UCard v-else>
      <ul class="divide-y divide-[var(--color-border-subtle)]">
        <li
          v-for="appointment in appointments"
          :key="appointment.id"
          class="py-3 first:pt-0 last:pb-0 flex items-center justify-between cursor-pointer hover:bg-surface-muted -mx-4 px-4 transition-colors"
          @click="goToAppointment(appointment)"
        >
          <div>
            <p class="font-medium text-default">
              {{ formatDateTime(appointment.start_time) }}
            </p>
            <p class="text-sm text-muted">
              {{ appointment.treatment_type || '-' }}
            </p>
          </div>
          <UBadge
            :color="getStatusColor(appointment.status)"
            variant="subtle"
          >
            {{ t(`appointments.${appointment.status}`) }}
          </UBadge>
        </li>
      </ul>
    </UCard>
  </div>
</template>
