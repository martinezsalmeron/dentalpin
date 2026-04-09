<script setup lang="ts">
import type { BudgetItemCreate, TreatmentCatalogItem } from '~/types'

const props = defineProps<{
  open: boolean
  budgetId: string
  currency?: string
}>()

const emit = defineEmits<{
  'update:open': [value: boolean]
  'added': []
}>()

const { t } = useI18n()
const toast = useToast()
const { searchItems, getItemName, formatPrice } = useCatalog()
const { addItem } = useBudgets()

// Search state
const searchQuery = ref('')
const searchResults = ref<TreatmentCatalogItem[]>([])
const isSearching = ref(false)
const selectedItem = ref<TreatmentCatalogItem | null>(null)

// Item form
const form = reactive<BudgetItemCreate>({
  catalog_item_id: '',
  quantity: 1,
  tooth_number: undefined,
  surfaces: [],
  discount_type: undefined,
  discount_value: undefined,
  notes: ''
})

const isSubmitting = ref(false)

// Debounced search
let searchTimeout: ReturnType<typeof setTimeout> | null = null

watch(searchQuery, (val) => {
  if (searchTimeout) clearTimeout(searchTimeout)

  if (val.length < 2) {
    searchResults.value = []
    return
  }

  searchTimeout = setTimeout(async () => {
    await performSearch(val)
  }, 300)
})

async function performSearch(query: string) {
  isSearching.value = true
  try {
    const results = await searchItems(query, 20)
    // Cast to TreatmentCatalogItem for display
    searchResults.value = results as unknown as TreatmentCatalogItem[]
  } catch {
    searchResults.value = []
  } finally {
    isSearching.value = false
  }
}

function selectCatalogItem(item: TreatmentCatalogItem) {
  selectedItem.value = item
  form.catalog_item_id = item.id
  searchQuery.value = getItemName(item)
  searchResults.value = []
}

function clearSelection() {
  selectedItem.value = null
  form.catalog_item_id = ''
  searchQuery.value = ''
}

// Tooth surfaces
const toothSurfaces = ['M', 'O', 'D', 'V', 'L', 'P', 'I']

function toggleSurface(surface: string) {
  if (!form.surfaces) form.surfaces = []
  const index = form.surfaces.indexOf(surface)
  if (index >= 0) {
    form.surfaces.splice(index, 1)
  } else {
    form.surfaces.push(surface)
  }
}

// Calculate preview total
const previewTotal = computed(() => {
  if (!selectedItem.value) return 0

  const price = selectedItem.value.default_price || 0
  const subtotal = price * (form.quantity || 1)

  if (!form.discount_type || !form.discount_value) {
    return subtotal
  }

  if (form.discount_type === 'percentage') {
    return subtotal * (1 - form.discount_value / 100)
  }

  return subtotal - form.discount_value
})

// Submit
async function handleSubmit() {
  if (!form.catalog_item_id) return

  isSubmitting.value = true

  try {
    await addItem(props.budgetId, {
      catalog_item_id: form.catalog_item_id,
      quantity: form.quantity,
      tooth_number: form.tooth_number || undefined,
      surfaces: form.surfaces?.length ? form.surfaces : undefined,
      discount_type: form.discount_type || undefined,
      discount_value: form.discount_value || undefined,
      notes: form.notes || undefined
    })

    toast.add({
      title: t('common.success'),
      description: t('budget.messages.itemAdded'),
      color: 'success'
    })

    emit('added')
    close()
  } catch {
    toast.add({
      title: t('common.error'),
      description: t('budget.errors.create'),
      color: 'error'
    })
  } finally {
    isSubmitting.value = false
  }
}

function close() {
  resetForm()
  emit('update:open', false)
}

function resetForm() {
  selectedItem.value = null
  searchQuery.value = ''
  searchResults.value = []
  form.catalog_item_id = ''
  form.quantity = 1
  form.tooth_number = undefined
  form.surfaces = []
  form.discount_type = undefined
  form.discount_value = undefined
  form.notes = ''
}

// Reset form when modal opens
watch(() => props.open, (isOpen) => {
  if (isOpen) {
    resetForm()
  }
})
</script>

<template>
  <UModal
    :open="open"
    @update:open="emit('update:open', $event)"
  >
    <template #content>
      <UCard class="w-full max-w-lg">
        <template #header>
          <div class="flex items-center justify-between">
            <h2 class="text-lg font-semibold">
              {{ t('budget.items.add') }}
            </h2>
            <UButton
              variant="ghost"
              color="neutral"
              icon="i-lucide-x"
              @click="close"
            />
          </div>
        </template>

        <form
          class="space-y-4"
          @submit.prevent="handleSubmit"
        >
          <!-- Catalog item search -->
          <UFormField
            :label="t('budget.items.treatment')"
            required
          >
            <div class="relative">
              <UInput
                v-model="searchQuery"
                :placeholder="t('budget.items.searchCatalog')"
                icon="i-lucide-search"
                :loading="isSearching"
                @focus="searchQuery.length >= 2 && performSearch(searchQuery)"
              >
                <template
                  v-if="selectedItem"
                  #trailing
                >
                  <UButton
                    variant="ghost"
                    color="neutral"
                    icon="i-lucide-x"
                    size="xs"
                    class="-mr-2"
                    @click.stop="clearSelection"
                  />
                </template>
              </UInput>

              <!-- Search results dropdown -->
              <div
                v-if="searchResults.length > 0"
                class="absolute z-50 w-full mt-1 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg max-h-60 overflow-auto"
              >
                <div
                  v-for="item in searchResults"
                  :key="item.id"
                  class="p-3 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                  @click="selectCatalogItem(item)"
                >
                  <div class="flex items-center justify-between">
                    <div>
                      <p class="font-medium text-gray-900 dark:text-white">
                        {{ getItemName(item) }}
                      </p>
                      <p class="text-sm text-gray-500">
                        {{ item.internal_code }}
                      </p>
                    </div>
                    <span class="font-medium text-primary-600">
                      {{ formatPrice(item.default_price, currency || 'EUR') }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </UFormField>

          <!-- Selected item info -->
          <div
            v-if="selectedItem"
            class="p-3 bg-primary-50 dark:bg-primary-900/20 rounded-lg"
          >
            <div class="flex items-center justify-between">
              <div>
                <p class="font-medium text-gray-900 dark:text-white">
                  {{ getItemName(selectedItem) }}
                </p>
                <p class="text-sm text-gray-500">
                  {{ selectedItem.internal_code }}
                </p>
              </div>
              <span class="text-lg font-semibold text-primary-600">
                {{ formatPrice(selectedItem.default_price, currency || 'EUR') }}
              </span>
            </div>
          </div>

          <!-- Quantity -->
          <div class="grid grid-cols-2 gap-4">
            <UFormField :label="t('budget.items.quantity')">
              <UInput
                v-model.number="form.quantity"
                type="number"
                min="1"
                required
              />
            </UFormField>

            <UFormField :label="t('budget.items.toothNumber')">
              <UInput
                v-model.number="form.tooth_number"
                type="number"
                min="11"
                max="85"
                :placeholder="t('budget.items.toothNumberPlaceholder')"
              />
            </UFormField>
          </div>

          <!-- Tooth surfaces -->
          <UFormField
            v-if="form.tooth_number"
            :label="t('budget.items.surfaces')"
          >
            <div class="flex flex-wrap gap-2">
              <UButton
                v-for="surface in toothSurfaces"
                :key="surface"
                size="sm"
                :variant="form.surfaces?.includes(surface) ? 'solid' : 'outline'"
                :color="form.surfaces?.includes(surface) ? 'primary' : 'neutral'"
                @click="toggleSurface(surface)"
              >
                {{ surface }}
              </UButton>
            </div>
          </UFormField>

          <!-- Discount -->
          <div class="grid grid-cols-2 gap-4">
            <UFormField :label="t('budget.discountType')">
              <USelectMenu
                v-model="form.discount_type"
                :items="[
                  { label: '-', value: '' },
                  { label: t('budget.percentage'), value: 'percentage' },
                  { label: t('budget.absolute'), value: 'absolute' }
                ]"
                value-key="value"
              />
            </UFormField>
            <UFormField
              v-if="form.discount_type"
              :label="t('budget.discountValue')"
            >
              <UInput
                v-model.number="form.discount_value"
                type="number"
                step="0.01"
                min="0"
                :max="form.discount_type === 'percentage' ? 100 : undefined"
              />
            </UFormField>
          </div>

          <!-- Notes -->
          <UFormField :label="t('budget.items.notes')">
            <UTextarea
              v-model="form.notes"
              :placeholder="t('budget.items.notesPlaceholder')"
              :rows="2"
            />
          </UFormField>

          <!-- Preview total -->
          <div
            v-if="selectedItem"
            class="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg"
          >
            <span class="text-gray-600 dark:text-gray-400">{{ t('budget.items.lineTotal') }}</span>
            <span class="text-xl font-bold text-gray-900 dark:text-white">
              {{ formatPrice(previewTotal, currency || 'EUR') }}
            </span>
          </div>
        </form>

        <template #footer>
          <div class="flex justify-end gap-3">
            <UButton
              variant="outline"
              color="neutral"
              @click="close"
            >
              {{ t('common.cancel') }}
            </UButton>
            <UButton
              color="primary"
              icon="i-lucide-plus"
              :disabled="!form.catalog_item_id"
              :loading="isSubmitting"
              @click="handleSubmit"
            >
              {{ t('budget.items.add') }}
            </UButton>
          </div>
        </template>
      </UCard>
    </template>
  </UModal>
</template>
