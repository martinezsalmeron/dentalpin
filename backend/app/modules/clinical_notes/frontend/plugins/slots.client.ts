import { defineAsyncComponent } from 'vue'
import { registerSlot } from '~~/app/composables/useModuleSlots'

/**
 * Slot registrations for the clinical_notes module.
 *
 * Hosts (`patients`, `odontogram`, `treatment_plan`, `patient_timeline`)
 * expose stable slot names and never import from this module. The slot
 * registry is the only contract.
 */
export default defineNuxtPlugin(() => {
  // Patient Summary tab — recent notes feed.
  registerSlot('patient.summary.feed', {
    id: 'clinical_notes.patient.summary.feed',
    component: defineAsyncComponent(
      () => import('../components/RecentNotesFeed.vue')
    ),
    order: 10,
    permission: 'clinical_notes.notes.read'
  })

  // Diagnosis-mode right rail (odontogram).
  registerSlot('odontogram.diagnosis.sidebar', {
    id: 'clinical_notes.odontogram.diagnosis.sidebar',
    component: defineAsyncComponent(
      () => import('../components/DiagnosisNotesSidebar.vue')
    ),
    order: 10,
    permission: 'clinical_notes.notes.read'
  })

  // Per-treatment note action — reused inside the diagnosis conditions list
  // and the treatment-plan rows.
  registerSlot('odontogram.condition.actions', {
    id: 'clinical_notes.odontogram.condition.actions',
    component: defineAsyncComponent(
      () => import('../components/TreatmentNoteButton.vue')
    ),
    order: 10,
    permission: 'clinical_notes.notes.read'
  })

  // Patient timeline — plan-grouped notes (was registered by treatment_plan).
  registerSlot('patient.timeline.treatments', {
    id: 'clinical_notes.patient.timeline.treatments',
    component: defineAsyncComponent(
      () => import('../components/PatientClinicalNotesByPlan.vue')
    ),
    order: 10,
    permission: 'clinical_notes.notes.read'
  })
})
