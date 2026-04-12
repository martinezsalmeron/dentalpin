<script setup lang="ts">
import type { Patient, PatientUpdate, Appointment, BudgetListItem, PaginatedResponse, ApiResponse } from '~/types'
import { PERMISSIONS } from '~/config/permissions'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const api = useApi()
const toast = useToast()
const { can } = usePermissions()

const patientId = route.params.id as string

// Handle returnTo query param (from invoice edit page)
const returnTo = computed(() => route.query.returnTo as string | undefined)
const openBillingEdit = computed(() => route.query.tab === 'billing')

// Fetch patient
const { data: patient, status, refresh } = await useAsyncData(
  `patient:${patientId}`,
  async () => {
    try {
      const response = await api.get<ApiResponse<Patient>>(
        `/api/v1/clinical/patients/${patientId}`
      )
      return response.data
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

// Fetch patient budgets
const { data: budgetsData, status: budgetsStatus } = await useAsyncData(
  `patient:${patientId}:budgets`,
  async () => {
    try {
      return await api.get<PaginatedResponse<BudgetListItem>>(
        `/api/v1/budget/budgets?patient_id=${patientId}`
      )
    } catch {
      return { data: [], total: 0, page: 1, page_size: 20 }
    }
  }
)

const budgets = computed(() => budgetsData.value?.data || [])

// Tabs - computed to filter by permissions
const activeTab = ref('info')

const tabs = computed(() => {
  const baseTabs = [
    { value: 'info', label: t('patientDetail.tabs.info'), icon: 'i-lucide-user', slot: 'info' }
  ]

  // Add odontogram tab if user has permission
  if (can(PERMISSIONS.odontogram.read)) {
    baseTabs.push({
      value: 'odontogram',
      label: t('patientDetail.tabs.odontogram'),
      icon: 'i-lucide-grid-3x3',
      slot: 'odontogram'
    })
  }

  // Add budgets tab if user has permission
  if (can(PERMISSIONS.budget.read)) {
    baseTabs.push({
      value: 'budgets',
      label: t('patientDetail.tabs.budgets'),
      icon: 'i-lucide-file-text',
      slot: 'budgets'
    })
  }

  baseTabs.push(
    { value: 'history', label: t('patientDetail.tabs.history'), icon: 'i-lucide-history', slot: 'history' },
    { value: 'appointments', label: t('patientDetail.tabs.appointments'), icon: 'i-lucide-calendar', slot: 'appointments' }
  )

  return baseTabs
})

// Check if user can edit odontogram
const canEditOdontogram = computed(() => can(PERMISSIONS.odontogram.write))

// Edit mode
const isEditing = ref(false)
const isSubmitting = ref(false)
const editForm = reactive<PatientUpdate>({
  first_name: '',
  last_name: '',
  phone: '',
  email: '',
  date_of_birth: '',
  notes: '',
  // Billing fields
  billing_name: '',
  billing_tax_id: '',
  billing_email: '',
  billing_address: {
    street: '',
    city: '',
    postal_code: '',
    province: '',
    country: 'ES'
  }
})

function startEditing() {
  if (patient.value) {
    editForm.first_name = patient.value.first_name
    editForm.last_name = patient.value.last_name
    editForm.phone = patient.value.phone || ''
    editForm.email = patient.value.email || ''
    editForm.date_of_birth = patient.value.date_of_birth || ''
    editForm.notes = patient.value.notes || ''
    // Billing fields
    editForm.billing_name = patient.value.billing_name || ''
    editForm.billing_tax_id = patient.value.billing_tax_id || ''
    editForm.billing_email = patient.value.billing_email || ''
    editForm.billing_address = patient.value.billing_address || {
      street: '',
      city: '',
      postal_code: '',
      province: '',
      country: 'ES'
    }
  }
  isEditing.value = true
}

function cancelEditing() {
  isEditing.value = false
}

// Auto-start editing billing if coming from invoice edit
watch(
  () => patient.value,
  (newPatient) => {
    if (openBillingEdit.value && newPatient && !isEditing.value) {
      startEditing()
    }
  },
  { immediate: true }
)

async function savePatient() {
  isSubmitting.value = true

  // Prepare billing address (only send if has content)
  const billingAddress = editForm.billing_address?.street
    ? editForm.billing_address
    : null

  try {
    await api.put(
      `/api/v1/clinical/patients/${patientId}`,
      {
        first_name: editForm.first_name,
        last_name: editForm.last_name,
        phone: editForm.phone || null,
        email: editForm.email || null,
        date_of_birth: editForm.date_of_birth || null,
        notes: editForm.notes || null,
        billing_name: editForm.billing_name || null,
        billing_tax_id: editForm.billing_tax_id || null,
        billing_email: editForm.billing_email || null,
        billing_address: billingAddress
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

// Format currency
const { locale } = useI18n()

function formatCurrency(amount: number, currency: string = 'EUR'): string {
  return new Intl.NumberFormat(locale.value, {
    style: 'currency',
    currency
  }).format(amount)
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
      <!-- Return to invoice banner -->
      <div
        v-if="returnTo"
        class="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3 flex items-center justify-between"
      >
        <span class="text-blue-800 dark:text-blue-200 text-sm">
          {{ t('patients.editingBillingForInvoice') }}
        </span>
        <UButton
          variant="soft"
          color="primary"
          size="sm"
          icon="i-lucide-arrow-left"
          :to="returnTo"
        >
          {{ t('patients.returnToInvoice') }}
        </UButton>
      </div>

      <!-- Page header -->
      <div class="flex items-center gap-4">
        <UButton
          variant="ghost"
          color="neutral"
          icon="i-lucide-arrow-left"
          :to="returnTo || '/patients'"
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

      <!-- Tabs with content -->
      <UTabs
        v-model="activeTab"
        :items="tabs"
        default-value="info"
        class="w-full"
      >
        <!-- Info tab content -->
        <template #info>
          <UCard class="mt-4">
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

              <!-- Billing Section -->
              <div class="pt-4 border-t border-gray-200 dark:border-gray-700">
                <div class="flex items-center gap-3 mb-4">
                  <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
                    {{ t('patients.billingSection') }}
                  </h3>
                  <UBadge
                    v-if="patient.has_complete_billing_info"
                    color="success"
                    variant="subtle"
                  >
                    <UIcon
                      name="i-lucide-check"
                      class="w-3 h-3 mr-1"
                    />
                    {{ t('patients.billingComplete') }}
                  </UBadge>
                  <UBadge
                    v-else
                    color="warning"
                    variant="subtle"
                  >
                    <UIcon
                      name="i-lucide-alert-triangle"
                      class="w-3 h-3 mr-1"
                    />
                    {{ t('patients.billingIncomplete') }}
                  </UBadge>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label class="text-sm font-medium text-gray-500 dark:text-gray-400">
                      {{ t('patients.billingName') }}
                    </label>
                    <p class="text-gray-900 dark:text-white">
                      {{ patient.billing_name || '-' }}
                    </p>
                  </div>

                  <div>
                    <label class="text-sm font-medium text-gray-500 dark:text-gray-400">
                      {{ t('patients.billingTaxId') }}
                    </label>
                    <p class="text-gray-900 dark:text-white">
                      {{ patient.billing_tax_id || '-' }}
                    </p>
                  </div>

                  <div>
                    <label class="text-sm font-medium text-gray-500 dark:text-gray-400">
                      {{ t('patients.billingEmail') }}
                    </label>
                    <p class="text-gray-900 dark:text-white">
                      {{ patient.billing_email || '-' }}
                    </p>
                  </div>

                  <div>
                    <label class="text-sm font-medium text-gray-500 dark:text-gray-400">
                      {{ t('patients.billingAddress') }}
                    </label>
                    <p
                      v-if="patient.billing_address"
                      class="text-gray-900 dark:text-white"
                    >
                      {{ patient.billing_address.street || '' }}
                      <br v-if="patient.billing_address.city || patient.billing_address.postal_code">
                      {{ patient.billing_address.postal_code }} {{ patient.billing_address.city }}
                      <br v-if="patient.billing_address.province">
                      {{ patient.billing_address.province }}
                    </p>
                    <p
                      v-else
                      class="text-gray-900 dark:text-white"
                    >
                      -
                    </p>
                  </div>
                </div>
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

              <!-- Billing Section in Edit Mode -->
              <div class="pt-4 border-t border-gray-200 dark:border-gray-700">
                <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                  {{ t('patients.billingSection') }}
                </h3>
                <p class="text-sm text-gray-500 dark:text-gray-400 mb-4">
                  {{ t('patients.billingSectionHint') }}
                </p>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <UFormField :label="t('patients.billingName')">
                    <UInput
                      v-model="editForm.billing_name"
                      :placeholder="t('patients.billingNamePlaceholder')"
                    />
                  </UFormField>

                  <UFormField :label="t('patients.billingTaxId')">
                    <UInput
                      v-model="editForm.billing_tax_id"
                      placeholder="NIF/CIF"
                    />
                  </UFormField>

                  <UFormField :label="t('patients.billingEmail')">
                    <UInput
                      v-model="editForm.billing_email"
                      type="email"
                    />
                  </UFormField>
                </div>

                <div class="mt-4">
                  <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                    {{ t('patients.billingAddress') }}
                  </h4>
                  <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div class="md:col-span-2">
                      <UFormField :label="t('invoice.street')">
                        <UInput v-model="editForm.billing_address!.street" />
                      </UFormField>
                    </div>

                    <UFormField :label="t('invoice.city')">
                      <UInput v-model="editForm.billing_address!.city" />
                    </UFormField>

                    <UFormField :label="t('invoice.postalCode')">
                      <UInput v-model="editForm.billing_address!.postal_code" />
                    </UFormField>

                    <UFormField :label="t('invoice.province')">
                      <UInput v-model="editForm.billing_address!.province" />
                    </UFormField>

                    <UFormField :label="t('invoice.country')">
                      <UInput v-model="editForm.billing_address!.country" />
                    </UFormField>
                  </div>
                </div>
              </div>

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
          </UCard>
        </template>

        <!-- Odontogram tab content -->
        <template #odontogram>
          <UCard class="mt-4">
            <OdontogramChart
              :patient-id="patientId"
              :readonly="!canEditOdontogram"
            />
          </UCard>
        </template>

        <!-- Budgets tab content -->
        <template #budgets>
          <UCard class="mt-4">
            <!-- Loading -->
            <div
              v-if="budgetsStatus === 'pending'"
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
              v-else-if="budgets.length === 0"
              class="text-center py-12"
            >
              <UIcon
                name="i-lucide-file-text"
                class="w-12 h-12 text-gray-400 mx-auto mb-4"
              />
              <p class="text-gray-500 dark:text-gray-400 mb-4">
                {{ t('patientDetail.noBudgets') }}
              </p>
              <UButton
                v-if="can(PERMISSIONS.budget.write)"
                :to="`/budgets/new?patient_id=${patientId}`"
                icon="i-lucide-plus"
              >
                {{ t('patientDetail.createBudget') }}
              </UButton>
            </div>

            <!-- Budgets list -->
            <ul
              v-else
              class="divide-y divide-gray-200 dark:divide-gray-800"
            >
              <li
                v-for="budget in budgets"
                :key="budget.id"
                class="py-4"
              >
                <NuxtLink
                  :to="`/budgets/${budget.id}`"
                  class="flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-800 -mx-4 px-4 py-2 rounded-lg transition-colors"
                >
                  <div>
                    <div class="flex items-center gap-3">
                      <span class="font-medium text-gray-900 dark:text-white">
                        {{ budget.budget_number }}
                      </span>
                      <span class="text-sm text-gray-500">
                        v{{ budget.version }}
                      </span>
                      <BudgetStatusBadge :status="budget.status" />
                    </div>
                    <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
                      {{ formatDate(budget.created_at) }}
                    </p>
                  </div>
                  <div class="flex items-center gap-4">
                    <span class="font-semibold text-gray-900 dark:text-white">
                      {{ formatCurrency(budget.total, budget.currency) }}
                    </span>
                    <UIcon
                      name="i-lucide-chevron-right"
                      class="w-5 h-5 text-gray-400"
                    />
                  </div>
                </NuxtLink>
              </li>
            </ul>

            <!-- Create new budget button at bottom if there are budgets -->
            <div
              v-if="budgets.length > 0 && can(PERMISSIONS.budget.write)"
              class="pt-4 border-t border-gray-200 dark:border-gray-800 mt-4"
            >
              <UButton
                :to="`/budgets/new?patient_id=${patientId}`"
                icon="i-lucide-plus"
                variant="outline"
              >
                {{ t('patientDetail.createBudget') }}
              </UButton>
            </div>
          </UCard>
        </template>

        <!-- History tab content -->
        <template #history>
          <UCard class="mt-4">
            <div class="text-center py-12">
              <UIcon
                name="i-lucide-file-text"
                class="w-12 h-12 text-gray-400 mx-auto mb-4"
              />
              <p class="text-gray-500 dark:text-gray-400">
                {{ t('patientDetail.historyPlaceholder') }}
              </p>
            </div>
          </UCard>
        </template>

        <!-- Appointments tab content -->
        <template #appointments>
          <UCard class="mt-4">
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
          </UCard>
        </template>
      </UTabs>
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
