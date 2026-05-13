<script setup lang="ts">
import type { DropdownMenuItem } from '@nuxt/ui'
import type { BudgetItem, InvoiceListItem, PaginatedResponse, SignatureCreate } from '~~/app/types'
import PublicBudgetLinkCard from '../../components/budget/PublicBudgetLinkCard.vue'
import BudgetSignatureCard from '../../components/budget/BudgetSignatureCard.vue'

const route = useRoute()
const router = useRouter()
const { t, locale } = useI18n()
const toast = useToast()
const { can } = usePermissions()
const api = useApi()

const {
  currentBudget,
  isLoading,
  fetchBudget,
  updateBudget,
  removeItem,
  sendBudget,
  acceptBudget,
  rejectBudget,
  cancelBudget,
  duplicateBudget,
  downloadPDF,
  canEdit,
  canSend,
  canAccept,
  canCancel
} = useBudgets()

const hasActiveInvoice = ref(false)

// Check if budget can be invoiced (budget accepted and has uninvoiced items)
function canInvoice(): boolean {
  if (!currentBudget.value) return false
  // Budget must be accepted or completed to be invoiced
  if (!['accepted', 'completed'].includes(currentBudget.value.status)) {
    return false
  }
  // Hide if budget already has a non-cancelled invoice
  if (hasActiveInvoice.value) return false
  // Must have at least one item with available quantity to invoice
  return currentBudget.value.items.some(item =>
    item.quantity > (item.invoiced_quantity || 0)
  )
}

async function checkActiveInvoice(budgetId: string) {
  try {
    const response = await api.get<PaginatedResponse<InvoiceListItem>>(
      `/api/v1/billing/invoices?budget_id=${budgetId}&page_size=100`
    )
    hasActiveInvoice.value = response.data.some(inv => inv.status !== 'cancelled')
  } catch {
    hasActiveInvoice.value = false
  }
}

function goToCreateInvoice() {
  if (!currentBudget.value) return
  router.push(`/invoices/from-budget/${currentBudget.value.id}`)
}

const budgetId = computed(() => route.params.id as string)
const comesFromPatient = computed(() => route.query.from === 'patient' && route.query.patientId)
const backLabel = computed(() => comesFromPatient.value ? t('actions.back') : t('budget.title'))

// Load budget
async function loadBudget() {
  const budget = await fetchBudget(budgetId.value)
  if (!budget) {
    toast.add({
      title: t('common.error'),
      description: t('budget.errors.notFound'),
      color: 'error'
    })
    router.push('/budgets')
    return
  }
  if (can('billing.read')) {
    await checkActiveInvoice(budget.id)
  }
}

onMounted(() => {
  loadBudget()
})

// Modal states
const isAddItemModalOpen = ref(false)
const isSignatureModalOpen = ref(false)
const isSendModalOpen = ref(false)
const isShareLinkModalOpen = ref(false)
const isSignatureViewModalOpen = ref(false)
const signatureAction = ref<'accept' | 'reject'>('accept')

// Send form
const sendForm = reactive({
  send_email: false,
  custom_message: ''
})

// Edit state
const isEditing = ref(false)
const editForm = reactive({
  valid_from: '',
  valid_until: '',
  global_discount_type: '',
  global_discount_value: '',
  internal_notes: '',
  patient_notes: ''
})

function startEditing() {
  if (!currentBudget.value) return
  editForm.valid_from = currentBudget.value.valid_from
  editForm.valid_until = currentBudget.value.valid_until || ''
  editForm.global_discount_type = currentBudget.value.global_discount_type || ''
  editForm.global_discount_value = currentBudget.value.global_discount_value?.toString() || ''
  editForm.internal_notes = currentBudget.value.internal_notes || ''
  editForm.patient_notes = currentBudget.value.patient_notes || ''
  isEditing.value = true
}

async function saveEdits() {
  if (!currentBudget.value) return

  try {
    await updateBudget(currentBudget.value.id, {
      valid_from: editForm.valid_from || undefined,
      valid_until: editForm.valid_until || undefined,
      global_discount_type: (editForm.global_discount_type as 'percentage' | 'absolute') || undefined,
      global_discount_value: editForm.global_discount_value
        ? parseFloat(editForm.global_discount_value)
        : undefined,
      internal_notes: editForm.internal_notes || undefined,
      patient_notes: editForm.patient_notes || undefined
    })

    toast.add({
      title: t('common.success'),
      description: t('budget.messages.updated'),
      color: 'success'
    })
    isEditing.value = false
  } catch {
    toast.add({
      title: t('common.error'),
      description: t('budget.errors.update'),
      color: 'error'
    })
  }
}

// Item management
function handleItemAdded() {
  isAddItemModalOpen.value = false
  loadBudget()
}

async function handleRemoveItem(item: BudgetItem) {
  if (!currentBudget.value) return
  if (!confirm(t('budget.items.remove') + '?')) return

  try {
    await removeItem(currentBudget.value.id, item.id)
    toast.add({
      title: t('common.success'),
      description: t('budget.messages.itemRemoved'),
      color: 'success'
    })
  } catch {
    toast.add({
      title: t('common.error'),
      description: t('budget.errors.delete'),
      color: 'error'
    })
  }
}

// Workflow actions
function openSignatureModal(action: 'accept' | 'reject') {
  signatureAction.value = action
  isSignatureModalOpen.value = true
}

// Signature form
const signatureForm = reactive<SignatureCreate>({
  signed_by_name: '',
  signed_by_email: '',
  relationship_to_patient: 'patient'
})

async function handleSignatureSubmit() {
  if (!currentBudget.value || !signatureForm.signed_by_name) return

  try {
    if (signatureAction.value === 'accept') {
      await acceptBudget(currentBudget.value.id, { signature: signatureForm })
      toast.add({
        title: t('common.success'),
        description: t('budget.messages.accepted'),
        color: 'success'
      })
    } else {
      await rejectBudget(currentBudget.value.id, { signature: signatureForm })
      toast.add({
        title: t('common.success'),
        description: t('budget.messages.rejected'),
        color: 'success'
      })
    }

    isSignatureModalOpen.value = false
    resetSignatureForm()
    await loadBudget()
  } catch {
    toast.add({
      title: t('common.error'),
      description: signatureAction.value === 'accept'
        ? t('budget.errors.accept')
        : t('budget.errors.reject'),
      color: 'error'
    })
  }
}

function resetSignatureForm() {
  signatureForm.signed_by_name = ''
  signatureForm.signed_by_email = ''
  signatureForm.relationship_to_patient = 'patient'
}

async function handleCancel() {
  if (!currentBudget.value) return
  if (!confirm(t('budget.confirmations.cancel'))) return

  try {
    await cancelBudget(currentBudget.value.id)
    toast.add({
      title: t('common.success'),
      description: t('budget.messages.cancelled'),
      color: 'success'
    })
    await loadBudget()
  } catch {
    toast.add({
      title: t('common.error'),
      description: t('budget.errors.update'),
      color: 'error'
    })
  }
}

async function handleSend() {
  if (!currentBudget.value) return

  try {
    await sendBudget(currentBudget.value.id, {
      send_email: sendForm.send_email,
      custom_message: sendForm.custom_message || undefined
    })

    const message = sendForm.send_email
      ? t('budget.messages.sentByEmail')
      : t('budget.messages.sentManually')

    toast.add({
      title: t('common.success'),
      description: message,
      color: 'success'
    })

    isSendModalOpen.value = false
    resetSendForm()
    await loadBudget()
  } catch {
    toast.add({
      title: t('common.error'),
      description: t('budget.errors.send'),
      color: 'error'
    })
  }
}

function resetSendForm() {
  sendForm.send_email = false
  sendForm.custom_message = ''
}

async function handleDuplicate() {
  if (!currentBudget.value) return

  try {
    const newBudget = await duplicateBudget(currentBudget.value.id)
    toast.add({
      title: t('common.success'),
      description: t('budget.messages.duplicated'),
      color: 'success'
    })
    router.push(`/budgets/${newBudget.id}`)
  } catch {
    toast.add({
      title: t('common.error'),
      description: t('budget.errors.create'),
      color: 'error'
    })
  }
}

async function handleDownloadPDF() {
  if (!currentBudget.value) return

  try {
    await downloadPDF(currentBudget.value.id, locale.value)
  } catch {
    toast.add({
      title: t('common.error'),
      description: t('budget.pdf.downloadError'),
      color: 'error'
    })
  }
}

// Format helpers
const { format: formatMoney } = useCurrency()

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString(locale.value)
}

const moreMenuItems = computed<DropdownMenuItem[][]>(() => {
  if (!currentBudget.value) return []
  const primary: DropdownMenuItem[] = [
    {
      label: t('budget.actions.downloadPdf'),
      icon: 'i-lucide-download',
      onSelect: handleDownloadPDF
    }
  ]
  if (can('budget.write')) {
    primary.push({
      label: t('budget.actions.duplicate'),
      icon: 'i-lucide-copy',
      onSelect: handleDuplicate
    })
  }
  const groups: DropdownMenuItem[][] = [primary]
  if (canCancel(currentBudget.value) && can('budget.write')) {
    groups.push([
      {
        label: t('budget.actions.cancel'),
        icon: 'i-lucide-ban',
        color: 'error',
        onSelect: handleCancel
      }
    ])
  }
  return groups
})

function getItemName(item: BudgetItem): string {
  if (!item.catalog_item) return '-'
  return item.catalog_item.names[locale.value] || item.catalog_item.names.es || item.catalog_item.internal_code
}
</script>

<template>
  <div class="space-y-6">
    <!-- Loading -->
    <div
      v-if="isLoading"
      class="space-y-4"
    >
      <USkeleton class="h-12 w-1/3" />
      <USkeleton class="h-64 w-full" />
    </div>

    <template v-else-if="currentBudget">
      <!-- Header -->
      <div>
        <UButton
          variant="ghost"
          color="neutral"
          icon="i-lucide-arrow-left"
          size="sm"
          class="-ml-2 mb-3"
          @click="comesFromPatient ? router.push(`/patients/${route.query.patientId}`) : router.push('/budgets')"
        >
          {{ backLabel }}
        </UButton>

        <div class="flex items-start justify-between gap-4">
          <div class="min-w-0 flex-1">
            <div class="flex items-center gap-3 flex-wrap">
              <h1 class="text-display text-default">
                {{ currentBudget.budget_number }}
              </h1>
              <span class="text-subtle">v{{ currentBudget.version }}</span>
              <BudgetStatusBadge :status="currentBudget.status" />
            </div>
            <NuxtLink
              v-if="currentBudget.patient"
              :to="`/patients/${currentBudget.patient.id}`"
              class="mt-1 inline-block text-body text-primary-accent hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300 hover:underline"
            >
              {{ currentBudget.patient.first_name }} {{ currentBudget.patient.last_name }}
            </NuxtLink>
          </div>

          <!-- Actions -->
          <div class="flex items-center gap-2 shrink-0">
            <!-- Primary contextual actions -->
            <UButton
              v-if="canSend(currentBudget) && can('budget.write')"
              color="primary"
              icon="i-lucide-send"
              size="sm"
              @click="isSendModalOpen = true"
            >
              {{ t('budget.actions.send') }}
            </UButton>

            <UButton
              v-if="currentBudget.public_token && ['sent', 'accepted', 'rejected', 'expired'].includes(currentBudget.status)"
              color="primary"
              variant="soft"
              icon="i-lucide-share-2"
              size="sm"
              @click="isShareLinkModalOpen = true"
            >
              {{ t('budget.publicLink.action') }}
            </UButton>

            <UButton
              v-if="['accepted', 'completed'].includes(currentBudget.status)"
              color="primary"
              variant="soft"
              icon="i-lucide-pen-tool"
              size="sm"
              @click="isSignatureViewModalOpen = true"
            >
              {{ t('budget.signature.viewAction') }}
            </UButton>

            <template v-if="canAccept(currentBudget) && can('budget.write')">
              <UButton
                color="error"
                variant="ghost"
                icon="i-lucide-x"
                size="sm"
                @click="openSignatureModal('reject')"
              >
                {{ t('budget.actions.reject') }}
              </UButton>
              <UButton
                color="success"
                icon="i-lucide-check"
                size="sm"
                @click="openSignatureModal('accept')"
              >
                {{ t('budget.actions.accept') }}
              </UButton>
            </template>

            <UButton
              v-if="canInvoice() && can('billing.write')"
              color="primary"
              icon="i-lucide-receipt"
              size="sm"
              @click="goToCreateInvoice"
            >
              {{ t('invoice.createFromBudget') }}
            </UButton>

            <!-- Secondary actions in dropdown -->
            <UDropdownMenu :items="moreMenuItems">
              <UButton
                variant="ghost"
                color="neutral"
                icon="i-lucide-more-horizontal"
                size="sm"
                :aria-label="t('common.actions')"
              />
            </UDropdownMenu>
          </div>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Main content -->
        <div class="lg:col-span-2 space-y-6 lg:order-1">
          <!-- Budget details -->
          <UCard>
            <template #header>
              <div class="flex items-center justify-between">
                <h2 class="text-h1 text-default">
                  {{ t('budget.view') }}
                </h2>
                <UButton
                  v-if="canEdit(currentBudget) && can('budget.write') && !isEditing"
                  variant="ghost"
                  color="neutral"
                  icon="i-lucide-pencil"
                  size="sm"
                  @click="startEditing"
                >
                  {{ t('common.edit') }}
                </UButton>
              </div>
            </template>

            <!-- View mode -->
            <div
              v-if="!isEditing"
              class="grid grid-cols-1 sm:grid-cols-2 gap-4"
            >
              <div>
                <span class="text-caption text-subtle">{{ t('budget.validFrom') }}</span>
                <p class="font-medium">
                  {{ formatDate(currentBudget.valid_from) }}
                </p>
              </div>
              <div>
                <span class="text-caption text-subtle">{{ t('budget.validUntil') }}</span>
                <p class="font-medium">
                  {{ currentBudget.valid_until ? formatDate(currentBudget.valid_until) : t('budget.noExpiry') }}
                </p>
              </div>
              <div v-if="currentBudget.global_discount_value">
                <span class="text-caption text-subtle">{{ t('budget.globalDiscount') }}</span>
                <p class="font-medium">
                  {{ currentBudget.global_discount_type === 'percentage'
                    ? `${currentBudget.global_discount_value}%`
                    : formatMoney(currentBudget.global_discount_value) }}
                </p>
              </div>
              <div v-if="currentBudget.patient_notes">
                <span class="text-caption text-subtle">{{ t('budget.patientNotes') }}</span>
                <p class="mt-1">
                  {{ currentBudget.patient_notes }}
                </p>
              </div>
            </div>

            <!-- Edit mode -->
            <form
              v-else
              class="space-y-4"
              @submit.prevent="saveEdits"
            >
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <UFormField :label="t('budget.validFrom')">
                  <UInput
                    v-model="editForm.valid_from"
                    type="date"
                  />
                </UFormField>
                <UFormField :label="t('budget.validUntil')">
                  <UInput
                    v-model="editForm.valid_until"
                    type="date"
                  />
                </UFormField>
              </div>

              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <UFormField :label="t('budget.discountType')">
                  <USelect
                    v-model="editForm.global_discount_type"
                    :items="[
                      { label: '-', value: '' },
                      { label: t('budget.percentage'), value: 'percentage' },
                      { label: t('budget.absolute'), value: 'absolute' }
                    ]"
                  />
                </UFormField>
                <UFormField :label="t('budget.discountValue')">
                  <UInput
                    v-model="editForm.global_discount_value"
                    type="number"
                    step="0.01"
                    min="0"
                  />
                </UFormField>
              </div>

              <UFormField :label="t('budget.patientNotes')">
                <UTextarea
                  v-model="editForm.patient_notes"
                  :placeholder="t('budget.patientNotesPlaceholder')"
                  :rows="3"
                />
              </UFormField>

              <UFormField :label="t('budget.internalNotes')">
                <UTextarea
                  v-model="editForm.internal_notes"
                  :placeholder="t('budget.internalNotesPlaceholder')"
                  :rows="3"
                />
              </UFormField>

              <div class="flex justify-end gap-2">
                <UButton
                  variant="outline"
                  color="neutral"
                  @click="isEditing = false"
                >
                  {{ t('common.cancel') }}
                </UButton>
                <UButton
                  type="submit"
                  color="primary"
                >
                  {{ t('common.save') }}
                </UButton>
              </div>
            </form>
          </UCard>

          <!-- Items -->
          <UCard>
            <template #header>
              <div class="flex items-center justify-between">
                <h2 class="text-h1 text-default">
                  {{ t('budget.items.title') }}
                </h2>
                <UButton
                  v-if="canEdit(currentBudget) && can('budget.write')"
                  icon="i-lucide-plus"
                  size="sm"
                  @click="isAddItemModalOpen = true"
                >
                  {{ t('budget.items.add') }}
                </UButton>
              </div>
            </template>

            <div
              v-if="currentBudget.items.length === 0"
              class="text-center py-8 text-subtle"
            >
              {{ t('budget.items.empty') }}
            </div>

            <div
              v-else
              class="divide-y divide-[var(--color-border-subtle)]"
            >
              <div
                v-for="item in currentBudget.items"
                :key="item.id"
                class="py-4 flex items-start gap-4"
              >
                <div class="flex-1">
                  <div class="flex items-center gap-2">
                    <span class="font-medium">{{ getItemName(item) }}</span>
                    <span
                      v-if="item.tooth_number"
                      class="text-caption text-subtle"
                    >
                      #{{ item.tooth_number }}
                      <span v-if="item.surfaces?.length">({{ item.surfaces.join(', ') }})</span>
                    </span>
                  </div>
                  <div class="text-caption text-subtle mt-1">
                    {{ item.quantity }} x {{ formatMoney(item.unit_price) }}
                    <span
                      v-if="item.line_discount > 0"
                      class="text-success-accent"
                    >
                      -{{ formatMoney(item.line_discount) }}
                    </span>
                  </div>
                  <p
                    v-if="item.notes"
                    class="text-caption text-subtle mt-1"
                  >
                    {{ item.notes }}
                  </p>
                </div>
                <div class="text-right">
                  <p class="font-semibold">
                    {{ formatMoney(item.line_total) }}
                  </p>
                </div>
                <UButton
                  v-if="canEdit(currentBudget) && can('budget.write')"
                  variant="ghost"
                  color="error"
                  icon="i-lucide-trash-2"
                  size="sm"
                  @click="handleRemoveItem(item)"
                />
              </div>
            </div>
          </UCard>
        </div>

        <!-- Sidebar -->
        <div class="space-y-6">
          <!-- Totals -->
          <UCard>
            <template #header>
              <h2 class="text-h1 text-default">
                {{ t('budget.total') }}
              </h2>
            </template>

            <div class="space-y-3">
              <div class="flex justify-between">
                <span class="text-subtle">{{ t('budget.subtotal') }}</span>
                <span>{{ formatMoney(currentBudget.subtotal) }}</span>
              </div>
              <div
                v-if="currentBudget.total_discount > 0"
                class="flex justify-between text-success-accent"
              >
                <span>{{ t('budget.totalDiscount') }}</span>
                <span>-{{ formatMoney(currentBudget.total_discount) }}</span>
              </div>
              <div
                v-if="currentBudget.total_tax > 0"
                class="flex justify-between"
              >
                <span class="text-subtle">{{ t('budget.totalTax') }}</span>
                <span>{{ formatMoney(currentBudget.total_tax) }}</span>
              </div>
              <div class="border-t pt-3 flex justify-between font-bold text-lg">
                <span>{{ t('budget.total') }}</span>
                <span>{{ formatMoney(currentBudget.total) }}</span>
              </div>
            </div>
          </UCard>

          <!-- Info -->
          <UCard>
            <div class="space-y-3 text-sm">
              <div>
                <span class="text-subtle">{{ t('budget.budgetNumber') }}</span>
                <p class="font-medium">
                  {{ currentBudget.budget_number }}
                </p>
              </div>
              <div>
                <span class="text-subtle">{{ t('budget.version') }}</span>
                <p class="font-medium">
                  v{{ currentBudget.version }}
                </p>
              </div>
              <div v-if="currentBudget.creator">
                <span class="text-subtle">{{ t('common.createdBy') }}</span>
                <p class="font-medium">
                  {{ currentBudget.creator.first_name }} {{ currentBudget.creator.last_name }}
                </p>
              </div>
              <div>
                <span class="text-subtle">{{ t('common.date') }}</span>
                <p class="font-medium">
                  {{ formatDate(currentBudget.created_at) }}
                </p>
              </div>
              <div v-if="currentBudget.treatment_plan">
                <span class="text-subtle">{{ t('budget.treatmentPlan') }}</span>
                <NuxtLink
                  :to="`/treatment-plans/${currentBudget.treatment_plan.id}`"
                  class="block font-medium text-primary-accent hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300 hover:underline"
                >
                  {{ currentBudget.treatment_plan.plan_number }}
                  <span
                    v-if="currentBudget.treatment_plan.title"
                    class="text-subtle font-normal"
                  >
                    - {{ currentBudget.treatment_plan.title }}
                  </span>
                </NuxtLink>
              </div>
            </div>
          </UCard>

        </div>

        <!-- Sidebar slot — module-driven extension point. Modules
             (e.g. payments) register cards via
             ``registerSlot('budget.detail.sidebar', ...)``. Budget
             never imports them; the registry is the only contract. -->
        <aside class="space-y-6 lg:order-2">
          <ModuleSlot
            name="budget.detail.sidebar"
            :ctx="{ budget: currentBudget }"
          />
        </aside>
      </div>
    </template>

    <!-- Add Item Modal -->
    <BudgetItemModal
      v-model:open="isAddItemModalOpen"
      :budget-id="budgetId"
      @added="handleItemAdded"
    />

    <!-- Send Modal -->
    <UModal v-model:open="isSendModalOpen">
      <template #content>
        <UCard>
          <template #header>
            <div class="flex items-center justify-between">
              <h2 class="text-h1 text-default">
                {{ t('budget.actions.send') }}
              </h2>
              <UButton
                variant="ghost"
                color="neutral"
                icon="i-lucide-x"
                @click="isSendModalOpen = false"
              />
            </div>
          </template>

          <div class="space-y-4">
            <p class="text-muted dark:text-subtle">
              {{ t('budget.send.description') }}
            </p>

            <div class="flex items-center gap-3">
              <UCheckbox
                v-model="sendForm.send_email"
                :label="t('budget.send.sendByEmail')"
              />
            </div>

            <div
              v-if="sendForm.send_email"
              class="space-y-3"
            >
              <p
                v-if="currentBudget?.patient?.email"
                class="text-caption text-subtle"
              >
                {{ t('budget.send.willSendTo') }}: <strong>{{ currentBudget.patient.email }}</strong>
              </p>
              <p
                v-else
                class="text-sm text-warning-accent"
              >
                {{ t('budget.send.noPatientEmail') }}
              </p>

              <UFormField :label="t('budget.send.customMessage')">
                <UTextarea
                  v-model="sendForm.custom_message"
                  :placeholder="t('budget.send.customMessagePlaceholder')"
                  :rows="3"
                />
              </UFormField>
            </div>

            <p
              v-if="!sendForm.send_email"
              class="text-caption text-subtle"
            >
              {{ t('budget.send.manualNote') }}
            </p>
          </div>

          <template #footer>
            <div class="flex justify-end gap-3">
              <UButton
                variant="outline"
                color="neutral"
                @click="isSendModalOpen = false"
              >
                {{ t('common.cancel') }}
              </UButton>
              <UButton
                color="primary"
                :disabled="sendForm.send_email && !currentBudget?.patient?.email"
                @click="handleSend"
              >
                {{ sendForm.send_email ? t('budget.send.sendEmail') : t('budget.send.markAsSent') }}
              </UButton>
            </div>
          </template>
        </UCard>
      </template>
    </UModal>

    <!-- Signature Modal -->
    <UModal v-model:open="isSignatureModalOpen">
      <template #content>
        <UCard>
          <template #header>
            <div class="flex items-center justify-between">
              <h2 class="text-h1 text-default">
                {{ signatureAction === 'accept' ? t('budget.actions.accept') : t('budget.actions.reject') }}
              </h2>
              <UButton
                variant="ghost"
                color="neutral"
                icon="i-lucide-x"
                @click="isSignatureModalOpen = false"
              />
            </div>
          </template>

          <form
            class="space-y-4"
            @submit.prevent="handleSignatureSubmit"
          >
            <UFormField
              :label="t('budget.signature.signedBy')"
              required
            >
              <UInput
                v-model="signatureForm.signed_by_name"
                :placeholder="t('budget.signature.signedBy')"
                required
              />
            </UFormField>

            <UFormField :label="t('budget.signature.email')">
              <UInput
                v-model="signatureForm.signed_by_email"
                type="email"
                :placeholder="t('budget.signature.email')"
              />
            </UFormField>

            <UFormField :label="t('budget.signature.relationship')">
              <USelect
                v-model="signatureForm.relationship_to_patient"
                :items="[
                  { label: t('budget.signature.patient'), value: 'patient' },
                  { label: t('budget.signature.guardian'), value: 'guardian' },
                  { label: t('budget.signature.representative'), value: 'representative' }
                ]"
              />
            </UFormField>
          </form>

          <template #footer>
            <div class="flex justify-end gap-3">
              <UButton
                variant="outline"
                color="neutral"
                @click="isSignatureModalOpen = false"
              >
                {{ t('common.cancel') }}
              </UButton>
              <UButton
                :color="signatureAction === 'accept' ? 'success' : 'error'"
                :disabled="!signatureForm.signed_by_name"
                @click="handleSignatureSubmit"
              >
                {{ signatureAction === 'accept' ? t('budget.actions.accept') : t('budget.actions.reject') }}
              </UButton>
            </div>
          </template>
        </UCard>
      </template>
    </UModal>

    <!-- View signature modal -->
    <UModal v-model:open="isSignatureViewModalOpen">
      <template #content>
        <div class="p-1">
          <BudgetSignatureCard
            v-if="currentBudget && ['accepted', 'completed'].includes(currentBudget.status)"
            :budget-id="currentBudget.id"
            :budget-status="currentBudget.status"
            :locale="locale"
          />
        </div>
      </template>
    </UModal>

    <!-- Share public link modal -->
    <UModal v-model:open="isShareLinkModalOpen">
      <template #content>
        <div class="p-1">
          <PublicBudgetLinkCard
            v-if="currentBudget?.public_token"
            :token="currentBudget.public_token"
            :status="currentBudget.status"
            :patient-phone="currentBudget.patient?.phone"
            :patient-first-name="currentBudget.patient?.first_name"
            :budget-number="currentBudget.budget_number"
          />
        </div>
      </template>
    </UModal>
  </div>
</template>
