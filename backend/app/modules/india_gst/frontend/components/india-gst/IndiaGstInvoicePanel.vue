<script setup lang="ts">
// Mounted into billing's "invoice.detail.compliance" slot for India
// clinics. Renders the persisted issue-time snapshot
// (`invoice.compliance_data.IN`) — never live settings — so this
// always matches what was actually invoiced, even if clinic settings
// change afterward. All fields here are read-only: corrections happen
// via credit note, never by editing an issued invoice.

interface ComplianceSnapshot {
  place_of_supply?: string | null
  place_of_supply_name?: string | null
  tax_type?: 'intra' | 'inter' | null
  cgst_total?: string | null
  sgst_total?: string | null
  igst_total?: string | null
  gst_document_number?: string | null
  original_reference?: string | null
  einvoice_state?: string | null
  supplier?: { trade_name?: string | null, gstin?: string | null } | null
  recipient?: { gstin?: string | null } | null
}

interface InvoiceCtx {
  invoice?: {
    id?: string
    compliance_data?: { IN?: ComplianceSnapshot } | null
    credit_note_for_id?: string | null
  } | null
  clinic?: { country?: string | null, settings?: { country?: string | null } | null } | null
}

const props = defineProps<{ ctx: InvoiceCtx }>()
const { t } = useI18n()

const cd = computed<ComplianceSnapshot | null>(() => props.ctx?.invoice?.compliance_data?.IN ?? null)
const isCreditNote = computed(() => !!props.ctx?.invoice?.credit_note_for_id)

const einvoiceLabel = computed(() => {
  const state = cd.value?.einvoice_state
  const map: Record<string, string> = {
    not_required: t('indiaGst.einvoice.notRequired'),
    not_configured: t('indiaGst.einvoice.notConfigured'),
    pending: t('indiaGst.einvoice.pending'),
    generated: t('indiaGst.einvoice.generated'),
    rejected: t('indiaGst.einvoice.rejected'),
    error: t('indiaGst.einvoice.error')
  }
  return state ? (map[state] ?? state) : t('indiaGst.einvoice.notRequired')
})

const einvoiceColor = computed(() => {
  const state = cd.value?.einvoice_state
  if (state === 'generated') return 'success'
  if (state === 'rejected' || state === 'error') return 'error'
  if (state === 'pending') return 'warning'
  return 'neutral'
})
</script>

<template>
  <UCard
    v-if="cd"
    id="india-gst-panel"
  >
    <template #header>
      <h3 class="font-semibold text-default">
        {{ t('indiaGst.panel.title') }}
      </h3>
    </template>

    <div class="space-y-4">
      <div
        v-if="isCreditNote && cd.original_reference"
        class="text-caption text-subtle"
      >
        {{ t('indiaGst.panel.correctsDocument') }}: <span class="font-medium text-default">{{ cd.original_reference }}</span>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <p class="text-caption text-subtle">
            {{ t('indiaGst.panel.documentNumber') }}
          </p>
          <p class="font-medium text-default">
            {{ cd.gst_document_number || '-' }}
          </p>
        </div>
        <div>
          <p class="text-caption text-subtle">
            {{ t('indiaGst.panel.placeOfSupply') }}
          </p>
          <p class="font-medium text-default">
            {{ cd.place_of_supply_name || '-' }}
          </p>
        </div>
        <div>
          <p class="text-caption text-subtle">
            {{ t('indiaGst.panel.gstinOnInvoice') }}
          </p>
          <p class="font-medium text-default">
            {{ cd.recipient?.gstin || t('indiaGst.panel.notProvided') }}
          </p>
        </div>
        <div>
          <p class="text-caption text-subtle">
            {{ t('indiaGst.panel.calculation') }}
          </p>
          <p class="font-medium text-default">
            {{ cd.tax_type === 'intra' ? t('indiaGst.panel.intraState') : t('indiaGst.panel.interState') }}
          </p>
        </div>
      </div>

      <div class="rounded-lg border border-default p-3 space-y-1">
        <div class="flex justify-between text-sm">
          <span class="text-subtle">CGST</span>
          <span class="font-medium">{{ cd.cgst_total ?? '0.00' }}</span>
        </div>
        <div class="flex justify-between text-sm">
          <span class="text-subtle">SGST</span>
          <span class="font-medium">{{ cd.sgst_total ?? '0.00' }}</span>
        </div>
        <div class="flex justify-between text-sm">
          <span class="text-subtle">IGST</span>
          <span class="font-medium">{{ cd.igst_total ?? '0.00' }}</span>
        </div>
      </div>

      <div class="flex items-center justify-between rounded-lg border border-default p-3">
        <div>
          <p class="text-caption text-subtle">
            {{ t('indiaGst.panel.einvoiceStatus') }}
          </p>
          <p class="font-medium text-default">
            {{ einvoiceLabel }}
          </p>
        </div>
        <UBadge
          :color="einvoiceColor"
          variant="subtle"
        >
          {{ einvoiceLabel }}
        </UBadge>
      </div>
      <p
        v-if="cd.einvoice_state === 'not_required'"
        class="text-caption text-subtle"
      >
        {{ t('indiaGst.einvoice.notRequiredHint') }}
      </p>
      <p
        v-else-if="cd.einvoice_state === 'not_configured'"
        class="text-caption text-subtle"
      >
        {{ t('indiaGst.einvoice.notConfiguredHint') }}
        <NuxtLink
          to="/settings/india-gst"
          class="text-primary-500 hover:underline"
        >
          {{ t('indiaGst.einvoice.reviewSettings') }}
        </NuxtLink>
      </p>
    </div>
  </UCard>
</template>
