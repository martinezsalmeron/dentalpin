import { defineAsyncComponent } from 'vue'
import { registerSlot } from '~~/app/composables/useModuleSlots'

export default defineNuxtPlugin(() => {
  registerSlot('dashboard.activity', {
    id: 'patients.dashboard.recent',
    component: defineAsyncComponent(() => import('../components/home/RecentPatientsPanel.vue')),
    order: 10,
    permission: 'patients.read'
  })
})
