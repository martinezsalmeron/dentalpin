<script setup lang="ts">
import type { Appointment } from '~/types'

interface Props {
  appointment: Appointment | null
  patientId: string
  loading?: boolean
}

const props = defineProps<Props>()
const { t, locale } = useI18n()

// Navigate to calendar with appointment highlighted
function goToReschedule() {
  if (!props.appointment) return
  const date = props.appointment.start_time.split('T')[0]
  navigateTo(`/appointments?highlight=${props.appointment.id}&date=${date}`)
}

// Format appointment date
const formattedDate = computed(() => {
  if (!props.appointment) return ''
  const date = new Date(props.appointment.start_time)
  return date.toLocaleDateString(locale.value, {
    weekday: 'short',
    day: 'numeric',
    month: 'short'
  })
})

const formattedTime = computed(() => {
  if (!props.appointment) return ''
  const date = new Date(props.appointment.start_time)
  return date.toLocaleTimeString(locale.value, {
    hour: '2-digit',
    minute: '2-digit'
  })
})

// Days until appointment
const daysUntil = computed(() => {
  if (!props.appointment) return null
  const now = new Date()
  const apt = new Date(props.appointment.start_time)
  const diff = Math.ceil((apt.getTime() - now.getTime()) / (1000 * 60 * 60 * 24))
  return diff
})

const isToday = computed(() => daysUntil.value === 0)
const isTomorrow = computed(() => daysUntil.value === 1)
</script>

<template>
  <div class="next-appointment-widget">
    <!-- Loading state -->
    <template v-if="loading">
      <div class="widget-header">
        <UIcon
          name="i-lucide-calendar"
          class="w-4 h-4 text-gray-400"
        />
        <span class="font-medium text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide">
          {{ t('patientDetail.nextAppointment') }}
        </span>
      </div>
      <USkeleton class="h-4 w-full mb-2" />
      <USkeleton class="h-3 w-2/3" />
    </template>

    <!-- Has appointment -->
    <template v-else-if="appointment">
      <div class="widget-header">
        <UIcon
          name="i-lucide-calendar"
          class="w-4 h-4"
          :class="isToday ? 'text-success-500' : 'text-primary-500'"
        />
        <span class="font-medium text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide">
          {{ t('patientDetail.nextAppointment') }}
        </span>
        <UBadge
          v-if="isToday"
          color="success"
          size="xs"
          variant="subtle"
        >
          {{ t('appointments.today') }}
        </UBadge>
        <UBadge
          v-else-if="isTomorrow"
          color="info"
          size="xs"
          variant="subtle"
        >
          {{ t('appointments.tomorrow') }}
        </UBadge>
      </div>

      <div class="flex items-center gap-2 mb-1">
        <span class="font-semibold text-sm text-gray-900 dark:text-white">
          {{ formattedDate }}
        </span>
        <span class="text-sm text-gray-500">{{ formattedTime }}</span>
      </div>

      <p
        v-if="appointment.treatment_type"
        class="text-xs text-gray-500 dark:text-gray-400 mb-2 line-clamp-1"
      >
        {{ appointment.treatment_type }}
      </p>

      <p
        v-if="appointment.professional"
        class="text-xs text-gray-500 dark:text-gray-400 mb-2"
      >
        {{ appointment.professional.first_name }} {{ appointment.professional.last_name }}
      </p>

      <button
        type="button"
        class="text-xs text-primary-500 hover:text-primary-600 font-medium inline-flex items-center gap-1"
        @click="goToReschedule"
      >
        {{ t('patientDetail.reschedule') }}
      </button>
    </template>

    <!-- No appointment -->
    <template v-else>
      <div class="widget-header">
        <UIcon
          name="i-lucide-calendar"
          class="w-4 h-4 text-gray-400"
        />
        <span class="font-medium text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide">
          {{ t('patientDetail.nextAppointment') }}
        </span>
      </div>

      <p class="text-sm text-gray-500 dark:text-gray-400 mb-2">
        {{ t('patientDetail.noUpcomingAppointments') }}
      </p>

      <NuxtLink
        to="/appointments"
        class="text-xs text-primary-500 hover:text-primary-600 font-medium inline-flex items-center gap-1"
      >
        <UIcon
          name="i-lucide-plus"
          class="w-3 h-3"
        />
        {{ t('patientDetail.scheduleAppointment') }}
      </NuxtLink>
    </template>
  </div>
</template>

<style scoped>
.next-appointment-widget {
  padding: 0.75rem;
  border-radius: 0.5rem;
  border: 1px solid #E5E7EB;
  background-color: #F9FAFB;
}

:root.dark .next-appointment-widget {
  border-color: #374151;
  background-color: rgba(31, 41, 55, 0.5);
}

.widget-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
  flex-wrap: wrap;
}
</style>
