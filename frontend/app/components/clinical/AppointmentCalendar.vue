<script setup lang="ts">
import type { Appointment, Professional } from '~/types'

interface Cabinet {
  name: string
  color: string
}

interface ProfessionalWithColor extends Professional {
  color: string
}

const props = defineProps<{
  appointments: Appointment[]
  cabinets?: Cabinet[]
  professionals?: ProfessionalWithColor[]
  currentWeekStart: Date
  isLoading?: boolean
}>()

const emit = defineEmits<{
  'slot-click': [date: Date, time: string]
  'slot-drag-create': [date: Date, startTime: string, endTime: string]
  'appointment-click': [appointment: Appointment]
  'week-change': [weekStart: Date]
  'appointment-move': [appointmentId: string, newDate: string, newStartTime: string, newEndTime: string]
  'appointment-resize': [appointmentId: string, newEndTime: string]
}>()

const { t, locale } = useI18n()

// Format date as YYYY-MM-DD in local timezone (not UTC)
function formatLocalDate(date: Date): string {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

// Time slots configuration
const START_HOUR = 8
const END_HOUR = 21
const SLOT_MINUTES = 15
const SLOTS_PER_HOUR = 60 / SLOT_MINUTES
const SLOT_HEIGHT = 24 // pixels per slot (h-6)

// Drag state
const dragState = ref<{
  type: 'move' | 'resize' | null
  appointmentId: string | null
  startY: number
  startX: number
  originalTop: number
  originalHeight: number
  originalDayIndex: number
  currentDayIndex: number
  currentTop: number
  currentHeight: number
} | null>(null)

// Create drag state (drag on empty slot to define duration)
const createDragState = ref<{
  date: Date
  dayIndex: number
  startSlot: number
  currentSlot: number
  startY: number
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

// Generate days of the week
const weekDays = computed(() => {
  const days: Date[] = []
  for (let i = 0; i < 7; i++) {
    const day = new Date(props.currentWeekStart)
    day.setDate(day.getDate() + i)
    days.push(day)
  }
  return days
})

// Format day header
function formatDayHeader(date: Date): string {
  const dayName = date.toLocaleDateString(locale.value, { weekday: 'short' })
  const dayNum = date.getDate()
  return `${dayName} ${dayNum}`
}

// Check if date is today
function isToday(date: Date): boolean {
  const today = new Date()
  return date.toDateString() === today.toDateString()
}

// Navigate weeks
function prevWeek() {
  const newStart = new Date(props.currentWeekStart)
  newStart.setDate(newStart.getDate() - 7)
  emit('week-change', newStart)
}

function nextWeek() {
  const newStart = new Date(props.currentWeekStart)
  newStart.setDate(newStart.getDate() + 7)
  emit('week-change', newStart)
}

function goToToday() {
  const today = new Date()
  const dayOfWeek = today.getDay()
  const diff = dayOfWeek === 0 ? -6 : 1 - dayOfWeek // Monday as start
  const monday = new Date(today)
  monday.setDate(today.getDate() + diff)
  monday.setHours(0, 0, 0, 0)
  emit('week-change', monday)
}

// Calculate appointment position and height
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

function getAppointmentStyle(appointment: Appointment): Record<string, string> {
  // Check if this appointment is being dragged
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

// Get the day index for drag preview
function getAppointmentDayIndex(appointment: Appointment): number {
  if (dragState.value?.appointmentId === appointment.id && dragState.value.type === 'move') {
    return dragState.value.currentDayIndex
  }
  const aptDate = appointment.start_time.split('T')[0]
  return weekDays.value.findIndex(d => formatLocalDate(d) === aptDate)
}

// Get cabinet color
function getCabinetColor(cabinetName: string): string {
  const cabinet = props.cabinets?.find(c => c.name === cabinetName)
  return cabinet?.color || '#6B7280' // Default gray
}

// Get professional by ID
function getProfessional(professionalId: string): ProfessionalWithColor | undefined {
  return props.professionals?.find(p => p.id === professionalId)
}

// Get professional initials
function getProfessionalInitials(professionalId: string): string {
  const prof = getProfessional(professionalId)
  if (!prof) return '?'
  const first = prof.first_name.charAt(0).toUpperCase()
  const last = prof.last_name.charAt(0).toUpperCase()
  return `${first}${last}`
}

// Get professional color
function getProfessionalColor(professionalId: string): string {
  const prof = getProfessional(professionalId)
  return prof?.color || '#6B7280'
}

// Get professional full name
function getProfessionalFullName(professionalId: string): string {
  const prof = getProfessional(professionalId)
  if (!prof) return 'Desconocido'
  return `${prof.first_name} ${prof.last_name}`
}

// Get appointment style with cabinet color
function getAppointmentColorStyle(appointment: Appointment): Record<string, string> {
  const color = getCabinetColor(appointment.cabinet)
  return {
    '--cabinet-color': color,
    'borderLeftColor': color,
    'borderLeftWidth': '4px'
  }
}

// Get status-based styling
function getStatusClass(status: Appointment['status']): string {
  const baseClass = 'bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700'

  switch (status) {
    case 'scheduled':
      return `${baseClass} text-gray-800 dark:text-gray-200`
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
    case 'confirmed':
      return 'i-lucide-check'
    case 'in_progress':
      return 'i-lucide-play'
    case 'completed':
      return 'i-lucide-check-check'
    case 'cancelled':
      return 'i-lucide-x'
    case 'no_show':
      return 'i-lucide-user-x'
    default:
      return ''
  }
}

// Handle drag-to-create on empty slot
function startCreateDrag(date: Date, timeSlot: string, dayIndex: number, event: MouseEvent) {
  if (dragState.value) return
  event.preventDefault()

  const startSlot = getSlotIndex(timeSlot)
  createDragState.value = {
    date,
    dayIndex,
    startSlot,
    currentSlot: startSlot,
    startY: event.clientY
  }

  document.addEventListener('mousemove', handleDragMove)
  document.addEventListener('mouseup', handleDragEnd)
}

// Handle appointment click
function handleAppointmentClick(appointment: Appointment, event: Event) {
  if (dragState.value || wasDragging.value) return // Don't trigger click during/after drag
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
  const aptDate = appointment.start_time.split('T')[0]
  const dayIndex = weekDays.value.findIndex(d => formatLocalDate(d) === aptDate)

  dragState.value = {
    type,
    appointmentId: appointment.id,
    startY: event.clientY,
    startX: event.clientX,
    originalTop: startSlot * SLOT_HEIGHT,
    originalHeight: Math.max(1, endSlot - startSlot) * SLOT_HEIGHT,
    originalDayIndex: dayIndex,
    currentDayIndex: dayIndex,
    currentTop: startSlot * SLOT_HEIGHT,
    currentHeight: Math.max(1, endSlot - startSlot) * SLOT_HEIGHT
  }

  document.addEventListener('mousemove', handleDragMove)
  document.addEventListener('mouseup', handleDragEnd)
}

function handleDragMove(event: MouseEvent) {
  if (createDragState.value) {
    const deltaY = event.clientY - createDragState.value.startY
    const slotDelta = Math.floor(deltaY / SLOT_HEIGHT)
    const maxSlot = (END_HOUR - START_HOUR) * SLOTS_PER_HOUR - 1
    createDragState.value.currentSlot = Math.max(
      createDragState.value.startSlot,
      Math.min(maxSlot, createDragState.value.startSlot + slotDelta)
    )
    return
  }

  if (!dragState.value) return

  const deltaY = event.clientY - dragState.value.startY
  const deltaX = event.clientX - dragState.value.startX

  // Detect if there was significant movement (more than 5 pixels)
  if (Math.abs(deltaY) > 5 || Math.abs(deltaX) > 5) {
    hasMoved.value = true
  }

  if (dragState.value.type === 'resize') {
    // Resize: change height
    const newHeight = Math.max(SLOT_HEIGHT, dragState.value.originalHeight + deltaY)
    // Snap to slot boundaries
    const slots = Math.round(newHeight / SLOT_HEIGHT)
    dragState.value.currentHeight = slots * SLOT_HEIGHT
  } else if (dragState.value.type === 'move') {
    // Move: change position and potentially day
    const newTop = Math.max(0, dragState.value.originalTop + deltaY)
    // Snap to slot boundaries
    const slots = Math.round(newTop / SLOT_HEIGHT)
    const maxSlots = (END_HOUR - START_HOUR) * SLOTS_PER_HOUR - Math.round(dragState.value.currentHeight / SLOT_HEIGHT)
    dragState.value.currentTop = Math.min(slots, maxSlots) * SLOT_HEIGHT

    // Calculate day change based on horizontal movement
    // Estimate column width (calendar width / 8 columns, first is time)
    if (calendarRef.value) {
      const calendarWidth = calendarRef.value.offsetWidth
      const columnWidth = calendarWidth / 8
      const dayDelta = Math.round(deltaX / columnWidth)
      const newDayIndex = Math.max(0, Math.min(6, dragState.value.originalDayIndex + dayDelta))
      dragState.value.currentDayIndex = newDayIndex
    }
  }
}

function handleDragEnd() {
  document.removeEventListener('mousemove', handleDragMove)
  document.removeEventListener('mouseup', handleDragEnd)

  if (createDragState.value) {
    const { date, startSlot, currentSlot } = createDragState.value
    createDragState.value = null
    const startTime = slotIndexToTime(startSlot)
    if (currentSlot > startSlot) {
      emit('slot-drag-create', date, startTime, slotIndexToTime(currentSlot + 1))
    } else {
      emit('slot-click', date, startTime)
    }
    return
  }

  // Only set flag if there was actual movement
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
    // Calculate new end time
    const startTime = appointment.start_time.split('T')[1]?.substring(0, 5) ?? '08:00'
    const startSlot = getSlotIndex(startTime)
    const newEndSlot = startSlot + Math.round(dragState.value.currentHeight / SLOT_HEIGHT)
    const newEndTime = slotIndexToTime(newEndSlot)

    // Only emit if changed
    const oldEndTime = appointment.end_time.split('T')[1]?.substring(0, 5) ?? ''
    if (newEndTime !== oldEndTime) {
      emit('appointment-resize', dragState.value.appointmentId, newEndTime)
    }
  } else if (dragState.value.type === 'move') {
    // Calculate new date and times
    const newStartSlot = Math.round(dragState.value.currentTop / SLOT_HEIGHT)
    const durationSlots = Math.round(dragState.value.currentHeight / SLOT_HEIGHT)
    const newEndSlot = newStartSlot + durationSlots

    const newStartTime = slotIndexToTime(newStartSlot)
    const newEndTime = slotIndexToTime(newEndSlot)
    const dayAtIndex = weekDays.value[dragState.value.currentDayIndex]
    const newDate = dayAtIndex ? formatLocalDate(dayAtIndex) : ''

    // Only emit if changed
    const oldDate = appointment.start_time.split('T')[0]
    const oldStartTime = appointment.start_time.split('T')[1]?.substring(0, 5) ?? ''

    if (newDate !== oldDate || newStartTime !== oldStartTime) {
      emit('appointment-move', dragState.value.appointmentId, newDate, newStartTime, newEndTime)
    }
  }

  dragState.value = null
}

// Format week range for header
const weekRangeText = computed(() => {
  const start = props.currentWeekStart
  const end = new Date(start)
  end.setDate(end.getDate() + 6)

  const startStr = start.toLocaleDateString(locale.value, { month: 'short', day: 'numeric' })
  const endStr = end.toLocaleDateString(locale.value, { month: 'short', day: 'numeric', year: 'numeric' })

  return `${startStr} - ${endStr}`
})

// Check if two appointments overlap in time
function appointmentsOverlap(apt1: Appointment, apt2: Appointment): boolean {
  const start1 = new Date(apt1.start_time).getTime()
  const end1 = new Date(apt1.end_time).getTime()
  const start2 = new Date(apt2.start_time).getTime()
  const end2 = new Date(apt2.end_time).getTime()

  return start1 < end2 && end1 > start2
}

// Group overlapping appointments and calculate their positions
function calculateOverlapGroups(dayAppointments: Appointment[]): Map<string, { index: number, total: number }> {
  const result = new Map<string, { index: number, total: number }>()

  if (dayAppointments.length === 0) return result

  // Sort by start time
  const sorted = [...dayAppointments].sort((a, b) =>
    new Date(a.start_time).getTime() - new Date(b.start_time).getTime()
  )

  // Find all overlapping groups
  const groups: Appointment[][] = []

  for (const apt of sorted) {
    // Find a group this appointment overlaps with
    let addedToGroup = false

    for (const group of groups) {
      // Check if this appointment overlaps with any in the group
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
        // Check if any appointment in group i overlaps with any in group j
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

  // Assign positions within each group
  for (const group of groups) {
    const total = group.length
    // Sort by start time within group for consistent positioning
    group.sort((a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime())

    group.forEach((apt, index) => {
      result.set(apt.id, { index, total })
    })
  }

  return result
}

// Computed overlap positions for all days
const overlapPositions = computed(() => {
  const positions = new Map<string, { index: number, total: number }>()

  for (let dayIndex = 0; dayIndex < 7; dayIndex++) {
    const day = weekDays.value[dayIndex]
    if (!day) continue

    const dateStr = formatLocalDate(day)
    const dayAppointments = props.appointments.filter((apt) => {
      if (apt.status === 'cancelled') return false
      const aptDate = apt.start_time.split('T')[0]
      return aptDate === dateStr
    })

    const dayPositions = calculateOverlapGroups(dayAppointments)
    dayPositions.forEach((pos, id) => positions.set(id, pos))
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

// All appointments flat for drag preview rendering
const allAppointmentsWithDayIndex = computed(() => {
  return props.appointments
    .filter(apt => apt.status !== 'cancelled')
    .map(apt => ({
      appointment: apt,
      dayIndex: getAppointmentDayIndex(apt)
    }))
    .filter(item => item.dayIndex >= 0 && item.dayIndex < 7)
})
</script>

<template>
  <div class="flex flex-col h-full">
    <!-- Calendar header -->
    <div class="flex items-center justify-between mb-4 flex-shrink-0">
      <div class="flex items-center gap-2">
        <UButton
          variant="outline"
          color="neutral"
          icon="i-lucide-chevron-left"
          @click="prevWeek"
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
          @click="nextWeek"
        />
      </div>

      <h2 class="text-lg font-semibold text-gray-900 dark:text-white">
        {{ weekRangeText }}
      </h2>
    </div>

    <!-- Loading overlay -->
    <div
      v-if="isLoading"
      class="flex items-center justify-center py-12"
    >
      <UIcon
        name="i-lucide-loader-2"
        class="w-8 h-8 animate-spin text-primary-500"
      />
    </div>

    <!-- Calendar grid -->
    <div
      v-else
      ref="calendarRef"
      class="flex-1 overflow-auto border border-gray-200 dark:border-gray-700 rounded-lg"
    >
      <div class="min-w-[800px]">
        <!-- Day headers -->
        <div class="grid grid-cols-8 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 sticky top-0 z-10">
          <!-- Time column header -->
          <div class="p-2 text-center text-xs font-medium text-gray-500 dark:text-gray-400 border-r border-gray-200 dark:border-gray-700">
            <!-- Empty -->
          </div>

          <!-- Day headers -->
          <div
            v-for="day in weekDays"
            :key="day.toISOString()"
            class="p-2 text-center border-r border-gray-200 dark:border-gray-700 last:border-r-0"
            :class="{ 'bg-primary-50 dark:bg-primary-900/20': isToday(day) }"
          >
            <span
              class="text-sm font-medium"
              :class="isToday(day) ? 'text-primary-600 dark:text-primary-400' : 'text-gray-900 dark:text-white'"
            >
              {{ formatDayHeader(day) }}
            </span>
          </div>
        </div>

        <!-- Time rows -->
        <div class="relative">
          <!-- Hour markers and grid -->
          <div
            v-for="(slot, slotIndex) in timeSlots"
            :key="slot"
            class="grid grid-cols-8 border-b border-gray-100 dark:border-gray-800"
            :class="{ 'border-gray-200 dark:border-gray-700': slotIndex % SLOTS_PER_HOUR === 0 }"
          >
            <!-- Time label (only show on hour marks) -->
            <div class="p-1 text-right border-r border-gray-200 dark:border-gray-700 h-6 flex items-center justify-end pr-2">
              <span
                v-if="slotIndex % SLOTS_PER_HOUR === 0"
                class="text-xs text-gray-500 dark:text-gray-400"
              >
                {{ slot }}
              </span>
            </div>

            <!-- Day columns -->
            <div
              v-for="(day, dayIdx) in weekDays"
              :key="`${day.toISOString()}-${slot}`"
              class="h-6 border-r border-gray-100 dark:border-gray-800 last:border-r-0 cursor-cell hover:bg-primary-50/40 dark:hover:bg-primary-900/10 transition-colors relative"
              :class="{
                'bg-primary-50/30 dark:bg-primary-900/10': isToday(day),
                'border-gray-200 dark:border-gray-700': slotIndex % SLOTS_PER_HOUR === 0
              }"
              @mousedown="startCreateDrag(day, slot, dayIdx, $event)"
            />
          </div>

          <!-- Appointments overlay -->
          <div class="absolute inset-0 pointer-events-none">
            <div class="grid grid-cols-8 h-full">
              <!-- Time column spacer -->
              <div class="border-r border-gray-200 dark:border-gray-700" />

              <!-- Day columns with appointments -->
              <div
                v-for="(day, dayIndex) in weekDays"
                :key="`appointments-${day.toISOString()}`"
                class="relative border-r border-gray-100 dark:border-gray-800 last:border-r-0"
              >
                <!-- Ghost block during drag-to-create -->
                <div
                  v-if="createDragState && createDragState.dayIndex === dayIndex"
                  class="absolute left-1 right-1 rounded border-2 border-dashed border-primary-500 bg-primary-100/60 dark:bg-primary-900/30 pointer-events-none z-40 flex items-start p-1"
                  :style="{
                    top: `${createDragState.startSlot * SLOT_HEIGHT}px`,
                    height: `${Math.max(1, createDragState.currentSlot - createDragState.startSlot + 1) * SLOT_HEIGHT}px`,
                    minHeight: `${SLOT_HEIGHT}px`
                  }"
                >
                  <span
                    v-if="createDragState.currentSlot > createDragState.startSlot"
                    class="text-xs text-primary-700 dark:text-primary-300 font-medium leading-none"
                  >
                    {{ slotIndexToTime(createDragState.startSlot) }} – {{ slotIndexToTime(createDragState.currentSlot + 1) }}
                  </span>
                </div>

                <div
                  v-for="{ appointment } in allAppointmentsWithDayIndex.filter(a => a.dayIndex === dayIndex)"
                  :key="appointment.id"
                  class="absolute rounded overflow-hidden pointer-events-auto select-none shadow-sm"
                  :class="[
                    getStatusClass(appointment.status),
                    dragState?.appointmentId === appointment.id ? 'cursor-grabbing ring-2 ring-primary-500' : 'cursor-grab hover:ring-2 hover:ring-primary-500'
                  ]"
                  :style="{ ...getAppointmentStyle(appointment), ...getAppointmentColorStyle(appointment), ...getOverlapStyle(appointment) }"
                  @click="handleAppointmentClick(appointment, $event)"
                  @mousedown="startDrag(appointment, $event, 'move')"
                >
                  <!-- Content -->
                  <div class="px-1.5 h-full flex flex-col py-0.5 relative">
                    <!-- Professional badge -->
                    <div
                      v-if="professionals && professionals.length > 0"
                      class="absolute top-0.5 right-0.5 w-5 h-5 rounded-full flex items-center justify-center text-white text-[10px] font-bold shadow-sm"
                      :style="{ backgroundColor: getProfessionalColor(appointment.professional_id) }"
                      :title="getProfessionalFullName(appointment.professional_id)"
                    >
                      {{ getProfessionalInitials(appointment.professional_id) }}
                    </div>
                    <div class="flex items-center gap-1 min-h-[18px] pr-5">
                      <UIcon
                        v-if="getStatusIcon(appointment.status)"
                        :name="getStatusIcon(appointment.status)"
                        class="w-3 h-3 flex-shrink-0"
                      />
                      <span class="text-xs font-medium truncate">
                        {{ appointment.patient ? `${appointment.patient.last_name}` : 'Sin paciente' }}
                      </span>
                    </div>
                    <div
                      v-if="appointment.treatment_type || appointment.cabinet"
                      class="text-xs opacity-60 truncate"
                    >
                      {{ appointment.cabinet }}{{ appointment.treatment_type ? ` · ${appointment.treatment_type}` : '' }}
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
