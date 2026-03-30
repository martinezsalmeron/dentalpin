<script setup lang="ts">
import type { Appointment } from '~/types'

const { t } = useI18n()
const toast = useToast()
const clinic = useClinic()
const { appointments, isLoading, fetchAppointments, updateAppointment } = useAppointments()

// Week state
const currentWeekStart = ref<Date>(getMonday(new Date()))

// Cabinet filter state
const selectedCabinets = ref<string[]>([])

// Initialize selected cabinets when clinic loads
watch(() => clinic.cabinets.value, (cabinets) => {
  if (cabinets.length > 0 && selectedCabinets.value.length === 0) {
    selectedCabinets.value = cabinets.map(c => c.name)
  }
}, { immediate: true })

// Filtered appointments based on selected cabinets
const filteredAppointments = computed(() => {
  if (selectedCabinets.value.length === 0) return appointments.value
  return appointments.value.filter(apt => selectedCabinets.value.includes(apt.cabinet))
})

// Cabinet filter options
const cabinetFilterOptions = computed(() => {
  return clinic.cabinets.value.map(cab => ({
    label: cab.name,
    value: cab.name,
    color: cab.color
  }))
})

// Toggle cabinet filter
function toggleCabinet(cabinetName: string) {
  const index = selectedCabinets.value.indexOf(cabinetName)
  if (index === -1) {
    selectedCabinets.value.push(cabinetName)
  } else {
    selectedCabinets.value.splice(index, 1)
  }
}

// Select all cabinets
function selectAllCabinets() {
  selectedCabinets.value = clinic.cabinets.value.map(c => c.name)
}

// Modal state
const isModalOpen = ref(false)
const selectedAppointment = ref<Appointment | null>(null)
const initialDate = ref<Date | undefined>()
const initialTime = ref<string | undefined>()

// Get Monday of the current week
function getMonday(date: Date): Date {
  const d = new Date(date)
  const day = d.getDay()
  const diff = day === 0 ? -6 : 1 - day
  d.setDate(d.getDate() + diff)
  d.setHours(0, 0, 0, 0)
  return d
}

// Get week end (Sunday)
function getWeekEnd(start: Date): Date {
  const end = new Date(start)
  end.setDate(end.getDate() + 6)
  end.setHours(23, 59, 59, 999)
  return end
}

// Load appointments for current week
async function loadWeekAppointments() {
  const start = currentWeekStart.value
  const end = getWeekEnd(start)
  await fetchAppointments(start, end)
}

// Handle week change
async function handleWeekChange(newStart: Date) {
  currentWeekStart.value = newStart
  await loadWeekAppointments()
}

// Handle slot click - open modal for new appointment
function handleSlotClick(date: Date, time: string) {
  selectedAppointment.value = null
  initialDate.value = date
  initialTime.value = time
  isModalOpen.value = true
}

// Handle appointment click - open modal for edit
function handleAppointmentClick(appointment: Appointment) {
  selectedAppointment.value = appointment
  initialDate.value = undefined
  initialTime.value = undefined
  isModalOpen.value = true
}

// Handle modal save
async function handleSaved() {
  await loadWeekAppointments()
}

// Handle appointment cancelled
async function handleCancelled() {
  await loadWeekAppointments()
}

// Handle appointment move (drag to different day/time)
async function handleAppointmentMove(appointmentId: string, newDate: string, newStartTime: string, newEndTime: string) {
  try {
    await updateAppointment(appointmentId, {
      start_time: `${newDate}T${newStartTime}:00`,
      end_time: `${newDate}T${newEndTime}:00`
    })
    toast.add({
      title: t('common.success'),
      description: t('appointments.updated'),
      color: 'success'
    })
    await loadWeekAppointments()
  } catch (error: unknown) {
    const fetchError = error as { statusCode?: number }
    if (fetchError.statusCode === 409) {
      toast.add({
        title: t('common.error'),
        description: t('appointments.conflict'),
        color: 'error'
      })
    } else {
      toast.add({
        title: t('common.error'),
        description: t('common.serverError'),
        color: 'error'
      })
    }
    await loadWeekAppointments() // Refresh to reset visual state
  }
}

// Handle appointment resize (change duration)
async function handleAppointmentResize(appointmentId: string, newEndTime: string) {
  const appointment = appointments.value.find(a => a.id === appointmentId)
  if (!appointment) return

  const date = appointment.start_time.split('T')[0]

  try {
    await updateAppointment(appointmentId, {
      end_time: `${date}T${newEndTime}:00`
    })
    toast.add({
      title: t('common.success'),
      description: t('appointments.updated'),
      color: 'success'
    })
    await loadWeekAppointments()
  } catch (error: unknown) {
    const fetchError = error as { statusCode?: number }
    if (fetchError.statusCode === 409) {
      toast.add({
        title: t('common.error'),
        description: t('appointments.conflict'),
        color: 'error'
      })
    } else {
      toast.add({
        title: t('common.error'),
        description: t('common.serverError'),
        color: 'error'
      })
    }
    await loadWeekAppointments() // Refresh to reset visual state
  }
}

// Open create modal from header button
function openCreateModal() {
  selectedAppointment.value = null
  initialDate.value = new Date()
  initialTime.value = '09:00'
  isModalOpen.value = true
}

// Load initial data
onMounted(async () => {
  await loadWeekAppointments()
})
</script>

<template>
  <div class="h-full flex flex-col space-y-4">
    <!-- Page header -->
    <div class="flex items-center justify-between flex-shrink-0">
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
        {{ t('appointments.title') }}
      </h1>
      <UButton
        icon="i-lucide-plus"
        @click="openCreateModal"
      >
        {{ t('appointments.create') }}
      </UButton>
    </div>

    <!-- Cabinet filters -->
    <div
      v-if="cabinetFilterOptions.length > 0"
      class="flex items-center gap-2 flex-shrink-0"
    >
      <span class="text-sm text-gray-500 dark:text-gray-400">
        {{ t('appointments.cabinet') }}:
      </span>
      <div class="flex items-center gap-2">
        <button
          v-for="cabinet in cabinetFilterOptions"
          :key="cabinet.value"
          class="flex items-center gap-1.5 px-2 py-1 rounded-md text-sm font-medium transition-all"
          :class="selectedCabinets.includes(cabinet.value)
            ? 'ring-2 ring-offset-1 ring-gray-400 dark:ring-gray-500'
            : 'opacity-40 hover:opacity-70'"
          @click="toggleCabinet(cabinet.value)"
        >
          <span
            class="w-3 h-3 rounded-full"
            :style="{ backgroundColor: cabinet.color }"
          />
          {{ cabinet.label }}
        </button>
      </div>
      <UButton
        v-if="selectedCabinets.length < cabinetFilterOptions.length"
        variant="ghost"
        color="neutral"
        size="xs"
        @click="selectAllCabinets"
      >
        {{ t('common.selectAll') }}
      </UButton>
    </div>

    <!-- Calendar -->
    <div class="flex-1 min-h-0">
      <AppointmentCalendar
        :appointments="filteredAppointments"
        :cabinets="clinic.cabinets.value"
        :current-week-start="currentWeekStart"
        :is-loading="isLoading"
        @slot-click="handleSlotClick"
        @appointment-click="handleAppointmentClick"
        @week-change="handleWeekChange"
        @appointment-move="handleAppointmentMove"
        @appointment-resize="handleAppointmentResize"
      />
    </div>

    <!-- Appointment Modal -->
    <AppointmentModal
      v-model:open="isModalOpen"
      :appointment="selectedAppointment"
      :initial-date="initialDate"
      :initial-time="initialTime"
      @saved="handleSaved"
      @cancelled="handleCancelled"
    />
  </div>
</template>
