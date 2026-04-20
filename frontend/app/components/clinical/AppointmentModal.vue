<script setup lang="ts">
import type {
  Appointment,
  AppointmentCreate,
  Patient,
  PlannedTreatmentItem,
  Surface
} from '~/types'

const props = defineProps<{
  open: boolean
  appointment?: Appointment | null
  initialDate?: Date
  initialTime?: string
  initialEndTime?: string
  initialProfessionalId?: string
  initialPatientId?: string
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
const api = useApi()
const { createAppointment, updateAppointment, cancelAppointment } = useAppointments()
const { professionals, fetchProfessionals, getProfessionalColor } = useProfessionals()
const { fetchSettings, getAutoSendStatus } = useNotificationSettings()
const { sendConfirmation, sendReminder, isSending: isSendingEmail } = useNotificationSend()

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
const sendConfirmationEmail = ref(true)
const selectedTreatments = ref<PlannedTreatmentItem[]>([])
const formData = reactive({
  date: '',
  startTime: '09:00',
  duration: 30,
  cabinet: '',
  notes: ''
})

// Duration options (in minutes)
const durationOptions = [
  { value: 15, label: '15 min' },
  { value: 30, label: '30 min' },
  { value: 45, label: '45 min' },
  { value: 60, label: '60 min' },
  { value: 90, label: '90 min' },
  { value: 120, label: '120 min' }
]
const validDurations = durationOptions.map(d => d.value)

// Edit mode check
const isEditMode = computed(() => !!props.appointment)

// Auto-update duration based on selected treatments
watch(selectedTreatments, (treatments) => {
  const totalMinutes = treatments.reduce((acc, t) => {
    // Get duration from catalog_item if available
    const duration = t.catalog_item?.default_price ? 30 : 0 // Default 30 min
    return acc + duration
  }, 0)
  if (totalMinutes > 0) {
    formData.duration = validDurations.reduce((prev, curr) =>
      Math.abs(curr - totalMinutes) < Math.abs(prev - totalMinutes) ? curr : prev
    )
  }
})

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
const modalTitle = computed(() =>
  isEditMode.value ? t('appointments.edit') : t('appointments.create')
)

const canSave = computed(() => {
  return selectedPatient.value && formData.date && formData.startTime && formData.cabinet && selectedProfessionalId.value
})

// Email notification computed properties
const autoSendEnabled = computed(() => getAutoSendStatus('appointment_confirmation'))
const patientHasEmail = computed(() => !!selectedPatient.value?.email)
const appointmentPatientHasEmail = computed(() => !!props.appointment?.patient?.email)

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

// Track initial overlaps when modal opens (to avoid warning about pre-existing overlaps)
const initialOverlapIds = ref<{ professional: Set<string>, cabinet: Set<string> }>({
  professional: new Set(),
  cabinet: new Set()
})
// Flag to know when initial data has been loaded
const initialDataLoaded = ref(false)
// Track if we've already shown the overlap warning for current config
const lastOverlapWarningKey = ref('')

// Show toast when NEW overlaps are detected (not pre-existing ones)
watch(overlappingAppointments, (overlaps) => {
  // Don't check until initial data is loaded
  if (!initialDataLoaded.value) return

  // Filter out overlaps that existed when modal opened
  const newProfessionalOverlaps = overlaps.sameProfessional.filter(
    apt => !initialOverlapIds.value.professional.has(apt.id)
  )
  const newCabinetOverlaps = overlaps.sameCabinet.filter(
    apt => !initialOverlapIds.value.cabinet.has(apt.id)
  )

  const hasNewProfessionalOverlap = newProfessionalOverlaps.length > 0
  const hasNewCabinetOverlap = newCabinetOverlaps.length > 0

  if (!hasNewProfessionalOverlap && !hasNewCabinetOverlap) {
    lastOverlapWarningKey.value = ''
    return
  }

  // Create a key to avoid showing the same warning repeatedly
  const warningKey = `${formData.date}-${formData.startTime}-${formData.duration}-${selectedProfessionalId.value}-${formData.cabinet}`

  if (warningKey === lastOverlapWarningKey.value) return
  lastOverlapWarningKey.value = warningKey

  // Build warning message
  const warnings: string[] = []
  if (hasNewProfessionalOverlap) {
    warnings.push(t('appointments.overlapProfessional', { count: newProfessionalOverlaps.length }))
  }
  if (hasNewCabinetOverlap) {
    warnings.push(t('appointments.overlapCabinet', { count: newCabinetOverlaps.length }))
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
    // Reset flags when modal opens
    initialDataLoaded.value = false
    lastOverlapWarningKey.value = ''
    initialOverlapIds.value = { professional: new Set(), cabinet: new Set() }

    // Fetch professionals and notification settings when modal opens
    await Promise.all([fetchProfessionals(), fetchSettings()])

    if (props.appointment) {
      // Edit mode - populate from appointment
      const apt = props.appointment
      selectedPatient.value = apt.patient || null
      selectedProfessionalId.value = apt.professional_id
      formData.date = apt.start_time.split('T')[0] ?? ''
      formData.startTime = apt.start_time.split('T')[1]?.substring(0, 5) ?? '09:00'
      formData.cabinet = apt.cabinet
      formData.notes = apt.notes || ''

      // Map each AppointmentTreatmentBrief into a PlannedTreatmentItem shape so the
      // shared selector can render it. The Treatment.id is not available in the
      // brief, so we leave treatment_id empty; it is only used server-side when
      // submitting, and the selector keys off the PlannedTreatmentItem.id.
      if (apt.treatments && apt.treatments.length > 0) {
        selectedTreatments.value = apt.treatments.map((t): PlannedTreatmentItem => ({
          id: t.planned_item_id,
          clinic_id: apt.clinic_id,
          treatment_plan_id: t.plan_id || '',
          treatment_id: '',
          sequence_order: 0,
          status: t.planned_item_status,
          completed_without_appointment: false,
          completed_at: undefined,
          completed_by: undefined,
          notes: undefined,
          created_at: '',
          updated_at: '',
          treatment: {
            id: '',
            clinical_type: 'crown',
            scope: 'tooth',
            arch: null,
            status: 'planned',
            catalog_item_id: t.catalog_item_id,
            price_snapshot: t.default_price ? String(t.default_price) : null,
            currency_snapshot: 'EUR',
            teeth: t.tooth_number
              ? [{
                  tooth_number: t.tooth_number,
                  role: null,
                  surfaces: (t.surfaces as Surface[] | undefined) ?? null
                }]
              : []
          },
          catalog_item: t.catalog_item_id
            ? {
                id: t.catalog_item_id,
                internal_code: t.internal_code,
                names: t.names,
                default_price: t.default_price != null ? String(t.default_price) : null,
                currency: 'EUR'
              }
            : undefined,
          media: []
        }))
      } else {
        selectedTreatments.value = []
      }

      // Calculate duration from start/end time, rounded to nearest valid option
      const start = new Date(apt.start_time)
      const end = new Date(apt.end_time)
      const calculatedDuration = Math.round((end.getTime() - start.getTime()) / 60000)
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

      // Pre-select patient if initialPatientId provided
      if (props.initialPatientId) {
        try {
          const response = await api.get<{ data: Patient }>(`/api/v1/patients/${props.initialPatientId}`)
          selectedPatient.value = response.data
        } catch {
          selectedPatient.value = null
        }
      } else {
        selectedPatient.value = null
      }
      if (props.initialEndTime) {
        const startParts = formData.startTime.split(':').map(Number)
        const endParts = props.initialEndTime.split(':').map(Number)
        const startMin = (startParts[0] ?? 9) * 60 + (startParts[1] ?? 0)
        const endMin = (endParts[0] ?? 9) * 60 + (endParts[1] ?? 0)
        const draggedMinutes = endMin - startMin
        formData.duration = draggedMinutes > 0
          ? validDurations.reduce((prev, curr) =>
              Math.abs(curr - draggedMinutes) < Math.abs(prev - draggedMinutes) ? curr : prev)
          : clinic.slotDuration.value || 30
      } else {
        formData.duration = clinic.slotDuration.value || 30
      }
      formData.cabinet = clinic.cabinets.value[0]?.name || ''
      formData.notes = ''
      selectedTreatments.value = []
      // Reset email checkbox for create mode
      sendConfirmationEmail.value = true
    }

    // Wait for next tick so overlappingAppointments computed can recalculate
    await nextTick()

    // Capture initial overlaps (these existed before user made changes)
    const currentOverlaps = overlappingAppointments.value
    initialOverlapIds.value = {
      professional: new Set(currentOverlaps.sameProfessional.map(apt => apt.id)),
      cabinet: new Set(currentOverlaps.sameCabinet.map(apt => apt.id))
    }

    // Now enable overlap warnings for new overlaps only
    initialDataLoaded.value = true
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
      planned_item_ids: selectedTreatments.value.length > 0
        ? selectedTreatments.value.map(t => t.id)
        : undefined,
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

      // Send confirmation email if checkbox is checked, auto_send is off, and patient has email
      if (!autoSendEnabled.value && sendConfirmationEmail.value && patientHasEmail.value) {
        await sendConfirmation(savedAppointment.id, savedAppointment.patient_id || '')
      }
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
            <h2 class="text-h1 text-default text-default">
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

        <div class="max-h-[60vh] overflow-y-auto pr-1">
          <form
            class="space-y-4"
            @submit.prevent="handleSave"
          >
            <!-- Patient search -->
            <UFormField
              :label="t('appointments.selectPatient')"
              required
            >
              <PatientVisualSelector
                v-model="selectedPatient"
                in-modal
              />
            </UFormField>

            <!-- Treatments from treatment plan -->
            <UFormField :label="t('appointments.treatments')">
              <PlannedTreatmentSelector
                v-model="selectedTreatments"
                :patient-id="selectedPatient?.id"
              />
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
                  :placeholder="t('appointments.selectDuration')"
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

            <!-- Notes -->
            <UFormField :label="t('appointments.notes')">
              <UTextarea
                v-model="formData.notes"
                :placeholder="t('appointments.notes')"
                :rows="3"
              />
            </UFormField>
          </form>
        </div>

        <template #footer>
          <div class="flex justify-between">
            <div class="flex items-center gap-2">
              <UButton
                v-if="isEditMode && appointment?.status !== 'cancelled'"
                variant="outline"
                color="error"
                :loading="isSubmitting"
                @click="handleCancel"
              >
                {{ t('appointments.cancel') }}
              </UButton>

              <!-- Email dropdown in edit mode -->
              <UDropdownMenu v-if="isEditMode && appointmentPatientHasEmail">
                <UButton
                  variant="outline"
                  icon="i-lucide-mail"
                  :loading="isSendingEmail"
                >
                  {{ t('appointments.sendEmail') }}
                </UButton>
                <template #content>
                  <UDropdownMenuContent>
                    <UDropdownMenuItem
                      icon="i-lucide-check-circle"
                      @click="sendConfirmation(appointment!.id, appointment!.patient_id!)"
                    >
                      {{ t('appointments.resendConfirmation') }}
                    </UDropdownMenuItem>
                    <UDropdownMenuItem
                      icon="i-lucide-clock"
                      @click="sendReminder(appointment!.id, appointment!.patient_id!)"
                    >
                      {{ t('appointments.sendReminderEmail') }}
                    </UDropdownMenuItem>
                  </UDropdownMenuContent>
                </template>
              </UDropdownMenu>
            </div>
            <div class="flex items-center gap-3">
              <!-- Checkbox for sending confirmation when creating -->
              <div
                v-if="!isEditMode && patientHasEmail"
                class="flex items-center gap-2"
              >
                <UCheckbox
                  v-model="sendConfirmationEmail"
                  :disabled="autoSendEnabled"
                />
                <span class="text-sm text-muted">
                  {{ t('appointments.sendConfirmationEmail') }}
                  <span
                    v-if="autoSendEnabled"
                    class="text-xs"
                  >({{ t('appointments.automatic') }})</span>
                </span>
              </div>
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
