<script setup lang="ts">
/**
 * PatientClinicalNotesByPlan — grouped clinical-notes feed for a patient.
 *
 * Renders one block per treatment plan (``Plan → Tratamiento → Notas``) so a
 * clinician can scan every plan / plan_item / visit note in a single view.
 * Data is served pre-grouped by ``GET /treatment_plan/patients/{id}/clinical-notes``;
 * rendering stays purely presentational here.
 *
 * Mounted into the ``patient.timeline.treatments`` slot by this module's
 * ``frontend/plugins/slots.client.ts`` so the host ``patient_timeline`` module
 * does not import anything from ``treatment_plan``.
 */

import type { PlanItemNotesGroup, PlanNotesGroup, PlannedTreatmentItem } from '~~/app/types'

const props = defineProps<{
  ctx: { patientId: string }
}>()

const { t, locale } = useI18n()
const { listGroupedForPatient } = useClinicalNotes()

const groups = ref<PlanNotesGroup[]>([])
const loading = ref(false)

async function refresh() {
  if (!props.ctx?.patientId) return
  loading.value = true
  try {
    groups.value = await listGroupedForPatient(props.ctx.patientId)
  } finally {
    loading.value = false
  }
}

watch(() => props.ctx?.patientId, refresh, { immediate: true })

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString()
  } catch {
    return iso
  }
}

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

function itemToothLabel(item: PlannedTreatmentItem): string {
  const teeth = (item.treatment?.teeth ?? []).map(x => x.tooth_number)
  if (teeth.length === 0) return ''
  return `${t('clinical.tooth')} ${teeth.join(', ')}`
}

function sourceBadgeColor(source: 'plan' | 'plan_item' | 'visit'): string {
  if (source === 'visit') return 'primary'
  if (source === 'plan_item') return 'success'
  return 'neutral'
}

const hasAny = computed(() =>
  groups.value.some(
    g => g.plan_notes.length > 0 || g.treatments.some(tr => tr.notes.length > 0)
  )
)
</script>

<template>
  <div class="space-y-6">
    <div
      v-if="loading"
      class="space-y-3"
    >
      <USkeleton
        v-for="i in 3"
        :key="i"
        class="h-20 w-full"
      />
    </div>

    <div
      v-else-if="groups.length === 0 || !hasAny"
      class="text-center py-8 text-subtle text-sm"
    >
      <UIcon
        name="i-lucide-notebook-pen"
        class="w-10 h-10 mx-auto mb-3 opacity-50"
      />
      <p>{{ t('treatmentPlans.byPlan.empty') }}</p>
    </div>

    <template v-else>
      <UCard
        v-for="group in groups"
        :key="group.plan.id"
      >
        <template #header>
          <div class="flex items-center justify-between gap-2">
            <div class="flex items-center gap-2 min-w-0">
              <UIcon
                name="i-lucide-clipboard-list"
                class="w-4 h-4 text-muted flex-shrink-0"
              />
              <span class="font-medium truncate">
                {{ group.plan.plan_number }}
                <span
                  v-if="group.plan.title"
                  class="text-muted font-normal"
                >— {{ group.plan.title }}</span>
              </span>
            </div>
            <UBadge
              variant="subtle"
              size="xs"
            >
              {{ t(`treatmentPlans.status.${group.plan.status}`) }}
            </UBadge>
          </div>
        </template>

        <div class="space-y-4">
          <!-- Plan-level notes -->
          <section v-if="group.plan_notes.length > 0">
            <h4 class="text-caption font-medium text-muted mb-2">
              {{ t('treatmentPlans.byPlan.planNotesLabel') }}
            </h4>
            <div class="space-y-2">
              <article
                v-for="note in group.plan_notes"
                :key="note.note_id || `plan-${note.owner_id}-${note.created_at}`"
                class="border border-default rounded-md p-3 bg-surface"
              >
                <header class="flex items-center justify-between mb-2 gap-2">
                  <span class="text-caption text-muted">
                    {{ formatDate(note.created_at) }}
                  </span>
                  <UBadge
                    :color="sourceBadgeColor(note.source)"
                    variant="subtle"
                    size="xs"
                  >
                    {{ t(`treatmentPlans.filterBy.${note.source === 'plan_item' ? 'item' : note.source}`) }}
                  </UBadge>
                </header>
                <div
                  class="prose prose-sm max-w-none"
                  v-html="note.body"
                />
              </article>
            </div>
          </section>

          <!-- Per-treatment notes -->
          <section
            v-for="tgroup in group.treatments"
            :key="tgroup.plan_item.id"
            class="border-t border-default pt-3 first:border-t-0 first:pt-0"
          >
            <header class="flex items-center gap-2 mb-2">
              <UIcon
                name="i-lucide-stethoscope"
                class="w-4 h-4 text-muted"
              />
              <span class="font-medium">{{ getItemName(tgroup.plan_item) }}</span>
              <span
                v-if="itemToothLabel(tgroup.plan_item)"
                class="text-caption text-muted"
              >
                · {{ itemToothLabel(tgroup.plan_item) }}
              </span>
            </header>

            <div
              v-if="tgroup.notes.length === 0"
              class="text-caption text-subtle italic pl-6"
            >
              {{ t('treatmentPlans.byPlan.noNotesForTreatment') }}
            </div>
            <div
              v-else
              class="space-y-2 pl-6"
            >
              <article
                v-for="note in tgroup.notes"
                :key="note.note_id || `visit-${note.owner_id}-${note.created_at}`"
                class="border border-default rounded-md p-3 bg-surface"
              >
                <header class="flex items-center justify-between mb-2 gap-2">
                  <span class="text-caption text-muted">
                    {{ formatDate(note.created_at) }}
                  </span>
                  <UBadge
                    :color="sourceBadgeColor(note.source)"
                    variant="subtle"
                    size="xs"
                  >
                    {{ t(`treatmentPlans.filterBy.${note.source === 'plan_item' ? 'item' : note.source}`) }}
                  </UBadge>
                </header>
                <div
                  class="prose prose-sm max-w-none"
                  v-html="note.body"
                />
              </article>
            </div>
          </section>
        </div>
      </UCard>
    </template>
  </div>
</template>
