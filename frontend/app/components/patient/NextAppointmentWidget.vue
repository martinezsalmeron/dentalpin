<script setup lang="ts">
import type { Appointment } from '~/types'

interface Props {
  appointment: Appointment | null
  patientId: string
  loading?: boolean
}

const props = defineProps<Props>()
const { t, locale } = useI18n()

function goToReschedule() {
  if (!props.appointment) return
  const date = props.appointment.start_time.split('T')[0]
  navigateTo(`/appointments?highlight=${props.appointment.id}&date=${date}`)
}

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

const daysUntil = computed(() => {
  if (!props.appointment) return null
  const now = new Date()
  const apt = new Date(props.appointment.start_time)
  return Math.ceil((apt.getTime() - now.getTime()) / (1000 * 60 * 60 * 24))
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
          class="w-4 h-4 text-subtle"
        />
        <span class="text-caption text-muted uppercase tracking-wide">
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
          :class="isToday ? 'text-success-accent' : 'text-primary-accent'"
        />
        <span class="text-caption text-muted uppercase tracking-wide">
          {{ t('patientDetail.nextAppointment') }}
        </span>
        <StatusBadge
          v-if="isToday"
          role="success"
          :label="t('appointments.today')"
          size="xs"
        />
        <StatusBadge
          v-else-if="isTomorrow"
          role="info"
          :label="t('appointments.tomorrow')"
          size="xs"
        />
      </div>

      <div class="flex items-center gap-2 mb-1">
        <span class="text-ui text-default">
          {{ formattedDate }}
        </span>
        <span class="text-caption text-subtle tnum">{{ formattedTime }}</span>
      </div>

      <p
        v-if="appointment.treatment_type"
        class="text-caption text-muted mb-2 line-clamp-1"
      >
        {{ appointment.treatment_type }}
      </p>

      <p
        v-if="appointment.professional"
        class="text-caption text-muted mb-2"
      >
        {{ appointment.professional.first_name }} {{ appointment.professional.last_name }}
      </p>

      <button
        type="button"
        class="text-caption text-primary-accent hover:underline inline-flex items-center gap-1"
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
          class="w-4 h-4 text-subtle"
        />
        <span class="text-caption text-muted uppercase tracking-wide">
          {{ t('patientDetail.nextAppointment') }}
        </span>
      </div>

      <p class="text-body text-muted mb-2">
        {{ t('patientDetail.noUpcomingAppointments') }}
      </p>

      <NuxtLink
        to="/appointments"
        class="text-caption text-primary-accent hover:underline inline-flex items-center gap-1"
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
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  background-color: var(--color-surface-muted);
}

.widget-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
  flex-wrap: wrap;
}
</style>
