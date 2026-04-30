/**
 * Flatten a Treatment (header + teeth[]) into per-tooth views.
 *
 * The odontogram descendants (ToothQuadrant, ToothDualView, ToothTooltip,
 * TreatmentListSection, TreatmentEditModal) were designed around the old
 * ToothTreatment shape (one row per tooth, with `treatment_type` and `surfaces`
 * at the top level). Until those components are fully migrated, this adapter
 * keeps their props stable: one input Treatment × N teeth → N ToothTreatmentView.
 */

import type { Surface, ToothTreatmentView, Treatment } from '~/types'

export function viewForTooth(treatment: Treatment, toothNumber: number): ToothTreatmentView | null {
  const member = treatment.teeth.find(t => t.tooth_number === toothNumber)
  if (!member) return null
  return {
    id: `${treatment.id}:${member.id}`,
    treatment_id: treatment.id,
    tooth_number: toothNumber,
    treatment_type: treatment.clinical_type,
    clinical_type: treatment.clinical_type,
    surfaces: (member.surfaces as Surface[] | null) ?? null,
    role: member.role,
    status: treatment.status,
    recorded_at: treatment.recorded_at,
    performed_at: treatment.performed_at,
    performed_by: treatment.performed_by,
    performed_by_name: treatment.performed_by_name,
    notes: treatment.notes,
    price_snapshot: treatment.price_snapshot,
    catalog_item_id: treatment.catalog_item_id,
    catalog_item: treatment.catalog_item,
    source_module: treatment.source_module,
    created_at: treatment.created_at,
    updated_at: treatment.updated_at,
    is_multi: treatment.teeth.length > 1,
    teeth_count: treatment.teeth.length
  }
}

export function viewsForTooth(treatments: Treatment[], toothNumber: number): ToothTreatmentView[] {
  const out: ToothTreatmentView[] = []
  for (const treatment of treatments) {
    const v = viewForTooth(treatment, toothNumber)
    if (v) out.push(v)
  }
  return out
}

/**
 * Resolve the display name for a treatment view.
 * Prefers the catalog item's localized name (so variants like "Puente metal-cerámica"
 * or "Puente zirconio" survive), then the i18n label for the generic clinical type,
 * then the raw clinical_type string.
 */
export function getTreatmentDisplayName(
  view: Pick<ToothTreatmentView, 'treatment_type' | 'catalog_item'>,
  locale: string,
  t: (key: string, fallback?: string) => string
): string {
  const names = view.catalog_item?.names
  if (names) {
    const name = names[locale] || names.es || names.en
    if (name) return name
  }
  const key = `odontogram.treatments.types.${view.treatment_type}`
  const translated = t(key, view.treatment_type)
  return translated !== key ? translated : view.treatment_type
}
