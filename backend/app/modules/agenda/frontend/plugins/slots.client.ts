import { defineAsyncComponent } from 'vue'
import { registerSlot } from '~~/app/composables/useModuleSlots'

export default defineNuxtPlugin(() => {
  registerSlot('dashboard.hero', {
    id: 'agenda.dashboard.todayAppointments',
    component: defineAsyncComponent(() => import('../components/home/TodayAppointmentsTile.vue')),
    order: 10,
    permission: 'agenda.appointments.read'
  })

  registerSlot('dashboard.hero', {
    id: 'agenda.dashboard.inClinicNow',
    component: defineAsyncComponent(() => import('../components/home/InClinicNowTile.vue')),
    order: 20,
    permission: 'agenda.appointments.read'
  })

  registerSlot('dashboard.timeline', {
    id: 'agenda.dashboard.todayTimeline',
    component: defineAsyncComponent(() => import('../components/home/TodayTimelineStrip.vue')),
    order: 10,
    permission: 'agenda.appointments.read'
  })

  registerSlot('dashboard.attention', {
    id: 'agenda.dashboard.unconfirmed',
    component: defineAsyncComponent(() => import('../components/home/UnconfirmedPanel.vue')),
    order: 10,
    permission: 'agenda.appointments.read'
  })
})
