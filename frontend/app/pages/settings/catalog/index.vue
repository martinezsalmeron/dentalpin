<script setup lang="ts">
import type { TreatmentCatalogItem, TreatmentCatalogItemUpdate, TreatmentCatalogItemCreate, TreatmentCatalogCategory, VatTypeBrief } from '~/types'

const { t, locale } = useI18n()
const { isAdmin } = usePermissions()
const catalog = useCatalog()

// Modal state
const showModal = ref(false)
const editingItem = ref<TreatmentCatalogItem | null>(null)
const isSaving = ref(false)

// Delete confirmation state
const showDeleteConfirm = ref(false)
const itemToDelete = ref<TreatmentCatalogItem | null>(null)
const isDeleting = ref(false)

// Filters
const searchQuery = ref('')
const selectedCategoryId = ref<string | undefined>(undefined)

// Track which categories are expanded (all expanded by default)
const expandedCategories = ref<Set<string>>(new Set())

// Load data on mount
onMounted(async () => {
  await Promise.all([
    catalog.fetchCategories(),
    catalog.fetchItems({ pageSize: 500 }) // Load all items for grouping
  ])
  // Expand all categories by default
  expandedCategories.value = new Set(catalog.categories.value.map(c => c.id))
})

// Filter items when search or category changes
watch([searchQuery, selectedCategoryId], () => {
  catalog.fetchItems({
    pageSize: 500, // Load all for grouping
    search: searchQuery.value || undefined,
    categoryId: selectedCategoryId.value
  })
})

// Group items by category
interface CategoryGroup {
  category: TreatmentCatalogCategory
  items: TreatmentCatalogItem[]
}

const groupedItems = computed<CategoryGroup[]>(() => {
  // If a specific category is selected, don't group
  if (selectedCategoryId.value) {
    return []
  }

  // Group items by category_id
  const groups = new Map<string, TreatmentCatalogItem[]>()
  for (const item of catalog.items.value) {
    const categoryId = item.category_id
    if (!groups.has(categoryId)) {
      groups.set(categoryId, [])
    }
    groups.get(categoryId)!.push(item)
  }

  // Convert to array with category info, sorted by display_order
  const result: CategoryGroup[] = []
  const sortedCategories = [...catalog.categories.value].sort((a, b) => a.display_order - b.display_order)
  for (const category of sortedCategories) {
    const items = groups.get(category.id)
    if (items && items.length > 0) {
      result.push({ category, items })
    }
  }

  return result
})

// Check if we should show grouped view
const showGroupedView = computed(() => !selectedCategoryId.value && groupedItems.value.length > 0)

// Toggle category expansion
function toggleCategory(categoryId: string) {
  if (expandedCategories.value.has(categoryId)) {
    expandedCategories.value.delete(categoryId)
  } else {
    expandedCategories.value.add(categoryId)
  }
  // Force reactivity
  expandedCategories.value = new Set(expandedCategories.value)
}

function isCategoryExpanded(categoryId: string): boolean {
  return expandedCategories.value.has(categoryId)
}

// Expand/collapse all
function expandAll() {
  expandedCategories.value = new Set(catalog.categories.value.map(c => c.id))
}

function collapseAll() {
  expandedCategories.value = new Set()
}

// Pagination (for filtered view)
function handlePageChange(page: number) {
  catalog.fetchItems({
    page,
    search: searchQuery.value || undefined,
    categoryId: selectedCategoryId.value
  })
}

// Create/Edit modal
function openCreateModal() {
  editingItem.value = null
  showModal.value = true
}

function openEditModal(item: TreatmentCatalogItem) {
  editingItem.value = item
  showModal.value = true
}

async function handleCreateItem(data: TreatmentCatalogItemCreate) {
  isSaving.value = true
  const result = await catalog.createItem(data)
  isSaving.value = false

  if (result) {
    showModal.value = false
  }
}

async function handleSaveItem(data: TreatmentCatalogItemUpdate) {
  if (!editingItem.value) return

  isSaving.value = true
  const result = await catalog.updateItem(editingItem.value.id, data)
  isSaving.value = false

  if (result) {
    showModal.value = false
    editingItem.value = null
  }
}

// Delete confirmation
function confirmDelete(item: TreatmentCatalogItem) {
  itemToDelete.value = item
  showDeleteConfirm.value = true
}

async function handleDeleteItem() {
  if (!itemToDelete.value) return

  isDeleting.value = true
  const result = await catalog.deleteItem(itemToDelete.value.id)
  isDeleting.value = false

  if (result) {
    showDeleteConfirm.value = false
    itemToDelete.value = null
  }
}

// Helpers
function getItemName(item: TreatmentCatalogItem): string {
  return catalog.getItemName(item)
}

function getCategoryName(categoryId: string): string {
  const category = catalog.categories.value.find(c => c.id === categoryId)
  return category ? catalog.getCategoryName(category) : '-'
}

function getVatTypeLabel(vatType: VatTypeBrief | undefined): string {
  if (!vatType) return '-'
  return vatType.names[locale.value] || vatType.names.es || vatType.names.en || '-'
}

function getVatTypeBadgeColor(vatType: VatTypeBrief | undefined): string {
  if (!vatType) return 'neutral'
  // Color based on rate: 0% = green, < 10% = yellow, >= 10% = red
  if (vatType.rate === 0) return 'green'
  if (vatType.rate < 10) return 'yellow'
  return 'red'
}

// Category options for filter
const categoryOptions = computed(() => [
  { value: undefined, label: t('common.all') },
  ...catalog.activeCategories.value.map(c => ({
    value: c.id,
    label: catalog.getCategoryName(c)
  }))
])
</script>

<template>
  <div class="space-y-6">
    <!-- Page header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
          {{ t('catalog.title') }}
        </h1>
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
          {{ t('catalog.description') }}
        </p>
      </div>
      <div class="flex items-center gap-2">
        <UButton
          v-if="isAdmin"
          icon="i-lucide-plus"
          @click="openCreateModal"
        >
          {{ t('catalog.newItem') }}
        </UButton>
        <NuxtLink to="/settings">
          <UButton
            variant="ghost"
            icon="i-lucide-arrow-left"
          >
            {{ t('common.back') }}
          </UButton>
        </NuxtLink>
      </div>
    </div>

    <!-- Filters -->
    <UCard>
      <div class="flex flex-col sm:flex-row gap-4">
        <div class="flex-1">
          <UInput
            v-model="searchQuery"
            icon="i-lucide-search"
            :placeholder="t('catalog.searchPlaceholder')"
          />
        </div>
        <div class="w-full sm:w-64">
          <USelect
            v-model="selectedCategoryId"
            :items="categoryOptions"
            value-key="value"
            label-key="label"
            :placeholder="t('catalog.selectCategory')"
          />
        </div>
      </div>
    </UCard>

    <!-- Items list - Grouped View -->
    <div
      v-if="showGroupedView"
      class="space-y-4"
    >
      <!-- Header with expand/collapse buttons -->
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <h2 class="font-semibold text-gray-900 dark:text-white">
            {{ t('catalog.items') }}
          </h2>
          <UBadge
            variant="subtle"
            color="neutral"
          >
            {{ catalog.totalItems.value }}
          </UBadge>
        </div>
        <div class="flex gap-2">
          <UButton
            variant="ghost"
            size="xs"
            icon="i-lucide-chevrons-down"
            @click="expandAll"
          >
            {{ t('catalog.expandAll') }}
          </UButton>
          <UButton
            variant="ghost"
            size="xs"
            icon="i-lucide-chevrons-up"
            @click="collapseAll"
          >
            {{ t('catalog.collapseAll') }}
          </UButton>
        </div>
      </div>

      <!-- Loading state -->
      <div
        v-if="catalog.loading.value"
        class="space-y-3"
      >
        <USkeleton class="h-16 w-full" />
        <USkeleton class="h-16 w-full" />
        <USkeleton class="h-16 w-full" />
      </div>

      <!-- Category groups -->
      <template v-else>
        <UCard
          v-for="group in groupedItems"
          :key="group.category.id"
          class="overflow-hidden"
        >
          <!-- Category header (clickable) -->
          <template #header>
            <button
              class="w-full flex items-center justify-between py-1 text-left"
              @click="toggleCategory(group.category.id)"
            >
              <div class="flex items-center gap-3">
                <UIcon
                  :name="isCategoryExpanded(group.category.id) ? 'i-lucide-chevron-down' : 'i-lucide-chevron-right'"
                  class="w-5 h-5 text-gray-400 transition-transform"
                />
                <UIcon
                  v-if="group.category.icon"
                  :name="group.category.icon"
                  class="w-5 h-5 text-primary-500"
                />
                <span class="font-semibold text-gray-900 dark:text-white">
                  {{ catalog.getCategoryName(group.category) }}
                </span>
                <UBadge
                  variant="subtle"
                  color="neutral"
                  size="xs"
                >
                  {{ group.items.length }}
                </UBadge>
              </div>
            </button>
          </template>

          <!-- Items table (collapsible) -->
          <div
            v-show="isCategoryExpanded(group.category.id)"
            class="overflow-x-auto -mx-4 sm:-mx-6"
          >
            <table class="w-full">
              <thead>
                <tr class="border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
                  <th class="text-left py-2 px-4 font-medium text-gray-500 dark:text-gray-400 text-sm">
                    {{ t('catalog.code') }}
                  </th>
                  <th class="text-left py-2 px-4 font-medium text-gray-500 dark:text-gray-400 text-sm">
                    {{ t('catalog.name') }}
                  </th>
                  <th class="text-right py-2 px-4 font-medium text-gray-500 dark:text-gray-400 text-sm">
                    {{ t('catalog.price') }}
                  </th>
                  <th class="text-center py-2 px-4 font-medium text-gray-500 dark:text-gray-400 text-sm">
                    {{ t('catalog.vatType') }}
                  </th>
                  <th class="text-center py-2 px-4 font-medium text-gray-500 dark:text-gray-400 text-sm">
                    {{ t('catalog.duration') }}
                  </th>
                  <th class="text-right py-2 px-4 font-medium text-gray-500 dark:text-gray-400 text-sm" />
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
                <tr
                  v-for="item in group.items"
                  :key="item.id"
                  class="hover:bg-gray-50 dark:hover:bg-gray-800"
                >
                  <td class="py-2.5 px-4">
                    <span class="font-mono text-sm text-gray-600 dark:text-gray-400">
                      {{ item.internal_code }}
                    </span>
                  </td>
                  <td class="py-2.5 px-4">
                    <span class="font-medium text-gray-900 dark:text-white">
                      {{ getItemName(item) }}
                    </span>
                    <UBadge
                      v-if="item.is_system"
                      variant="subtle"
                      color="blue"
                      class="ml-2"
                      size="xs"
                    >
                      {{ t('catalog.system') }}
                    </UBadge>
                    <UBadge
                      v-if="!item.is_active"
                      variant="subtle"
                      color="red"
                      class="ml-2"
                      size="xs"
                    >
                      {{ t('common.inactive') }}
                    </UBadge>
                  </td>
                  <td class="py-2.5 px-4 text-right font-medium">
                    {{ catalog.formatPrice(item.default_price, item.currency) }}
                  </td>
                  <td class="py-2.5 px-4 text-center">
                    <UBadge
                      :color="getVatTypeBadgeColor(item.vat_type)"
                      variant="subtle"
                      size="xs"
                    >
                      {{ getVatTypeLabel(item.vat_type) }}
                    </UBadge>
                  </td>
                  <td class="py-2.5 px-4 text-center text-gray-600 dark:text-gray-400">
                    {{ item.default_duration_minutes ? `${item.default_duration_minutes} min` : '-' }}
                  </td>
                  <td class="py-2.5 px-4 text-right">
                    <div
                      v-if="isAdmin"
                      class="flex items-center justify-end gap-1"
                    >
                      <UButton
                        icon="i-lucide-pencil"
                        size="xs"
                        variant="ghost"
                        color="neutral"
                        @click="openEditModal(item)"
                      />
                      <UButton
                        v-if="!item.is_system"
                        icon="i-lucide-trash-2"
                        size="xs"
                        variant="ghost"
                        color="error"
                        @click="confirmDelete(item)"
                      />
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </UCard>
      </template>
    </div>

    <!-- Items list - Flat View (when category is filtered) -->
    <UCard v-else>
      <template #header>
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <UIcon
              name="i-lucide-list"
              class="w-5 h-5 text-primary-500"
            />
            <h2 class="font-semibold text-gray-900 dark:text-white">
              {{ t('catalog.items') }}
            </h2>
            <UBadge
              variant="subtle"
              color="neutral"
            >
              {{ catalog.totalItems.value }}
            </UBadge>
          </div>
        </div>
      </template>

      <!-- Loading state -->
      <div
        v-if="catalog.loading.value"
        class="space-y-3"
      >
        <USkeleton class="h-12 w-full" />
        <USkeleton class="h-12 w-full" />
        <USkeleton class="h-12 w-full" />
      </div>

      <!-- Empty state -->
      <div
        v-else-if="catalog.items.value.length === 0"
        class="text-center py-12 text-gray-500 dark:text-gray-400"
      >
        <UIcon
          name="i-lucide-package"
          class="w-12 h-12 mx-auto mb-4 opacity-50"
        />
        <p>{{ t('catalog.noItems') }}</p>
      </div>

      <!-- Items table -->
      <div
        v-else
        class="overflow-x-auto"
      >
        <table class="w-full">
          <thead>
            <tr class="border-b border-gray-200 dark:border-gray-700">
              <th class="text-left py-3 px-4 font-medium text-gray-500 dark:text-gray-400">
                {{ t('catalog.code') }}
              </th>
              <th class="text-left py-3 px-4 font-medium text-gray-500 dark:text-gray-400">
                {{ t('catalog.name') }}
              </th>
              <th class="text-left py-3 px-4 font-medium text-gray-500 dark:text-gray-400">
                {{ t('catalog.category') }}
              </th>
              <th class="text-right py-3 px-4 font-medium text-gray-500 dark:text-gray-400">
                {{ t('catalog.price') }}
              </th>
              <th class="text-center py-3 px-4 font-medium text-gray-500 dark:text-gray-400">
                {{ t('catalog.vatType') }}
              </th>
              <th class="text-center py-3 px-4 font-medium text-gray-500 dark:text-gray-400">
                {{ t('catalog.duration') }}
              </th>
              <th class="text-right py-3 px-4 font-medium text-gray-500 dark:text-gray-400" />
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
            <tr
              v-for="item in catalog.items.value"
              :key="item.id"
              class="hover:bg-gray-50 dark:hover:bg-gray-800"
            >
              <td class="py-3 px-4">
                <span class="font-mono text-sm text-gray-600 dark:text-gray-400">
                  {{ item.internal_code }}
                </span>
              </td>
              <td class="py-3 px-4">
                <span class="font-medium text-gray-900 dark:text-white">
                  {{ getItemName(item) }}
                </span>
                <UBadge
                  v-if="item.is_system"
                  variant="subtle"
                  color="blue"
                  class="ml-2"
                  size="xs"
                >
                  {{ t('catalog.system') }}
                </UBadge>
                <UBadge
                  v-if="!item.is_active"
                  variant="subtle"
                  color="red"
                  class="ml-2"
                  size="xs"
                >
                  {{ t('common.inactive') }}
                </UBadge>
              </td>
              <td class="py-3 px-4 text-gray-600 dark:text-gray-400">
                {{ getCategoryName(item.category_id) }}
              </td>
              <td class="py-3 px-4 text-right font-medium">
                {{ catalog.formatPrice(item.default_price, item.currency) }}
              </td>
              <td class="py-3 px-4 text-center">
                <UBadge
                  :color="getVatTypeBadgeColor(item.vat_type)"
                  variant="subtle"
                  size="xs"
                >
                  {{ getVatTypeLabel(item.vat_type) }}
                </UBadge>
              </td>
              <td class="py-3 px-4 text-center text-gray-600 dark:text-gray-400">
                {{ item.default_duration_minutes ? `${item.default_duration_minutes} min` : '-' }}
              </td>
              <td class="py-3 px-4 text-right">
                <div
                  v-if="isAdmin"
                  class="flex items-center justify-end gap-1"
                >
                  <UButton
                    icon="i-lucide-pencil"
                    size="xs"
                    variant="ghost"
                    color="neutral"
                    @click="openEditModal(item)"
                  />
                  <UButton
                    v-if="!item.is_system"
                    icon="i-lucide-trash-2"
                    size="xs"
                    variant="ghost"
                    color="error"
                    @click="confirmDelete(item)"
                  />
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div
        v-if="catalog.totalPages.value > 1"
        class="flex justify-center pt-4 border-t border-gray-200 dark:border-gray-700 mt-4"
      >
        <UPagination
          :model-value="catalog.currentPage.value"
          :total="catalog.totalItems.value"
          :page-count="catalog.pageSize.value"
          @update:model-value="handlePageChange"
        />
      </div>
    </UCard>

    <!-- Create/Edit Modal -->
    <CatalogItemModal
      v-model:open="showModal"
      :item="editingItem"
      :categories="catalog.categories.value"
      :loading="isSaving"
      @create="handleCreateItem"
      @save="handleSaveItem"
    />

    <!-- Delete Confirmation Modal -->
    <UModal v-model:open="showDeleteConfirm">
      <template #content>
        <div class="bg-white dark:bg-gray-900 rounded-lg shadow-xl p-6 max-w-md">
          <div class="flex items-start gap-4">
            <div class="flex-shrink-0 w-10 h-10 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center">
              <UIcon
                name="i-lucide-trash-2"
                class="w-5 h-5 text-red-600 dark:text-red-400"
              />
            </div>
            <div class="flex-1">
              <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
                {{ t('catalog.deleteItem') }}
              </h3>
              <p class="mt-2 text-sm text-gray-500 dark:text-gray-400">
                {{ t('catalog.deleteItemConfirm', { name: itemToDelete ? getItemName(itemToDelete) : '' }) }}
              </p>
              <p class="mt-1 text-sm text-gray-400 dark:text-gray-500">
                {{ t('catalog.deleteItemNote') }}
              </p>
            </div>
          </div>
          <div class="flex justify-end gap-2 mt-6">
            <UButton
              variant="ghost"
              @click="showDeleteConfirm = false"
            >
              {{ t('common.cancel') }}
            </UButton>
            <UButton
              color="error"
              :loading="isDeleting"
              @click="handleDeleteItem"
            >
              {{ t('common.delete') }}
            </UButton>
          </div>
        </div>
      </template>
    </UModal>
  </div>
</template>
