import { defineAsyncComponent } from 'vue'
import { registerSlot } from '~~/app/composables/useModuleSlots'

/**
 * Slot registrations for the `periodontogram` module.
 *
 * Hosts (`patients`) expose stable slot names and never import this
 * module. The registry is the only contract.
 */
export default defineNuxtPlugin(() => {
  // Sub-tab inside the Diagnosis mode of the patient clinical tab.
  registerSlot('patient.diagnosis.subtabs', {
    id: 'periodontogram',
    component: defineAsyncComponent(
      () => import('../components/PeriodontogramView.vue')
    ),
    order: 20,
    permission: 'periodontogram.read',
    labelKey: 'periodontogram.tab.label'
  })
})
