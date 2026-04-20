<script setup lang="ts">
import type { Patient, PatientCreate, PaginatedResponse, ApiResponse } from '~~/app/types'
import { PATIENT_STATUS_ROLE, type PatientStatus } from '~~/app/config/severity'

const { t } = useI18n()
const api = useApi()
const toast = useToast()
const router = useRouter()

const searchQuery = ref('')
const debouncedSearch = ref('')
const currentPage = ref(1)
const pageSize = 20

const { data: patientsData, status, refresh } = await useAsyncData(
  'patients:list',
  async () => {
    const params = new URLSearchParams({
      page: String(currentPage.value),
      page_size: String(pageSize)
    })
    if (debouncedSearch.value) params.append('search', debouncedSearch.value)
    try {
      return await api.get<PaginatedResponse<Patient>>(
        `/api/v1/patients?${params.toString()}`
      )
    } catch {
      return { data: [], total: 0, page: 1, page_size: pageSize }
    }
  },
  {
    watch: [currentPage, debouncedSearch]
  }
)

const patients = computed(() => patientsData.value?.data || [])
const totalPatients = computed(() => patientsData.value?.total || 0)
const totalPages = computed(() => Math.ceil(totalPatients.value / pageSize))

function onSearchDebounced(val: string) {
  debouncedSearch.value = val
  currentPage.value = 1
}

// Create patient modal
const isCreateModalOpen = ref(false)
const isSubmitting = ref(false)
const newPatient = reactive<PatientCreate>({
  first_name: '',
  last_name: '',
  phone: '',
  email: '',
  date_of_birth: '',
  notes: ''
})

function resetForm() {
  Object.assign(newPatient, {
    first_name: '',
    last_name: '',
    phone: '',
    email: '',
    date_of_birth: '',
    notes: ''
  })
}

async function createPatient() {
  isSubmitting.value = true
  try {
    const response = await api.post<ApiResponse<Patient>>(
      '/api/v1/patients',
      {
        first_name: newPatient.first_name,
        last_name: newPatient.last_name,
        phone: newPatient.phone || null,
        email: newPatient.email || null,
        date_of_birth: newPatient.date_of_birth || null,
        notes: newPatient.notes || null
      }
    )
    toast.add({
      title: t('common.success'),
      description: t('patients.created'),
      color: 'success'
    })
    isCreateModalOpen.value = false
    resetForm()
    await refresh()
    await router.push(`/patients/${response.data.id}`)
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
</script>

<template>
  <div>
    <PageHeader :title="t('patients.title')">
      <template #actions>
        <UButton
          color="primary"
          variant="soft"
          icon="i-lucide-plus"
          @click="isCreateModalOpen = true"
        >
          {{ t('patients.create') }}
        </UButton>
      </template>
    </PageHeader>

    <!-- Search -->
    <div class="mb-[var(--density-gap,1rem)]">
      <SearchBar
        v-model="searchQuery"
        :placeholder="t('patients.searchPlaceholder')"
        @update:debounced="onSearchDebounced"
      />
    </div>

    <UCard>
      <div
        v-if="status === 'pending'"
        class="space-y-3"
      >
        <USkeleton
          v-for="i in 5"
          :key="i"
          class="h-12 w-full"
        />
      </div>

      <EmptyState
        v-else-if="patients.length === 0"
        icon="i-lucide-users"
        :title="debouncedSearch ? t('patients.noResults') : t('patients.empty')"
        :description="!debouncedSearch ? t('dashboard.welcomeMessage') : undefined"
      >
        <template
          v-if="!debouncedSearch"
          #actions
        >
          <UButton
            color="primary"
            variant="soft"
            icon="i-lucide-plus"
            @click="isCreateModalOpen = true"
          >
            {{ t('patients.emptyAction') }}
          </UButton>
        </template>
      </EmptyState>

      <div
        v-else
        class="divide-y divide-[var(--color-border-subtle)]"
      >
        <ListRow
          v-for="patient in patients"
          :key="patient.id"
          :to="`/patients/${patient.id}`"
        >
          <template #leading>
            <UAvatar
              :alt="patient.first_name"
              size="sm"
            />
          </template>
          <template #title>
            {{ patient.last_name }}, {{ patient.first_name }}
          </template>
          <template #subtitle>
            {{ patient.phone || patient.email || '—' }}
          </template>
          <template #meta>
            <StatusBadge
              :role="PATIENT_STATUS_ROLE[patient.status as PatientStatus] || 'neutral'"
              :label="t(`patients.status.${patient.status}`)"
            />
          </template>
        </ListRow>
      </div>

      <PaginationBar
        v-model:page="currentPage"
        :total-pages="totalPages"
        :total="totalPatients"
        :page-size="pageSize"
      />
    </UCard>

    <!-- Create patient modal -->
    <UModal v-model:open="isCreateModalOpen">
      <template #content>
        <UCard>
          <template #header>
            <div class="flex items-center justify-between">
              <h2 class="text-h1 text-default">
                {{ t('patients.create') }}
              </h2>
              <UButton
                variant="ghost"
                color="neutral"
                icon="i-lucide-x"
                :aria-label="t('common.close', 'Cerrar')"
                @click="isCreateModalOpen = false"
              />
            </div>
          </template>

          <form
            class="space-y-4"
            @submit.prevent="createPatient"
          >
            <div class="grid grid-cols-2 gap-4">
              <UFormField
                :label="t('patients.firstName')"
                required
              >
                <UInput
                  v-model="newPatient.first_name"
                  :placeholder="t('patients.firstName')"
                  required
                />
              </UFormField>
              <UFormField
                :label="t('patients.lastName')"
                required
              >
                <UInput
                  v-model="newPatient.last_name"
                  :placeholder="t('patients.lastName')"
                  required
                />
              </UFormField>
            </div>

            <div class="grid grid-cols-2 gap-4">
              <UFormField :label="t('patients.phone')">
                <UInput
                  v-model="newPatient.phone"
                  :placeholder="t('patients.phone')"
                  type="tel"
                />
              </UFormField>
              <UFormField :label="t('patients.email')">
                <UInput
                  v-model="newPatient.email"
                  :placeholder="t('patients.email')"
                  type="email"
                />
              </UFormField>
            </div>

            <UFormField :label="t('patients.dateOfBirth')">
              <UInput
                v-model="newPatient.date_of_birth"
                type="date"
              />
            </UFormField>

            <UFormField :label="t('patients.notes')">
              <UTextarea
                v-model="newPatient.notes"
                :placeholder="t('patients.notes')"
                :rows="3"
              />
            </UFormField>
          </form>

          <template #footer>
            <div class="flex justify-end gap-3">
              <UButton
                variant="outline"
                color="neutral"
                @click="isCreateModalOpen = false"
              >
                {{ t('common.cancel') }}
              </UButton>
              <UButton
                color="primary"
                variant="solid"
                :loading="isSubmitting"
                :disabled="!newPatient.first_name || !newPatient.last_name"
                @click="createPatient"
              >
                {{ t('common.save') }}
              </UButton>
            </div>
          </template>
        </UCard>
      </template>
    </UModal>
  </div>
</template>
