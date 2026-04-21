import { defineAsyncComponent } from 'vue'
import { registerSlot } from '~~/app/composables/useModuleSlots'

export default defineNuxtPlugin(() => {
  registerSlot('settings.sections', {
    id: 'schedules.settings.cards',
    component: defineAsyncComponent(() => import('../components/SettingsCardsSlot.vue')),
    order: 40
  })
})
