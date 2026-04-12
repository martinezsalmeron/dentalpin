<script setup lang="ts">
import type { InvoiceItemCreate, VatType } from '~/types'

const route = useRoute()
const router = useRouter()
const { t, locale } = useI18n()
const toast = useToast()
const api = useApi()
const {
  currentInvoice,
  isLoading,
  fetchInvoice,
  updateInvoice,
  addItem,
  updateItem,
  removeItem,
  canEdit,
  formatCurrency
} = useInvoices()

const invoiceId = computed(() => route.params.id as string)

// State
const isSaving = ref(false)
const vatTypes = ref<VatType[]>([])

// Form data
const form = ref({
  billing_name: '',
  billing_tax_id: '',
  billing_email: '',
  billing_address: {
    street: '',
    city: '',
    postal_code: '',
    province: '',
    country: 'ES'
  },
  payment_term_days: 30,
  due_date: '',
  internal_notes: '',
  public_notes: ''
})

// Track modified items for saving
const modifiedItems = ref<Map<string, { description: string, unit_price: number, quantity: number, vat_type_id?: string }>>(new Map())
const deletedItemIds = ref<Set<string>>(new Set())

// New item form
const newItem = ref<InvoiceItemCreate>({
  description: '',
  unit_price: 0,
  quantity: 1,
  vat_type_id: undefined,
  display_order: 0
})
const newItems = ref<InvoiceItemCreate[]>([])

// Load invoice and VAT types
onMounted(async () => {
  const [invoice] = await Promise.all([
    fetchInvoice(invoiceId.value),
    loadVatTypes()
  ])

  if (!invoice) {
    toast.add({
      title: t('common.error'),
      description: t('invoice.notFound'),
      color: 'error'
    })
    router.push('/invoices')
    return
  }

  if (!canEdit(invoice)) {
    toast.add({
      title: t('common.error'),
      description: t('invoice.errors.cannotEdit'),
      color: 'error'
    })
    router.push(`/invoices/${invoiceId.value}`)
    return
  }

  // Populate form with invoice data
  form.value = {
    billing_name: invoice.billing_name || '',
    billing_tax_id: invoice.billing_tax_id || '',
    billing_email: invoice.billing_email || '',
    billing_address: invoice.billing_address || {
      street: '',
      city: '',
      postal_code: '',
      province: '',
      country: 'ES'
    },
    payment_term_days: invoice.payment_term_days || 30,
    due_date: invoice.due_date?.split('T')[0] || '',
    internal_notes: invoice.internal_notes || '',
    public_notes: invoice.public_notes || ''
  }
})

async function loadVatTypes() {
  try {
    const response = await api.get<{ data: VatType[] }>('/api/v1/catalog/vat-types')
    vatTypes.value = response.data
  } catch (e) {
    console.error('Failed to load VAT types:', e)
  }
}

// Get VAT type options
const vatTypeOptions = computed(() =>
  vatTypes.value
    .filter(v => v.is_active)
    .map(v => ({
      label: `${v.names[locale.value] || v.names.es || 'IVA'} (${v.rate}%)`,
      value: v.id
    }))
)

// Get current items (excluding deleted)
const currentItems = computed(() => {
  if (!currentInvoice.value?.items) return []
  return currentInvoice.value.items.filter(item => !deletedItemIds.value.has(item.id))
})

// Track item changes
function onItemChange(itemId: string, field: string, value: string | number) {
  const item = currentInvoice.value?.items.find(i => i.id === itemId)
  if (!item) return

  const existing = modifiedItems.value.get(itemId) || {
    description: item.description,
    unit_price: item.unit_price,
    quantity: item.quantity,
    vat_type_id: item.vat_type_id
  }

  modifiedItems.value.set(itemId, {
    ...existing,
    [field]: value
  })
}

// Get item value (modified or original)
function getItemValue(itemId: string, field: 'description' | 'unit_price' | 'quantity' | 'vat_type_id') {
  const modified = modifiedItems.value.get(itemId)
  if (modified && field in modified) {
    return modified[field]
  }
  const item = currentInvoice.value?.items.find(i => i.id === itemId)
  return item ? item[field] : ''
}

// Mark item for deletion
function markItemForDeletion(itemId: string) {
  deletedItemIds.value.add(itemId)
  modifiedItems.value.delete(itemId)
}

// Add new item to pending list
function addNewItem() {
  if (!newItem.value.description || newItem.value.unit_price <= 0) {
    toast.add({
      title: t('common.error'),
      description: t('invoice.errors.itemRequired'),
      color: 'error'
    })
    return
  }

  newItems.value.push({
    ...newItem.value,
    display_order: (currentItems.value.length || 0) + newItems.value.length
  })

  // Reset form
  newItem.value = {
    description: '',
    unit_price: 0,
    quantity: 1,
    vat_type_id: vatTypes.value.find(v => v.is_default)?.id,
    display_order: 0
  }
}

// Remove pending new item
function removeNewItem(index: number) {
  newItems.value.splice(index, 1)
}

// Calculate item total
function getItemTotal(unitPrice: number, quantity: number, vatTypeId?: string): number {
  const subtotal = unitPrice * quantity
  const vatType = vatTypes.value.find(v => v.id === vatTypeId)
  const vatRate = vatType?.rate || 0
  const tax = subtotal * (vatRate / 100)
  return subtotal + tax
}

// Calculate totals
const totals = computed(() => {
  let subtotal = 0
  let totalTax = 0

  // Existing items (excluding deleted)
  currentItems.value.forEach((item) => {
    const modified = modifiedItems.value.get(item.id)
    const unitPrice = modified?.unit_price ?? item.unit_price
    const quantity = modified?.quantity ?? item.quantity
    const vatTypeId = modified?.vat_type_id ?? item.vat_type_id

    const itemSubtotal = unitPrice * quantity
    const vatType = vatTypes.value.find(v => v.id === vatTypeId)
    const vatRate = vatType?.rate || 0
    const tax = itemSubtotal * (vatRate / 100)

    subtotal += itemSubtotal
    totalTax += tax
  })

  // New items
  newItems.value.forEach((item) => {
    const itemSubtotal = item.unit_price * (item.quantity || 1)
    const vatType = vatTypes.value.find(v => v.id === item.vat_type_id)
    const vatRate = vatType?.rate || 0
    const tax = itemSubtotal * (vatRate / 100)

    subtotal += itemSubtotal
    totalTax += tax
  })

  return {
    subtotal,
    totalTax,
    total: subtotal + totalTax
  }
})

// Save changes
async function handleSave() {
  const totalItems = currentItems.value.length + newItems.value.length
  if (totalItems === 0) {
    toast.add({
      title: t('common.error'),
      description: t('invoice.errors.itemsRequired'),
      color: 'error'
    })
    return
  }

  isSaving.value = true

  try {
    // 1. Update invoice details
    await updateInvoice(invoiceId.value, {
      billing_name: form.value.billing_name || undefined,
      billing_tax_id: form.value.billing_tax_id || undefined,
      billing_email: form.value.billing_email || undefined,
      billing_address: form.value.billing_address.street ? form.value.billing_address : undefined,
      payment_term_days: form.value.payment_term_days,
      due_date: form.value.due_date || undefined,
      internal_notes: form.value.internal_notes || undefined,
      public_notes: form.value.public_notes || undefined
    })

    // 2. Delete removed items
    for (const itemId of deletedItemIds.value) {
      await removeItem(invoiceId.value, itemId)
    }

    // 3. Update modified items
    for (const [itemId, data] of modifiedItems.value.entries()) {
      await updateItem(invoiceId.value, itemId, data)
    }

    // 4. Add new items
    for (const item of newItems.value) {
      await addItem(invoiceId.value, item)
    }

    toast.add({
      title: t('common.success'),
      description: t('invoice.messages.updated'),
      color: 'success'
    })

    router.push(`/invoices/${invoiceId.value}`)
  } catch {
    toast.add({
      title: t('common.error'),
      description: t('invoice.errors.update'),
      color: 'error'
    })
  } finally {
    isSaving.value = false
  }
}

function goBack() {
  router.push(`/invoices/${invoiceId.value}`)
}
</script>

<template>
  <div class="space-y-6">
    <!-- Loading state -->
    <div
      v-if="isLoading && !currentInvoice"
      class="space-y-4"
    >
      <USkeleton class="h-8 w-48" />
      <USkeleton class="h-64 w-full" />
    </div>

    <!-- Content -->
    <template v-else-if="currentInvoice">
      <!-- Header -->
      <div class="flex items-center gap-4">
        <UButton
          variant="ghost"
          color="neutral"
          icon="i-lucide-arrow-left"
          @click="goBack"
        />
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
          {{ t('invoice.edit') }}: {{ currentInvoice.invoice_number || t('invoice.draftNoNumber') }}
        </h1>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Left column - Form -->
        <div class="lg:col-span-2 space-y-6">
          <!-- Patient info (read-only) -->
          <UCard>
            <template #header>
              <h3 class="font-semibold text-gray-900 dark:text-white">
                {{ t('invoice.patient') }}
              </h3>
            </template>

            <div
              v-if="currentInvoice.patient"
              class="flex items-center justify-between"
            >
              <div>
                <p class="font-medium text-gray-900 dark:text-white">
                  {{ currentInvoice.patient.last_name }}, {{ currentInvoice.patient.first_name }}
                </p>
                <p class="text-sm text-gray-500">
                  {{ currentInvoice.patient.email || '-' }}
                </p>
              </div>
              <UBadge
                color="gray"
                variant="subtle"
              >
                {{ t('common.readOnly') }}
              </UBadge>
            </div>
          </UCard>

          <!-- Billing data -->
          <UCard>
            <template #header>
              <h3 class="font-semibold text-gray-900 dark:text-white">
                {{ t('invoice.billingData') }}
              </h3>
            </template>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <UFormField :label="t('invoice.billingName')">
                <UInput v-model="form.billing_name" />
              </UFormField>

              <UFormField :label="t('invoice.taxId')">
                <UInput
                  v-model="form.billing_tax_id"
                  placeholder="NIF/CIF"
                />
              </UFormField>

              <UFormField :label="t('invoice.billingEmail')">
                <UInput
                  v-model="form.billing_email"
                  type="email"
                />
              </UFormField>

              <UFormField :label="t('invoice.paymentTermDays')">
                <UInput
                  v-model.number="form.payment_term_days"
                  type="number"
                  :min="0"
                />
              </UFormField>

              <UFormField :label="t('invoice.dueDate')">
                <UInput
                  v-model="form.due_date"
                  type="date"
                />
              </UFormField>
            </div>
          </UCard>

          <!-- Items -->
          <UCard>
            <template #header>
              <h3 class="font-semibold text-gray-900 dark:text-white">
                {{ t('invoice.items') }}
              </h3>
            </template>

            <!-- Existing items -->
            <div
              v-if="currentItems.length > 0"
              class="divide-y divide-gray-200 dark:divide-gray-800 mb-6"
            >
              <div
                v-for="item in currentItems"
                :key="item.id"
                class="py-3"
              >
                <div class="grid grid-cols-1 md:grid-cols-12 gap-3 items-end">
                  <div class="md:col-span-4">
                    <UFormField :label="t('invoice.itemDescription')">
                      <UInput
                        :model-value="getItemValue(item.id, 'description') as string"
                        @update:model-value="onItemChange(item.id, 'description', $event)"
                      />
                    </UFormField>
                  </div>
                  <div class="md:col-span-2">
                    <UFormField :label="t('invoice.itemPrice')">
                      <UInput
                        type="number"
                        :min="0"
                        step="0.01"
                        :model-value="getItemValue(item.id, 'unit_price') as number"
                        @update:model-value="onItemChange(item.id, 'unit_price', Number($event))"
                      />
                    </UFormField>
                  </div>
                  <div class="md:col-span-2">
                    <UFormField :label="t('invoice.itemQuantity')">
                      <UInput
                        type="number"
                        :min="1"
                        :model-value="getItemValue(item.id, 'quantity') as number"
                        @update:model-value="onItemChange(item.id, 'quantity', Number($event))"
                      />
                    </UFormField>
                  </div>
                  <div class="md:col-span-2">
                    <UFormField :label="t('invoice.vat')">
                      <USelectMenu
                        :model-value="getItemValue(item.id, 'vat_type_id') as string"
                        :items="vatTypeOptions"
                        @update:model-value="onItemChange(item.id, 'vat_type_id', $event)"
                      />
                    </UFormField>
                  </div>
                  <div class="md:col-span-2 flex items-center justify-between">
                    <span class="font-semibold text-gray-900 dark:text-white">
                      {{ formatCurrency(getItemTotal(
                        getItemValue(item.id, 'unit_price') as number,
                        getItemValue(item.id, 'quantity') as number,
                        getItemValue(item.id, 'vat_type_id') as string
                      )) }}
                    </span>
                    <UButton
                      variant="ghost"
                      color="error"
                      icon="i-lucide-trash-2"
                      size="sm"
                      @click="markItemForDeletion(item.id)"
                    />
                  </div>
                </div>
              </div>
            </div>

            <!-- New items pending -->
            <div
              v-if="newItems.length > 0"
              class="divide-y divide-gray-200 dark:divide-gray-800 mb-6 border-l-4 border-green-500 pl-4"
            >
              <p class="text-sm text-green-600 mb-2">
                {{ t('invoice.newItemsPending') }}
              </p>
              <div
                v-for="(item, index) in newItems"
                :key="`new-${index}`"
                class="py-3 flex items-center justify-between"
              >
                <div class="flex-1">
                  <p class="font-medium text-gray-900 dark:text-white">
                    {{ item.description }}
                  </p>
                  <p class="text-sm text-gray-500">
                    {{ item.quantity }} x {{ formatCurrency(item.unit_price) }}
                  </p>
                </div>
                <div class="flex items-center gap-4">
                  <span class="font-semibold text-gray-900 dark:text-white">
                    {{ formatCurrency(getItemTotal(item.unit_price, item.quantity || 1, item.vat_type_id)) }}
                  </span>
                  <UButton
                    variant="ghost"
                    color="error"
                    icon="i-lucide-trash-2"
                    size="sm"
                    @click="removeNewItem(index)"
                  />
                </div>
              </div>
            </div>

            <!-- Add new item -->
            <div class="border-t border-gray-200 dark:border-gray-800 pt-4">
              <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                {{ t('invoice.addItem') }}
              </h4>
              <div class="grid grid-cols-1 md:grid-cols-4 gap-3">
                <div class="md:col-span-2">
                  <UInput
                    v-model="newItem.description"
                    :placeholder="t('invoice.itemDescription')"
                  />
                </div>
                <div>
                  <UInput
                    v-model.number="newItem.unit_price"
                    type="number"
                    :min="0"
                    step="0.01"
                    :placeholder="t('invoice.itemPrice')"
                  />
                </div>
                <div>
                  <UInput
                    v-model.number="newItem.quantity"
                    type="number"
                    :min="1"
                    :placeholder="t('invoice.itemQuantity')"
                  />
                </div>
                <div class="md:col-span-2">
                  <USelectMenu
                    v-model="newItem.vat_type_id"
                    :items="vatTypeOptions"
                    :placeholder="t('invoice.selectVatType')"
                  />
                </div>
                <div class="md:col-span-2 flex justify-end">
                  <UButton
                    icon="i-lucide-plus"
                    @click="addNewItem"
                  >
                    {{ t('invoice.addItem') }}
                  </UButton>
                </div>
              </div>
            </div>
          </UCard>

          <!-- Notes -->
          <UCard>
            <template #header>
              <h3 class="font-semibold text-gray-900 dark:text-white">
                {{ t('invoice.notes') }}
              </h3>
            </template>

            <div class="space-y-4">
              <UFormField :label="t('invoice.publicNotes')">
                <UTextarea
                  v-model="form.public_notes"
                  :rows="2"
                  :placeholder="t('invoice.publicNotesPlaceholder')"
                />
              </UFormField>

              <UFormField :label="t('invoice.internalNotes')">
                <UTextarea
                  v-model="form.internal_notes"
                  :rows="2"
                  :placeholder="t('invoice.internalNotesPlaceholder')"
                />
              </UFormField>
            </div>
          </UCard>
        </div>

        <!-- Right column - Summary -->
        <div class="space-y-6">
          <UCard>
            <template #header>
              <h3 class="font-semibold text-gray-900 dark:text-white">
                {{ t('invoice.summary') }}
              </h3>
            </template>

            <div class="space-y-3">
              <div class="flex justify-between">
                <span class="text-gray-500">{{ t('invoice.subtotal') }}</span>
                <span class="font-medium">{{ formatCurrency(totals.subtotal) }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-500">{{ t('invoice.tax') }}</span>
                <span class="font-medium">{{ formatCurrency(totals.totalTax) }}</span>
              </div>
              <div class="flex justify-between pt-3 border-t border-gray-200 dark:border-gray-700">
                <span class="font-semibold text-gray-900 dark:text-white">{{ t('invoice.total') }}</span>
                <span class="font-bold text-lg text-gray-900 dark:text-white">
                  {{ formatCurrency(totals.total) }}
                </span>
              </div>
            </div>

            <div class="mt-6 space-y-3">
              <UButton
                block
                color="primary"
                :loading="isSaving"
                @click="handleSave"
              >
                {{ t('common.save') }}
              </UButton>
              <UButton
                block
                variant="outline"
                color="neutral"
                @click="goBack"
              >
                {{ t('common.cancel') }}
              </UButton>
            </div>
          </UCard>
        </div>
      </div>
    </template>
  </div>
</template>
