<script setup lang="ts">
import type { Patient, PatientUpdate, Appointment, PaginatedResponse } from '~/types'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const api = useApi()
const toast = useToast()

const patientId = route.params.id as string

// Fetch patient
const { data: patient, status, refresh } = await useAsyncData(
  `patient:${patientId}`,
  async () => {
    try {
      return await api.get<Patient>(
        `/api/v1/clinical/patients/${patientId}`
      )
    } catch (error: unknown) {
      const fetchError = error as { statusCode?: number }
      if (fetchError.statusCode === 404) {
        throw createError({
          statusCode: 404,
          message: t('patients.notFound')
        })
      }
      throw error
    }
  }
)

// Fetch patient appointments
const { data: appointmentsData, status: appointmentsStatus } = await useAsyncData(
  `patient:${patientId}:appointments`,
  async () => {
    try {
      return await api.get<PaginatedResponse<Appointment>>(
        `/api/v1/clinical/appointments?patient_id=${patientId}`
      )
    } catch {
      return { data: [], total: 0, page: 1, page_size: 20 }
    }
  }
)

const appointments = computed(() => appointmentsData.value?.data || [])

// Tabs
const activeTab = ref('info')
const tabs = [
  { key: 'info', label: t('patientDetail.tabs.info'), icon: 'i-lucide-user' },
  { key: 'history', label: t('patientDetail.tabs.history'), icon: 'i-lucide-file-text' },
  { key: 'appointments', label: t('patientDetail.tabs.appointments'), icon: 'i-lucide-calendar' }
]

// Edit mode
const isEditing = ref(false)
const isSubmitting = ref(false)
const editForm = reactive<PatientUpdate>({
  first_name: '',
  last_name: '',
  phone: '',
  email: '',
  date_of_birth: '',
  notes: ''
})

function startEditing() {
  if (patient.value) {
    editForm.first_name = patient.value.first_name
    editForm.last_name = patient.value.last_name
    editForm.phone = patient.value.phone || ''
    editForm.email = patient.value.email || ''
    editForm.date_of_birth = patient.value.date_of_birth || ''
    editForm.notes = patient.value.notes || ''
  }
  isEditing.value = true
}

function cancelEditing() {
  isEditing.value = false
}

async function savePatient() {
  isSubmitting.value = true

  try {
    await api.put(
      `/api/v1/clinical/patients/${patientId}`,
      {
        first_name: editForm.first_name,
        last_name: editForm.last_name,
        phone: editForm.phone || null,
        email: editForm.email || null,
        date_of_birth: editForm.date_of_birth || null,
        notes: editForm.notes || null
      }
    )

    toast.add({
      title: t('common.success'),
      description: t('patients.updated'),
      color: 'success'
    })

    isEditing.value = false
    await refresh()
  } catch (error: unknown) {
    const fetchError = error as { statusCode?: number, data?: { message?: string } }

    toast.add({
      title: t('common.error'),
      description: fetchError.data?.message || t('common.serverError'),
      color: 'error'
    })
  } finally {
    isSubmitting.value = false
  }
}

// Archive patient
const isArchiveModalOpen = ref(false)

async function archivePatient() {
  isSubmitting.value = true

  try {
    await api.del(`/api/v1/clinical/patients/${patientId}`)

    toast.add({
      title: t('common.success'),
      description: t('patients.archived'),
      color: 'success'
    })

    await router.push('/patients')
  } catch (error: unknown) {
    const fetchError = error as { statusCode?: number, data?: { message?: string } }

    toast.add({
      title: t('common.error'),
      description: fetchError.data?.message || t('common.serverError'),
      color: 'error'
    })
  } finally {
    isSubmitting.value = false
    isArchiveModalOpen.value = false
  }
}

// Format date
function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('es-ES', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  })
}

function formatDateTime(dateStr: string): string {
  return new Date(dateStr).toLocaleString('es-ES', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// Status badge color
type BadgeColor = 'success' | 'warning' | 'neutral' | 'error' | 'info' | 'primary' | 'secondary'

function getStatusColor(status: string): BadgeColor {
  switch (status) {
    case 'scheduled':
      return 'info'
    case 'confirmed':
      return 'success'
    case 'in_progress':
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
</script>

<template>
  <div class="space-y-6">
    <!-- Loading state -->
    <div
      v-if="status === 'pending'"
      class="space-y-4"
    >
      <USkeleton class="h-8 w-48" />
      <USkeleton class="h-64 w-full" />
    </div>

    <!-- Patient content -->
    <template v-else-if="patient">
      <!-- Page header -->
      <div class="flex items-center gap-4">
        <UButton
          variant="ghost"
          color="neutral"
          icon="i-lucide-arrow-left"
          to="/patients"
        />
        <div class="flex-1">
          <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
            {{ patient.first_name }} {{ patient.last_name }}
          </h1>
        </div>
        <UButton
          v-if="!isEditing"
          variant="outline"
          color="neutral"
          icon="i-lucide-archive"
          @click="isArchiveModalOpen = true"
        >
          {{ t('patients.archive') }}
        </UButton>
      </div>

      <!-- Tabs -->
      <UTabs
        v-model="activeTab"
        :items="tabs"
      />

      <!-- Tab content -->
      <UCard>
        <!-- Info tab -->
        <div v-if="activeTab === 'info'">
          <!-- View mode -->
          <div
            v-if="!isEditing"
            class="space-y-6"
          >
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label class="text-sm font-medium text-gray-500 dark:text-gray-400">
                  {{ t('patients.firstName') }}
                </label>
                <p class="text-gray-900 dark:text-white">
                  {{ patient.first_name }}
                </p>
              </div>

              <div>
                <label class="text-sm font-medium text-gray-500 dark:text-gray-400">
                  {{ t('patients.lastName') }}
                </label>
                <p class="text-gray-900 dark:text-white">
                  {{ patient.last_name }}
                </p>
              </div>

              <div>
                <label class="text-sm font-medium text-gray-500 dark:text-gray-400">
                  {{ t('patients.phone') }}
                </label>
                <p class="text-gray-900 dark:text-white">
                  {{ patient.phone || '-' }}
                </p>
              </div>

              <div>
                <label class="text-sm font-medium text-gray-500 dark:text-gray-400">
                  {{ t('patients.email') }}
                </label>
                <p class="text-gray-900 dark:text-white">
                  {{ patient.email || '-' }}
                </p>
              </div>

              <div>
                <label class="text-sm font-medium text-gray-500 dark:text-gray-400">
                  {{ t('patients.dateOfBirth') }}
                </label>
                <p class="text-gray-900 dark:text-white">
                  {{ patient.date_of_birth ? formatDate(patient.date_of_birth) : '-' }}
                </p>
              </div>

              <div>
                <label class="text-sm font-medium text-gray-500 dark:text-gray-400">
                  {{ t('patients.status') }}
                </label>
                <p class="text-gray-900 dark:text-white">
                  {{ t(`patients.status${patient.status.charAt(0).toUpperCase() + patient.status.slice(1)}`) }}
                </p>
              </div>
            </div>

            <div>
              <label class="text-sm font-medium text-gray-500 dark:text-gray-400">
                {{ t('patients.notes') }}
              </label>
              <p class="text-gray-900 dark:text-white whitespace-pre-wrap">
                {{ patient.notes || '-' }}
              </p>
            </div>

            <div class="flex justify-end">
              <UButton
                icon="i-lucide-pencil"
                @click="startEditing"
              >
                {{ t('common.edit') }}
              </UButton>
            </div>
          </div>

          <!-- Edit mode -->
          <form
            v-else
            class="space-y-4"
            @submit.prevent="savePatient"
          >
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <UFormField
                :label="t('patients.firstName')"
                required
              >
                <UInput
                  v-model="editForm.first_name"
                  required
                />
              </UFormField>

              <UFormField
                :label="t('patients.lastName')"
                required
              >
                <UInput
                  v-model="editForm.last_name"
                  required
                />
              </UFormField>

              <UFormField :label="t('patients.phone')">
                <UInput
                  v-model="editForm.phone"
                  type="tel"
                />
              </UFormField>

              <UFormField :label="t('patients.email')">
                <UInput
                  v-model="editForm.email"
                  type="email"
                />
              </UFormField>

              <UFormField :label="t('patients.dateOfBirth')">
                <UInput
                  v-model="editForm.date_of_birth"
                  type="date"
                />
              </UFormField>
            </div>

            <UFormField :label="t('patients.notes')">
              <UTextarea
                v-model="editForm.notes"
                :rows="4"
              />
            </UFormField>

            <div class="flex justify-end gap-3">
              <UButton
                variant="outline"
                color="neutral"
                @click="cancelEditing"
              >
                {{ t('common.cancel') }}
              </UButton>
              <UButton
                type="submit"
                :loading="isSubmitting"
                :disabled="!editForm.first_name || !editForm.last_name"
              >
                {{ t('common.save') }}
              </UButton>
            </div>
          </form>
        </div>

        <!-- History tab -->
        <div
          v-else-if="activeTab === 'history'"
          class="text-center py-12"
        >
          <UIcon
            name="i-lucide-file-text"
            class="w-12 h-12 text-gray-400 mx-auto mb-4"
          />
          <p class="text-gray-500 dark:text-gray-400">
            {{ t('patientDetail.historyPlaceholder') }}
          </p>
        </div>

        <!-- Appointments tab -->
        <div v-else-if="activeTab === 'appointments'">
          <!-- Loading -->
          <div
            v-if="appointmentsStatus === 'pending'"
            class="space-y-3"
          >
            <USkeleton
              v-for="i in 3"
              :key="i"
              class="h-12 w-full"
            />
          </div>

          <!-- Empty state -->
          <div
            v-else-if="appointments.length === 0"
            class="text-center py-12"
          >
            <UIcon
              name="i-lucide-calendar"
              class="w-12 h-12 text-gray-400 mx-auto mb-4"
            />
            <p class="text-gray-500 dark:text-gray-400 mb-4">
              {{ t('patientDetail.noAppointments') }}
            </p>
            <UButton
              to="/appointments"
              icon="i-lucide-plus"
            >
              {{ t('patientDetail.scheduleAppointment') }}
            </UButton>
          </div>

          <!-- Appointments list -->
          <ul
            v-else
            class="divide-y divide-gray-200 dark:divide-gray-800"
          >
            <li
              v-for="appointment in appointments"
              :key="appointment.id"
              class="py-4 flex items-center justify-between"
            >
              <div>
                <p class="font-medium text-gray-900 dark:text-white">
                  {{ formatDateTime(appointment.start_time) }}
                </p>
                <p class="text-sm text-gray-500 dark:text-gray-400">
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
        </div>
      </UCard>
    </template>

    <!-- Archive confirmation modal -->
    <UModal v-model:open="isArchiveModalOpen">
      <template #content>
        <UCard>
          <template #header>
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white">
              {{ t('patients.archiveConfirm', { name: `${patient?.first_name} ${patient?.last_name}` }) }}
            </h2>
          </template>

          <p class="text-gray-500 dark:text-gray-400">
            {{ t('patients.archiveDescription') }}
          </p>

          <template #footer>
            <div class="flex justify-end gap-3">
              <UButton
                variant="outline"
                color="neutral"
                @click="isArchiveModalOpen = false"
              >
                {{ t('patients.cancel') }}
              </UButton>
              <UButton
                color="error"
                :loading="isSubmitting"
                @click="archivePatient"
              >
                {{ t('patients.archive') }}
              </UButton>
            </div>
          </template>
        </UCard>
      </template>
    </UModal>
  </div>
</template>
