import type { OverdueInvoice } from '~~/app/types'

/**
 * Shared state for reports widgets on the home dashboard. Overdue
 * invoices are fetched once and reused by the hero tile and the
 * attention panel.
 */
export function useHomeReports() {
  const { fetchOverdueInvoices } = useReports()

  const overdue = useState<OverdueInvoice[]>('reports.home:overdue', () => [])
  const overdueLoaded = useState<boolean>('reports.home:overdue-loaded', () => false)

  async function loadOverdue(): Promise<OverdueInvoice[]> {
    overdue.value = await fetchOverdueInvoices()
    overdueLoaded.value = true
    return overdue.value
  }

  return {
    overdue: readonly(overdue),
    overdueLoaded: readonly(overdueLoaded),
    loadOverdue
  }
}
