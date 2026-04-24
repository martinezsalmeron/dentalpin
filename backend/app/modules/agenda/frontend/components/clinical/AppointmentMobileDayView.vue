<script setup lang="ts">
import type { Appointment, Professional } from '~~/app/types'

interface ProfessionalWithColor extends Professional {
  color: string
}

const props = defineProps<{
  appointments: Appointment[]
  professionals: ProfessionalWithColor[]
  currentDate: Date
  isLoading?: boolean
  highlightedAppointmentId?: string | null
}>()

const emit = defineEmits<{
  'appointment-click': [appointment: Appointment]
  'date-change': [date: Date]
  'create-at': [date: Date]
  'highlight-cleared': []
}>()

const { t, locale } = useI18n()

watch(() => props.highlightedAppointmentId, (newId) => {
  if (newId) {
    setTimeout(() => emit('highlight-cleared'), 5000)
  }
}, { immediate: true })

function isSameDay(a: Date, b: Date): boolean {
  return a.getFullYear() === b.getFullYear()
    && a.getMonth() === b.getMonth()
    && a.getDate() === b.getDate()
}

function getMonday(date: Date): Date {
  const d = new Date(date)
  const day = d.getDay()
  const diff = day === 0 ? -6 : 1 - day
  d.setDate(d.getDate() + diff)
  d.setHours(0, 0, 0, 0)
  return d
}

const weekDays = computed<Date[]>(() => {
  const start = getMonday(props.currentDate)
  return Array.from({ length: 7 }, (_, i) => {
    const d = new Date(start)
    d.setDate(start.getDate() + i)
    return d
  })
})

function formatWeekdayShort(date: Date): string {
  return new Intl.DateTimeFormat(locale.value, { weekday: 'narrow' }).format(date)
}

function formatHeaderDate(date: Date): string {
  return new Intl.DateTimeFormat(locale.value, {
    weekday: 'long',
    day: 'numeric',
    month: 'short',
    year: 'numeric'
  }).format(date)
}

function formatTime(iso: string): string {
  const d = new Date(iso)
  return d.toLocaleTimeString(locale.value, { hour: '2-digit', minute: '2-digit', hour12: false })
}

function minutesBetween(startIso: string, endIso: string): number {
  return Math.round((new Date(endIso).getTime() - new Date(startIso).getTime()) / 60000)
}

function countForDay(day: Date): number {
  return props.appointments.filter((apt) => {
    const d = new Date(apt.start_time)
    return isSameDay(d, day) && apt.status !== 'cancelled'
  }).length
}

const dayAppointments = computed(() => {
  const filtered = props.appointments.filter((apt) => {
    const d = new Date(apt.start_time)
    return isSameDay(d, props.currentDate)
  })
  return [...filtered].sort((a, b) => a.start_time.localeCompare(b.start_time))
})

function professionalFor(id: string): ProfessionalWithColor | undefined {
  return props.professionals.find(p => p.id === id)
}

function professionalInitials(p: ProfessionalWithColor): string {
  return `${p.first_name?.[0] ?? ''}${p.last_name?.[0] ?? ''}`.toUpperCase()
}

function patientName(apt: Appointment): string {
  if (apt.patient) {
    return `${apt.patient.first_name ?? ''} ${apt.patient.last_name ?? ''}`.trim() || t('appointments.noPatient')
  }
  return t('appointments.noPatient')
}

function statusLabel(s: Appointment['status']): string {
  return t(`appointments.status.${s}`, s)
}

function statusColor(s: Appointment['status']): 'neutral' | 'primary' | 'success' | 'warning' | 'error' | 'info' {
  switch (s) {
    case 'scheduled': return 'neutral'
    case 'confirmed': return 'info'
    case 'checked_in': return 'warning'
    case 'in_treatment': return 'primary'
    case 'completed': return 'success'
    case 'cancelled': return 'neutral'
    case 'no_show': return 'error'
    default: return 'neutral'
  }
}

function shiftDay(days: number) {
  const next = new Date(props.currentDate)
  next.setDate(next.getDate() + days)
  emit('date-change', next)
}

function selectDay(d: Date) {
  if (!isSameDay(d, props.currentDate)) emit('date-change', new Date(d))
}

function isToday(d: Date): boolean {
  return isSameDay(d, new Date())
}

function createNow() {
  emit('create-at', new Date(props.currentDate))
}
</script>

<template>
  <div class="flex flex-col h-full w-full min-w-0">
    <!-- Sticky header: date nav + week strip -->
    <div class="sticky top-0 z-20 bg-surface border-b border-subtle">
      <div class="flex items-center justify-between px-3 py-2">
        <UButton
          variant="ghost"
          color="neutral"
          size="sm"
          icon="i-lucide-chevron-left"
          :aria-label="t('common.previous', 'Anterior')"
          @click="shiftDay(-1)"
        />
        <button
          type="button"
          class="text-ui text-default capitalize px-3 py-1 rounded-token-md hover:bg-surface-muted"
          @click="emit('date-change', new Date())"
        >
          {{ formatHeaderDate(currentDate) }}
        </button>
        <UButton
          variant="ghost"
          color="neutral"
          size="sm"
          icon="i-lucide-chevron-right"
          :aria-label="t('common.next', 'Siguiente')"
          @click="shiftDay(1)"
        />
      </div>

      <!-- 7-day strip -->
      <div class="grid grid-cols-7 gap-1 px-2 pb-2">
        <button
          v-for="d in weekDays"
          :key="d.toISOString()"
          type="button"
          class="flex flex-col items-center gap-1 py-2 rounded-token-md transition-colors"
          :class="[
            isSameDay(d, currentDate)
              ? 'bg-[var(--color-primary-soft)] text-[var(--color-primary-soft-text)]'
              : 'text-muted hover:bg-surface-muted',
            isToday(d) && !isSameDay(d, currentDate) ? 'ring-1 ring-[var(--color-primary)]' : ''
          ]"
          @click="selectDay(d)"
        >
          <span class="text-caption uppercase">{{ formatWeekdayShort(d) }}</span>
          <span class="text-ui tnum font-medium">{{ d.getDate() }}</span>
          <span
            v-if="countForDay(d) > 0"
            class="text-[10px] leading-none px-1.5 py-0.5 rounded-full bg-[var(--color-primary)] text-white tnum"
          >
            {{ countForDay(d) }}
          </span>
          <span v-else class="h-[14px]" />
        </button>
      </div>
    </div>

    <!-- Appointment list -->
    <div class="flex-1 overflow-y-auto pb-24">
      <div v-if="isLoading" class="p-6 flex justify-center">
        <UIcon
          name="i-lucide-loader-2"
          class="w-8 h-8 animate-spin"
          :style="{ color: 'var(--color-primary)' }"
        />
      </div>

      <div
        v-else-if="dayAppointments.length === 0"
        class="p-6 flex flex-col items-center gap-3 text-center"
      >
        <UIcon name="i-lucide-calendar-x" class="w-10 h-10 text-subtle" />
        <p class="text-ui text-muted">
          {{ t('appointments.emptyDay', 'No hay citas este día') }}
        </p>
        <UButton
          color="primary"
          variant="soft"
          icon="i-lucide-plus"
          @click="createNow"
        >
          {{ t('appointments.create') }}
        </UButton>
      </div>

      <ul v-else class="divide-y divide-subtle">
        <li
          v-for="apt in dayAppointments"
          :key="apt.id"
        >
          <button
            type="button"
            class="w-full flex items-start gap-3 px-3 py-3 text-left hover:bg-surface-muted transition-colors"
            :class="{ 'bg-[var(--color-primary-soft)]/30': apt.id === highlightedAppointmentId }"
            @click="emit('appointment-click', apt)"
          >
            <!-- Time column -->
            <div class="flex flex-col items-end shrink-0 w-14 pt-0.5">
              <span class="text-ui font-medium text-default tnum">
                {{ formatTime(apt.start_time) }}
              </span>
              <span class="text-caption text-subtle tnum">
                {{ minutesBetween(apt.start_time, apt.end_time) }}m
              </span>
            </div>

            <!-- Colored accent based on professional -->
            <span
              class="w-1 self-stretch rounded-full shrink-0"
              :style="{ backgroundColor: professionalFor(apt.professional_id)?.color || 'var(--color-primary)' }"
            />

            <!-- Body -->
            <div class="flex-1 min-w-0 flex flex-col gap-1">
              <div class="flex items-center gap-2 min-w-0">
                <span class="text-ui text-default truncate font-medium">
                  {{ patientName(apt) }}
                </span>
              </div>
              <div class="flex items-center gap-2 flex-wrap text-caption text-subtle">
                <span
                  v-if="professionalFor(apt.professional_id)"
                  class="inline-flex items-center gap-1"
                >
                  <span
                    class="inline-flex items-center justify-center w-4 h-4 rounded-full text-[9px] text-white font-medium"
                    :style="{ backgroundColor: professionalFor(apt.professional_id)?.color }"
                  >
                    {{ professionalInitials(professionalFor(apt.professional_id)!) }}
                  </span>
                  <span class="truncate">
                    {{ professionalFor(apt.professional_id)?.first_name }}
                    {{ professionalFor(apt.professional_id)?.last_name }}
                  </span>
                </span>
                <span v-if="apt.cabinet" class="inline-flex items-center gap-1">
                  <UIcon name="i-lucide-door-open" class="w-3 h-3" />
                  {{ apt.cabinet }}
                </span>
              </div>
            </div>

            <UBadge
              :color="statusColor(apt.status)"
              variant="soft"
              size="sm"
              class="shrink-0"
            >
              {{ statusLabel(apt.status) }}
            </UBadge>
          </button>
        </li>
      </ul>
    </div>

    <!-- FAB: create appointment -->
    <UButton
      class="fixed right-4 z-30 shadow-lg"
      :style="{ bottom: 'calc(1rem + env(safe-area-inset-bottom))' }"
      color="primary"
      size="lg"
      icon="i-lucide-plus"
      :aria-label="t('appointments.create')"
      @click="createNow"
    />
  </div>
</template>
