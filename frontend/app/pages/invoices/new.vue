<script setup lang="ts">
import type { InvoiceItemCreate, Patient, VatType } from '~/types'

const { t, locale } = useI18n()
const router = useRouter()
const toast = useToast()
const { createInvoice } = useInvoices()
const api = useApi()

// State
const isLoading = ref(false)
const patients = ref<Patient[]>([])
const vatTypes = ref<VatType[]>([])
const selectedPatient = ref<Patient | null>(null)
const patientSearch = ref('')

// Form data
const form = ref({
  patient_id: '',
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

// Items
const items = ref<InvoiceItemCreate[]>([])

// New item form
const newItem = ref<InvoiceItemCreate>({
  description: '',
  unit_price: 0,
  quantity: 1,
  vat_type_id: undefined,
  display_order: 0
})

// Debounced patient search
const debouncedPatientSearch = ref('')
let searchTimeout: ReturnType<typeof setTimeout> | null = null

watch(patientSearch, (val) => {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    debouncedPatientSearch.value = val
  }, 300)
})

// Search patients
watch(debouncedPatientSearch, async (search) => {
  if (search.length < 2) {
    patients.value = []
    return
  }

  try {
    const response = await api.get<{ data: Patient[] }>(
      `/api/v1/clinical/patients?search=${encodeURIComponent(search)}&page_size=10`
    )
    patients.value = response.data
  } catch (e) {
    console.error('Failed to search patients:', e)
  }
})

// Load VAT types
onMounted(async () => {
  try {
    const response = await api.get<{ data: VatType[] }>('/api/v1/catalog/vat-types')
    vatTypes.value = response.data
  } catch (e) {
    console.error('Failed to load VAT types:', e)
  }
})

// When patient is selected
function selectPatient(patient: Patient) {
  selectedPatient.value = patient
  form.value.patient_id = patient.id
  form.value.billing_name = `${patient.first_name} ${patient.last_name}`
  form.value.billing_email = patient.email || ''
  patientSearch.value = ''
  patients.value = []
}

// Clear patient selection
function clearPatient() {
  selectedPatient.value = null
  form.value.patient_id = ''
  form.value.billing_name = ''
  form.value.billing_email = ''
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

// Add item
function addItem() {
  if (!newItem.value.description || newItem.value.unit_price <= 0) {
    toast.add({
      title: t('common.error'),
      description: t('invoice.errors.itemRequired'),
      color: 'error'
    })
    return
  }

  items.value.push({
    ...newItem.value,
    display_order: items.value.length
  })

  // Reset new item form
  newItem.value = {
    description: '',
    unit_price: 0,
    quantity: 1,
    vat_type_id: vatTypes.value.find(v => v.is_default)?.id,
    display_order: 0
  }
}

// Remove item
function removeItem(index: number) {
  items.value.splice(index, 1)
  // Update display order
  items.value.forEach((item, i) => {
    item.display_order = i
  })
}

// Calculate item total
function getItemTotal(item: InvoiceItemCreate): number {
  const subtotal = item.unit_price * (item.quantity || 1)
  const vatType = vatTypes.value.find(v => v.id === item.vat_type_id)
  const vatRate = vatType?.rate || 0
  const tax = subtotal * (vatRate / 100)
  return subtotal + tax
}

// Calculate totals
const totals = computed(() => {
  let subtotal = 0
  let totalTax = 0

  items.value.forEach((item) => {
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

// Format currency
function formatCurrency(amount: number): string {
  return new Intl.NumberFormat(locale.value, {
    style: 'currency',
    currency: 'EUR'
  }).format(amount)
}

// Submit
async function handleSubmit() {
  if (!form.value.patient_id) {
    toast.add({
      title: t('common.error'),
      description: t('invoice.errors.patientRequired'),
      color: 'error'
    })
    return
  }

  if (items.value.length === 0) {
    toast.add({
      title: t('common.error'),
      description: t('invoice.errors.itemsRequired'),
      color: 'error'
    })
    return
  }

  isLoading.value = true

  try {
    const invoice = await createInvoice({
      patient_id: form.value.patient_id,
      billing_name: form.value.billing_name || undefined,
      billing_tax_id: form.value.billing_tax_id || undefined,
      billing_email: form.value.billing_email || undefined,
      billing_address: form.value.billing_address.street ? form.value.billing_address : undefined,
      payment_term_days: form.value.payment_term_days,
      due_date: form.value.due_date || undefined,
      internal_notes: form.value.internal_notes || undefined,
      public_notes: form.value.public_notes || undefined,
      items: items.value
    })

    toast.add({
      title: t('common.success'),
      description: t('invoice.messages.created'),
      color: 'success'
    })

    router.push(`/invoices/${invoice.id}`)
  } catch {
    toast.add({
      title: t('common.error'),
      description: t('invoice.errors.create'),
      color: 'error'
    })
  } finally {
    isLoading.value = false
  }
}

function goBack() {
  router.push('/invoices')
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center gap-4">
      <UButton
        variant="ghost"
        color="neutral"
        icon="i-lucide-arrow-left"
        @click="goBack"
      />
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
        {{ t('invoice.new') }}
      </h1>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Left column - Form -->
      <div class="lg:col-span-2 space-y-6">
        <!-- Patient selection -->
        <UCard>
          <template #header>
            <h3 class="font-semibold text-gray-900 dark:text-white">
              {{ t('invoice.patient') }}
            </h3>
          </template>

          <div v-if="!selectedPatient">
            <UFormField :label="t('invoice.searchPatient')">
              <UInput
                v-model="patientSearch"
                :placeholder="t('invoice.searchPatientPlaceholder')"
                icon="i-lucide-search"
              />
            </UFormField>

            <div
              v-if="patients.length > 0"
              class="mt-2 divide-y divide-gray-200 dark:divide-gray-800 border border-gray-200 dark:border-gray-800 rounded-md"
            >
              <div
                v-for="patient in patients"
                :key="patient.id"
                class="p-3 hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer"
                @click="selectPatient(patient)"
              >
                <p class="font-medium text-gray-900 dark:text-white">
                  {{ patient.last_name }}, {{ patient.first_name }}
                </p>
                <p class="text-sm text-gray-500">
                  {{ patient.email || patient.phone || '-' }}
                </p>
              </div>
            </div>
          </div>

          <div
            v-else
            class="flex items-center justify-between"
          >
            <div>
              <p class="font-medium text-gray-900 dark:text-white">
                {{ selectedPatient.last_name }}, {{ selectedPatient.first_name }}
              </p>
              <p class="text-sm text-gray-500">
                {{ selectedPatient.email || selectedPatient.phone || '-' }}
              </p>
            </div>
            <UButton
              variant="ghost"
              color="neutral"
              icon="i-lucide-x"
              @click="clearPatient"
            />
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
            v-if="items.length > 0"
            class="divide-y divide-gray-200 dark:divide-gray-800 mb-6"
          >
            <div
              v-for="(item, index) in items"
              :key="index"
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
                  {{ formatCurrency(getItemTotal(item)) }}
                </span>
                <UButton
                  variant="ghost"
                  color="error"
                  icon="i-lucide-trash-2"
                  size="sm"
                  @click="removeItem(index)"
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
                  @click="addItem"
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
              :loading="isLoading"
              :disabled="!form.patient_id || items.length === 0"
              @click="handleSubmit"
            >
              {{ t('invoice.createDraft') }}
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
  </div>
</template>
