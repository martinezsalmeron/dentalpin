<script setup lang="ts">
import type { Patient, PaginatedResponse, ApiResponse } from '~/types'

const props = defineProps<{
  modelValue?: Patient | null
  placeholder?: string
  inModal?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [patient: Patient | null]
}>()

const { t } = useI18n()
const api = useApi()

// State
const recentPatients = ref<Patient[]>([])
const searchResults = ref<Patient[]>([])
const isSearching = ref(false)
const isLoadingRecent = ref(false)
const selectedPatient = ref<Patient | null>(props.modelValue || null)

// Load recent patients on mount
onMounted(async () => {
  await loadRecentPatients()
})

async function loadRecentPatients() {
  isLoadingRecent.value = true
  try {
    const response = await api.get<ApiResponse<Patient[]>>(
      '/api/v1/clinical/patients/recent?limit=8'
    )
    recentPatients.value = response.data
  } catch {
    recentPatients.value = []
  } finally {
    isLoadingRecent.value = false
  }
}

async function handleSearch(query: string) {
  if (!query || query.length < 2) {
    searchResults.value = []
    return
  }

  isSearching.value = true
  try {
    const params = new URLSearchParams({
      search: query,
      page: '1',
      page_size: '10'
    })
    const response = await api.get<PaginatedResponse<Patient>>(
      `/api/v1/clinical/patients?${params.toString()}`
    )
    searchResults.value = response.data
  } catch {
    searchResults.value = []
  } finally {
    isSearching.value = false
  }
}

function handleSelect(patient: Patient | null) {
  selectedPatient.value = patient
  emit('update:modelValue', patient)
}

// Sync with parent
watch(() => props.modelValue, (newVal) => {
  selectedPatient.value = newVal || null
})
</script>

<template>
  <div class="relative">
    <!-- Selected patient display -->
    <div
      v-if="selectedPatient"
      class="flex items-center gap-3 p-3 bg-surface-muted rounded-lg"
    >
      <UAvatar
        :alt="selectedPatient.first_name"
        size="sm"
      />
      <div class="min-w-0 flex-1">
        <p class="font-medium text-default truncate">
          {{ selectedPatient.last_name }}, {{ selectedPatient.first_name }}
        </p>
        <p class="text-sm text-muted truncate">
          {{ selectedPatient.phone || selectedPatient.email || '-' }}
        </p>
      </div>
      <UButton
        variant="ghost"
        color="neutral"
        icon="i-lucide-x"
        size="sm"
        @click="handleSelect(null)"
      />
    </div>

    <!-- Visual selector when no selection -->
    <VisualSelector
      v-else
      :model-value="selectedPatient"
      :initial-items="recentPatients"
      :search-results="searchResults"
      :is-searching="isSearching || isLoadingRecent"
      :placeholder="placeholder || t('patients.searchPlaceholder')"
      :empty-label="t('selector.noRecentPatients')"
      :grid-cols="2"
      :in-modal="inModal"
      @update:model-value="handleSelect"
      @search="handleSearch"
    >
      <template #item="{ item }">
        <div class="flex items-center gap-2">
          <UAvatar
            :alt="item.first_name"
            size="xs"
          />
          <div class="min-w-0 flex-1">
            <p class="text-sm font-medium text-default truncate">
              {{ item.last_name }}, {{ item.first_name }}
            </p>
            <p class="text-xs text-muted truncate">
              {{ item.phone || item.email || '-' }}
            </p>
          </div>
        </div>
      </template>
    </VisualSelector>
  </div>
</template>
