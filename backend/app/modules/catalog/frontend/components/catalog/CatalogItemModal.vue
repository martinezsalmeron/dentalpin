<script setup lang="ts">
import type {
  TreatmentCatalogCategory,
  TreatmentCatalogItem,
  TreatmentCatalogItemUpdate,
  TreatmentCatalogItemCreate
} from '~~/app/types'
import {
  ALL_TREATMENT_TYPES,
  TREATMENT_CATEGORIES,
  VISUALIZATION_RULES,
  isSurfaceTreatment
} from '~~/app/config/odontogramConstants'

const props = defineProps<{
  item: TreatmentCatalogItem | null
  categories: TreatmentCatalogCategory[]
  loading: boolean
}>()

const open = defineModel<boolean>('open', { default: false })
const emit = defineEmits<{
  save: [data: TreatmentCatalogItemUpdate]
  create: [data: TreatmentCatalogItemCreate]
}>()

const { t, locale } = useI18n()

// VAT Types
const {
  vatTypeOptions,
  defaultVatType,
  fetchVatTypes
} = useVatTypes()

// Fetch VAT types on mount
onMounted(() => {
  fetchVatTypes()
})

// Determine if we're in create or edit mode
const isCreateMode = computed(() => !props.item)

// Form state
const formData = ref<TreatmentCatalogItemUpdate>({})

// Computed for single name field (stores in current locale)
const itemName = computed({
  get: () => formData.value.names?.[locale.value] || '',
  set: (value: string) => {
    if (!formData.value.names) {
      formData.value.names = {}
    }
    formData.value.names[locale.value] = value
  }
})

// Odontogram mapping state
const odontogramType = ref<string | undefined>(undefined)
const clinicalCategory = ref<string | undefined>(undefined)

// Watch for item changes to populate form
watch(
  () => props.item,
  (newItem) => {
    if (newItem) {
      // Edit mode: populate with existing item
      formData.value = {
        internal_code: newItem.internal_code,
        category_id: newItem.category_id,
        names: { ...newItem.names },
        descriptions: newItem.descriptions ? { ...newItem.descriptions } : undefined,
        default_price: newItem.default_price,
        cost_price: newItem.cost_price,
        pricing_strategy: newItem.pricing_strategy || 'flat',
        pricing_config: newItem.pricing_config ?? null,
        surface_prices: newItem.surface_prices ? { ...newItem.surface_prices } : null,
        default_duration_minutes: newItem.default_duration_minutes,
        requires_appointment: newItem.requires_appointment,
        vat_type_id: newItem.vat_type_id,
        treatment_scope: newItem.treatment_scope,
        is_diagnostic: newItem.is_diagnostic,
        requires_surfaces: newItem.requires_surfaces,
        material_notes: newItem.material_notes,
        is_active: newItem.is_active
      }
      // Load existing odontogram mapping
      if (newItem.odontogram_mapping) {
        odontogramType.value = newItem.odontogram_mapping.odontogram_treatment_type
        clinicalCategory.value = newItem.odontogram_mapping.clinical_category
      } else {
        odontogramType.value = undefined
        clinicalCategory.value = undefined
      }
    } else {
      // Create mode: set default values, use default VAT type
      formData.value = {
        internal_code: '',
        category_id: props.categories[0]?.id,
        names: { [locale.value]: '' },
        default_price: 0,
        cost_price: 0,
        pricing_strategy: 'flat',
        pricing_config: null,
        surface_prices: null,
        default_duration_minutes: 30,
        requires_appointment: true,
        vat_type_id: defaultVatType.value?.id,
        treatment_scope: 'tooth',
        is_diagnostic: false,
        requires_surfaces: false,
        is_active: true
      }
      odontogramType.value = undefined
      clinicalCategory.value = undefined
    }
  },
  { immediate: true }
)

// Treatment scope options — aligned with Treatment.scope.
const scopeOptions = [
  { value: 'tooth', label: t('catalog.scopeTypes.tooth') },
  { value: 'multi_tooth', label: t('catalog.scopeTypes.multi_tooth') },
  { value: 'global_mouth', label: t('catalog.scopeTypes.global_mouth') },
  { value: 'global_arch', label: t('catalog.scopeTypes.global_arch') }
]

// Pricing strategy options
const strategyOptions = computed(() => [
  { value: 'flat', label: t('catalog.pricingStrategy.flat') },
  { value: 'per_tooth', label: t('catalog.pricingStrategy.per_tooth') },
  { value: 'per_surface', label: t('catalog.pricingStrategy.per_surface') },
  { value: 'per_role', label: t('catalog.pricingStrategy.per_role') }
])

const SURFACE_TIERS = ['1', '2', '3', '4', '5'] as const

// True when the tier-pricing editor should render.
const showSurfacePrices = computed(() => formData.value.pricing_strategy === 'per_surface')

// When strategy switches to per_surface, seed all tiers with default_price so the
// user sees a starting matrix they can tweak. Switching away clears the map.
watch(
  () => formData.value.pricing_strategy,
  (strategy) => {
    if (strategy === 'per_surface') {
      if (!formData.value.surface_prices) {
        const base = Number(formData.value.default_price) || 0
        formData.value.surface_prices = {
          1: base,
          2: base,
          3: base,
          4: base,
          5: base
        } as unknown as Record<string, number>
      }
    } else {
      formData.value.surface_prices = null
    }
  }
)

function getTierPrice(tier: string): number | undefined {
  const v = formData.value.surface_prices?.[tier]
  return typeof v === 'number' ? v : typeof v === 'string' ? Number(v) : undefined
}

function setTierPrice(tier: string, value: number | string | undefined) {
  if (!formData.value.surface_prices) {
    formData.value.surface_prices = {}
  }
  const n = value === undefined || value === '' ? 0 : Number(value)
  formData.value.surface_prices[tier] = Number.isFinite(n) ? n : 0
}

// Category options for select
const categoryOptions = computed(() =>
  props.categories.map(c => ({
    value: c.id,
    label: c.names[locale.value] || c.names.es || c.names.en || c.key
  }))
)

// Odontogram treatment type options
const odontogramTypeOptions = computed(() => [
  { value: undefined, label: t('catalog.noOdontogramMapping') },
  ...ALL_TREATMENT_TYPES.map(type => ({
    value: type,
    label: t(`odontogram.treatments.${type}`, type)
  }))
])

// Clinical category options (for TreatmentBar grouping)
const clinicalCategoryOptions = computed(() =>
  TREATMENT_CATEGORIES.map(c => ({
    value: c.key,
    label: t(c.labelKey, c.key)
  }))
)

// Auto-select clinical category based on odontogram type
watch(odontogramType, (newType) => {
  if (newType) {
    // Find the category that contains this treatment
    const category = TREATMENT_CATEGORIES.find(c => c.treatments.includes(newType))
    if (category) {
      clinicalCategory.value = category.key
    }
    // Also update treatment characteristics based on type.
    // `treatment_scope` stays `tooth` by default — multi_tooth/globals are an explicit
    // admin choice. Only the `requires_surfaces` flag is inferred automatically.
    formData.value.requires_surfaces = isSurfaceTreatment(newType)
  }
})

// Helper to get visualization rules for a treatment type
function getVisualizationRules(treatmentType: string): string[] {
  const rules: string[] = []
  for (const [rule, treatments] of Object.entries(VISUALIZATION_RULES)) {
    if (treatments.includes(treatmentType)) {
      rules.push(rule)
    }
  }
  return rules
}

// Form validation
const isValid = computed(() => {
  return (
    formData.value.internal_code
    && itemName.value
    && formData.value.category_id
  )
})

function handleSubmit() {
  if (!isValid.value) return

  // Clean up undefined values
  const cleanData: Record<string, unknown> = {}
  for (const [key, value] of Object.entries(formData.value)) {
    if (value !== undefined) {
      cleanData[key] = value
    }
  }

  // Add odontogram mapping if type is selected
  if (odontogramType.value && clinicalCategory.value) {
    cleanData.odontogram_mapping = {
      odontogram_treatment_type: odontogramType.value,
      visualization_rules: getVisualizationRules(odontogramType.value),
      visualization_config: {},
      clinical_category: clinicalCategory.value
    }
  }

  if (isCreateMode.value) {
    emit('create', cleanData as TreatmentCatalogItemCreate)
  } else {
    emit('save', cleanData as TreatmentCatalogItemUpdate)
  }
}

function handleClose() {
  open.value = false
}
</script>

<template>
  <UModal v-model:open="open">
    <template #content>
      <div class="bg-surface rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] flex flex-col">
        <!-- Header -->
        <div class="flex items-center gap-2 p-4 border-b border-default  shrink-0">
          <UIcon
            :name="isCreateMode ? 'i-lucide-plus' : 'i-lucide-edit'"
            class="w-5 h-5 text-primary-accent"
          />
          <h3 class="font-semibold text-default dark:text-white">
            {{ isCreateMode ? t('catalog.newItem') : t('catalog.editItem') }}
          </h3>
        </div>

        <!-- Scrollable content -->
        <div class="overflow-y-auto flex-1 p-4">
          <form
            id="catalog-edit-form"
            class="space-y-6"
            @submit.prevent="handleSubmit"
          >
            <!-- Basic info -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <UFormField :label="t('catalog.code')">
                <UInput
                  v-model="formData.internal_code"
                  :disabled="!isCreateMode && item?.is_system"
                  required
                />
              </UFormField>

              <UFormField :label="t('catalog.category')">
                <USelect
                  v-model="formData.category_id"
                  :items="categoryOptions"
                  value-key="value"
                  label-key="label"
                  :placeholder="t('catalog.selectCategory')"
                  :disabled="!isCreateMode && item?.is_system"
                />
              </UFormField>
            </div>

            <!-- Name -->
            <UFormField :label="t('catalog.name')">
              <UInput
                v-model="itemName"
                required
              />
            </UFormField>

            <!-- Pricing -->
            <div class="border-t border-default  pt-4">
              <h4 class="font-medium text-default dark:text-white mb-4">
                {{ t('catalog.pricing') }}
              </h4>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <UFormField :label="t('catalog.defaultPrice')">
                  <UInput
                    v-model.number="formData.default_price"
                    type="number"
                    step="0.01"
                    min="0"
                  />
                </UFormField>

                <UFormField :label="t('catalog.costPrice')">
                  <UInput
                    v-model.number="formData.cost_price"
                    type="number"
                    step="0.01"
                    min="0"
                  />
                </UFormField>
              </div>

              <!-- Pricing strategy -->
              <div class="mt-4">
                <UFormField
                  :label="t('catalog.pricingStrategy.label')"
                  :help="t('catalog.pricingStrategy.help')"
                >
                  <USelect
                    v-model="formData.pricing_strategy"
                    :items="strategyOptions"
                    value-key="value"
                    label-key="label"
                    :disabled="!isCreateMode && item?.is_system"
                  />
                </UFormField>
              </div>

              <!-- Surface price tiers (per_surface strategy) -->
              <div
                v-if="showSurfacePrices"
                class="mt-4 rounded-token-md alert-surface-info p-4"
              >
                <div class="flex items-center gap-2 mb-3">
                  <UIcon
                    name="i-lucide-layers"
                    class="w-4 h-4 text-info-accent"
                  />
                  <h5 class="font-medium text-sm text-default dark:text-white">
                    {{ t('catalog.surfacePrices.title') }}
                  </h5>
                </div>
                <p class="text-xs text-muted mb-3">
                  {{ t('catalog.surfacePrices.help') }}
                </p>
                <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-2">
                  <UFormField
                    v-for="tier in SURFACE_TIERS"
                    :key="tier"
                    :label="t('catalog.surfacePrices.tier', { n: tier })"
                    class="text-xs"
                  >
                    <UInput
                      :model-value="getTierPrice(tier)"
                      type="number"
                      step="0.01"
                      min="0"
                      size="sm"
                      @update:model-value="setTierPrice(tier, $event)"
                    />
                  </UFormField>
                </div>
              </div>
            </div>

            <!-- Tax -->
            <UFormField :label="t('catalog.vatType')">
              <USelect
                v-model="formData.vat_type_id"
                :items="vatTypeOptions"
                value-key="value"
                label-key="label"
                :placeholder="t('catalog.selectVatType')"
              />
            </UFormField>

            <!-- Scheduling -->
            <div class="border-t border-default  pt-4">
              <h4 class="font-medium text-default dark:text-white mb-4">
                {{ t('catalog.scheduling') }}
              </h4>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <UFormField :label="t('catalog.duration')">
                  <UInput
                    v-model.number="formData.default_duration_minutes"
                    type="number"
                    min="0"
                    max="480"
                  >
                    <template #trailing>
                      min
                    </template>
                  </UInput>
                </UFormField>

                <div class="flex items-center gap-3 pt-6">
                  <USwitch v-model="formData.requires_appointment" />
                  <span class="text-sm text-muted">
                    {{ t('catalog.requiresAppointment') }}
                  </span>
                </div>
              </div>
            </div>

            <!-- Treatment characteristics -->
            <div class="border-t border-default  pt-4">
              <h4 class="font-medium text-default dark:text-white mb-4">
                {{ t('catalog.characteristics') }}
              </h4>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <UFormField :label="t('catalog.scope')">
                  <USelect
                    v-model="formData.treatment_scope"
                    :items="scopeOptions"
                    value-key="value"
                    label-key="label"
                    :placeholder="t('catalog.selectScope')"
                    :disabled="!isCreateMode && item?.is_system"
                  />
                </UFormField>

                <div class="space-y-3 pt-6">
                  <div class="flex items-center gap-3">
                    <USwitch
                      v-model="formData.is_diagnostic"
                      :disabled="!isCreateMode && item?.is_system"
                    />
                    <span class="text-sm text-muted">
                      {{ t('catalog.isDiagnostic') }}
                    </span>
                  </div>

                  <div class="flex items-center gap-3">
                    <USwitch
                      v-model="formData.requires_surfaces"
                      :disabled="!isCreateMode && item?.is_system"
                    />
                    <span class="text-sm text-muted">
                      {{ t('catalog.requiresSurfaces') }}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Odontogram mapping -->
            <div class="border-t border-default  pt-4">
              <h4 class="font-medium text-default dark:text-white mb-4">
                {{ t('catalog.odontogramMapping') }}
              </h4>
              <p class="text-caption text-subtle  mb-4">
                {{ t('catalog.odontogramMappingDescription') }}
              </p>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <UFormField :label="t('catalog.odontogramType')">
                  <USelect
                    v-model="odontogramType"
                    :items="odontogramTypeOptions"
                    value-key="value"
                    label-key="label"
                    :placeholder="t('catalog.selectOdontogramType')"
                  />
                </UFormField>

                <UFormField :label="t('catalog.clinicalCategory')">
                  <USelect
                    v-model="clinicalCategory"
                    :items="clinicalCategoryOptions"
                    value-key="value"
                    label-key="label"
                    :placeholder="t('catalog.selectClinicalCategory')"
                    :disabled="!odontogramType"
                  />
                </UFormField>
              </div>
              <p
                v-if="odontogramType"
                class="text-caption text-subtle  mt-2"
              >
                {{ t('catalog.odontogramMappingHint') }}
              </p>
            </div>

            <!-- Material notes -->
            <UFormField :label="t('catalog.materialNotes')">
              <UTextarea
                v-model="formData.material_notes"
                rows="2"
                :placeholder="t('catalog.materialNotesPlaceholder')"
              />
            </UFormField>

            <!-- Status -->
            <div class="flex items-center gap-3 border-t border-default  pt-4">
              <USwitch
                v-model="formData.is_active"
                :disabled="!isCreateMode && item?.is_system"
              />
              <span class="text-sm text-muted">
                {{ t('catalog.active') }}
              </span>
            </div>
          </form>
        </div>

        <!-- Footer -->
        <div class="flex justify-end gap-2 p-4 border-t border-default  shrink-0">
          <UButton
            variant="ghost"
            @click="handleClose"
          >
            {{ t('common.cancel') }}
          </UButton>
          <UButton
            :loading="loading"
            :disabled="!isValid"
            @click="handleSubmit"
          >
            {{ t('common.save') }}
          </UButton>
        </div>
      </div>
    </template>
  </UModal>
</template>
