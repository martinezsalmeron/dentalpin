/**
 * Composable for odontogram-catalog integration.
 *
 * Provides treatments from the catalog with odontogram mappings,
 * with fallback to hardcoded constants if catalog is empty.
 */

import type { ApiResponse, OdontogramTreatment } from '~/types'
import {
  TREATMENT_CATEGORIES,
  TREATMENT_COLORS,
  VISUALIZATION_RULES,
  isSurfaceTreatment,
  normalizeTreatmentType,
  type TreatmentClinicalCategory
} from '~/config/odontogramConstants'

export function useTreatmentCatalog() {
  const api = useApi()

  // State
  const treatments = useState<OdontogramTreatment[]>('treatmentCatalog:treatments', () => [])
  const loading = useState<boolean>('treatmentCatalog:loading', () => false)
  const error = useState<string | null>('treatmentCatalog:error', () => null)
  const initialized = useState<boolean>('treatmentCatalog:initialized', () => false)

  // ============================================================================
  // Fetch treatments from catalog
  // ============================================================================

  async function fetchTreatments(): Promise<void> {
    try {
      loading.value = true
      error.value = null

      const response = await api.get<ApiResponse<OdontogramTreatment[]>>(
        '/api/v1/catalog/odontogram-treatments'
      )
      treatments.value = response.data
      initialized.value = true
    } catch (e) {
      error.value = 'Failed to fetch treatments from catalog'
      console.error('Error fetching treatments from catalog:', e)
      // Fallback will be used via computed properties
      initialized.value = true
    } finally {
      loading.value = false
    }
  }

  // ============================================================================
  // Computed - with fallback to constants
  // ============================================================================

  /**
   * Whether to use catalog treatments or fallback to constants.
   */
  const useCatalog = computed(() => treatments.value.length > 0)

  /**
   * Treatments grouped by clinical category.
   * Falls back to hardcoded constants if catalog is empty.
   */
  const treatmentsByCategory = computed(() => {
    if (useCatalog.value) {
      // Group catalog treatments by clinical_category
      const grouped: Record<string, OdontogramTreatment[]> = {}
      for (const treatment of treatments.value) {
        const category = treatment.clinical_category
        if (!grouped[category]) {
          grouped[category] = []
        }
        grouped[category].push(treatment)
      }
      return grouped
    }

    // Fallback to constants
    const grouped: Record<string, OdontogramTreatment[]> = {}
    for (const category of TREATMENT_CATEGORIES) {
      grouped[category.key] = category.treatments.map(treatmentType => ({
        id: treatmentType,
        internal_code: treatmentType.toUpperCase(),
        names: { es: treatmentType, en: treatmentType },
        default_price: undefined,
        treatment_scope: isSurfaceTreatment(treatmentType) ? 'surface' : 'whole_tooth',
        requires_surfaces: isSurfaceTreatment(treatmentType),
        is_diagnostic: category.key === 'diagnostico',
        odontogram_treatment_type: treatmentType,
        visualization_rules: getVisualizationRulesForType(treatmentType),
        visualization_config: {
          color: TREATMENT_COLORS[treatmentType] || { light: '#6B7280', dark: '#9CA3AF' }
        },
        clinical_category: category.key,
        category_key: category.key,
        category_names: { es: category.labelKey, en: category.labelKey }
      }))
    }
    return grouped
  })

  /**
   * All available clinical categories.
   */
  const clinicalCategories = computed(() => {
    if (useCatalog.value) {
      return Object.keys(treatmentsByCategory.value)
    }
    return TREATMENT_CATEGORIES.map(c => c.key)
  })

  /**
   * Get treatments for a specific category.
   */
  function getTreatmentsForCategory(categoryKey: string): OdontogramTreatment[] {
    return treatmentsByCategory.value[categoryKey] || []
  }

  /**
   * Get a single treatment by its odontogram_treatment_type.
   */
  function getTreatmentByType(treatmentType: string): OdontogramTreatment | undefined {
    const normalized = normalizeTreatmentType(treatmentType)

    if (useCatalog.value) {
      return treatments.value.find(t => t.odontogram_treatment_type === normalized)
    }

    // Fallback to creating from constants
    for (const category of TREATMENT_CATEGORIES) {
      if (category.treatments.includes(normalized)) {
        return {
          id: normalized,
          internal_code: normalized.toUpperCase(),
          names: { es: normalized, en: normalized },
          default_price: undefined,
          treatment_scope: isSurfaceTreatment(normalized) ? 'surface' : 'whole_tooth',
          requires_surfaces: isSurfaceTreatment(normalized),
          is_diagnostic: category.key === 'diagnostico',
          odontogram_treatment_type: normalized,
          visualization_rules: getVisualizationRulesForType(normalized),
          visualization_config: {
            color: TREATMENT_COLORS[normalized] || { light: '#6B7280', dark: '#9CA3AF' }
          },
          clinical_category: category.key,
          category_key: category.key,
          category_names: { es: category.labelKey, en: category.labelKey }
        }
      }
    }

    return undefined
  }

  /**
   * Get effective treatment type for odontogram rendering.
   * This is what should be used when applying treatments to teeth.
   */
  function getEffectiveTreatmentType(catalogItemId: string | undefined, fallbackType: string): string {
    if (catalogItemId && useCatalog.value) {
      const treatment = treatments.value.find(t => t.id === catalogItemId)
      if (treatment) {
        return treatment.odontogram_treatment_type
      }
    }
    return normalizeTreatmentType(fallbackType)
  }

  /**
   * Get treatment name for display.
   */
  function getTreatmentName(
    treatmentType: string,
    locale = 'es'
  ): string {
    const treatment = getTreatmentByType(treatmentType)
    if (treatment) {
      return treatment.names[locale] || treatment.names.es || treatmentType
    }
    return treatmentType
  }

  /**
   * Get treatment price for display.
   */
  function getTreatmentPrice(treatmentType: string): number | undefined {
    const treatment = getTreatmentByType(treatmentType)
    return treatment?.default_price
  }

  /**
   * Check if treatment requires surface selection.
   */
  function treatmentRequiresSurfaces(treatmentType: string): boolean {
    const treatment = getTreatmentByType(treatmentType)
    return treatment?.requires_surfaces ?? isSurfaceTreatment(treatmentType)
  }

  /**
   * Check if treatment is diagnostic (should only allow 'existing' status).
   */
  function treatmentIsDiagnostic(treatmentType: string): boolean {
    const treatment = getTreatmentByType(treatmentType)
    return treatment?.is_diagnostic ?? false
  }

  // ============================================================================
  // Helpers
  // ============================================================================

  function getVisualizationRulesForType(treatmentType: string): string[] {
    const rules: string[] = []
    for (const [rule, treatments] of Object.entries(VISUALIZATION_RULES)) {
      if (treatments.includes(treatmentType)) {
        rules.push(rule)
      }
    }
    return rules
  }

  function getCategoryLabel(categoryKey: string, locale = 'es'): string {
    if (useCatalog.value) {
      const treatments = treatmentsByCategory.value[categoryKey]
      if (treatments && treatments.length > 0) {
        return treatments[0].category_names[locale] || categoryKey
      }
    }

    // Fallback to constants
    const category = TREATMENT_CATEGORIES.find(c => c.key === categoryKey)
    return category?.labelKey || categoryKey
  }

  function isCategoryDiagnostic(categoryKey: TreatmentClinicalCategory): boolean {
    return categoryKey === 'diagnostico'
  }

  return {
    // State
    treatments,
    loading,
    error,
    initialized,

    // Fetch
    fetchTreatments,

    // Computed
    useCatalog,
    treatmentsByCategory,
    clinicalCategories,

    // Treatment getters
    getTreatmentsForCategory,
    getTreatmentByType,
    getEffectiveTreatmentType,
    getTreatmentName,
    getTreatmentPrice,
    treatmentRequiresSurfaces,
    treatmentIsDiagnostic,

    // Helpers
    getCategoryLabel,
    isCategoryDiagnostic
  }
}
