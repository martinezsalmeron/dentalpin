<script setup lang="ts">
/**
 * PlanTreatmentList - Display treatment items in a plan
 *
 * Features:
 * - Hover linking with odontogram (highlight items when tooth hovered)
 * - Complete/remove item actions
 * - Pending and completed sections
 * - Drag & drop reorder (mouse + keyboard Alt+↑/↓)
 */

import type { PlannedTreatmentItem } from '~~/app/types'
import { VueDraggable } from 'vue-draggable-plus'

const props = defineProps<{
  items: PlannedTreatmentItem[]
  highlightedItems?: string[]
  readonly?: boolean
  /**
   * When true, the "mark complete" action stays available even if `readonly` is true.
   * Use for plans locked by an active budget — structural edits are blocked but
   * completing items is still a valid clinical action.
   */
  allowComplete?: boolean
  /** Plan status — drives empty-state guidance copy (draft shows 3-step onboarding). */
  planStatus?: string
}>()

const completeEnabled = computed(() => !props.readonly || props.allowComplete)

const emit = defineEmits<{
  'item-hover': [itemId: string | null]
  'item-complete': [itemId: string]
  'item-remove': [itemId: string]
  /** Fired after the user reorders pending items (drag or keyboard). */
  'reorder': [itemIds: string[]]
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

// Separate pending and completed items.
// `localPending` is a writable copy so VueDraggable can mutate it during drag.
// We sync it with props.items and flush a reorder event on drag end.
const localPending = ref<PlannedTreatmentItem[]>([])

function syncPendingFromProps() {
  localPending.value = props.items
    .filter(i => i.status === 'pending')
    .slice()
    .sort((a, b) => a.sequence_order - b.sequence_order)
}

watch(() => props.items, syncPendingFromProps, { immediate: true })

const completedItems = computed(() =>
  props.items
    .filter(i => i.status === 'completed')
    .slice()
    .sort((a, b) => a.sequence_order - b.sequence_order)
)

function emitReorder() {
  // Build full ordering: pending (reordered) first, completed last (original order).
  const ids = [
    ...localPending.value.map(i => i.id),
    ...completedItems.value.map(i => i.id)
  ]
  emit('reorder', ids)
}

function moveItem(index: number, delta: -1 | 1) {
  const next = index + delta
  if (next < 0 || next >= localPending.value.length) return
  const arr = [...localPending.value]
  const tmp = arr[index]!
  arr[index] = arr[next]!
  arr[next] = tmp
  localPending.value = arr
  emitReorder()
}

function handleKeydown(e: KeyboardEvent, index: number) {
  if (!e.altKey) return
  if (e.key === 'ArrowUp') {
    e.preventDefault()
    moveItem(index, -1)
  } else if (e.key === 'ArrowDown') {
    e.preventDefault()
    moveItem(index, 1)
  }
}

// Check if item is highlighted
function isHighlighted(itemId: string): boolean {
  return props.highlightedItems?.includes(itemId) ?? false
}

// Format item name: catalog name (localized) > clinical_type i18n key.
// The catalog link lives on the Treatment — check item.catalog_item first (item
// level, used for historical records), then item.treatment.catalog_item.
function getItemName(item: PlannedTreatmentItem): string {
  const names = item.catalog_item?.names || item.treatment?.catalog_item?.names
  if (names) {
    const name = names[locale.value] || names.es
    if (name) return name
  }
  const clinicalType = item.treatment?.clinical_type
  if (clinicalType) {
    const key = `odontogram.treatments.types.${clinicalType}`
    const translated = t(key)
    if (translated !== key) return translated
    return clinicalType
  }
  return t('clinical.plans.unknownTreatment')
}

function itemTeeth(item: PlannedTreatmentItem): number[] {
  return (item.treatment?.teeth ?? []).map(t => t.tooth_number)
}

function itemSurfaces(item: PlannedTreatmentItem): string[] {
  const first = item.treatment?.teeth?.[0]
  return (first?.surfaces as string[] | undefined) ?? []
}

function formatToothInfo(item: PlannedTreatmentItem): string {
  const teeth = itemTeeth(item)
  if (teeth.length === 0) return ''
  const label = teeth.length === 1
    ? `${t('clinical.tooth')} ${teeth[0]}`
    : `${t('clinical.tooth')} ${teeth.join(', ')}`
  const surfaces = itemSurfaces(item)
  return surfaces.length > 0 ? `${label} (${surfaces.join(', ')})` : label
}

function hasToothInfo(item: PlannedTreatmentItem): boolean {
  return itemTeeth(item).length > 0
}

function getItemPrice(item: PlannedTreatmentItem): number | undefined {
  const snap = item.treatment?.price_snapshot
  if (!snap) return undefined
  const parsed = Number(snap)
  return Number.isFinite(parsed) ? parsed : undefined
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
  <div class="space-y-[var(--density-gap,0.5rem)]">
    <!-- Empty state: guided 3-step onboarding for draft plans; plain text otherwise. -->
    <div
      v-if="items.length === 0 && planStatus === 'draft'"
      class="empty-draft-guide"
    >
      <div class="empty-draft-title">
        <UIcon
          name="i-lucide-sparkles"
          class="w-4 h-4 text-primary-accent"
        />
        <span>{{ t('clinical.plans.emptyDraft.title') }}</span>
      </div>
      <ol class="empty-draft-steps">
        <li>
          <span class="step-num">1</span>
          <span>{{ t('clinical.plans.emptyDraft.step1') }}</span>
        </li>
        <li>
          <span class="step-num">2</span>
          <span>{{ t('clinical.plans.emptyDraft.step2') }}</span>
        </li>
        <li>
          <span class="step-num">3</span>
          <span>{{ t('clinical.plans.emptyDraft.step3') }}</span>
        </li>
      </ol>
      <div class="empty-draft-arrow">
        <UIcon
          name="i-lucide-arrow-down-left"
          class="w-5 h-5 animate-bounce"
        />
        <span>{{ t('clinical.plans.emptyDraft.step1') }}</span>
      </div>
    </div>

    <div
      v-else-if="items.length === 0"
      class="text-center py-6 text-muted"
    >
      <UIcon
        name="i-lucide-list"
        class="w-8 h-8 mx-auto mb-2 opacity-50"
      />
      <p>{{ t('clinical.plans.noItems') }}</p>
    </div>

    <!-- Pending items (draggable). Disabled when readonly or fewer than 2 items. -->
    <VueDraggable
      v-model="localPending"
      :disabled="readonly || localPending.length < 2"
      handle=".drag-handle"
      :animation="180"
      ghost-class="plan-item-ghost"
      drag-class="plan-item-drag"
      class="space-y-[var(--density-gap,0.5rem)]"
      @end="emitReorder"
    >
      <div
        v-for="(item, index) in localPending"
        :key="item.id"
        tabindex="0"
        class="plan-item p-[var(--density-card-padding-y,0.75rem)_var(--density-card-padding-x,0.75rem)] rounded-token-md border transition-colors cursor-pointer outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-primary)]"
        :class="{
          'alert-surface-warning border-transparent': isHighlighted(item.id),
          'bg-surface border-default': !isHighlighted(item.id)
        }"
        :aria-label="t('clinical.plans.reorderHint')"
        @mouseenter="emit('item-hover', item.id)"
        @mouseleave="emit('item-hover', null)"
        @keydown="handleKeydown($event, index)"
      >
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2 min-w-0">
            <button
              v-if="!readonly && localPending.length > 1"
              type="button"
              class="drag-handle shrink-0 text-subtle hover:text-default cursor-grab active:cursor-grabbing"
              :title="t('clinical.plans.dragToReorder')"
              :aria-label="t('clinical.plans.dragToReorder')"
            >
              <UIcon
                name="i-lucide-grip-vertical"
                class="w-4 h-4"
              />
            </button>
            <span class="text-subtle text-caption tnum w-6 text-center shrink-0">
              {{ index + 1 }}.
            </span>
            <div class="min-w-0">
              <div class="font-medium truncate">
                {{ getItemName(item) }}
              </div>
              <div
                v-if="hasToothInfo(item)"
                class="text-sm text-muted"
              >
                {{ formatToothInfo(item) }}
              </div>
            </div>
          </div>
          <div class="flex items-center gap-2 shrink-0">
            <span
              v-if="getItemPrice(item) !== undefined"
              class="font-medium text-sm"
            >
              {{ formatCurrency(getItemPrice(item)) }}
            </span>
            <UButton
              v-if="completeEnabled"
              size="xs"
              variant="ghost"
              color="success"
              icon="i-lucide-check"
              :title="t('clinical.plans.markComplete')"
              @click.stop="openConfirmModal(item)"
            />
            <UButton
              v-if="!readonly"
              size="xs"
              variant="ghost"
              color="error"
              icon="i-lucide-trash-2"
              :title="t('clinical.plans.removeItem')"
              @click.stop="emit('item-remove', item.id)"
            />
          </div>
        </div>
      </div>
    </VueDraggable>

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
            class="p-2 rounded bg-surface-muted text-muted"
            @mouseenter="emit('item-hover', item.id)"
            @mouseleave="emit('item-hover', null)"
          >
            <div class="flex items-center gap-2">
              <UIcon
                name="i-lucide-check-circle"
                class="w-4 h-4 text-success-accent shrink-0"
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
              <div class="w-10 h-10 rounded-full bg-[var(--color-success-soft)] flex items-center justify-center">
                <UIcon
                  name="i-lucide-check"
                  class="w-5 h-5 text-success-accent"
                />
              </div>
              <h3 class="text-h2 text-default">
                {{ t('treatmentPlans.confirmations.completeItem') }}
              </h3>
            </div>
          </template>

          <div
            v-if="itemToComplete"
            class="space-y-3"
          >
            <div class="p-3 bg-surface-muted rounded-lg">
              <p class="font-medium text-default">
                {{ getItemName(itemToComplete) }}
              </p>
              <p
                v-if="hasToothInfo(itemToComplete)"
                class="text-sm text-muted mt-1"
              >
                {{ formatToothInfo(itemToComplete) }}
              </p>
            </div>
            <p class="text-sm text-muted">
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

<style scoped>
/* Onboarding empty state for a freshly created draft plan. */
.empty-draft-guide {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 18px 14px;
  border: 1px dashed #93C5FD;
  border-radius: 10px;
  background: linear-gradient(180deg, #EFF6FF 0%, #FFFFFF 100%);
}

:root.dark .empty-draft-guide {
  border-color: rgba(59, 130, 246, 0.45);
  background: linear-gradient(180deg, rgba(59, 130, 246, 0.08) 0%, rgba(24, 24, 27, 0) 100%);
}

.empty-draft-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  font-size: 14px;
  color: #1E40AF;
}

:root.dark .empty-draft-title {
  color: #93C5FD;
}

.empty-draft-steps {
  display: flex;
  flex-direction: column;
  gap: 8px;
  list-style: none;
  padding: 0;
  margin: 0;
}

.empty-draft-steps li {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  font-size: 13px;
  line-height: 1.35;
  color: #334155;
}

:root.dark .empty-draft-steps li {
  color: #CBD5E1;
}

.step-num {
  flex-shrink: 0;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #3B82F6;
  color: white;
  font-size: 12px;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.empty-draft-arrow {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  margin-top: 2px;
  font-size: 12px;
  font-weight: 500;
  color: #1D4ED8;
  background: #DBEAFE;
  border-radius: 8px;
}

:root.dark .empty-draft-arrow {
  background: rgba(59, 130, 246, 0.15);
  color: #BFDBFE;
}

/* Placeholder shown in the slot where the dragged item will land. */
.plan-item-ghost {
  opacity: 0.4;
  background: #EFF6FF;
  border-style: dashed !important;
}

:root.dark .plan-item-ghost {
  background: rgba(59, 130, 246, 0.1);
}

/* Visual style of the item while being dragged. */
.plan-item-drag {
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
  transform: rotate(1deg);
}
</style>
