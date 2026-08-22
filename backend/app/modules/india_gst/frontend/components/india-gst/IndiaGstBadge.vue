<script setup lang="ts">
// Compact GST badge — same component for the invoice list row and the
// invoice detail header, mirroring verifactu's ComplianceBadge.vue.
// Shows a "Needs attention" warning when an Indian clinic's non-draft
// invoice is missing GST compliance data.

interface InvoiceCtx {
  invoice?: {
    status?: string
    compliance_data?: { IN?: { severity?: string, einvoice_state?: string, gst_document_number?: string } } | null
  } | null
  clinic?: { country?: string | null, settings?: { country?: string | null } | null } | null
}

const props = defineProps<{ ctx: InvoiceCtx }>()
const { t } = useI18n()

const cd = computed(() => props.ctx?.invoice?.compliance_data?.IN ?? null)
const isIndianClinic = computed(() => {
  const country = props.ctx?.clinic?.country ?? props.ctx?.clinic?.settings?.country ?? null
  return country === 'IN'
})
const isNonDraft = computed(() => {
  const status = props.ctx?.invoice?.status
  return status && status !== 'draft'
})

const badge = computed(() => {
  const data = cd.value
  if (!data) {
    // Indian clinic, issued/paid/partial invoice with no GST data —
    // the hook never fired (issued before module install or country
    // wasn't set). Surface a "Needs attention" warning so the user
    // knows GST is missing.
    if (isIndianClinic.value && isNonDraft.value) {
      return {
        color: 'warning' as const,
        label: t('indiaGst.badge.needsAttention'),
        tooltip: t('indiaGst.badge.missingGst')
      }
    }
    return null
  }
  const severity = data.severity ?? 'ok'
  const colorMap: Record<string, 'success' | 'warning' | 'neutral' | 'error'> = {
    ok: 'success',
    warning: 'warning',
    pending: 'neutral',
    error: 'error'
  }
  const einvoiceState = data.einvoice_state
  let label = t('indiaGst.badge.gst')
  if (einvoiceState === 'generated') label = t('indiaGst.badge.irnGenerated')
  else if (einvoiceState === 'rejected' || einvoiceState === 'error') label = t('indiaGst.badge.einvoiceIssue')

  return {
    color: colorMap[severity] ?? 'neutral',
    label,
    tooltip: data.gst_document_number ?? t('indiaGst.badge.gst')
  }
})
</script>

<template>
  <UTooltip
    v-if="badge"
    :text="badge.tooltip"
  >
    <UBadge
      :color="badge.color"
      variant="subtle"
      size="xs"
      icon="i-lucide-receipt-indian-rupee"
      class="cursor-help"
    >
      {{ badge.label }}
    </UBadge>
  </UTooltip>
</template>
