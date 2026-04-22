import type {
  ApiResponse,
  BillingSummary,
  OverdueInvoice,
  PaymentMethodSummary,
  ProfessionalBillingSummary,
  VatSummaryItem,
  NumberingGap
} from '~~/app/types'

// Budget report types
export interface BudgetSummary {
  period_start: string
  period_end: string
  total_created: number
  total_amount: string
  accepted_count: number
  accepted_amount: string
  rejected_count: number
  pending_count: number
  completed_count: number
  completed_amount: string
  acceptance_rate: number
  average_value: string
}

export interface BudgetByProfessional {
  professional_id: string | null
  professional_name: string
  budget_count: number
  total_amount: string
  accepted_count: number
  acceptance_rate: number
}

export interface BudgetByTreatment {
  catalog_item_id: string | null
  treatment_name: string
  occurrence_count: number
  total_quantity: number
  total_amount: string
}

export interface BudgetByStatus {
  status: string
  count: number
  total_amount: string
}

// Scheduling report types
export interface SchedulingSummary {
  period_start: string
  period_end: string
  total_appointments: number
  completed: number
  cancelled: number
  no_show: number
  scheduled: number
  confirmed: number
  checked_in: number
  in_treatment: number
  completion_rate: number
  cancellation_rate: number
  no_show_rate: number
}

// Appointment lifecycle analytics (issue #49)
export interface AnalyticsBucket {
  label: string
  count: number
}

export interface WaitingTimeStats {
  period_start: string
  period_end: string
  sample_size: number
  avg_minutes: number | null
  median_minutes: number | null
  p90_minutes: number | null
  distribution: AnalyticsBucket[]
}

export interface PunctualityStats {
  period_start: string
  period_end: string
  sample_size: number
  avg_delta_minutes: number | null
  median_delta_minutes: number | null
  on_time_pct: number | null
  distribution: AnalyticsBucket[]
}

export interface DurationVarianceStats {
  period_start: string
  period_end: string
  sample_size: number
  avg_overrun_pct: number | null
  avg_delta_minutes: number | null
  overrun_count: number
  under_count: number
}

export interface AppointmentFunnel {
  period_start: string
  period_end: string
  total: number
  counts_by_status: Record<string, number>
  completion_rate: number | null
  no_show_rate: number | null
  cancellation_rate: number | null
}

export interface FirstVisitsSummary {
  period_start: string
  period_end: string
  new_patients: number
  total_appointments: number
  first_visit_rate: number
}

export interface HoursByProfessional {
  professional_id: string | null
  professional_name: string
  appointment_count: number
  completed_count: number
  cancelled_count: number
  no_show_count: number
  total_minutes: number
  total_hours: number
}

export interface CabinetUtilization {
  cabinet: string
  appointment_count: number
  completed_count: number
  total_minutes: number
  total_hours: number
}

export interface DayOfWeekStats {
  day_of_week: number
  day_name: string
  appointment_count: number
  completed_count: number
  cancelled_count: number
  no_show_count: number
}

export function useReports() {
  const api = useApi()
  const { t } = useI18n()

  // ============================================================================
  // Billing Reports
  // ============================================================================

  async function fetchBillingSummary(
    dateFrom: string,
    dateTo: string
  ): Promise<BillingSummary | null> {
    try {
      const response = await api.get<ApiResponse<BillingSummary>>(
        `/api/v1/reports/billing/summary?date_from=${dateFrom}&date_to=${dateTo}`
      )
      return response.data
    } catch (e) {
      console.error('Failed to fetch billing summary:', e)
      return null
    }
  }

  async function fetchOverdueInvoices(): Promise<OverdueInvoice[]> {
    try {
      const response = await api.get<ApiResponse<OverdueInvoice[]>>(
        '/api/v1/reports/billing/overdue'
      )
      return response.data
    } catch (e) {
      console.error('Failed to fetch overdue invoices:', e)
      return []
    }
  }

  async function fetchByPaymentMethod(
    dateFrom: string,
    dateTo: string
  ): Promise<PaymentMethodSummary[]> {
    try {
      const response = await api.get<ApiResponse<PaymentMethodSummary[]>>(
        `/api/v1/reports/billing/by-payment-method?date_from=${dateFrom}&date_to=${dateTo}`
      )
      return response.data
    } catch (e) {
      console.error('Failed to fetch payments by method:', e)
      return []
    }
  }

  async function fetchBillingByProfessional(
    dateFrom: string,
    dateTo: string
  ): Promise<ProfessionalBillingSummary[]> {
    try {
      const response = await api.get<ApiResponse<ProfessionalBillingSummary[]>>(
        `/api/v1/reports/billing/by-professional?date_from=${dateFrom}&date_to=${dateTo}`
      )
      return response.data
    } catch (e) {
      console.error('Failed to fetch billing by professional:', e)
      return []
    }
  }

  async function fetchVatSummary(
    dateFrom: string,
    dateTo: string
  ): Promise<VatSummaryItem[]> {
    try {
      const response = await api.get<ApiResponse<VatSummaryItem[]>>(
        `/api/v1/reports/billing/vat-summary?date_from=${dateFrom}&date_to=${dateTo}`
      )
      return response.data
    } catch (e) {
      console.error('Failed to fetch VAT summary:', e)
      return []
    }
  }

  async function fetchNumberingGaps(): Promise<NumberingGap[]> {
    try {
      const response = await api.get<ApiResponse<NumberingGap[]>>(
        '/api/v1/reports/billing/gaps'
      )
      return response.data
    } catch (e) {
      console.error('Failed to fetch numbering gaps:', e)
      return []
    }
  }

  // ============================================================================
  // Budget Reports
  // ============================================================================

  async function fetchBudgetSummary(
    dateFrom: string,
    dateTo: string
  ): Promise<BudgetSummary | null> {
    try {
      const response = await api.get<ApiResponse<BudgetSummary>>(
        `/api/v1/reports/budgets/summary?date_from=${dateFrom}&date_to=${dateTo}`
      )
      return response.data
    } catch (e) {
      console.error('Failed to fetch budget summary:', e)
      return null
    }
  }

  async function fetchBudgetsByProfessional(
    dateFrom: string,
    dateTo: string
  ): Promise<BudgetByProfessional[]> {
    try {
      const response = await api.get<ApiResponse<BudgetByProfessional[]>>(
        `/api/v1/reports/budgets/by-professional?date_from=${dateFrom}&date_to=${dateTo}`
      )
      return response.data
    } catch (e) {
      console.error('Failed to fetch budgets by professional:', e)
      return []
    }
  }

  async function fetchBudgetsByTreatment(
    dateFrom: string,
    dateTo: string,
    limit: number = 10
  ): Promise<BudgetByTreatment[]> {
    try {
      const response = await api.get<ApiResponse<BudgetByTreatment[]>>(
        `/api/v1/reports/budgets/by-treatment?date_from=${dateFrom}&date_to=${dateTo}&limit=${limit}`
      )
      return response.data
    } catch (e) {
      console.error('Failed to fetch budgets by treatment:', e)
      return []
    }
  }

  async function fetchBudgetsByStatus(
    dateFrom: string,
    dateTo: string
  ): Promise<BudgetByStatus[]> {
    try {
      const response = await api.get<ApiResponse<BudgetByStatus[]>>(
        `/api/v1/reports/budgets/by-status?date_from=${dateFrom}&date_to=${dateTo}`
      )
      return response.data
    } catch (e) {
      console.error('Failed to fetch budgets by status:', e)
      return []
    }
  }

  // ============================================================================
  // Scheduling Reports
  // ============================================================================

  async function fetchSchedulingSummary(
    dateFrom: string,
    dateTo: string
  ): Promise<SchedulingSummary | null> {
    try {
      const response = await api.get<ApiResponse<SchedulingSummary>>(
        `/api/v1/reports/scheduling/summary?date_from=${dateFrom}&date_to=${dateTo}`
      )
      return response.data
    } catch (e) {
      console.error('Failed to fetch scheduling summary:', e)
      return null
    }
  }

  async function fetchFirstVisits(
    dateFrom: string,
    dateTo: string
  ): Promise<FirstVisitsSummary | null> {
    try {
      const response = await api.get<ApiResponse<FirstVisitsSummary>>(
        `/api/v1/reports/scheduling/first-visits?date_from=${dateFrom}&date_to=${dateTo}`
      )
      return response.data
    } catch (e) {
      console.error('Failed to fetch first visits:', e)
      return null
    }
  }

  async function fetchHoursByProfessional(
    dateFrom: string,
    dateTo: string
  ): Promise<HoursByProfessional[]> {
    try {
      const response = await api.get<ApiResponse<HoursByProfessional[]>>(
        `/api/v1/reports/scheduling/by-professional?date_from=${dateFrom}&date_to=${dateTo}`
      )
      return response.data
    } catch (e) {
      console.error('Failed to fetch hours by professional:', e)
      return []
    }
  }

  async function fetchCabinetUtilization(
    dateFrom: string,
    dateTo: string
  ): Promise<CabinetUtilization[]> {
    try {
      const response = await api.get<ApiResponse<CabinetUtilization[]>>(
        `/api/v1/reports/scheduling/by-cabinet?date_from=${dateFrom}&date_to=${dateTo}`
      )
      return response.data
    } catch (e) {
      console.error('Failed to fetch cabinet utilization:', e)
      return []
    }
  }

  async function fetchByDayOfWeek(
    dateFrom: string,
    dateTo: string
  ): Promise<DayOfWeekStats[]> {
    try {
      const response = await api.get<ApiResponse<DayOfWeekStats[]>>(
        `/api/v1/reports/scheduling/by-day-of-week?date_from=${dateFrom}&date_to=${dateTo}`
      )
      return response.data
    } catch (e) {
      console.error('Failed to fetch by day of week:', e)
      return []
    }
  }

  function _buildAnalyticsQuery(
    dateFrom: string,
    dateTo: string,
    filters?: { cabinetId?: string | null, professionalId?: string | null }
  ): string {
    const params = new URLSearchParams({ date_from: dateFrom, date_to: dateTo })
    if (filters?.cabinetId) params.set('cabinet_id', filters.cabinetId)
    if (filters?.professionalId) params.set('professional_id', filters.professionalId)
    return params.toString()
  }

  async function fetchWaitingTimes(
    dateFrom: string,
    dateTo: string,
    filters?: { cabinetId?: string | null, professionalId?: string | null }
  ): Promise<WaitingTimeStats | null> {
    try {
      const response = await api.get<ApiResponse<WaitingTimeStats>>(
        `/api/v1/reports/scheduling/waiting-times?${_buildAnalyticsQuery(dateFrom, dateTo, filters)}`
      )
      return response.data
    } catch (e) {
      console.error('Failed to fetch waiting times:', e)
      return null
    }
  }

  async function fetchPunctuality(
    dateFrom: string,
    dateTo: string,
    filters?: { cabinetId?: string | null, professionalId?: string | null }
  ): Promise<PunctualityStats | null> {
    try {
      const response = await api.get<ApiResponse<PunctualityStats>>(
        `/api/v1/reports/scheduling/punctuality?${_buildAnalyticsQuery(dateFrom, dateTo, filters)}`
      )
      return response.data
    } catch (e) {
      console.error('Failed to fetch punctuality:', e)
      return null
    }
  }

  async function fetchDurationVariance(
    dateFrom: string,
    dateTo: string,
    filters?: { cabinetId?: string | null, professionalId?: string | null }
  ): Promise<DurationVarianceStats | null> {
    try {
      const response = await api.get<ApiResponse<DurationVarianceStats>>(
        `/api/v1/reports/scheduling/duration-variance?${_buildAnalyticsQuery(dateFrom, dateTo, filters)}`
      )
      return response.data
    } catch (e) {
      console.error('Failed to fetch duration variance:', e)
      return null
    }
  }

  async function fetchFunnel(
    dateFrom: string,
    dateTo: string,
    filters?: { cabinetId?: string | null, professionalId?: string | null }
  ): Promise<AppointmentFunnel | null> {
    try {
      const response = await api.get<ApiResponse<AppointmentFunnel>>(
        `/api/v1/reports/scheduling/funnel?${_buildAnalyticsQuery(dateFrom, dateTo, filters)}`
      )
      return response.data
    } catch (e) {
      console.error('Failed to fetch funnel:', e)
      return null
    }
  }

  // ============================================================================
  // Helpers
  // ============================================================================

  function formatCurrency(value: string | number): string {
    const num = typeof value === 'string' ? parseFloat(value) : value
    return new Intl.NumberFormat('es-ES', {
      style: 'currency',
      currency: 'EUR'
    }).format(num)
  }

  function getBudgetStatusLabel(status: string): string {
    const labels: Record<string, string> = {
      draft: t('budget.status.draft'),
      accepted: t('budget.status.accepted'),
      rejected: t('budget.status.rejected'),
      completed: t('budget.status.completed'),
      expired: t('budget.status.expired'),
      cancelled: t('budget.status.cancelled')
    }
    return labels[status] || status
  }

  function getBudgetStatusColor(status: string): string {
    const colors: Record<string, string> = {
      draft: 'neutral',
      accepted: 'success',
      rejected: 'error',
      completed: 'info',
      expired: 'warning',
      cancelled: 'neutral'
    }
    return colors[status] || 'neutral'
  }

  function getDayOfWeekLabel(dayName: string): string {
    const labels: Record<string, string> = {
      sunday: t('common.days.sunday'),
      monday: t('common.days.monday'),
      tuesday: t('common.days.tuesday'),
      wednesday: t('common.days.wednesday'),
      thursday: t('common.days.thursday'),
      friday: t('common.days.friday'),
      saturday: t('common.days.saturday')
    }
    return labels[dayName] || dayName
  }

  function formatHours(minutes: number): string {
    const hours = Math.floor(minutes / 60)
    const mins = minutes % 60
    if (hours === 0) return `${mins}m`
    if (mins === 0) return `${hours}h`
    return `${hours}h ${mins}m`
  }

  function getPaymentMethodLabel(method: string): string {
    const labels: Record<string, string> = {
      cash: t('invoice.paymentMethods.cash'),
      card: t('invoice.paymentMethods.card'),
      bank_transfer: t('invoice.paymentMethods.bank_transfer'),
      direct_debit: t('invoice.paymentMethods.direct_debit'),
      other: t('invoice.paymentMethods.other')
    }
    return labels[method] || method
  }

  return {
    // Billing
    fetchBillingSummary,
    fetchOverdueInvoices,
    fetchByPaymentMethod,
    fetchBillingByProfessional,
    fetchVatSummary,
    fetchNumberingGaps,
    // Budget
    fetchBudgetSummary,
    fetchBudgetsByProfessional,
    fetchBudgetsByTreatment,
    fetchBudgetsByStatus,
    // Scheduling
    fetchSchedulingSummary,
    fetchFirstVisits,
    fetchHoursByProfessional,
    fetchCabinetUtilization,
    fetchByDayOfWeek,
    fetchWaitingTimes,
    fetchPunctuality,
    fetchDurationVariance,
    fetchFunnel,
    // Helpers
    formatCurrency,
    getBudgetStatusLabel,
    getBudgetStatusColor,
    getDayOfWeekLabel,
    formatHours,
    getPaymentMethodLabel
  }
}
