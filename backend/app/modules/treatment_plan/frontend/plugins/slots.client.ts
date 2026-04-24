import { defineAsyncComponent } from 'vue'
import { registerSlot } from '~~/app/composables/useModuleSlots'

export default defineNuxtPlugin(() => {
  // Grouped clinical-notes feed (Plan → Tratamiento → Notas). The host
  // `patient_timeline` module renders this slot inside its "treatment"
  // category view without importing anything from treatment_plan.
  registerSlot('patient.timeline.treatments', {
    id: 'treatment_plan.patient.timeline.treatments',
    component: defineAsyncComponent(
      () => import('../components/clinical/notes/PatientClinicalNotesByPlan.vue')
    ),
    order: 10,
    permission: 'treatment_plan.notes.read'
  })
})
