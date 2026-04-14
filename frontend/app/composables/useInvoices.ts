import type {
  ApiResponse,
  BillingSettings,
  BillingSettingsUpdate,
  CreditNoteCreate,
  Invoice,
  InvoiceCreate,
  InvoiceDetail,
  InvoiceFromBudgetCreate,
  InvoiceHistoryEntry,
  InvoiceItem,
  InvoiceItemCreate,
  InvoiceItemUpdate,
  InvoiceIssueRequest,
  InvoiceListItem,
  InvoiceSeries,
  InvoiceSeriesCreate,
  InvoiceSeriesUpdate,
  InvoiceSendRequest,
  InvoiceStatus,
  InvoiceUpdate,
  PaginatedResponse,
  PatientBillingSummary,
  Payment,
  PaymentCreate,
  PaymentVoidRequest,
  SeriesResetRequest
} from '~/types'

export interface InvoiceListParams {
  page?: number
  page_size?: number
  patient_id?: string
  status?: InvoiceStatus[]
  date_from?: string
  date_to?: string
  due_from?: string
  due_to?: string
  overdue?: boolean
  search?: string
  budget_id?: string
  is_credit_note?: boolean
}

// Status colors for badges
const STATUS_COLORS: Record<InvoiceStatus, string> = {
  draft: 'gray',
  issued: 'blue',
  partial: 'amber',
  paid: 'green',
  cancelled: 'red',
  voided: 'neutral'
}

// Payment method labels
const PAYMENT_METHOD_LABELS: Record<string, string> = {
  cash: 'Efectivo',
  card: 'Tarjeta',
  bank_transfer: 'Transferencia',
  direct_debit: 'Domiciliación',
  other: 'Otro'
}

export function useInvoices() {
  const api = useApi()
  const config = useRuntimeConfig()
  const auth = useAuth()

  // State
  const invoices = useState<InvoiceListItem[]>('invoices:list', () => [])
  const currentInvoice = useState<InvoiceDetail | null>('invoices:current', () => null)
  const isLoading = useState<boolean>('invoices:loading', () => false)
  const error = useState<string | null>('invoices:error', () => null)
  const total = useState<number>('invoices:total', () => 0)

  // ============================================================================
  // Series Operations
  // ============================================================================

  async function fetchSeries(seriesType?: string, activeOnly: boolean = true): Promise<InvoiceSeries[]> {
    try {
      const params = new URLSearchParams()
      if (seriesType) params.set('series_type', seriesType)
      if (!activeOnly) params.set('active_only', 'false')

      const response = await api.get<ApiResponse<InvoiceSeries[]>>(
        `/api/v1/billing/series?${params.toString()}`
      )
      return response.data
    } catch (e) {
      console.error('Failed to fetch series:', e)
      return []
    }
  }

  async function createSeries(data: InvoiceSeriesCreate): Promise<InvoiceSeries> {
    const response = await api.post<ApiResponse<InvoiceSeries>>(
      '/api/v1/billing/series',
      data as unknown as Record<string, unknown>
    )
    return response.data
  }

  async function updateSeries(id: string, data: InvoiceSeriesUpdate): Promise<InvoiceSeries> {
    const response = await api.put<ApiResponse<InvoiceSeries>>(
      `/api/v1/billing/series/${id}`,
      data as unknown as Record<string, unknown>
    )
    return response.data
  }

  async function resetSeriesCounter(id: string, data: SeriesResetRequest): Promise<InvoiceSeries> {
    const response = await api.post<ApiResponse<InvoiceSeries>>(
      `/api/v1/billing/series/${id}/reset`,
      data as unknown as Record<string, unknown>
    )
    return response.data
  }

  // ============================================================================
  // CRUD Operations
  // ============================================================================

  async function fetchInvoices(params: InvoiceListParams = {}): Promise<InvoiceListItem[]> {
    isLoading.value = true
    error.value = null

    try {
      const searchParams = new URLSearchParams()

      if (params.page) searchParams.set('page', params.page.toString())
      if (params.page_size) searchParams.set('page_size', params.page_size.toString())
      if (params.patient_id) searchParams.set('patient_id', params.patient_id)
      if (params.status?.length) {
        params.status.forEach(s => searchParams.append('status', s))
      }
      if (params.date_from) searchParams.set('date_from', params.date_from)
      if (params.date_to) searchParams.set('date_to', params.date_to)
      if (params.due_from) searchParams.set('due_from', params.due_from)
      if (params.due_to) searchParams.set('due_to', params.due_to)
      if (params.overdue !== undefined) searchParams.set('overdue', params.overdue.toString())
      if (params.search) searchParams.set('search', params.search)
      if (params.budget_id) searchParams.set('budget_id', params.budget_id)
      if (params.is_credit_note !== undefined) searchParams.set('is_credit_note', params.is_credit_note.toString())

      const response = await api.get<PaginatedResponse<InvoiceListItem>>(
        `/api/v1/billing/invoices?${searchParams.toString()}`
      )

      invoices.value = response.data
      total.value = response.total
      return response.data
    } catch (e) {
      error.value = 'Failed to fetch invoices'
      console.error('Failed to fetch invoices:', e)
      return []
    } finally {
      isLoading.value = false
    }
  }

  async function fetchInvoice(id: string): Promise<InvoiceDetail | null> {
    isLoading.value = true
    error.value = null

    try {
      const response = await api.get<ApiResponse<InvoiceDetail>>(
        `/api/v1/billing/invoices/${id}`
      )
      currentInvoice.value = response.data
      return response.data
    } catch (e) {
      error.value = 'Failed to fetch invoice'
      console.error('Failed to fetch invoice:', e)
      return null
    } finally {
      isLoading.value = false
    }
  }

  async function createInvoice(data: InvoiceCreate): Promise<Invoice> {
    const response = await api.post<ApiResponse<Invoice>>(
      '/api/v1/billing/invoices',
      data as unknown as Record<string, unknown>
    )

    // Add to local list
    const listItem: InvoiceListItem = {
      id: response.data.id,
      invoice_number: response.data.invoice_number,
      status: response.data.status,
      issue_date: response.data.issue_date,
      due_date: response.data.due_date,
      total: response.data.total,
      total_paid: response.data.total_paid,
      balance_due: response.data.balance_due,
      currency: response.data.currency,
      created_at: response.data.created_at,
      patient: response.data.patient,
      creator: response.data.creator
    }
    invoices.value = [listItem, ...invoices.value]

    return response.data
  }

  async function createFromBudget(budgetId: string, data: InvoiceFromBudgetCreate): Promise<Invoice> {
    const response = await api.post<ApiResponse<Invoice>>(
      `/api/v1/billing/invoices/from-budget/${budgetId}`,
      data as unknown as Record<string, unknown>
    )

    // Add to local list
    const listItem: InvoiceListItem = {
      id: response.data.id,
      invoice_number: response.data.invoice_number,
      status: response.data.status,
      issue_date: response.data.issue_date,
      due_date: response.data.due_date,
      total: response.data.total,
      total_paid: response.data.total_paid,
      balance_due: response.data.balance_due,
      currency: response.data.currency,
      created_at: response.data.created_at,
      patient: response.data.patient,
      creator: response.data.creator
    }
    invoices.value = [listItem, ...invoices.value]

    return response.data
  }

  async function updateInvoice(id: string, data: InvoiceUpdate): Promise<Invoice> {
    const response = await api.put<ApiResponse<Invoice>>(
      `/api/v1/billing/invoices/${id}`,
      data as unknown as Record<string, unknown>
    )

    // Update local state
    invoices.value = invoices.value.map(i =>
      i.id === id
        ? {
            ...i,
            total: response.data.total,
            total_paid: response.data.total_paid,
            balance_due: response.data.balance_due
          }
        : i
    )
    if (currentInvoice.value?.id === id) {
      currentInvoice.value = { ...currentInvoice.value, ...response.data }
    }

    return response.data
  }

  async function deleteInvoice(id: string): Promise<void> {
    await api.del(`/api/v1/billing/invoices/${id}`)

    // Remove from local state
    invoices.value = invoices.value.filter(i => i.id !== id)
    if (currentInvoice.value?.id === id) {
      currentInvoice.value = null
    }
  }

  // ============================================================================
  // Item Operations
  // ============================================================================

  async function addItem(invoiceId: string, data: InvoiceItemCreate): Promise<InvoiceItem> {
    const response = await api.post<ApiResponse<InvoiceItem>>(
      `/api/v1/billing/invoices/${invoiceId}/items`,
      data as unknown as Record<string, unknown>
    )

    // Refetch current invoice to get updated totals
    if (currentInvoice.value?.id === invoiceId) {
      await fetchInvoice(invoiceId)
    }

    return response.data
  }

  async function updateItem(
    invoiceId: string,
    itemId: string,
    data: InvoiceItemUpdate
  ): Promise<InvoiceItem> {
    const response = await api.put<ApiResponse<InvoiceItem>>(
      `/api/v1/billing/invoices/${invoiceId}/items/${itemId}`,
      data as unknown as Record<string, unknown>
    )

    // Refetch current invoice to get updated totals
    if (currentInvoice.value?.id === invoiceId) {
      await fetchInvoice(invoiceId)
    }

    return response.data
  }

  async function removeItem(invoiceId: string, itemId: string): Promise<void> {
    await api.del(`/api/v1/billing/invoices/${invoiceId}/items/${itemId}`)

    // Refetch current invoice to get updated totals
    if (currentInvoice.value?.id === invoiceId) {
      await fetchInvoice(invoiceId)
    }
  }

  // ============================================================================
  // Workflow Operations
  // ============================================================================

  async function issueInvoice(id: string, data: InvoiceIssueRequest = {}): Promise<Invoice> {
    const response = await api.post<ApiResponse<Invoice>>(
      `/api/v1/billing/invoices/${id}/issue`,
      data as unknown as Record<string, unknown>
    )

    // Update local state
    updateInvoiceStatus(id, response.data.status)

    return response.data
  }

  async function voidInvoice(id: string, reason?: string): Promise<Invoice> {
    const params = reason ? `?reason=${encodeURIComponent(reason)}` : ''
    const response = await api.post<ApiResponse<Invoice>>(
      `/api/v1/billing/invoices/${id}/void${params}`,
      {}
    )

    // Update local state
    updateInvoiceStatus(id, response.data.status)

    return response.data
  }

  async function sendInvoice(id: string, data: InvoiceSendRequest): Promise<Invoice> {
    const response = await api.post<ApiResponse<Invoice>>(
      `/api/v1/billing/invoices/${id}/send-email`,
      data as unknown as Record<string, unknown>
    )

    return response.data
  }

  async function createCreditNote(id: string, data: CreditNoteCreate): Promise<Invoice> {
    const response = await api.post<ApiResponse<Invoice>>(
      `/api/v1/billing/invoices/${id}/credit-note`,
      data as unknown as Record<string, unknown>
    )

    // Add credit note to list
    const listItem: InvoiceListItem = {
      id: response.data.id,
      invoice_number: response.data.invoice_number,
      status: response.data.status,
      issue_date: response.data.issue_date,
      due_date: response.data.due_date,
      total: response.data.total,
      total_paid: response.data.total_paid,
      balance_due: response.data.balance_due,
      currency: response.data.currency,
      created_at: response.data.created_at,
      patient: response.data.patient,
      creator: response.data.creator
    }
    invoices.value = [listItem, ...invoices.value]

    // Update original invoice status
    updateInvoiceStatus(id, 'cancelled')

    return response.data
  }

  // ============================================================================
  // Payment Operations
  // ============================================================================

  async function fetchPayments(invoiceId: string, includeVoided: boolean = false): Promise<Payment[]> {
    try {
      const params = includeVoided ? '?include_voided=true' : ''
      const response = await api.get<ApiResponse<Payment[]>>(
        `/api/v1/billing/invoices/${invoiceId}/payments${params}`
      )
      return response.data
    } catch (e) {
      console.error('Failed to fetch payments:', e)
      return []
    }
  }

  async function recordPayment(invoiceId: string, data: PaymentCreate): Promise<Payment> {
    const response = await api.post<ApiResponse<Payment>>(
      `/api/v1/billing/invoices/${invoiceId}/payments`,
      data as unknown as Record<string, unknown>
    )

    // Refetch invoice to get updated totals
    if (currentInvoice.value?.id === invoiceId) {
      await fetchInvoice(invoiceId)
    }

    // Update list item
    const invoice = invoices.value.find(i => i.id === invoiceId)
    if (invoice) {
      invoice.total_paid = (invoice.total_paid || 0) + data.amount
      invoice.balance_due = invoice.total - invoice.total_paid
      if (invoice.balance_due <= 0) {
        invoice.status = 'paid'
      } else {
        invoice.status = 'partial'
      }
    }

    return response.data
  }

  async function voidPayment(paymentId: string, data: PaymentVoidRequest): Promise<Payment> {
    const response = await api.post<ApiResponse<Payment>>(
      `/api/v1/billing/payments/${paymentId}/void`,
      data as unknown as Record<string, unknown>
    )

    // Refetch current invoice if we have one
    if (currentInvoice.value) {
      await fetchInvoice(currentInvoice.value.id)
    }

    return response.data
  }

  // ============================================================================
  // History
  // ============================================================================

  async function fetchHistory(id: string): Promise<InvoiceHistoryEntry[]> {
    try {
      const response = await api.get<ApiResponse<InvoiceHistoryEntry[]>>(
        `/api/v1/billing/invoices/${id}/history`
      )
      return response.data
    } catch (e) {
      console.error('Failed to fetch invoice history:', e)
      return []
    }
  }

  // ============================================================================
  // Settings
  // ============================================================================

  async function fetchSettings(): Promise<BillingSettings | null> {
    try {
      const response = await api.get<ApiResponse<BillingSettings>>(
        '/api/v1/billing/settings'
      )
      return response.data
    } catch (e) {
      console.error('Failed to fetch billing settings:', e)
      return null
    }
  }

  async function updateSettings(data: BillingSettingsUpdate): Promise<BillingSettings> {
    const response = await api.put<ApiResponse<BillingSettings>>(
      '/api/v1/billing/settings',
      data as unknown as Record<string, unknown>
    )
    return response.data
  }

  // ============================================================================
  // Patient Summary (used by patient billing tab)
  // ============================================================================

  async function fetchPatientSummary(patientId: string): Promise<PatientBillingSummary | null> {
    try {
      const response = await api.get<ApiResponse<PatientBillingSummary>>(
        `/api/v1/billing/patients/${patientId}/summary`
      )
      return response.data
    } catch (e) {
      console.error('Failed to fetch patient billing summary:', e)
      return null
    }
  }

  // ============================================================================
  // PDF
  // ============================================================================

  async function downloadPDF(id: string, locale: string = 'es'): Promise<void> {
    const baseUrl = config.public.apiBaseUrl
    const token = auth.accessToken.value

    const response = await fetch(
      `${baseUrl}/api/v1/billing/invoices/${id}/pdf?locale=${locale}`,
      {
        headers: {
          Authorization: `Bearer ${token}`
        }
      }
    )

    if (!response.ok) {
      throw new Error('Failed to download PDF')
    }

    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url

    // Extract filename from Content-Disposition header or generate one
    const contentDisposition = response.headers.get('Content-Disposition')
    const filenameMatch = contentDisposition?.match(/filename="?(.+)"?/)
    link.download = filenameMatch?.[1] || `factura_${id}.pdf`

    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  }

  function getPDFPreviewUrl(id: string, locale: string = 'es'): string {
    const baseUrl = config.public.apiBaseUrl
    return `${baseUrl}/api/v1/billing/invoices/${id}/pdf/preview?locale=${locale}`
  }

  // ============================================================================
  // Helpers
  // ============================================================================

  function getStatusColor(status: InvoiceStatus): string {
    return STATUS_COLORS[status] || 'gray'
  }

  function getPaymentMethodLabel(method: string): string {
    return PAYMENT_METHOD_LABELS[method] || method
  }

  function canEdit(invoice: Invoice | InvoiceDetail | InvoiceListItem): boolean {
    return invoice.status === 'draft'
  }

  function canIssue(invoice: Invoice | InvoiceDetail | InvoiceListItem): boolean {
    return invoice.status === 'draft'
  }

  function canRecordPayment(invoice: Invoice | InvoiceDetail | InvoiceListItem): boolean {
    return ['issued', 'partial'].includes(invoice.status)
  }

  function canVoid(invoice: Invoice | InvoiceDetail | InvoiceListItem): boolean {
    return invoice.status === 'draft'
  }

  function canCreateCreditNote(invoice: Invoice | InvoiceDetail | InvoiceListItem): boolean {
    // Can't create credit note for a credit note (check if it's already a rectificativa)
    const isCreditNote = 'credit_note_for_id' in invoice && invoice.credit_note_for_id != null
    return ['issued', 'partial', 'paid'].includes(invoice.status) && !isCreditNote
  }

  function canSend(invoice: Invoice | InvoiceDetail | InvoiceListItem): boolean {
    // Can only send issued, partial, or paid invoices (not drafts or voided)
    return ['issued', 'partial', 'paid'].includes(invoice.status)
  }

  function formatCurrency(amount: number, currency: string = 'EUR'): string {
    return new Intl.NumberFormat('es-ES', {
      style: 'currency',
      currency
    }).format(amount)
  }

  // Internal helper to update status in local state
  function updateInvoiceStatus(id: string, status: InvoiceStatus): void {
    invoices.value = invoices.value.map(i =>
      i.id === id ? { ...i, status } : i
    )
    if (currentInvoice.value?.id === id) {
      currentInvoice.value = { ...currentInvoice.value, status }
    }
  }

  return {
    // State
    invoices: readonly(invoices),
    currentInvoice: readonly(currentInvoice),
    isLoading: readonly(isLoading),
    error: readonly(error),
    total: readonly(total),

    // Series
    fetchSeries,
    createSeries,
    updateSeries,
    resetSeriesCounter,

    // CRUD
    fetchInvoices,
    fetchInvoice,
    createInvoice,
    createFromBudget,
    updateInvoice,
    deleteInvoice,

    // Items
    addItem,
    updateItem,
    removeItem,

    // Workflow
    issueInvoice,
    voidInvoice,
    sendInvoice,
    createCreditNote,

    // Payments
    fetchPayments,
    recordPayment,
    voidPayment,

    // History
    fetchHistory,

    // Settings
    fetchSettings,
    updateSettings,

    // Patient Summary
    fetchPatientSummary,

    // PDF
    downloadPDF,
    getPDFPreviewUrl,

    // Helpers
    getStatusColor,
    getPaymentMethodLabel,
    canEdit,
    canIssue,
    canRecordPayment,
    canVoid,
    canCreateCreditNote,
    canSend,
    formatCurrency
  }
}
