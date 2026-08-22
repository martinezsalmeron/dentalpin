import { defineAsyncComponent } from 'vue'
import { registerSlot } from '~~/app/composables/useModuleSlots'

interface InvoiceCtx {
  invoice?: { compliance_data?: Record<string, unknown> | null } | null
  clinic?: { country?: string | null, settings?: { country?: string | null } | null } | null
}

// Server-authoritative country gate: always reads from the clinic
// object as returned by the backend API (`clinic.country` or the
// legacy `clinic.settings.country`), never a client-editable field.
function isIndiaInvoiceCtx(raw: unknown): boolean {
  const ctx = (raw ?? {}) as InvoiceCtx
  const country = ctx.clinic?.country ?? ctx.clinic?.settings?.country ?? null
  const hasIN = !!(ctx.invoice?.compliance_data as Record<string, unknown> | undefined)?.IN
  return country === 'IN' || hasIN
}

export default defineNuxtPlugin(() => {
  registerSlot('settings.sections', {
    id: 'india_gst.settings.cards',
    component: defineAsyncComponent(
      // Prefixed name — verifactu ships its own SettingsCardsSlot.vue and
      // both layers auto-import components with pathPrefix: false.
      () => import('../components/india-gst/IndiaGstSettingsCardsSlot.vue')
    ),
    order: 61,
    category: 'billing',
    labelKey: 'indiaGst.settingsCards.title',
    descriptionKey: 'indiaGst.settingsCards.description',
    searchKeywords: ['india', 'gst', 'gstin', 'cgst', 'sgst', 'igst', 'e-invoice', 'irn']
  })

  // Read-only GST + e-invoice panel on the issued invoice detail page.
  registerSlot('invoice.detail.compliance', {
    id: 'india_gst.invoice.detail.compliance',
    component: defineAsyncComponent(() => import('../components/india-gst/IndiaGstInvoicePanel.vue')),
    order: 20,
    condition: isIndiaInvoiceCtx
  })

  // Editable place-of-supply / SAC panel on the draft edit page.
  registerSlot('invoice.form.compliance', {
    id: 'india_gst.invoice.form.compliance',
    component: defineAsyncComponent(() => import('../components/india-gst/IndiaGstInvoiceFormPanel.vue')),
    order: 20,
    condition: isIndiaInvoiceCtx
  })

  registerSlot('app.banners', {
    id: 'india_gst.app.banners.unregistered',
    component: defineAsyncComponent(() => import('../components/india-gst/IndiaGstUnregisteredBanner.vue')),
    order: 20
  })

  registerSlot('invoice.list.row.meta', {
    id: 'india_gst.invoice.list.row.meta',
    component: defineAsyncComponent(() => import('../components/india-gst/IndiaGstBadge.vue')),
    order: 20,
    condition: isIndiaInvoiceCtx
  })

  registerSlot('invoice.detail.header.meta', {
    id: 'india_gst.invoice.detail.header.meta',
    component: defineAsyncComponent(() => import('../components/india-gst/IndiaGstBadge.vue')),
    order: 20,
    condition: isIndiaInvoiceCtx
  })

  registerSlot('invoice.list.toolbar.filters', {
    id: 'india_gst.invoice.list.toolbar.filters',
    component: defineAsyncComponent(() => import('../components/india-gst/IndiaGstListFilter.vue')),
    order: 20,
    condition: (raw) => {
      const ctx = (raw ?? {}) as { clinic?: { country?: string | null, settings?: { country?: string | null } | null } }
      const country = ctx.clinic?.country ?? ctx.clinic?.settings?.country ?? null
      return country === 'IN'
    }
  })
})
