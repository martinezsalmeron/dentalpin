import { defineAsyncComponent } from 'vue'
import { registerSlot } from '~~/app/composables/useModuleSlots'

export default defineNuxtPlugin(() => {
  registerSlot('settings.sections', {
    id: 'verifactu.settings.cards',
    component: defineAsyncComponent(() => import('../components/SettingsCardsSlot.vue')),
    order: 60,
    category: 'billing',
    labelKey: 'verifactu.settingsCards.title',
    descriptionKey: 'verifactu.settingsCards.description',
    searchKeywords: ['verifactu', 'aeat', 'impuesto', 'factura electronica', 'factura electrónica', 'rd 1007/2023']
  })
})
