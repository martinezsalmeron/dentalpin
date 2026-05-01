import { defineAsyncComponent } from 'vue'
import { registerSlot } from '~~/app/composables/useModuleSlots'

/**
 * Slot registrations for the `recalls` module.
 *
 * Hosts (`patients`, `agenda`, `odontogram`) expose stable slot names
 * and never import this module. The slot registry is the only contract.
 */
export default defineNuxtPlugin(() => {
  // Patient summary hero — "Set recall" action button.
  registerSlot('patient.summary.actions', {
    id: 'recalls.patient.set-recall',
    component: defineAsyncComponent(() => import('../components/SetRecallButton.vue')),
    permission: 'recalls.write',
    order: 20
  })

  // Patient summary feed — pill + recent recall history.
  registerSlot('patient.summary.feed', {
    id: 'recalls.patient.feed',
    component: defineAsyncComponent(() => import('../components/RecallSummaryFeed.vue')),
    permission: 'recalls.read',
    order: 30
  })

  // Per-treatment "Set recall" action (odontogram diagnosis row +
  // treatment-plan items).
  registerSlot('odontogram.condition.actions', {
    id: 'recalls.plan-item.set-recall',
    component: defineAsyncComponent(() => import('../components/SetRecallFromTreatmentButton.vue')),
    permission: 'recalls.write',
    order: 30
  })

  // Post-completion follow-up prompt rendered by AppointmentQuickActions.
  registerSlot('appointment.completed.followup', {
    id: 'recalls.appointment.closeout-prompt',
    component: defineAsyncComponent(() => import('../components/RecallCloseoutPrompt.vue')),
    permission: 'recalls.write',
    order: 10
  })

  // Dashboard widget — counters strip.
  registerSlot('dashboard.attention', {
    id: 'recalls.dashboard.due-overdue',
    component: defineAsyncComponent(() => import('../components/RecallDashboardWidget.vue')),
    permission: 'recalls.read',
    order: 30
  })

  // Settings — reason intervals + category map editor.
  registerSlot('settings.sections', {
    id: 'recalls.settings.section',
    component: defineAsyncComponent(() => import('../components/RecallSettingsPanel.vue')),
    permission: 'recalls.write',
    labelKey: 'recalls.settings.title',
    descriptionKey: 'recalls.settings.description',
    category: 'clinical',
    order: 40
  })
})
