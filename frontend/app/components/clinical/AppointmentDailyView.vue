<script setup lang="ts">
import type { Appointment, Professional } from '~/types'

interface ProfessionalWithColor extends Professional {
  color: string
}

const props = defineProps<{
  appointments: Appointment[]
  professionals: ProfessionalWithColor[]
  currentDate: Date
  isLoading?: boolean
}>()

const emit = defineEmits<{
  'slot-click': [professionalId: string, time: string]
  'appointment-click': [appointment: Appointment]
  'date-change': [date: Date]
  'appointment-move': [appointmentId: string, newProfessionalId: string, newStartTime: string, newEndTime: string]
  'appointment-resize': [appointmentId: string, newEndTime: string]
}>()

const { t, locale } = useI18n()

// Format date as YYYY-MM-DD in local timezone
function formatLocalDate(date: Date): string {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

// Time slots configuration (same as weekly view)
const START_HOUR = 8
const END_HOUR = 21
const SLOT_MINUTES = 15
const SLOTS_PER_HOUR = 60 / SLOT_MINUTES
const SLOT_HEIGHT = 24

// Drag state
const dragState = ref<{
  type: 'move' | 'resize' | null
  appointmentId: string | null
  startY: number
  startX: number
  originalTop: number
  originalHeight: number
  originalProfessionalIndex: number
  currentProfessionalIndex: number
  currentTop: number
  currentHeight: number
} | null>(null)

const calendarRef = ref<HTMLElement | null>(null)
const wasDragging = ref(false)
const hasMoved = ref(false)

// Generate time slots
const timeSlots = computed(() => {
  const slots: string[] = []
  for (let hour = START_HOUR; hour < END_HOUR; hour++) {
    for (let quarter = 0; quarter < SLOTS_PER_HOUR; quarter++) {
      const minutes = quarter * SLOT_MINUTES
      slots.push(`${hour.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`)
    }
  }
  return slots
})

// Format date for header
const formattedDate = computed(() => {
  return props.currentDate.toLocaleDateString(locale.value, {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
})

// Check if current date is today
const isToday = computed(() => {
  const today = new Date()
  return props.currentDate.toDateString() === today.toDateString()
})

// Navigate days
function prevDay() {
  const newDate = new Date(props.currentDate)
  newDate.setDate(newDate.getDate() - 1)
  emit('date-change', newDate)
}

function nextDay() {
  const newDate = new Date(props.currentDate)
  newDate.setDate(newDate.getDate() + 1)
  emit('date-change', newDate)
}

function goToToday() {
  emit('date-change', new Date())
}

// Calculate slot index from time string
function getSlotIndex(timeStr: string): number {
  const parts = timeStr.split(':').map(Number)
  const hours = parts[0] ?? 0
  const minutes = parts[1] ?? 0
  return (hours - START_HOUR) * SLOTS_PER_HOUR + Math.floor(minutes / SLOT_MINUTES)
}

function slotIndexToTime(slotIndex: number): string {
  const totalMinutes = START_HOUR * 60 + slotIndex * SLOT_MINUTES
  const hours = Math.floor(totalMinutes / 60)
  const minutes = totalMinutes % 60
  return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`
}

// Get appointment style
function getAppointmentStyle(appointment: Appointment): Record<string, string> {
  if (dragState.value?.appointmentId === appointment.id) {
    return {
      top: `${dragState.value.currentTop}px`,
      height: `${dragState.value.currentHeight}px`,
      minHeight: '24px',
      opacity: '0.8',
      zIndex: '50'
    }
  }

  const startTime = appointment.start_time.split('T')[1]?.substring(0, 5) ?? '08:00'
  const endTime = appointment.end_time.split('T')[1]?.substring(0, 5) ?? '08:15'

  const startSlot = getSlotIndex(startTime)
  const endSlot = getSlotIndex(endTime)
  const spanSlots = Math.max(1, endSlot - startSlot)

  const height = spanSlots * SLOT_HEIGHT
  const topOffset = startSlot * SLOT_HEIGHT

  return {
    top: `${topOffset}px`,
    height: `${height}px`,
    minHeight: '24px'
  }
}

// Get professional index for appointment (considering drag)
function getAppointmentProfessionalIndex(appointment: Appointment): number {
  if (dragState.value?.appointmentId === appointment.id && dragState.value.type === 'move') {
    return dragState.value.currentProfessionalIndex
  }
  return props.professionals.findIndex(p => p.id === appointment.professional_id)
}

// Status styling
function getStatusClass(status: Appointment['status']): string {
  const baseClass = 'bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700'
  switch (status) {
    case 'scheduled':
    case 'confirmed':
      return `${baseClass} text-gray-800 dark:text-gray-200`
    case 'in_progress':
      return `${baseClass} text-gray-800 dark:text-gray-200 animate-pulse`
    case 'completed':
      return `${baseClass} text-gray-500 dark:text-gray-400 opacity-60`
    case 'cancelled':
      return `${baseClass} text-gray-500 dark:text-gray-400 line-through opacity-50`
    case 'no_show':
      return `${baseClass} text-gray-500 dark:text-gray-400 opacity-60`
    default:
      return baseClass
  }
}

function getStatusIcon(status: Appointment['status']): string {
  switch (status) {
    case 'confirmed': return 'i-lucide-check'
    case 'in_progress': return 'i-lucide-play'
    case 'completed': return 'i-lucide-check-check'
    case 'cancelled': return 'i-lucide-x'
    case 'no_show': return 'i-lucide-user-x'
    default: return ''
  }
}

// Handle slot click
function handleSlotClick(professionalId: string, timeSlot: string) {
  if (dragState.value) return
  emit('slot-click', professionalId, timeSlot)
}

// Handle appointment click
function handleAppointmentClick(appointment: Appointment, event: Event) {
  if (dragState.value || wasDragging.value) return
  event.stopPropagation()
  emit('appointment-click', appointment)
}

// Drag handlers
function startDrag(appointment: Appointment, event: MouseEvent, type: 'move' | 'resize') {
  event.preventDefault()
  event.stopPropagation()

  const startTime = appointment.start_time.split('T')[1]?.substring(0, 5) ?? '08:00'
  const endTime = appointment.end_time.split('T')[1]?.substring(0, 5) ?? '08:15'
  const startSlot = getSlotIndex(startTime)
  const endSlot = getSlotIndex(endTime)
  const professionalIndex = props.professionals.findIndex(p => p.id === appointment.professional_id)

  dragState.value = {
    type,
    appointmentId: appointment.id,
    startY: event.clientY,
    startX: event.clientX,
    originalTop: startSlot * SLOT_HEIGHT,
    originalHeight: Math.max(1, endSlot - startSlot) * SLOT_HEIGHT,
    originalProfessionalIndex: professionalIndex,
    currentProfessionalIndex: professionalIndex,
    currentTop: startSlot * SLOT_HEIGHT,
    currentHeight: Math.max(1, endSlot - startSlot) * SLOT_HEIGHT
  }

  document.addEventListener('mousemove', handleDragMove)
  document.addEventListener('mouseup', handleDragEnd)
}

function handleDragMove(event: MouseEvent) {
  if (!dragState.value) return

  const deltaY = event.clientY - dragState.value.startY
  const deltaX = event.clientX - dragState.value.startX

  if (Math.abs(deltaY) > 5 || Math.abs(deltaX) > 5) {
    hasMoved.value = true
  }

  if (dragState.value.type === 'resize') {
    const newHeight = Math.max(SLOT_HEIGHT, dragState.value.originalHeight + deltaY)
    const slots = Math.round(newHeight / SLOT_HEIGHT)
    dragState.value.currentHeight = slots * SLOT_HEIGHT
  } else if (dragState.value.type === 'move') {
    const newTop = Math.max(0, dragState.value.originalTop + deltaY)
    const slots = Math.round(newTop / SLOT_HEIGHT)
    const maxSlots = (END_HOUR - START_HOUR) * SLOTS_PER_HOUR - Math.round(dragState.value.currentHeight / SLOT_HEIGHT)
    dragState.value.currentTop = Math.min(slots, maxSlots) * SLOT_HEIGHT

    // Calculate professional change
    if (calendarRef.value && props.professionals.length > 1) {
      const calendarWidth = calendarRef.value.offsetWidth
      const columnWidth = calendarWidth / (props.professionals.length + 1) // +1 for time column
      const profDelta = Math.round(deltaX / columnWidth)
      const newProfIndex = Math.max(0, Math.min(props.professionals.length - 1, dragState.value.originalProfessionalIndex + profDelta))
      dragState.value.currentProfessionalIndex = newProfIndex
    }
  }
}

function handleDragEnd() {
  document.removeEventListener('mousemove', handleDragMove)
  document.removeEventListener('mouseup', handleDragEnd)

  if (hasMoved.value) {
    wasDragging.value = true
    setTimeout(() => {
      wasDragging.value = false
    }, 100)
  }
  hasMoved.value = false

  if (!dragState.value || !dragState.value.appointmentId) {
    dragState.value = null
    return
  }

  const appointment = props.appointments.find(a => a.id === dragState.value?.appointmentId)
  if (!appointment) {
    dragState.value = null
    return
  }

  if (dragState.value.type === 'resize') {
    const startTime = appointment.start_time.split('T')[1]?.substring(0, 5) ?? '08:00'
    const startSlot = getSlotIndex(startTime)
    const newEndSlot = startSlot + Math.round(dragState.value.currentHeight / SLOT_HEIGHT)
    const newEndTime = slotIndexToTime(newEndSlot)

    const oldEndTime = appointment.end_time.split('T')[1]?.substring(0, 5) ?? ''
    if (newEndTime !== oldEndTime) {
      emit('appointment-resize', dragState.value.appointmentId, newEndTime)
    }
  } else if (dragState.value.type === 'move') {
    const newStartSlot = Math.round(dragState.value.currentTop / SLOT_HEIGHT)
    const durationSlots = Math.round(dragState.value.currentHeight / SLOT_HEIGHT)
    const newEndSlot = newStartSlot + durationSlots

    const newStartTime = slotIndexToTime(newStartSlot)
    const newEndTime = slotIndexToTime(newEndSlot)
    const newProfessional = props.professionals[dragState.value.currentProfessionalIndex]

    const oldStartTime = appointment.start_time.split('T')[1]?.substring(0, 5) ?? ''
    const oldProfessionalId = appointment.professional_id

    if (newProfessional && (newStartTime !== oldStartTime || newProfessional.id !== oldProfessionalId)) {
      emit('appointment-move', dragState.value.appointmentId, newProfessional.id, newStartTime, newEndTime)
    }
  }

  dragState.value = null
}

// Check if two appointments overlap in time
function appointmentsOverlap(apt1: Appointment, apt2: Appointment): boolean {
  const start1 = new Date(apt1.start_time).getTime()
  const end1 = new Date(apt1.end_time).getTime()
  const start2 = new Date(apt2.start_time).getTime()
  const end2 = new Date(apt2.end_time).getTime()

  return start1 < end2 && end1 > start2
}

// Group overlapping appointments and calculate their positions
function calculateOverlapGroups(profAppointments: Appointment[]): Map<string, { index: number, total: number }> {
  const result = new Map<string, { index: number, total: number }>()

  if (profAppointments.length === 0) return result

  const sorted = [...profAppointments].sort((a, b) =>
    new Date(a.start_time).getTime() - new Date(b.start_time).getTime()
  )

  const groups: Appointment[][] = []

  for (const apt of sorted) {
    let addedToGroup = false

    for (const group of groups) {
      const overlapsWithGroup = group.some(existing => appointmentsOverlap(apt, existing))

      if (overlapsWithGroup) {
        group.push(apt)
        addedToGroup = true
        break
      }
    }

    if (!addedToGroup) {
      groups.push([apt])
    }
  }

  // Merge groups that have overlapping appointments
  let merged = true
  while (merged) {
    merged = false
    for (let i = 0; i < groups.length; i++) {
      for (let j = i + 1; j < groups.length; j++) {
        const shouldMerge = groups[i]!.some(apt1 =>
          groups[j]!.some(apt2 => appointmentsOverlap(apt1, apt2))
        )

        if (shouldMerge) {
          groups[i]!.push(...groups[j]!)
          groups.splice(j, 1)
          merged = true
          break
        }
      }
      if (merged) break
    }
  }

  for (const group of groups) {
    const total = group.length
    group.sort((a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime())

    group.forEach((apt, index) => {
      result.set(apt.id, { index, total })
    })
  }

  return result
}

// Computed overlap positions for each professional
const overlapPositions = computed(() => {
  const positions = new Map<string, { index: number, total: number }>()
  const dateStr = formatLocalDate(props.currentDate)

  for (const prof of props.professionals) {
    const profAppointments = props.appointments.filter((apt) => {
      if (apt.status === 'cancelled') return false
      const aptDate = apt.start_time.split('T')[0]
      return aptDate === dateStr && apt.professional_id === prof.id
    })

    const profPositions = calculateOverlapGroups(profAppointments)
    profPositions.forEach((pos, id) => positions.set(id, pos))
  }

  return positions
})

// Get overlap style for an appointment
function getOverlapStyle(appointment: Appointment): Record<string, string> {
  const pos = overlapPositions.value.get(appointment.id)
  if (!pos || pos.total <= 1) {
    return { left: '2px', right: '2px' }
  }

  const widthPercent = 100 / pos.total
  const leftPercent = pos.index * widthPercent

  return {
    left: `calc(${leftPercent}% + 1px)`,
    width: `calc(${widthPercent}% - 2px)`,
    right: 'auto'
  }
}

// All appointments for current date
const allAppointmentsWithProfIndex = computed(() => {
  const dateStr = formatLocalDate(props.currentDate)
  return props.appointments
    .filter((apt) => {
      const aptDate = apt.start_time.split('T')[0]
      return aptDate === dateStr && apt.status !== 'cancelled'
    })
    .map(apt => ({
      appointment: apt,
      profIndex: getAppointmentProfessionalIndex(apt)
    }))
    .filter(item => item.profIndex >= 0)
})
</script>

<template>
  <div class="flex flex-col h-full">
    <!-- Header -->
    <div class="flex items-center justify-between mb-4 flex-shrink-0">
      <div class="flex items-center gap-2">
        <UButton
          variant="outline"
          color="neutral"
          icon="i-lucide-chevron-left"
          @click="prevDay"
        />
        <UButton
          variant="outline"
          color="neutral"
          @click="goToToday"
        >
          {{ t('appointments.today') }}
        </UButton>
        <UButton
          variant="outline"
          color="neutral"
          icon="i-lucide-chevron-right"
          @click="nextDay"
        />
      </div>

      <h2
        class="text-lg font-semibold capitalize"
        :class="isToday ? 'text-primary-600 dark:text-primary-400' : 'text-gray-900 dark:text-white'"
      >
        {{ formattedDate }}
      </h2>
    </div>

    <!-- Loading -->
    <div
      v-if="isLoading"
      class="flex items-center justify-center py-12"
    >
      <UIcon
        name="i-lucide-loader-2"
        class="w-8 h-8 animate-spin text-primary-500"
      />
    </div>

    <!-- No professionals message -->
    <div
      v-else-if="professionals.length === 0"
      class="flex items-center justify-center py-12 text-gray-500"
    >
      {{ t('appointments.noProfessionals') }}
    </div>

    <!-- Calendar grid -->
    <div
      v-else
      ref="calendarRef"
      class="flex-1 overflow-auto border border-gray-200 dark:border-gray-700 rounded-lg"
    >
      <div
        class="min-w-[600px]"
        :style="{ minWidth: `${200 * professionals.length + 80}px` }"
      >
        <!-- Professional headers -->
        <div
          class="grid border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 sticky top-0 z-10"
          :style="{ gridTemplateColumns: `80px repeat(${professionals.length}, 1fr)` }"
        >
          <!-- Time column header -->
          <div class="p-2 text-center text-xs font-medium text-gray-500 dark:text-gray-400 border-r border-gray-200 dark:border-gray-700" />

          <!-- Professional headers -->
          <div
            v-for="prof in professionals"
            :key="prof.id"
            class="p-2 text-center border-r border-gray-200 dark:border-gray-700 last:border-r-0"
          >
            <div class="flex items-center justify-center gap-2">
              <span
                class="w-6 h-6 rounded-full flex items-center justify-center text-white text-xs font-bold"
                :style="{ backgroundColor: prof.color }"
              >
                {{ prof.first_name.charAt(0) }}{{ prof.last_name.charAt(0) }}
              </span>
              <span class="text-sm font-medium text-gray-900 dark:text-white">
                {{ prof.first_name }} {{ prof.last_name }}
              </span>
            </div>
          </div>
        </div>

        <!-- Time rows -->
        <div class="relative">
          <!-- Grid -->
          <div
            v-for="(slot, slotIndex) in timeSlots"
            :key="slot"
            class="grid border-b border-gray-100 dark:border-gray-800"
            :class="{ 'border-gray-200 dark:border-gray-700': slotIndex % SLOTS_PER_HOUR === 0 }"
            :style="{ gridTemplateColumns: `80px repeat(${professionals.length}, 1fr)` }"
          >
            <!-- Time label -->
            <div class="p-1 text-right border-r border-gray-200 dark:border-gray-700 h-6 flex items-center justify-end pr-2">
              <span
                v-if="slotIndex % SLOTS_PER_HOUR === 0"
                class="text-xs text-gray-500 dark:text-gray-400"
              >
                {{ slot }}
              </span>
            </div>

            <!-- Professional columns -->
            <div
              v-for="prof in professionals"
              :key="`${prof.id}-${slot}`"
              class="h-6 border-r border-gray-100 dark:border-gray-800 last:border-r-0 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors relative"
              :class="{ 'border-gray-200 dark:border-gray-700': slotIndex % SLOTS_PER_HOUR === 0 }"
              @click="handleSlotClick(prof.id, slot)"
            />
          </div>

          <!-- Appointments overlay -->
          <div class="absolute inset-0 pointer-events-none">
            <div
              class="grid h-full"
              :style="{ gridTemplateColumns: `80px repeat(${professionals.length}, 1fr)` }"
            >
              <!-- Time column spacer -->
              <div class="border-r border-gray-200 dark:border-gray-700" />

              <!-- Professional columns -->
              <div
                v-for="(prof, profIndex) in professionals"
                :key="`appointments-${prof.id}`"
                class="relative border-r border-gray-100 dark:border-gray-800 last:border-r-0"
              >
                <div
                  v-for="{ appointment } in allAppointmentsWithProfIndex.filter(a => a.profIndex === profIndex)"
                  :key="appointment.id"
                  class="absolute rounded overflow-hidden pointer-events-auto select-none shadow-sm border-l-4"
                  :class="[
                    getStatusClass(appointment.status),
                    dragState?.appointmentId === appointment.id ? 'cursor-grabbing ring-2 ring-primary-500' : 'cursor-grab hover:ring-2 hover:ring-primary-500'
                  ]"
                  :style="{ ...getAppointmentStyle(appointment), ...getOverlapStyle(appointment), borderLeftColor: prof.color }"
                  @click="handleAppointmentClick(appointment, $event)"
                  @mousedown="startDrag(appointment, $event, 'move')"
                >
                  <!-- Content -->
                  <div class="px-1.5 h-full flex flex-col py-0.5">
                    <div class="flex items-center gap-1 min-h-[18px]">
                      <UIcon
                        v-if="getStatusIcon(appointment.status)"
                        :name="getStatusIcon(appointment.status)"
                        class="w-3 h-3 flex-shrink-0"
                      />
                      <span class="text-xs font-medium truncate">
                        {{ appointment.patient ? `${appointment.patient.first_name} ${appointment.patient.last_name}` : 'Sin paciente' }}
                      </span>
                    </div>
                    <div
                      v-if="appointment.treatment_type"
                      class="text-xs opacity-60 truncate"
                    >
                      {{ appointment.treatment_type }}
                    </div>
                  </div>

                  <!-- Resize handle -->
                  <div
                    class="absolute bottom-0 left-0 right-0 h-2 cursor-ns-resize hover:bg-black/10 dark:hover:bg-white/10 transition-colors"
                    @mousedown.stop="startDrag(appointment, $event, 'resize')"
                  >
                    <div class="absolute bottom-0.5 left-1/2 -translate-x-1/2 w-8 h-0.5 bg-current opacity-30 rounded" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
