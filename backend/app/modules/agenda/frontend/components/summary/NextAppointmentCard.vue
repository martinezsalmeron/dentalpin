<script setup lang="ts">
/**
 * NextAppointmentCard — smart-card for the patient Resumen grid.
 *
 * Registered in ``patient.summary.cards`` by the agenda module. The
 * patients host page never imports this file. Fetches the patient's
 * upcoming appointments via the agenda API and shows the soonest one
 * with day-relative formatting.
 */
import type { Appointment, PaginatedResponse, PatientExtended } from '~~/app/types'

interface Ctx {
  patient: PatientExtended
}

const props = defineProps<{ ctx: Ctx }>()

const { t, locale } = useI18n()
const api = useApi()

const patientId = computed(() => props.ctx.patient.id)

const { data, status } = await useAsyncData(
  () => `agenda:summary-card:${patientId.value}`,
  async () => {
    try {
      return await api.get<PaginatedResponse<Appointment>>(
        `/api/v1/agenda/appointments?patient_id=${patientId.value}`
      )
    } catch {
      return { data: [], total: 0, page: 1, page_size: 20 }
    }
  },
  { watch: [patientId], server: false }
)

const upcoming = computed<Appointment | null>(() => {
  const now = Date.now()
  const list = data.value?.data ?? []
  const future = list
    .filter(a => new Date(a.start_time).getTime() > now && a.status !== 'cancelled')
    .sort((a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime())
  return future[0] ?? null
})

const dayLabel = computed(() => {
  if (!upcoming.value) return ''
  const now = new Date()
  const apt = new Date(upcoming.value.start_time)
  const days = Math.ceil((apt.getTime() - now.getTime()) / (1000 * 60 * 60 * 24))
  if (days === 0) return t('appointments.today', 'Hoy')
  if (days === 1) return t('appointments.tomorrow', 'Mañana')
  return apt.toLocaleDateString(locale.value, { weekday: 'short', day: 'numeric', month: 'short' })
})

const timeLabel = computed(() => {
  if (!upcoming.value) return ''
  return new Date(upcoming.value.start_time).toLocaleTimeString(locale.value, {
    hour: '2-digit',
    minute: '2-digit'
  })
})

const isToday = computed(() => {
  if (!upcoming.value) return false
  const days = Math.ceil((new Date(upcoming.value.start_time).getTime() - Date.now()) / (1000 * 60 * 60 * 24))
  return days === 0
})

const href = computed(() => {
  if (!upcoming.value) {
    // Empty state — drop the user on the agenda with `patient_id` in
    // the URL so the create modal pre-fills the patient picker the
    // moment they pick a free slot. No auto-open.
    return `/appointments?patient_id=${patientId.value}`
  }
  const date = upcoming.value.start_time.split('T')[0]
  return `/appointments?highlight=${upcoming.value.id}&date=${date}`
})

const severity = computed<'neutral' | 'info' | 'success'>(() => {
  if (!upcoming.value) return 'neutral'
  return isToday.value ? 'success' : 'info'
})

const professionalName = computed(() => {
  const p = upcoming.value?.professional
  if (!p) return ''
  return [p.first_name, p.last_name].filter(Boolean).join(' ')
})
</script>

<template>
  <SummaryCard
    :title="t('patientDetail.nextAppointment', 'Próxima cita')"
    icon="i-lucide-calendar"
    :severity="severity"
    :loading="status === 'pending'"
    :empty="!upcoming"
    :to="href"
  >
    <template #empty>
      {{ t('patientDetail.noUpcomingAppointments', 'Sin citas programadas') }}
    </template>

    <div class="space-y-1">
      <div class="flex items-baseline gap-2 flex-wrap">
        <span class="text-h2 text-default">{{ dayLabel }}</span>
        <span class="text-ui text-muted tnum">{{ timeLabel }}</span>
      </div>
      <p
        v-if="professionalName"
        class="text-caption text-muted truncate"
      >
        {{ professionalName }}
      </p>
      <p
        v-if="upcoming?.treatment_type"
        class="text-caption text-subtle truncate"
      >
        {{ upcoming.treatment_type }}
      </p>
    </div>

    <template #footer>
      <span>{{ upcoming ? t('patientDetail.openAppointment', 'Abrir cita') : t('patientDetail.scheduleAppointment', 'Agendar') }}</span>
    </template>
  </SummaryCard>
</template>
