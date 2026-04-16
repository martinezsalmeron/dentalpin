<script setup lang="ts">
/**
 * PlanTreatmentList - Display treatment items in a plan
 *
 * Features:
 * - Hover linking with odontogram (highlight items when tooth hovered)
 * - Complete/remove item actions
 * - Pending and completed sections
 */

import type { PlannedTreatmentItem } from '~/types'

const props = defineProps<{
  items: PlannedTreatmentItem[]
  highlightedItems?: string[]
  readonly?: boolean
}>()

const emit = defineEmits<{
  'item-hover': [itemId: string | null]
  'item-complete': [itemId: string]
  'item-remove': [itemId: string]
}>()

const { t, locale } = useI18n()

// Confirmation modal state
const showConfirmModal = ref(false)
const itemToComplete = ref<PlannedTreatmentItem | null>(null)

function openConfirmModal(item: PlannedTreatmentItem) {
  itemToComplete.value = item
  showConfirmModal.value = true
}

function confirmComplete() {
  if (itemToComplete.value) {
    emit('item-complete', itemToComplete.value.id)
  }
  showConfirmModal.value = false
  itemToComplete.value = null
}

function cancelComplete() {
  showConfirmModal.value = false
  itemToComplete.value = null
}

// Separate pending and completed items
const pendingItems = computed(() =>
  props.items.filter(i => i.status === 'pending')
)

const completedItems = computed(() =>
  props.items.filter(i => i.status === 'completed')
)

// Check if item is highlighted
function isHighlighted(itemId: string): boolean {
  return props.highlightedItems?.includes(itemId) ?? false
}

// Format item name
function getItemName(item: PlannedTreatmentItem): string {
  // Try catalog item names (localized)
  if (item.catalog_item?.names) {
    const name = item.catalog_item.names[locale.value] || item.catalog_item.names.es
    if (name) return name
  }

  // Try tooth_treatment for odontogram treatments
  if (item.tooth_treatment?.treatment_type) {
    const key = `odontogram.treatments.types.${item.tooth_treatment.treatment_type}`
    const translated = t(key)
    if (translated !== key) return translated
  }

  // Try treatment_type directly
  if (item.treatment_type) {
    const key = `odontogram.treatments.types.${item.treatment_type}`
    const translated = t(key)
    if (translated !== key) return translated
    return item.treatment_type
  }

  return item.description || t('clinical.plans.unknownTreatment')
}

// Format tooth info
function formatToothInfo(item: PlannedTreatmentItem): string {
  const toothNumber = item.tooth_number || item.tooth_treatment?.tooth_number
  if (!toothNumber) return ''

  let info = `${t('clinical.tooth')} ${toothNumber}`
  const surfaces = item.surfaces || item.tooth_treatment?.surfaces
  if (surfaces && surfaces.length > 0) {
    info += ` (${surfaces.join(', ')})`
  }
  return info
}

// Check if item has tooth info
function hasToothInfo(item: PlannedTreatmentItem): boolean {
  return !!(item.tooth_number || item.tooth_treatment?.tooth_number)
}

// Format currency
function formatCurrency(amount: number | undefined): string {
  if (amount === undefined) return ''
  return new Intl.NumberFormat(locale.value, {
    style: 'currency',
    currency: 'EUR'
  }).format(amount)
}
</script>

<template>
  <div class="space-y-2">
    <!-- No items -->
    <div
      v-if="items.length === 0"
      class="text-center py-6 text-gray-500 dark:text-gray-400"
    >
      <UIcon
        name="i-lucide-list"
        class="w-8 h-8 mx-auto mb-2 opacity-50"
      />
      <p>{{ t('clinical.plans.noItems') }}</p>
    </div>

    <!-- Pending items -->
    <div
      v-for="(item, index) in pendingItems"
      :key="item.id"
      class="p-3 rounded-lg border transition-colors cursor-pointer"
      :class="{
        'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-300 dark:border-yellow-700': isHighlighted(item.id),
        'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700': !isHighlighted(item.id)
      }"
      @mouseenter="emit('item-hover', item.id)"
      @mouseleave="emit('item-hover', null)"
    >
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3 min-w-0">
          <span class="text-gray-400 text-sm w-6 text-center shrink-0">
            {{ index + 1 }}.
          </span>
          <div class="min-w-0">
            <div class="font-medium truncate">
              {{ getItemName(item) }}
            </div>
            <div
              v-if="hasToothInfo(item)"
              class="text-sm text-gray-500 dark:text-gray-400"
            >
              {{ formatToothInfo(item) }}
            </div>
          </div>
        </div>
        <div class="flex items-center gap-2 shrink-0">
          <span
            v-if="item.price"
            class="font-medium text-sm"
          >
            {{ formatCurrency(item.price) }}
          </span>
          <template v-if="!readonly">
            <UButton
              size="xs"
              variant="ghost"
              color="green"
              icon="i-lucide-check"
              class="hover:bg-green-100 dark:hover:bg-green-900/40 hover:text-green-700 dark:hover:text-green-300"
              :title="t('clinical.plans.markComplete')"
              @click.stop="openConfirmModal(item)"
            />
            <UButton
              size="xs"
              variant="ghost"
              color="red"
              icon="i-lucide-trash-2"
              :title="t('clinical.plans.removeItem')"
              @click.stop="emit('item-remove', item.id)"
            />
          </template>
        </div>
      </div>
    </div>

    <!-- Completed items (collapsible) -->
    <UAccordion
      v-if="completedItems.length > 0"
      :items="[{
        label: `${t('common.completed')} (${completedItems.length})`,
        slot: 'completed'
      }]"
      class="mt-3"
    >
      <template #completed>
        <div class="space-y-2 pt-2">
          <div
            v-for="item in completedItems"
            :key="item.id"
            class="p-2 rounded bg-gray-50 dark:bg-gray-800 text-gray-500 dark:text-gray-400"
            @mouseenter="emit('item-hover', item.id)"
            @mouseleave="emit('item-hover', null)"
          >
            <div class="flex items-center gap-2">
              <UIcon
                name="i-lucide-check-circle"
                class="w-4 h-4 text-green-500 shrink-0"
              />
              <span class="line-through truncate">
                {{ getItemName(item) }}
              </span>
              <span
                v-if="hasToothInfo(item)"
                class="text-xs"
              >
                - {{ formatToothInfo(item) }}
              </span>
            </div>
          </div>
        </div>
      </template>
    </UAccordion>

    <!-- Confirmation Modal -->
    <UModal v-model:open="showConfirmModal">
      <template #content>
        <UCard>
          <template #header>
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center">
                <UIcon
                  name="i-lucide-check"
                  class="w-5 h-5 text-green-600 dark:text-green-400"
                />
              </div>
              <h3 class="font-semibold text-gray-900 dark:text-white">
                {{ t('treatmentPlans.confirmations.completeItem') }}
              </h3>
            </div>
          </template>

          <div
            v-if="itemToComplete"
            class="space-y-3"
          >
            <div class="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <p class="font-medium text-gray-900 dark:text-white">
                {{ getItemName(itemToComplete) }}
              </p>
              <p
                v-if="hasToothInfo(itemToComplete)"
                class="text-sm text-gray-500 dark:text-gray-400 mt-1"
              >
                {{ formatToothInfo(itemToComplete) }}
              </p>
            </div>
            <p class="text-sm text-gray-500 dark:text-gray-400">
              {{ t('treatmentPlans.confirmations.completeItemDescription') }}
            </p>
          </div>

          <template #footer>
            <div class="flex justify-end gap-2">
              <UButton
                color="neutral"
                variant="ghost"
                @click="cancelComplete"
              >
                {{ t('actions.cancel') }}
              </UButton>
              <UButton
                color="success"
                variant="solid"
                icon="i-lucide-check"
                class="font-semibold"
                @click="confirmComplete"
              >
                {{ t('treatmentPlans.actions.complete') }}
              </UButton>
            </div>
          </template>
        </UCard>
      </template>
    </UModal>
  </div>
</template>
