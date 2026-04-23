import { defineAsyncComponent } from 'vue'
import { registerSlot } from '~~/app/composables/useModuleSlots'

export default defineNuxtPlugin(() => {
  registerSlot('dashboard.hero', {
    id: 'reports.dashboard.overdueHero',
    component: defineAsyncComponent(() => import('../components/home/OverdueHeroTile.vue')),
    order: 30,
    permission: 'reports.billing.read'
  })

  registerSlot('dashboard.attention', {
    id: 'reports.dashboard.overduePanel',
    component: defineAsyncComponent(() => import('../components/home/OverdueInvoicesPanel.vue')),
    order: 20,
    permission: 'reports.billing.read'
  })

  registerSlot('dashboard.activity', {
    id: 'reports.dashboard.weekGlance',
    component: defineAsyncComponent(() => import('../components/home/WeekGlancePanel.vue')),
    order: 20,
    permission: 'reports.billing.read'
  })
})
