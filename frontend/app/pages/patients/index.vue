<script setup lang="ts">
import type { Patient, PatientCreate, PaginatedResponse, ApiResponse } from '~/types'

const { t } = useI18n()
const api = useApi()
const toast = useToast()
const router = useRouter()

// Search and pagination state
const searchQuery = ref('')
const currentPage = ref(1)
const pageSize = 20

// Debounced search
const debouncedSearch = ref('')
let searchTimeout: ReturnType<typeof setTimeout> | null = null

watch(searchQuery, (val) => {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    debouncedSearch.value = val
    currentPage.value = 1
  }, 300)
})

// Fetch patients
const { data: patientsData, status, refresh } = await useAsyncData(
  'patients:list',
  async () => {
    const params = new URLSearchParams({
      page: String(currentPage.value),
      page_size: String(pageSize)
    })

    if (debouncedSearch.value) {
      params.append('search', debouncedSearch.value)
    }

    try {
      return await api.get<PaginatedResponse<Patient>>(
        `/api/v1/clinical/patients?${params.toString()}`
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

// Modal state
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
  newPatient.first_name = ''
  newPatient.last_name = ''
  newPatient.phone = ''
  newPatient.email = ''
  newPatient.date_of_birth = ''
  newPatient.notes = ''
}

async function createPatient() {
  isSubmitting.value = true

  try {
    const response = await api.post<ApiResponse<Patient>>(
      '/api/v1/clinical/patients',
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

    // Navigate to patient detail
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

function goToPatient(patient: Patient) {
  router.push(`/patients/${patient.id}`)
}

// Status badge color
type BadgeColor = 'success' | 'warning' | 'neutral' | 'error' | 'info' | 'primary' | 'secondary'

function getStatusColor(status: string): BadgeColor {
  switch (status) {
    case 'active':
      return 'success'
    case 'inactive':
      return 'warning'
    case 'archived':
      return 'neutral'
    default:
      return 'neutral'
  }
}
</script>

<template>
  <div class="space-y-6">
    <!-- Page header -->
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
        {{ t('patients.title') }}
      </h1>
      <UButton
        icon="i-lucide-plus"
        @click="isCreateModalOpen = true"
      >
        {{ t('patients.create') }}
      </UButton>
    </div>

    <!-- Search -->
    <div class="flex gap-4">
      <UInput
        v-model="searchQuery"
        :placeholder="t('patients.searchPlaceholder')"
        icon="i-lucide-search"
        class="max-w-sm"
      />
    </div>

    <!-- Patients table -->
    <UCard>
      <!-- Loading state -->
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

      <!-- Empty state -->
      <div
        v-else-if="patients.length === 0"
        class="text-center py-12"
      >
        <UIcon
          name="i-lucide-users"
          class="w-12 h-12 text-gray-400 mx-auto mb-4"
        />
        <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">
          {{ debouncedSearch ? t('patients.noResults') : t('patients.empty') }}
        </h3>
        <p
          v-if="!debouncedSearch"
          class="text-gray-500 dark:text-gray-400 mb-6"
        >
          {{ t('dashboard.welcomeMessage') }}
        </p>
        <UButton
          v-if="!debouncedSearch"
          icon="i-lucide-plus"
          @click="isCreateModalOpen = true"
        >
          {{ t('patients.emptyAction') }}
        </UButton>
      </div>

      <!-- Patient list -->
      <div
        v-else
        class="divide-y divide-gray-200 dark:divide-gray-800"
      >
        <div
          v-for="patient in patients"
          :key="patient.id"
          class="flex items-center py-4 px-2 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors rounded-lg -mx-2"
          @click="goToPatient(patient)"
        >
          <div class="flex items-center gap-3 flex-1">
            <UAvatar
              :alt="patient.first_name"
              size="sm"
            />
            <div class="min-w-0 flex-1">
              <p class="font-medium text-gray-900 dark:text-white truncate">
                {{ patient.last_name }}, {{ patient.first_name }}
              </p>
              <p class="text-sm text-gray-500 dark:text-gray-400 truncate">
                {{ patient.phone || patient.email || '-' }}
              </p>
            </div>
          </div>
          <UBadge
            :color="getStatusColor(patient.status)"
            variant="subtle"
            class="mr-4"
          >
            {{ t(`patients.status.${patient.status}`) }}
          </UBadge>
          <UIcon
            name="i-lucide-chevron-right"
            class="w-5 h-5 text-gray-400"
          />
        </div>
      </div>

      <!-- Pagination -->
      <div
        v-if="totalPages > 1"
        class="flex items-center justify-between pt-4 border-t border-gray-200 dark:border-gray-800"
      >
        <span class="text-sm text-gray-500 dark:text-gray-400">
          {{ t('common.page', { current: currentPage, total: totalPages }) }}
        </span>
        <div class="flex gap-2">
          <UButton
            variant="outline"
            color="neutral"
            size="sm"
            :disabled="currentPage <= 1"
            @click="currentPage--"
          >
            {{ t('common.previous') }}
          </UButton>
          <UButton
            variant="outline"
            color="neutral"
            size="sm"
            :disabled="currentPage >= totalPages"
            @click="currentPage++"
          >
            {{ t('common.next') }}
          </UButton>
        </div>
      </div>
    </UCard>

    <!-- Create patient modal -->
    <UModal v-model:open="isCreateModalOpen">
      <template #content>
        <UCard>
          <template #header>
            <div class="flex items-center justify-between">
              <h2 class="text-lg font-semibold text-gray-900 dark:text-white">
                {{ t('patients.create') }}
              </h2>
              <UButton
                variant="ghost"
                color="neutral"
                icon="i-lucide-x"
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
