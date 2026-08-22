<script setup lang="ts">
// Mounted into billing's "invoice.form.compliance" slot on the draft
// edit page. Self-contained: saves independently via its own action
// (the generic <ModuleSlot> contract has no channel back into the
// host form's submit handler), calling
// PUT /api/v1/india_gst/invoices/{id} directly. Only rendered for
// draft invoices — issued invoices show the read-only
// IndiaGstInvoicePanel instead.

interface InvoiceItemLite {
  id: string
  vat_rate: number
  line_tax: string | number
  catalog_item_id?: string | null
  description?: string
}

interface FormCtx {
  invoice?: {
    id?: string
    compliance_data?: { IN?: { place_of_supply?: string | null } } | null
    items?: InvoiceItemLite[]
    status?: string
  } | null
  clinic?: { country?: string | null, settings?: { country?: string | null } | null } | null
}

const props = defineProps<{ ctx: FormCtx }>()
const { t } = useI18n()
const toast = useToast()
const { options: stateOptions } = useIndiaGstStates()
const { getSettings, updateInvoiceGstFields, taxPreview } = useIndiaGst()

const placeOfSupply = ref<string | undefined>(props.ctx.invoice?.compliance_data?.IN?.place_of_supply ?? undefined)
const sacByItem = ref<Record<string, string>>({})
const isSaving = ref(false)
const clinicGstin = ref<string | null>(null)
const clinicTradeName = ref<string | null>(null)
const preview = ref<{ is_intra: boolean, cgst_total: string, sgst_total: string, igst_total: string } | null>(null)

onMounted(async () => {
  try {
    const settings = await getSettings()
    clinicGstin.value = settings.gstin
    clinicTradeName.value = settings.trade_name
  } catch {
    // Module not active for this clinic — panel still renders (place
    // of supply may still be relevant), just without the summary card.
  }
  await refreshPreview()
})

async function refreshPreview() {
  const items = props.ctx.invoice?.items ?? []
  if (!items.length) {
    preview.value = null
    return
  }
  try {
    preview.value = await taxPreview(
      items.map(i => ({ vat_rate: i.vat_rate, line_tax: i.line_tax })),
      placeOfSupply.value ?? null
    )
  } catch {
    preview.value = null
  }
}

watch(placeOfSupply, refreshPreview)

async function save() {
  const invoiceId = props.ctx.invoice?.id
  if (!invoiceId) return
  isSaving.value = true
  try {
    await updateInvoiceGstFields(invoiceId, {
      place_of_supply: placeOfSupply.value ?? null,
      items: Object.entries(sacByItem.value).map(([invoice_item_id, sac_code]) => ({ invoice_item_id, sac_code }))
    })
    toast.add({ title: t('common.success'), description: t('indiaGst.form.saved'), color: 'success' })
  } catch {
    toast.add({ title: t('common.error'), description: t('indiaGst.form.saveError'), color: 'error' })
  } finally {
    isSaving.value = false
  }
}
</script>

<template>
  <UCard v-if="ctx.invoice?.status === 'draft'">
    <template #header>
      <h3 class="font-semibold text-default">
        {{ t('indiaGst.form.title') }}
      </h3>
    </template>

    <div class="space-y-4">
      <div
        v-if="clinicGstin || clinicTradeName"
        class="rounded-lg bg-surface-muted p-3 text-sm"
      >
        <p class="text-subtle">
          {{ t('indiaGst.form.clinicGstDetails') }}
        </p>
        <p class="font-medium text-default">
          {{ clinicTradeName || '-' }} · {{ clinicGstin || t('indiaGst.panel.notProvided') }}
        </p>
      </div>

      <UFormField
        :label="t('indiaGst.form.placeOfSupply')"
        :hint="t('indiaGst.form.placeOfSupplyHint')"
        required
      >
        <USelectMenu
          v-model="placeOfSupply"
          :items="stateOptions"
          value-key="value"
          :placeholder="t('indiaGst.form.selectState')"
        />
      </UFormField>

      <div
        v-if="preview"
        class="rounded-lg border border-default p-3 space-y-1 text-sm"
      >
        <p class="font-medium text-default">
          {{ preview.is_intra ? t('indiaGst.panel.intraState') : t('indiaGst.panel.interState') }}
        </p>
        <div class="flex justify-between">
          <span class="text-subtle">CGST</span><span>{{ preview.cgst_total }}</span>
        </div>
        <div class="flex justify-between">
          <span class="text-subtle">SGST</span><span>{{ preview.sgst_total }}</span>
        </div>
        <div class="flex justify-between">
          <span class="text-subtle">IGST</span><span>{{ preview.igst_total }}</span>
        </div>
      </div>
      <p
        v-else
        class="text-caption text-subtle"
      >
        {{ t('indiaGst.form.selectPlaceOfSupplyHint') }}
      </p>

      <div
        v-if="ctx.invoice?.items?.length"
        class="space-y-2"
      >
        <p class="text-caption text-subtle">
          {{ t('indiaGst.form.sacCodes') }}
        </p>
        <div
          v-for="item in ctx.invoice.items"
          :key="item.id"
          class="flex items-center gap-2"
        >
          <span class="flex-1 text-sm text-subtle truncate">{{ item.description }}</span>
          <UInput
            v-model="sacByItem[item.id]"
            size="xs"
            class="w-28"
            :placeholder="t('indiaGst.form.sacCode')"
          />
        </div>
        <p class="text-caption text-subtle italic">
          {{ t('indiaGst.form.sacOverrideHint') }}
        </p>
      </div>

      <UButton
        block
        variant="soft"
        :loading="isSaving"
        @click="save"
      >
        {{ t('indiaGst.form.save') }}
      </UButton>
    </div>
  </UCard>
</template>
