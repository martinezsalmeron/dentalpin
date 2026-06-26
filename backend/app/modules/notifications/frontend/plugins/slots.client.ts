import { defineAsyncComponent } from 'vue'
import { registerSlot } from '~~/app/composables/useModuleSlots'

/**
 * Slot registrations for the `notifications` module.
 *
 * The patient WhatsApp conversation thread (channel-agnostic comms log +
 * reply box) renders as a card on the patient summary. The slot registry is
 * the only contract — no host import.
 */
export default defineNuxtPlugin(() => {
  registerSlot('patient.summary.cards', {
    id: 'notifications.patient.conversation',
    component: defineAsyncComponent(() => import('../components/ConversationThread.vue')),
    permission: 'notifications.logs.read',
    order: 60
  })
})
