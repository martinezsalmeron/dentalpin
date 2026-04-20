<script setup lang="ts">
import type { TreatmentCatalogItem, ApiResponse } from '~/types'

const props = defineProps<{
  modelValue?: TreatmentCatalogItem | null
  placeholder?: string
  currency?: string
  inModal?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [item: TreatmentCatalogItem | null]
}>()

const { t, locale } = useI18n()
const api = useApi()
const { searchItems, getItemName, formatPrice } = useCatalog()

// State
const popularItems = ref<TreatmentCatalogItem[]>([])
const searchResults = ref<TreatmentCatalogItem[]>([])
const isSearching = ref(false)
const isLoadingPopular = ref(false)
const selectedItem = ref<TreatmentCatalogItem | null>(props.modelValue || null)

// Load popular items on mount
onMounted(async () => {
  await loadPopularItems()
})

async function loadPopularItems() {
  isLoadingPopular.value = true
  try {
    const response = await api.get<ApiResponse<TreatmentCatalogItem[]>>(
      '/api/v1/catalog/items/popular?limit=8'
    )
    popularItems.value = response.data
  } catch {
    popularItems.value = []
  } finally {
    isLoadingPopular.value = false
  }
}

async function handleSearch(query: string) {
  if (!query || query.length < 2) {
    searchResults.value = []
    return
  }

  isSearching.value = true
  try {
    const results = await searchItems(query, 12)
    searchResults.value = results as unknown as TreatmentCatalogItem[]
  } catch {
    searchResults.value = []
  } finally {
    isSearching.value = false
  }
}

function handleSelect(item: TreatmentCatalogItem | null) {
  selectedItem.value = item
  emit('update:modelValue', item)
}

// Sync with parent
watch(() => props.modelValue, (newVal) => {
  selectedItem.value = newVal || null
})

// Get category name from item
function getCategoryName(item: TreatmentCatalogItem): string {
  if (item.category && item.category.names) {
    return item.category.names[locale.value] || item.category.names.es || ''
  }
  return ''
}
</script>

<template>
  <div class="relative">
    <!-- Selected item display -->
    <div
      v-if="selectedItem"
      class="p-3 bg-[var(--color-primary-soft)] rounded-lg"
    >
      <div class="flex items-center justify-between">
        <div class="min-w-0 flex-1">
          <p class="font-medium text-default">
            {{ getItemName(selectedItem) }}
          </p>
          <div class="flex items-center gap-2 mt-1">
            <span class="text-caption text-subtle">{{ selectedItem.internal_code }}</span>
            <UBadge
              v-if="getCategoryName(selectedItem)"
              size="xs"
              color="neutral"
              variant="subtle"
            >
              {{ getCategoryName(selectedItem) }}
            </UBadge>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <span class="text-h1 text-default text-primary-accent">
            {{ formatPrice(selectedItem.default_price, currency || 'EUR') }}
          </span>
          <UButton
            variant="ghost"
            color="neutral"
            icon="i-lucide-x"
            size="sm"
            @click="handleSelect(null)"
          />
        </div>
      </div>
    </div>

    <!-- Visual selector when no selection -->
    <VisualSelector
      v-else
      :model-value="selectedItem"
      :initial-items="popularItems"
      :search-results="searchResults"
      :is-searching="isSearching || isLoadingPopular"
      :placeholder="placeholder || t('budget.items.searchCatalog')"
      :empty-label="t('selector.noCommonTreatments')"
      :grid-cols="2"
      :in-modal="inModal"
      @update:model-value="handleSelect"
      @search="handleSearch"
    >
      <template #item="{ item }">
        <div class="space-y-1">
          <p class="text-sm font-medium text-default line-clamp-1">
            {{ getItemName(item) }}
          </p>
          <div class="flex items-center justify-between">
            <span class="text-caption text-subtle">{{ item.internal_code }}</span>
            <span class="text-sm font-semibold text-primary-accent">
              {{ formatPrice(item.default_price, currency || 'EUR') }}
            </span>
          </div>
          <UBadge
            v-if="getCategoryName(item)"
            size="xs"
            color="neutral"
            variant="subtle"
            class="truncate max-w-full"
          >
            {{ getCategoryName(item) }}
          </UBadge>
        </div>
      </template>
    </VisualSelector>
  </div>
</template>
