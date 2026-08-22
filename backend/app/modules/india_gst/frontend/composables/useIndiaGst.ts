import type { ApiResponse } from '~~/app/types'

interface GstLineBreakdown {
  invoice_item_id: string | null
  sac_code: string | null
  tax_type: 'intra' | 'inter'
  cgst_rate: string
  cgst_amount: string
  sgst_rate: string
  sgst_amount: string
  igst_rate: string
  igst_amount: string
}

export interface GstBreakdown {
  is_intra: boolean
  lines: GstLineBreakdown[]
  cgst_total: string
  sgst_total: string
  igst_total: string
}

export interface IndiaGstSettings {
  id: string
  clinic_id: string
  trade_name: string | null
  gstin: string | null
  registration_type: 'regular' | 'composition' | 'unregistered' | 'exempt'
  clinic_state: string | null
  clinic_state_name: string | null
  turnover_threshold: string | null
  show_gstin_on_invoice: boolean
  show_sac_on_invoice: boolean
}

export interface IndiaGstEinvoice {
  invoice_id: string
  state: 'not_required' | 'not_configured' | 'pending' | 'generated' | 'rejected' | 'error'
  provider_error_message: string | null
}

export interface IndiaGstMissingSacItem {
  catalog_item_id: string
  /** `{ en: 'Zirconia crown', ta: '...' }` — resolved against the viewer's locale. */
  names: Record<string, string>
  name: string | null
  internal_code: string | null
}

export function useIndiaGst() {
  const api = useApi()

  async function getSettings() {
    const res = await api.get<ApiResponse<IndiaGstSettings>>('/api/v1/india_gst/settings')
    return res.data
  }

  async function updateSettings(payload: Partial<IndiaGstSettings>) {
    const res = await api.put<ApiResponse<IndiaGstSettings>>('/api/v1/india_gst/settings', payload)
    return res.data
  }

  async function getCatalogDefaults() {
    const res = await api.get<ApiResponse<{
      configured: Array<{ catalog_item_id: string, sac_code: string, notes: string | null }>
      missing: IndiaGstMissingSacItem[]
    }>>('/api/v1/india_gst/catalog-defaults')
    return res.data
  }

  async function autoconfigureCatalogDefaults() {
    const res = await api.post<ApiResponse<{ configured_count: number, sac_code: string }>>(
      '/api/v1/india_gst/catalog-defaults/autoconfigure',
      {}
    )
    return res.data
  }

  async function updateCatalogDefault(catalogItemId: string, sacCode: string, notes?: string) {
    const res = await api.put<ApiResponse<unknown>>(
      `/api/v1/india_gst/catalog-defaults/${catalogItemId}`,
      { sac_code: sacCode, notes: notes ?? null }
    )
    return res.data
  }

  async function taxPreview(
    items: Array<{ vat_rate: string | number, line_tax: string | number, sac_code?: string | null }>,
    placeOfSupply: string | null
  ) {
    const res = await api.post<ApiResponse<GstBreakdown>>('/api/v1/india_gst/tax-preview', {
      items,
      place_of_supply: placeOfSupply
    })
    return res.data
  }

  async function updateInvoiceGstFields(
    invoiceId: string,
    payload: { place_of_supply?: string | null, items?: Array<{ invoice_item_id: string, sac_code: string | null }> }
  ) {
    await api.put(`/api/v1/india_gst/invoices/${invoiceId}`, payload)
  }

  async function getEinvoiceStatus(invoiceId: string) {
    const res = await api.get<ApiResponse<IndiaGstEinvoice | null>>(
      `/api/v1/india_gst/invoices/${invoiceId}/einvoice`
    )
    return res.data
  }

  return {
    getSettings,
    updateSettings,
    getCatalogDefaults,
    autoconfigureCatalogDefaults,
    updateCatalogDefault,
    taxPreview,
    updateInvoiceGstFields,
    getEinvoiceStatus
  }
}
