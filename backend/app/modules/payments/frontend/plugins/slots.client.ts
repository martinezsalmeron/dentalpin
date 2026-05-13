import { defineAsyncComponent } from 'vue'
import { registerSlot } from '~~/app/composables/useModuleSlots'

/**
 * Slot registrations for the `payments` module.
 *
 * Hosts (`budget`) expose stable slot names. The slot registry is the
 * only contract — the budget module never imports payments code.
 */
export default defineNuxtPlugin(() => {
  // Cobros vinculados al presupuesto. Renders inside the budget-detail
  // sidebar with `ctx = { budget }`. Shows total / cobrado / pendiente
  // plus the allocation history and a "Cobrar" CTA that opens the
  // shared `PaymentCreateModal` pre-filled with budget + patient ids.
  registerSlot('budget.detail.sidebar', {
    id: 'payments.budget.detail.sidebar.collected',
    component: defineAsyncComponent(
      () => import('../components/BudgetPaymentsCard.vue')
    ),
    permission: 'payments.record.read',
    order: 10
  })

  // Payments report card on /reports. Lets the reports module stay
  // unaware of payments while users still discover the dashboard from
  // the central reports landing.
  registerSlot('reports.categories', {
    id: 'payments.reports.categories.dashboard',
    component: defineAsyncComponent(
      () => import('../components/PaymentsReportEntry.vue')
    ),
    permission: 'payments.reports.read',
    order: 40
  })
})
