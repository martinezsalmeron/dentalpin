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

// Most recent completed appointment (for visit summary card)
const lastVisit = computed(() => {
  const completed = appointments.value
    .filter(apt => apt.status === 'completed')
    .sort((a, b) => new Date(b.end_time).getTime() - new Date(a.end_time).getTime())
  return completed[0] || null
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
// Default tab is Summary (issue #60) — patient header + recent notes feed.
// Info, Clinical, Administration and Timeline follow.
const activeTab = ref('summary')

// Sync tab from query param. Falls back to summary on the patient landing.
watch(
  () => route.query.tab,
  (tab) => {
    if (tab && typeof tab === 'string') {
      activeTab.value = tab
    } else {
      activeTab.value = 'summary'
    }
  },
  { immediate: true }
)

const tabs = computed(() => {
  const baseTabs: Array<{ value: string, label: string, icon: string, slot: string }> = []

  // Summary tab — at-a-glance recent notes feed.
  baseTabs.push({
    value: 'summary',
    label: t('patientDetail.tabs.summary'),
    icon: 'i-lucide-layout-dashboard',
    slot: 'summary'
  })

  // Info tab (Demographics + Medical history)
  baseTabs.push({
    value: 'info',
    label: t('patientDetail.tabs.info'),
    icon: 'i-lucide-user',
    slot: 'info'
  })

  // Clinical tab (Odontogram + Treatment Plans)
  if (can(PERMISSIONS.odontogram.read) || can(PERMISSIONS.treatmentPlans.read)) {
    baseTabs.push({
      value: 'clinical',
      label: t('patientDetail.tabs.clinical'),
      icon: 'i-lucide-stethoscope',
      slot: 'clinical'
    })
  }

  // Administration tab (Budgets + Billing)
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

</script>

<template>
  <div class="space-y-6">
    <!-- Loading state -->
    <div
      v-if="status === 'pending'"
      class="space-y-4"
    >
      <USkeleton class="h-8 w-48" />
      <USkeleton class="h-32 w-full" />
      <USkeleton class="h-96 w-full" />
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

      <!-- Main content (full width — sidebar widgets now live inside the Resumen hero) -->
      <main class="w-full min-w-0">
        <UTabs
          v-model="activeTab"
          :items="tabs"
          default-value="summary"
          class="w-full"
          :ui="{ content: 'overflow-visible' }"
        >
          <!-- Summary tab content: left rail (snapshot) + main feed (notes) -->
          <template #summary>
            <div class="mt-4 flex flex-col lg:flex-row gap-4 lg:gap-6 overflow-visible">
              <aside class="lg:w-72 lg:shrink-0">
                <div class="lg:sticky lg:top-4">
                  <PatientSummaryHero
                    :patient="patient"
                    :active-plan="activePlan"
                    :next-appointment="nextAppointment"
                    :loading-plan="plansStatus === 'pending'"
                    :loading-appointment="appointmentsStatus === 'pending'"
                  />
                </div>
              </aside>
              <div class="flex-1 min-w-0">
                <ModuleSlot
                  name="patient.summary.feed"
                  :ctx="{ patient }"
                />
              </div>
            </div>
          </template>

          <!-- Info tab content -->
          <template #info>
            <div class="mt-4 space-y-3 lg:space-y-4 overflow-visible">
              <MedicalSnapshotCard
                :medical-history="medicalHistory"
                :active-alerts="patient.active_alerts"
                :can-edit="canEditMedicalHistory"
                @edit="openSectionModal('medical')"
                @complete-history="openSectionModal('medical')"
              />

              <VisitSummaryCard
                :last-visit="lastVisit"
                :next-appointment="nextAppointment"
              />

              <PersonalInfoCard
                :patient="patient"
                :can-edit="canEditPatient"
                @edit="openSectionModal('demographics')"
              />

              <ContactInfoCard
                :patient="patient"
                :is-minor="isMinor"
                :can-edit="canEditPatient"
                @edit-contact="openSectionModal('demographics')"
                @edit-emergency="openSectionModal('emergency')"
                @edit-guardian="openSectionModal('guardian')"
              />

              <AdministrativeCard
                :patient="patient"
                :can-edit="canEditPatient"
                @edit="openSectionModal('billing')"
              />

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
