<script setup lang="ts">
import type { Appointment, AppointmentCreate, Patient } from '~/types'

const props = defineProps<{
  open: boolean
  appointment?: Appointment | null
  initialDate?: Date
  initialTime?: string
  initialProfessionalId?: string
  existingAppointments?: Appointment[]
}>()

const emit = defineEmits<{
  'update:open': [value: boolean]
  'saved': [appointment: Appointment]
  'cancelled': [appointmentId: string]
}>()

const { t } = useI18n()
const toast = useToast()
const auth = useAuth()
const clinic = useClinic()
const { createAppointment, updateAppointment, cancelAppointment } = useAppointments()
const { professionals, fetchProfessionals, getProfessionalColor } = useProfessionals()

// Format date as YYYY-MM-DD in local timezone (not UTC)
function formatLocalDate(date: Date): string {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

// Form state
const isSubmitting = ref(false)
const selectedPatient = ref<Patient | null>(null)
const selectedProfessionalId = ref<string>('')
const formData = reactive({
  date: '',
  startTime: '09:00',
  duration: 30,
  cabinet: '',
  treatmentType: '',
  notes: ''
})

// Duration options
const durationOptions = [
  { value: 15, label: '15 min' },
  { value: 30, label: '30 min' },
  { value: 45, label: '45 min' },
  { value: 60, label: '60 min' },
  { value: 90, label: '90 min' },
  { value: 120, label: '120 min' }
]

// Cabinet options from clinic
const cabinetOptions = computed(() => {
  return clinic.cabinets.value.map(cab => ({
    value: cab.name,
    label: cab.name
  }))
})

// Professional options
const professionalOptions = computed(() => {
  return professionals.value.map(prof => ({
    value: prof.id,
    label: `${prof.first_name} ${prof.last_name}`,
    color: getProfessionalColor(prof.id)
  }))
})

// Computed
const isEditMode = computed(() => !!props.appointment)
const modalTitle = computed(() =>
  isEditMode.value ? t('appointments.edit') : t('appointments.create')
)

const canSave = computed(() => {
  return selectedPatient.value && formData.date && formData.startTime && formData.cabinet && selectedProfessionalId.value
})

// Check for overlapping appointments
const overlappingAppointments = computed(() => {
  if (!formData.date || !formData.startTime || !props.existingAppointments || props.existingAppointments.length === 0) {
    return { sameProfessional: [], sameCabinet: [] }
  }

  // Parse form time as minutes from midnight for comparison
  const formTimeParts = formData.startTime.split(':').map(Number)
  const formStartMinutes = (formTimeParts[0] ?? 0) * 60 + (formTimeParts[1] ?? 0)
  const formEndMinutes = formStartMinutes + formData.duration

  const sameProfessional: Appointment[] = []
  const sameCabinet: Appointment[] = []

  for (const apt of props.existingAppointments) {
    // Skip the current appointment being edited
    if (props.appointment && apt.id === props.appointment.id) continue
    // Skip cancelled appointments
    if (apt.status === 'cancelled') continue

    // Check if same date (compare date strings directly)
    const aptDate = apt.start_time.split('T')[0]
    if (aptDate !== formData.date) continue

    // Parse appointment times as minutes from midnight
    const aptStartTime = apt.start_time.split('T')[1]?.substring(0, 5) ?? '00:00'
    const aptEndTime = apt.end_time.split('T')[1]?.substring(0, 5) ?? '00:00'

    const aptStartParts = aptStartTime.split(':').map(Number)
    const aptEndParts = aptEndTime.split(':').map(Number)

    const aptStartMinutes = (aptStartParts[0] ?? 0) * 60 + (aptStartParts[1] ?? 0)
    const aptEndMinutes = (aptEndParts[0] ?? 0) * 60 + (aptEndParts[1] ?? 0)

    // Check if times overlap
    const overlaps = formStartMinutes < aptEndMinutes && formEndMinutes > aptStartMinutes

    if (overlaps) {
      if (apt.professional_id === selectedProfessionalId.value) {
        sameProfessional.push(apt)
      }
      if (apt.cabinet === formData.cabinet) {
        sameCabinet.push(apt)
      }
    }
  }

  return { sameProfessional, sameCabinet }
})

// Check if there are any overlaps
const hasOverlap = computed(() => {
  return overlappingAppointments.value.sameProfessional.length > 0 ||
         overlappingAppointments.value.sameCabinet.length > 0
})

// Track if we've already shown the overlap warning for current config
const lastOverlapWarningKey = ref('')

// Show toast when overlap is detected
watch(overlappingAppointments, (overlaps) => {
  const hasProfessionalOverlap = overlaps.sameProfessional.length > 0
  const hasCabinetOverlap = overlaps.sameCabinet.length > 0

  if (!hasProfessionalOverlap && !hasCabinetOverlap) {
    lastOverlapWarningKey.value = ''
    return
  }

  // Create a key to avoid showing the same warning repeatedly
  const warningKey = `${formData.date}-${formData.startTime}-${formData.duration}-${selectedProfessionalId.value}-${formData.cabinet}`

  if (warningKey === lastOverlapWarningKey.value) return
  lastOverlapWarningKey.value = warningKey

  // Build warning message
  const warnings: string[] = []
  if (hasProfessionalOverlap) {
    warnings.push(t('appointments.overlapProfessional', { count: overlaps.sameProfessional.length }))
  }
  if (hasCabinetOverlap) {
    warnings.push(t('appointments.overlapCabinet', { count: overlaps.sameCabinet.length }))
  }

  toast.add({
    title: t('appointments.overlapWarning'),
    description: warnings.join('. '),
    color: 'warning',
    icon: 'i-lucide-alert-triangle'
  })
}, { deep: true })

// Watch for initial values
watch(() => props.open, async (isOpen) => {
  if (isOpen) {
    // Fetch professionals when modal opens
    await fetchProfessionals()

    if (props.appointment) {
      // Edit mode - populate from appointment
      const apt = props.appointment
      selectedPatient.value = apt.patient || null
      selectedProfessionalId.value = apt.professional_id
      formData.date = apt.start_time.split('T')[0] ?? ''
      formData.startTime = apt.start_time.split('T')[1]?.substring(0, 5) ?? '09:00'
      formData.cabinet = apt.cabinet
      formData.treatmentType = apt.treatment_type || ''
      formData.notes = apt.notes || ''

      // Calculate duration from start/end time
      const start = new Date(apt.start_time)
      const end = new Date(apt.end_time)
      const calculatedDuration = Math.round((end.getTime() - start.getTime()) / 60000)

      // Round to nearest valid option (15, 30, 45, 60, 90, 120)
      const validDurations = [15, 30, 45, 60, 90, 120]
      formData.duration = validDurations.reduce((prev, curr) =>
        Math.abs(curr - calculatedDuration) < Math.abs(prev - calculatedDuration) ? curr : prev
      )
    } else {
      // Create mode - use initial values
      if (props.initialDate) {
        formData.date = formatLocalDate(props.initialDate)
      } else {
        formData.date = formatLocalDate(new Date())
      }

      if (props.initialTime) {
        formData.startTime = props.initialTime
      } else {
        formData.startTime = '09:00'
      }

      // Set professional - use initialProfessionalId, current user if professional, or first available
      if (props.initialProfessionalId) {
        selectedProfessionalId.value = props.initialProfessionalId
      } else {
        // Check if current user is a professional
        const currentUserId = auth.user.value?.id
        const isCurrentUserProfessional = professionals.value.some(p => p.id === currentUserId)
        if (isCurrentUserProfessional && currentUserId) {
          selectedProfessionalId.value = currentUserId
        } else {
          selectedProfessionalId.value = professionals.value[0]?.id || ''
        }
      }

      // Reset other fields
      selectedPatient.value = null
      formData.duration = clinic.slotDuration.value || 30
      formData.cabinet = clinic.cabinets.value[0]?.name || ''
      formData.treatmentType = ''
      formData.notes = ''
    }
  }
})

// Calculate end time from start time and duration
function calculateEndTime(): string {
  const timeParts = formData.startTime.split(':').map(Number)
  const startHours = timeParts[0] ?? 9
  const startMinutes = timeParts[1] ?? 0

  // Add duration in minutes
  const totalMinutes = startHours * 60 + startMinutes + formData.duration
  const endHours = Math.floor(totalMinutes / 60) % 24
  const endMinutes = totalMinutes % 60

  // Build end time string in same format as start time
  const endTimeStr = `${endHours.toString().padStart(2, '0')}:${endMinutes.toString().padStart(2, '0')}`

  return `${formData.date}T${endTimeStr}:00`
}

async function handleSave() {
  if (!canSave.value || !selectedPatient.value) return

  isSubmitting.value = true

  try {
    // Build start_time ISO string
    const startTime = `${formData.date}T${formData.startTime}:00`

    const appointmentData: AppointmentCreate = {
      patient_id: selectedPatient.value.id,
      professional_id: selectedProfessionalId.value,
      cabinet: formData.cabinet,
      start_time: startTime,
      end_time: calculateEndTime(),
      treatment_type: formData.treatmentType || undefined,
      notes: formData.notes || undefined
    }

    let savedAppointment: Appointment

    if (isEditMode.value && props.appointment) {
      savedAppointment = await updateAppointment(props.appointment.id, appointmentData)
      toast.add({
        title: t('common.success'),
        description: t('appointments.updated'),
        color: 'success'
      })
    } else {
      savedAppointment = await createAppointment(appointmentData)
      toast.add({
        title: t('common.success'),
        description: t('appointments.created'),
        color: 'success'
      })
    }

    emit('saved', savedAppointment)
    emit('update:open', false)
  } catch (error: unknown) {
    const fetchError = error as { statusCode?: number, data?: { message?: string, detail?: string } }

    if (fetchError.statusCode === 409) {
      toast.add({
        title: t('common.error'),
        description: t('appointments.conflict'),
        color: 'error'
      })
    } else {
      toast.add({
        title: t('common.error'),
        description: fetchError.data?.detail || fetchError.data?.message || t('common.serverError'),
        color: 'error'
      })
    }
  } finally {
    isSubmitting.value = false
  }
}

async function handleCancel() {
  if (!props.appointment) return

  isSubmitting.value = true

  try {
    await cancelAppointment(props.appointment.id)
    toast.add({
      title: t('common.success'),
      description: t('appointments.cancelled'),
      color: 'success'
    })
    emit('cancelled', props.appointment.id)
    emit('update:open', false)
  } catch {
    toast.add({
      title: t('common.error'),
      description: t('common.serverError'),
      color: 'error'
    })
  } finally {
    isSubmitting.value = false
  }
}

function closeModal() {
  emit('update:open', false)
}
</script>

<template>
  <UModal
    :open="open"
    @update:open="$emit('update:open', $event)"
  >
    <template #content>
      <UCard>
        <template #header>
          <div class="flex items-center justify-between">
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white">
              {{ modalTitle }}
            </h2>
            <UButton
              variant="ghost"
              color="neutral"
              icon="i-lucide-x"
              @click="closeModal"
            />
          </div>
        </template>

        <form
          class="space-y-4"
          @submit.prevent="handleSave"
        >
          <!-- Patient search -->
          <UFormField
            :label="t('appointments.selectPatient')"
            required
          >
            <PatientSearch v-model="selectedPatient" />
          </UFormField>

          <!-- Date and Time -->
          <div class="grid grid-cols-2 gap-4">
            <UFormField
              :label="t('appointments.date')"
              required
            >
              <UInput
                v-model="formData.date"
                type="date"
                required
              />
            </UFormField>

            <UFormField
              :label="t('appointments.startTime')"
              required
            >
              <UInput
                v-model="formData.startTime"
                type="time"
                required
              />
            </UFormField>
          </div>

          <!-- Duration and Cabinet -->
          <div class="grid grid-cols-2 gap-4">
            <UFormField :label="t('appointments.duration')">
              <USelect
                v-model="formData.duration"
                :items="durationOptions"
                value-key="value"
                label-key="label"
              />
            </UFormField>

            <UFormField
              :label="t('appointments.cabinet')"
              required
            >
              <USelect
                v-model="formData.cabinet"
                :items="cabinetOptions"
                value-key="value"
                label-key="label"
                :placeholder="t('appointments.cabinet')"
              />
            </UFormField>
          </div>

          <!-- Professional -->
          <UFormField
            :label="t('appointments.professional')"
            required
          >
            <USelect
              v-model="selectedProfessionalId"
              :items="professionalOptions"
              value-key="value"
              label-key="label"
              :placeholder="t('appointments.selectProfessional')"
            />
          </UFormField>

          <!-- Treatment type -->
          <UFormField :label="t('appointments.treatmentType')">
            <UInput
              v-model="formData.treatmentType"
              :placeholder="t('appointments.treatmentType')"
            />
          </UFormField>

          <!-- Notes -->
          <UFormField :label="t('appointments.notes')">
            <UTextarea
              v-model="formData.notes"
              :placeholder="t('appointments.notes')"
              :rows="3"
            />
          </UFormField>
        </form>

        <template #footer>
          <div class="flex justify-between">
            <div>
              <UButton
                v-if="isEditMode && appointment?.status !== 'cancelled'"
                variant="outline"
                color="error"
                :loading="isSubmitting"
                @click="handleCancel"
              >
                {{ t('appointments.cancel') }}
              </UButton>
            </div>
            <div class="flex gap-3">
              <UButton
                variant="outline"
                color="neutral"
                @click="closeModal"
              >
                {{ t('common.cancel') }}
              </UButton>
              <UButton
                :loading="isSubmitting"
                :disabled="!canSave"
                @click="handleSave"
              >
                {{ t('common.save') }}
              </UButton>
            </div>
          </div>
        </template>
      </UCard>
    </template>
  </UModal>
</template>
