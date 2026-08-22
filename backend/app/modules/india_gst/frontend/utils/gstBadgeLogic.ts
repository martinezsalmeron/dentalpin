// Pure logic extracted from IndiaGstBadge.vue and IndiaGstInvoicePanel.vue
// so it can be unit-tested without mounting Nuxt components.

export interface ComplianceSnapshot {
  severity?: string
  einvoice_state?: string | null
  gst_document_number?: string | null
}

export interface BadgeCtx {
  invoice?: {
    status?: string
    compliance_data?: { IN?: ComplianceSnapshot } | null
  } | null
  clinic?: {
    country?: string | null
    settings?: { country?: string | null } | null
  } | null
}

export type BadgeColor = 'success' | 'warning' | 'neutral' | 'error'

export interface BadgeResult {
  color: BadgeColor
  label: string
  tooltip: string
}

const COLOR_MAP: Record<string, BadgeColor> = {
  ok: 'success',
  warning: 'warning',
  pending: 'neutral',
  error: 'error'
}

export function isIndianClinic(ctx: BadgeCtx): boolean {
  const country = ctx.clinic?.country ?? ctx.clinic?.settings?.country ?? null
  return country === 'IN'
}

export function isNonDraft(ctx: BadgeCtx): boolean {
  const status = ctx.invoice?.status
  return !!status && status !== 'draft'
}

export function computeBadge(
  ctx: BadgeCtx,
  t: (key: string) => string
): BadgeResult | null {
  const data = ctx.invoice?.compliance_data?.IN ?? null

  if (!data) {
    if (isIndianClinic(ctx) && isNonDraft(ctx)) {
      return {
        color: 'warning',
        label: t('indiaGst.badge.needsAttention'),
        tooltip: t('indiaGst.badge.missingGst')
      }
    }
    return null
  }

  const severity = data.severity ?? 'ok'
  const einvoiceState = data.einvoice_state
  let label = t('indiaGst.badge.gst')
  if (einvoiceState === 'generated') label = t('indiaGst.badge.irnGenerated')
  else if (einvoiceState === 'rejected' || einvoiceState === 'error') label = t('indiaGst.badge.einvoiceIssue')

  return {
    color: COLOR_MAP[severity] ?? 'neutral',
    label,
    tooltip: data.gst_document_number ?? t('indiaGst.badge.gst')
  }
}

export function computeEinvoiceColor(state: string | null | undefined): BadgeColor {
  if (state === 'generated') return 'success'
  if (state === 'rejected' || state === 'error') return 'error'
  if (state === 'pending') return 'warning'
  return 'neutral'
}

export function computeEinvoiceLabel(
  state: string | null | undefined,
  t: (key: string) => string
): string {
  const map: Record<string, string> = {
    not_required: t('indiaGst.einvoice.notRequired'),
    not_configured: t('indiaGst.einvoice.notConfigured'),
    pending: t('indiaGst.einvoice.pending'),
    generated: t('indiaGst.einvoice.generated'),
    rejected: t('indiaGst.einvoice.rejected'),
    error: t('indiaGst.einvoice.error')
  }
  return state ? (map[state] ?? state) : t('indiaGst.einvoice.notRequired')
}
