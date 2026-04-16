<script setup lang="ts">
import type { PlannedTreatmentItem } from '~/types'

const props = defineProps<{
  modelValue?: PlannedTreatmentItem[]
  patientId?: string
  placeholder?: string
  currency?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [items: PlannedTreatmentItem[]]
}>()

const { t, locale } = useI18n()
const { fetchPatientPendingItems } = useTreatmentPlans()
const { formatPrice } = useCatalog()

// State
const pendingItems = ref<PlannedTreatmentItem[]>([])
const isLoading = ref(false)
const selectedItems = ref<PlannedTreatmentItem[]>(props.modelValue || [])
const showSelector = ref(false)
const searchQuery = ref('')

// Load pending items when patient changes
watch(() => props.patientId, async (newPatientId) => {
  if (newPatientId) {
    await loadPendingItems(newPatientId)
  } else {
    pendingItems.value = []
  }
}, { immediate: true })

async function loadPendingItems(patientId: string) {
  isLoading.value = true
  try {
    pendingItems.value = await fetchPatientPendingItems(patientId)
  } catch {
    pendingItems.value = []
  } finally {
    isLoading.value = false
  }
}

function handleSelect(item: PlannedTreatmentItem) {
  // Check if already selected
  if (selectedItems.value.some(s => s.id === item.id)) {
    return
  }

  selectedItems.value = [...selectedItems.value, item]
  emit('update:modelValue', selectedItems.value)
  showSelector.value = false
}

function removeItem(itemId: string) {
  selectedItems.value = selectedItems.value.filter(i => i.id !== itemId)
  emit('update:modelValue', selectedItems.value)
}

// Sync with parent
watch(() => props.modelValue, (newVal) => {
  selectedItems.value = newVal || []
})

// Get treatment name from item
function getItemName(item: PlannedTreatmentItem): string {
  if (item.catalog_item?.names) {
    return item.catalog_item.names[locale.value] || item.catalog_item.names.es || item.catalog_item.internal_code
  }
  if (item.tooth_treatment) {
    return item.tooth_treatment.treatment_type
  }
  return t('treatmentPlans.unknownTreatment')
}

// Get price from item
function getItemPrice(item: PlannedTreatmentItem): number | undefined {
  return item.catalog_item?.default_price
}

// Get tooth info string
function getToothInfo(item: PlannedTreatmentItem): string | null {
  if (item.is_global) {
    return t('treatmentPlans.globalTreatment')
  }
  if (item.tooth_treatment?.tooth_number) {
    const tooth = item.tooth_treatment.tooth_number
    const surfaces = item.tooth_treatment.surfaces?.join(', ')
    return surfaces ? `#${tooth} (${surfaces})` : `#${tooth}`
  }
  return null
}

// Get plan display name
function getPlanLabel(item: PlannedTreatmentItem): string | null {
  if (!item.treatment_plan) return null
  return item.treatment_plan.title || item.treatment_plan.plan_number
}

// Items available for selection (not already selected)
const availableItems = computed(() => {
  const selectedIds = new Set(selectedItems.value.map(s => s.id))
  let items = pendingItems.value.filter(item => !selectedIds.has(item.id))

  // Filter by search query
  if (searchQuery.value.length >= 2) {
    const query = searchQuery.value.toLowerCase()
    items = items.filter((item) => {
      const name = getItemName(item).toLowerCase()
      const code = item.catalog_item?.internal_code?.toLowerCase() || ''
      return name.includes(query) || code.includes(query)
    })
  }

  return items
})

// Check if patient has pending treatments
const hasPendingTreatments = computed(() => {
  return pendingItems.value.length > 0
})
</script>

<template>
  <div class="space-y-3">
    <!-- No patient selected message -->
    <div
      v-if="!patientId"
      class="text-sm text-gray-500 dark:text-gray-400 text-center py-4"
    >
      {{ t('appointments.selectPatientFirst') }}
    </div>

    <!-- Loading state -->
    <div
      v-else-if="isLoading"
      class="flex items-center justify-center py-4"
    >
      <UIcon
        name="i-lucide-loader-2"
        class="w-5 h-5 animate-spin text-gray-400"
      />
    </div>

    <!-- No pending treatments message -->
    <div
      v-else-if="!hasPendingTreatments && selectedItems.length === 0"
      class="text-sm text-gray-500 dark:text-gray-400 text-center py-4 bg-gray-50 dark:bg-gray-800 rounded-lg"
    >
      <UIcon
        name="i-lucide-clipboard-list"
        class="w-8 h-8 mx-auto mb-2 text-gray-300"
      />
      <p>{{ t('appointments.noPendingTreatments') }}</p>
      <p class="text-xs mt-1">
        {{ t('appointments.createPlanFirst') }}
      </p>
    </div>

    <template v-else>
      <!-- Selected treatments list -->
      <div
        v-if="selectedItems.length > 0"
        class="space-y-2"
      >
        <div
          v-for="item in selectedItems"
          :key="item.id"
          class="flex items-center justify-between p-2 bg-primary-50 dark:bg-primary-900/20 rounded-lg"
        >
          <div class="min-w-0 flex-1">
            <p class="text-sm font-medium text-gray-900 dark:text-white truncate">
              {{ getItemName(item) }}
            </p>
            <div class="flex items-center gap-2 flex-wrap">
              <span
                v-if="item.catalog_item?.internal_code"
                class="text-xs text-gray-500"
              >
                {{ item.catalog_item.internal_code }}
              </span>
              <UBadge
                v-if="getToothInfo(item)"
                size="xs"
                color="neutral"
                variant="subtle"
              >
                {{ getToothInfo(item) }}
              </UBadge>
              <UBadge
                v-if="getPlanLabel(item)"
                size="xs"
                color="primary"
                variant="subtle"
              >
                {{ getPlanLabel(item) }}
              </UBadge>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <span
              v-if="getItemPrice(item)"
              class="text-sm font-semibold text-primary-600"
            >
              {{ formatPrice(getItemPrice(item), currency || 'EUR') }}
            </span>
            <UButton
              variant="ghost"
              color="neutral"
              icon="i-lucide-x"
              size="xs"
              @click="removeItem(item.id)"
            />
          </div>
        </div>
      </div>

      <!-- Add treatment button / selector -->
      <div v-if="!showSelector && availableItems.length > 0">
        <UButton
          variant="soft"
          color="primary"
          icon="i-lucide-plus"
          size="sm"
          block
          @click="showSelector = true"
        >
          {{ t('appointments.addTreatmentFromPlan') }}
        </UButton>
      </div>

      <!-- Selector when adding -->
      <div
        v-if="showSelector"
        class="border border-gray-200 dark:border-gray-700 rounded-lg p-3"
      >
        <div class="flex items-center justify-between mb-3">
          <span class="text-sm font-medium text-gray-700 dark:text-gray-300">
            {{ t('appointments.selectPendingTreatment') }}
          </span>
          <UButton
            variant="ghost"
            color="neutral"
            icon="i-lucide-x"
            size="xs"
            @click="showSelector = false"
          />
        </div>

        <!-- Search input -->
        <UInput
          v-model="searchQuery"
          :placeholder="placeholder || t('common.search')"
          icon="i-lucide-search"
          class="mb-3"
        />

        <!-- Items grid -->
        <div class="grid grid-cols-1 gap-2 max-h-60 overflow-y-auto">
          <button
            v-for="item in availableItems"
            :key="item.id"
            type="button"
            class="text-left p-3 rounded-lg border border-gray-200 dark:border-gray-700 hover:border-primary-500 hover:bg-primary-50 dark:hover:bg-primary-900/20 transition-colors"
            @click="handleSelect(item)"
          >
            <div class="flex items-start justify-between gap-2">
              <div class="min-w-0 flex-1">
                <p class="text-sm font-medium text-gray-900 dark:text-white line-clamp-1">
                  {{ getItemName(item) }}
                </p>
                <div class="flex items-center gap-2 mt-1 flex-wrap">
                  <span
                    v-if="item.catalog_item?.internal_code"
                    class="text-xs text-gray-500"
                  >
                    {{ item.catalog_item.internal_code }}
                  </span>
                  <UBadge
                    v-if="getToothInfo(item)"
                    size="xs"
                    color="neutral"
                    variant="subtle"
                  >
                    {{ getToothInfo(item) }}
                  </UBadge>
                  <UBadge
                    v-if="getPlanLabel(item)"
                    size="xs"
                    color="primary"
                    variant="subtle"
                  >
                    {{ getPlanLabel(item) }}
                  </UBadge>
                </div>
              </div>
              <span
                v-if="getItemPrice(item)"
                class="text-sm font-semibold text-primary-600 whitespace-nowrap"
              >
                {{ formatPrice(getItemPrice(item), currency || 'EUR') }}
              </span>
            </div>
          </button>

          <!-- Empty state -->
          <div
            v-if="availableItems.length === 0 && searchQuery.length >= 2"
            class="text-sm text-gray-500 text-center py-4"
          >
            {{ t('common.noResults') }}
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
