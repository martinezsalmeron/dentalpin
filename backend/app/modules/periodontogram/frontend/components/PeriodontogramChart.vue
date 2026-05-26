<script setup lang="ts">
/**
 * SEPA chart orchestrator.
 *
 * Renders the indices banner on top and the two arch blocks below.
 * Click handlers bubble up so the parent (PeriodontogramView) can
 * open the site / tooth editors. Saving is wired in PR-6 — for now
 * the popover's "Save" call hits the API directly and the parent
 * refreshes.
 */
import { computed, ref } from 'vue'
import type { PerioSnapshotDetail, PerioSnapshotSummary, SiteCode } from '../types'

const props = defineProps<{
  snapshot: PerioSnapshotDetail
  readonly?: boolean
}>()

const emit = defineEmits<{
  refresh: []
}>()

const api = useApi()

const upperTeeth = computed(() =>
  props.snapshot.teeth.filter(t => Math.floor(t.tooth_number / 10) <= 2)
)
const lowerTeeth = computed(() =>
  props.snapshot.teeth.filter(t => Math.floor(t.tooth_number / 10) >= 3)
)

const editingSite = ref<{ toothNumber: number, siteCode: SiteCode } | null>(null)
const editingTooth = ref<number | null>(null)
const popoverOpen = ref(false)

const editingSiteValue = computed(() => {
  if (!editingSite.value) return null
  const tooth = props.snapshot.teeth.find(t => t.tooth_number === editingSite.value!.toothNumber)
  return tooth?.sites.find(s => s.site_code === editingSite.value!.siteCode) ?? null
})

function handleEditSite(toothNumber: number, siteCode: SiteCode) {
  if (props.readonly || props.snapshot.status === 'closed') return
  editingSite.value = { toothNumber, siteCode }
  editingTooth.value = null
  popoverOpen.value = true
}

function handleEditTooth(toothNumber: number) {
  if (props.readonly || props.snapshot.status === 'closed') return
  editingTooth.value = toothNumber
  editingSite.value = null
  // Tooth-level editor will land in PR-6 — surface a stub for now so
  // the user knows the click was registered.
  // eslint-disable-next-line no-alert
  alert(`Editor de diente ${toothNumber} llegará en PR-6`)
}

async function handleSaveSite(patch: Record<string, unknown>) {
  if (!editingSite.value) return
  const { toothNumber, siteCode } = editingSite.value
  await api.patch(
    `/api/v1/periodontogram/snapshots/${props.snapshot.id}/teeth/${toothNumber}/sites/${siteCode}`,
    patch
  )
  emit('refresh')
}

const summary = computed<PerioSnapshotSummary>(() => ({
  id: props.snapshot.id,
  patient_id: props.snapshot.patient_id,
  status: props.snapshot.status,
  recorded_at: props.snapshot.recorded_at,
  closed_at: props.snapshot.closed_at
}))
</script>

<template>
  <div class="periodontogram-chart space-y-4">
    <PerioIndicesBanner :indices="snapshot.indices" :snapshot="summary" />

    <div class="space-y-4">
      <PerioArchBlock
        arch="upper"
        :teeth="upperTeeth"
        :readonly="readonly || snapshot.status === 'closed'"
        @edit-tooth="handleEditTooth"
        @edit-site="handleEditSite"
      />
      <PerioArchBlock
        arch="lower"
        :teeth="lowerTeeth"
        :readonly="readonly || snapshot.status === 'closed'"
        @edit-tooth="handleEditTooth"
        @edit-site="handleEditSite"
      />
    </div>

    <PerioSiteInputPopover
      v-if="editingSite"
      v-model="popoverOpen"
      :tooth-number="editingSite.toothNumber"
      :site-code="editingSite.siteCode"
      :site="editingSiteValue"
      @save="handleSaveSite"
    />
  </div>
</template>
