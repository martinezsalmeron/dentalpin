import type {
  ApiResponse,
  PaginatedResponse,
  PatientLedger,
  PaymentRecord,
  PaymentRecordCreate,
  PaymentRefund,
  PaymentRefundCreate,
  PaymentReallocate,
  PaymentsSummary,
  PaymentsTrends,
  MethodBreakdown,
  ProfessionalBreakdown,
  AgingBuckets,
  RefundsReport,
  PaymentAllocation
} from '~~/app/types'

export interface PaymentListParams {
  page?: number
  page_size?: number
  date_from?: string
  date_to?: string
  method?: string
  patient_id?: string
}

export function usePayments() {
  const api = useApi()

  const payments = useState<PaymentRecord[]>('payments:list', () => [])
  const total = useState<number>('payments:total', () => 0)
  const isLoading = useState<boolean>('payments:loading', () => false)
  const error = useState<string | null>('payments:error', () => null)

  async function list(params: PaymentListParams = {}): Promise<PaymentRecord[]> {
    isLoading.value = true
    error.value = null
    try {
      const search = new URLSearchParams()
      Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined && v !== null && v !== '') search.set(k, String(v))
      })
      const qs = search.toString() ? `?${search.toString()}` : ''
      const resp = await api.get<PaginatedResponse<PaymentRecord>>(`/api/v1/payments${qs}`)
      payments.value = resp.data
      total.value = resp.total
      return resp.data
    } catch (e) {
      error.value = (e as Error).message
      return []
    } finally {
      isLoading.value = false
    }
  }

  async function get(id: string): Promise<PaymentRecord | null> {
    try {
      const resp = await api.get<ApiResponse<PaymentRecord>>(`/api/v1/payments/${id}`)
      return resp.data
    } catch (e) {
      error.value = (e as Error).message
      return null
    }
  }

  async function create(payload: PaymentRecordCreate): Promise<PaymentRecord | null> {
    try {
      const resp = await api.post<ApiResponse<PaymentRecord>>('/api/v1/payments', payload)
      return resp.data
    } catch (e) {
      error.value = (e as Error).message
      return null
    }
  }

  async function reallocate(id: string, payload: PaymentReallocate): Promise<PaymentRecord | null> {
    try {
      const resp = await api.post<ApiResponse<PaymentRecord>>(`/api/v1/payments/${id}/reallocate`, payload)
      return resp.data
    } catch (e) {
      error.value = (e as Error).message
      return null
    }
  }

  async function refund(id: string, payload: PaymentRefundCreate): Promise<PaymentRefund | null> {
    try {
      const resp = await api.post<ApiResponse<PaymentRefund>>(`/api/v1/payments/${id}/refunds`, payload)
      return resp.data
    } catch (e) {
      error.value = (e as Error).message
      return null
    }
  }

  async function listRefunds(id: string): Promise<PaymentRefund[]> {
    try {
      const resp = await api.get<ApiResponse<PaymentRefund[]>>(`/api/v1/payments/${id}/refunds`)
      return resp.data
    } catch {
      return []
    }
  }

  async function fetchPatientLedger(patientId: string): Promise<PatientLedger | null> {
    try {
      const resp = await api.get<ApiResponse<PatientLedger>>(`/api/v1/payments/patients/${patientId}/ledger`)
      return resp.data
    } catch {
      return null
    }
  }

  async function fetchBudgetAllocations(budgetId: string): Promise<PaymentAllocation[]> {
    try {
      const resp = await api.get<ApiResponse<PaymentAllocation[]>>(`/api/v1/payments/budgets/${budgetId}/allocations`)
      return resp.data
    } catch {
      return []
    }
  }

  return {
    payments,
    total,
    isLoading,
    error,
    list,
    get,
    create,
    reallocate,
    refund,
    listRefunds,
    fetchPatientLedger,
    fetchBudgetAllocations
  }
}

export function usePaymentReports() {
  const api = useApi()

  async function summary(date_from: string, date_to: string): Promise<PaymentsSummary | null> {
    try {
      const resp = await api.get<ApiResponse<PaymentsSummary>>(
        `/api/v1/payments/reports/summary?date_from=${date_from}&date_to=${date_to}`
      )
      return resp.data
    } catch {
      return null
    }
  }

  async function byMethod(date_from: string, date_to: string): Promise<MethodBreakdown[]> {
    try {
      const resp = await api.get<ApiResponse<MethodBreakdown[]>>(
        `/api/v1/payments/reports/by-method?date_from=${date_from}&date_to=${date_to}`
      )
      return resp.data
    } catch {
      return []
    }
  }

  async function byProfessional(date_from: string, date_to: string): Promise<ProfessionalBreakdown[]> {
    try {
      const resp = await api.get<ApiResponse<ProfessionalBreakdown[]>>(
        `/api/v1/payments/reports/by-professional?date_from=${date_from}&date_to=${date_to}`
      )
      return resp.data
    } catch {
      return []
    }
  }

  async function aging(): Promise<AgingBuckets | null> {
    try {
      const resp = await api.get<ApiResponse<AgingBuckets>>('/api/v1/payments/reports/aging-receivables')
      return resp.data
    } catch {
      return null
    }
  }

  async function refunds(date_from: string, date_to: string): Promise<RefundsReport | null> {
    try {
      const resp = await api.get<ApiResponse<RefundsReport>>(
        `/api/v1/payments/reports/refunds?date_from=${date_from}&date_to=${date_to}`
      )
      return resp.data
    } catch {
      return null
    }
  }

  async function trends(
    date_from: string,
    date_to: string,
    granularity: 'day' | 'week' | 'month' | 'year' = 'month'
  ): Promise<PaymentsTrends | null> {
    try {
      const resp = await api.get<ApiResponse<PaymentsTrends>>(
        `/api/v1/payments/reports/trends?date_from=${date_from}&date_to=${date_to}&granularity=${granularity}`
      )
      return resp.data
    } catch {
      return null
    }
  }

  return { summary, byMethod, byProfessional, aging, refunds, trends }
}
