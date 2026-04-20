<script setup lang="ts">
import type { PatientExtended, Appointment, BudgetListItem, TreatmentPlan, PaginatedResponse, ApiResponse } from '~~/app/types'
import { PERMISSIONS } from '~~/app/config/permissions'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const api = useApi()
const toast = useToast()
const { can } = usePermissions()

const patientId = route.params.id as string
const patientIdRef = computed(() => patientId)

// Handle returnTo query param (from invoice edit page)
const returnTo = computed(() => route.query.returnTo as string | undefined)
const openBillingEdit = computed(() => route.query.tab === 'billing')

// Fetch patient identity + clinical rows in parallel. Emergency contact,
// legal guardian and alerts live in the patients_clinical module
// (B.4), but we stitch them back onto the `PatientExtended` object so
// the rest of the page can consume them unchanged.
const { data: patient, status, refresh } = await useAsyncData(
  `patient:${patientId}`,
  async () => {
    try {
      const [identity, emergency, guardian, alertsResp] = await Promise.all([
        api.get<ApiResponse<PatientExtended>>(
          `/api/v1/patients/${patientId}/extended`
        ),
        api.get<ApiResponse<PatientExtended['emergency_contact']>>(
          `/api/v1/patients_clinical/patients/${patientId}/emergency-contact`
        ).catch(() => ({ data: null })),
        api.get<ApiResponse<PatientExtended['legal_guardian']>>(
          `/api/v1/patients_clinical/patients/${patientId}/legal-guardian`
        ).catch(() => ({ data: null })),
        api.get<ApiResponse<{ alerts: PatientExtended['active_alerts'] }>>(
          `/api/v1/patients_clinical/patients/${patientId}/alerts`
        ).catch(() => ({ data: { alerts: [] } }))
      ])

      return {
        ...identity.data,
        emergency_contact: emergency.data ?? undefined,
        legal_guardian: guardian.data ?? undefined,
        active_alerts: alertsResp.data?.alerts ?? []
      } as PatientExtended
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
        `/api/v1/agenda/appointments?patient_id=${patientId}`
      )
    } catch {
      return { data: [], total: 0, page: 1, page_size: 20 }
    }
  }
)

const appointments = computed(() => appointmentsData.value?.data || [])

// Next upcoming appointment (for sidebar widget)
const nextAppointment = computed(() => {
  const now = new Date()
  const upcoming = appointments.value
    .filter(apt => new Date(apt.start_time) > now && apt.status !== 'cancelled')
    .sort((a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime())
  return upcoming[0] || null
})

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

// Fetch patient treatment plans (for sidebar widget)
const { data: plansData, status: plansStatus } = await useAsyncData(
  `patient:${patientId}:plans`,
  async () => {
    if (!can(PERMISSIONS.treatmentPlans.read)) {
      return { data: [], total: 0, page: 1, page_size: 20 }
    }
    try {
      return await api.get<PaginatedResponse<TreatmentPlan>>(
        `/api/v1/treatment_plan/treatment-plans?patient_id=${patientId}`
      )
    } catch {
      return { data: [], total: 0, page: 1, page_size: 20 }
    }
  }
)

// Active plan (for sidebar widget)
const activePlan = computed(() => {
  const plans = plansData.value?.data || []
  return plans.find(p => p.status === 'active') || null
})

const budgets = computed(() => budgetsData.value?.data || [])

// Medical history composable
const { medicalHistory, isSaving: isSavingMedical, saveMedicalHistory } = useMedicalHistory(patientIdRef)

// Tabs - computed to filter by permissions
// New structure: Clinical (Odontogram+Plans) | Administration (Budgets+Billing) | Appointments | Documents | Timeline | Info
const activeTab = ref('clinical')

// Sync tab from query param
watch(
  () => route.query.tab,
  (tab) => {
    if (tab && typeof tab === 'string') {
      activeTab.value = tab
    }
  },
  { immediate: true }
)

const tabs = computed(() => {
  const baseTabs: Array<{ value: string, label: string, icon: string, slot: string }> = []

  // Clinical tab (Odontogram + Treatment Plans) - replaces separate odontogram tab
  if (can(PERMISSIONS.odontogram.read) || can(PERMISSIONS.treatmentPlans.read)) {
    baseTabs.push({
      value: 'clinical',
      label: t('patientDetail.tabs.clinical'),
      icon: 'i-lucide-stethoscope',
      slot: 'clinical'
    })
  }

  // Administration tab (Budgets + Billing) - merges budgets and billing
  if (can(PERMISSIONS.budget.read) || can(PERMISSIONS.billing.read)) {
    baseTabs.push({
      value: 'administration',
      label: t('patientDetail.tabs.administration'),
      icon: 'i-lucide-briefcase',
      slot: 'administration'
    })
  }

  // Timeline tab
  baseTabs.push({
    value: 'timeline',
    label: t('patientDetail.tabs.timeline'),
    icon: 'i-lucide-history',
    slot: 'timeline'
  })

  // Info tab (Demographics + Medical history)
  baseTabs.push({
    value: 'info',
    label: t('patientDetail.tabs.info'),
    icon: 'i-lucide-user',
    slot: 'info'
  })

  return baseTabs
})

// Check permissions
const canEditOdontogram = computed(() => can(PERMISSIONS.odontogram.write))
const canEditMedicalHistory = computed(() => can(PERMISSIONS.medicalHistory.write))
const canEditPatient = computed(() => can(PERMISSIONS.patients.write))

// Section edit modals state
type SectionType = 'demographics' | 'emergency' | 'guardian' | 'billing' | 'medical'
const editModalOpen = ref(false)
const editModalSection = ref<SectionType>('demographics')
const isSubmitting = ref(false)

function openSectionModal(section: SectionType) {
  editModalSection.value = section
  editModalOpen.value = true
}

// Auto-open billing modal if coming from invoice edit
watch(
  () => patient.value,
  (newPatient) => {
    if (openBillingEdit.value && newPatient && !editModalOpen.value) {
      openSectionModal('billing')
    }
  },
  { immediate: true }
)

async function handleSectionSave(_section: SectionType, _data: Record<string, unknown>) {
  // Refresh patient data after save
  await refresh()
}

async function handleMedicalSave() {
  const success = await saveMedicalHistory()
  if (success) {
    editModalOpen.value = false
  }
}

// Archive patient
const isArchiveModalOpen = ref(false)

async function archivePatient() {
  isSubmitting.value = true

  try {
    await api.del(`/api/v1/patients/${patientId}`)

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

// Check if patient is a minor (under 18)
const isMinor = computed(() => {
  if (!patient.value?.date_of_birth) return false
  const today = new Date()
  const birth = new Date(patient.value.date_of_birth)
  let years = today.getFullYear() - birth.getFullYear()
  const m = today.getMonth() - birth.getMonth()
  if (m < 0 || (m === 0 && today.getDate() < birth.getDate())) years--
  return years < 18
})

// Hide sidebar when viewing plan detail (gives more space)
const hideSidebar = ref(false)

function handlePlanViewChange(view: 'list' | 'detail') {
  hideSidebar.value = view === 'detail'
}

// Reset sidebar visibility when changing tabs
watch(activeTab, () => {
  hideSidebar.value = false
})

// Info tab accordion items - with edit buttons in headers
const infoAccordionItems = computed(() => {
  const items = [
    { label: t('patients.demographics'), icon: 'i-lucide-user', slot: 'demographics', defaultOpen: true },
    { label: t('patients.emergencyContact.title'), icon: 'i-lucide-phone-call', slot: 'emergency' }
  ]
  if (isMinor.value) {
    items.push({ label: t('patients.legalGuardian.title'), icon: 'i-lucide-shield-check', slot: 'guardian', defaultOpen: false })
  }
  items.push(
    { label: t('patients.medicalHistory.title'), icon: 'i-lucide-heart-pulse', slot: 'medical', defaultOpen: false },
    { label: t('patients.billingSection'), icon: 'i-lucide-receipt', slot: 'billing', defaultOpen: false }
  )
  return items
})
</script>

<template>
  <div class="space-y-6">
    <!-- Loading state -->
    <div
      v-if="status === 'pending'"
      class="space-y-4"
    >
      <USkeleton class="h-8 w-48" />
      <div class="flex gap-6">
        <USkeleton class="h-96 w-64" />
        <USkeleton class="h-96 flex-1" />
      </div>
    </div>

    <!-- Patient content -->
    <template v-else-if="patient">
      <!-- Return to invoice banner -->
      <div
        v-if="returnTo"
        class="alert-surface-info rounded-token-md px-3 py-2 flex items-center justify-between gap-3"
        role="status"
      >
        <span class="text-body">
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
      <div class="flex items-center gap-3 mb-6">
        <UButton
          variant="ghost"
          color="neutral"
          icon="i-lucide-arrow-left"
          :to="returnTo || '/patients'"
          :aria-label="t('common.back', 'Volver')"
        />
        <h1 class="text-display text-default text-pretty">
          {{ patient.first_name }} {{ patient.last_name }}
        </h1>
      </div>

      <!-- Main layout: Sidebar + Content -->
      <div class="flex flex-col lg:flex-row gap-6">
        <!-- Sticky Sidebar (hidden when viewing plan detail) -->
        <aside
          v-if="!hideSidebar"
          class="lg:w-72 lg:shrink-0 space-y-4"
        >
          <div class="lg:sticky lg:top-4">
            <UCard>
              <PatientQuickInfo
                :patient="patient"
                :active-plan="activePlan"
                :next-appointment="nextAppointment"
                :loading-plan="plansStatus === 'pending'"
                :loading-appointment="appointmentsStatus === 'pending'"
              />
            </UCard>
            <!-- Extension point for module-provided sidebar widgets. -->
            <ModuleSlot name="patient.detail.sidebar" :ctx="{ patient }" />
          </div>
        </aside>

        <!-- Main Content with Tabs -->
        <main class="flex-1 min-w-0">
          <!-- Tabs -->
          <UTabs
            v-model="activeTab"
            :items="tabs"
            default-value="info"
            class="w-full"
            :ui="{ content: 'overflow-visible' }"
          >
            <!-- Info tab content -->
            <template #info>
              <div class="mt-4 space-y-4 overflow-visible">
                <UCard>
                  <UAccordion
                    :items="infoAccordionItems"
                    :ui="{ item: { base: 'border rounded-lg' } }"
                    multiple
                  >
                    <!-- Demographics Section -->
                    <template #demographics>
                      <div class="p-4">
                        <div class="flex justify-end mb-3">
                          <UButton
                            v-if="canEditPatient"
                            variant="soft"
                            color="neutral"
                            icon="i-lucide-pencil"
                            size="xs"
                            @click="openSectionModal('demographics')"
                          >
                            {{ t('common.edit') }}
                          </UButton>
                        </div>
                        <dl class="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <DataField
                            :label="t('patients.firstName')"
                            :value="patient.first_name"
                          />
                          <DataField
                            :label="t('patients.lastName')"
                            :value="patient.last_name"
                          />
                          <DataField
                            :label="t('patients.phone')"
                            :value="patient.phone"
                          />
                          <DataField
                            :label="t('patients.email')"
                            :value="patient.email"
                          />
                          <DataField
                            :label="t('patients.dateOfBirth')"
                            :value="patient.date_of_birth ? formatDate(patient.date_of_birth) : null"
                          />
                          <DataField
                            :label="t('patients.gender.label')"
                            :value="patient.gender ? t(`patients.gender.${patient.gender}`) : null"
                          />
                          <DataField
                            v-if="patient.national_id"
                            :label="t('patients.nationalId')"
                            :value="`${patient.national_id_type?.toUpperCase() || ''}: ${patient.national_id}`"
                          />
                          <DataField
                            v-if="patient.profession"
                            :label="t('patients.profession')"
                            :value="patient.profession"
                          />
                        </dl>
                        <DataField
                          v-if="patient.notes"
                          class="mt-4"
                          :label="t('patients.notes')"
                          :value="patient.notes"
                          multiline
                        />
                      </div>
                    </template>

                    <!-- Emergency Contact Section -->
                    <template #emergency>
                      <div class="p-4">
                        <div class="flex justify-end mb-3">
                          <UButton
                            v-if="canEditPatient"
                            variant="soft"
                            color="neutral"
                            icon="i-lucide-pencil"
                            size="xs"
                            @click="openSectionModal('emergency')"
                          >
                            {{ t('common.edit') }}
                          </UButton>
                        </div>
                        <EmergencyContactForm
                          :model-value="patient.emergency_contact"
                          readonly
                        />
                      </div>
                    </template>

                    <!-- Legal Guardian Section (minors only) -->
                    <template #guardian>
                      <div class="p-4">
                        <div class="flex justify-end mb-3">
                          <UButton
                            v-if="canEditPatient"
                            variant="soft"
                            color="neutral"
                            icon="i-lucide-pencil"
                            size="xs"
                            @click="openSectionModal('guardian')"
                          >
                            {{ t('common.edit') }}
                          </UButton>
                        </div>
                        <LegalGuardianForm
                          :model-value="patient.legal_guardian"
                          readonly
                        />
                      </div>
                    </template>

                    <!-- Medical History Section -->
                    <template #medical>
                      <div class="p-4">
                        <div class="flex justify-end mb-3">
                          <UButton
                            v-if="canEditMedicalHistory"
                            variant="soft"
                            color="neutral"
                            icon="i-lucide-pencil"
                            size="xs"
                            @click="openSectionModal('medical')"
                          >
                            {{ t('common.edit') }}
                          </UButton>
                        </div>
                        <MedicalHistoryForm
                          :model-value="medicalHistory"
                          readonly
                        />
                      </div>
                    </template>

                    <!-- Billing Section -->
                    <template #billing>
                      <div class="p-4">
                        <div class="flex justify-between items-center mb-4">
                          <div class="flex items-center gap-3">
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
                          <UButton
                            v-if="canEditPatient"
                            variant="soft"
                            color="neutral"
                            icon="i-lucide-pencil"
                            size="xs"
                            @click="openSectionModal('billing')"
                          >
                            {{ t('common.edit') }}
                          </UButton>
                        </div>
                        <dl class="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <DataField
                            :label="t('patients.billingName')"
                            :value="patient.billing_name"
                          />
                          <DataField
                            :label="t('patients.billingTaxId')"
                            :value="patient.billing_tax_id"
                          />
                          <DataField
                            :label="t('patients.billingEmail')"
                            :value="patient.billing_email"
                          />
                          <DataField :label="t('patients.billingAddress')">
                            <template v-if="patient.billing_address">
                              {{ patient.billing_address.street || '' }}
                              <template v-if="patient.billing_address.city || patient.billing_address.postal_code">
                                <br>{{ patient.billing_address.postal_code }} {{ patient.billing_address.city }}
                              </template>
                              <template v-if="patient.billing_address.province">
                                <br>{{ patient.billing_address.province }}
                              </template>
                            </template>
                            <template v-else>
                              —
                            </template>
                          </DataField>
                        </dl>
                      </div>
                    </template>
                  </UAccordion>
                </UCard>

                <!-- Danger zone -->
                <div class="alert-surface-danger rounded-token-lg px-4 py-3 flex items-center justify-between gap-4">
                  <div class="min-w-0">
                    <div class="text-ui">
                      {{ t('patients.dangerZone.title') }}
                    </div>
                    <div class="text-caption">
                      {{ t('patients.dangerZone.archiveHelp') }}
                    </div>
                  </div>
                  <UButton
                    variant="outline"
                    color="error"
                    icon="i-lucide-archive"
                    size="sm"
                    @click="isArchiveModalOpen = true"
                  >
                    {{ t('patients.archive') }}
                  </UButton>
                </div>
              </div>
            </template>

            <!-- Clinical tab content (Odontogram + Treatment Plans) -->
            <template #clinical>
              <div class="mt-4">
                <ClinicalTab
                  :patient-id="patientId"
                  :readonly="!canEditOdontogram"
                  @plan-view-change="handlePlanViewChange"
                />
              </div>
            </template>

            <!-- Administration tab content (Budgets + Billing) -->
            <template #administration>
              <div class="mt-4">
                <AdministrationTab
                  :patient-id="patientId"
                  :budgets="budgets"
                  :budgets-loading="budgetsStatus === 'pending'"
                />
              </div>
            </template>

            <!-- Timeline tab content -->
            <template #timeline>
              <UCard class="mt-4">
                <PatientTimeline :patient-id="patientId" />
              </UCard>
            </template>
          </UTabs>
        </main>
      </div>
    </template>

    <!-- Section Edit Modal -->
    <PatientSectionEditModal
      v-if="patient"
      v-model:open="editModalOpen"
      :section="editModalSection"
      :patient="patient"
      :medical-history="medicalHistory"
      :is-saving-medical="isSavingMedical"
      @save="handleSectionSave"
      @save-medical="handleMedicalSave"
    />

    <!-- Archive confirmation modal -->
    <UModal v-model:open="isArchiveModalOpen">
      <template #content>
        <UCard>
          <template #header>
            <h2 class="text-h1 text-default">
              {{ t('patients.archiveConfirm', { name: `${patient?.first_name} ${patient?.last_name}` }) }}
            </h2>
          </template>
          <p class="text-body text-muted">
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
