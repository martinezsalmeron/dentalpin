<script setup lang="ts">
/**
 * SEPA chart orchestrator.
 *
 * Banner + 2 arch blocks + per-site / per-tooth editors. Autosave
 * batches edits via `usePeriodontogramSession`; the sticky session
 * actions bar lets the dentist close or discard the draft. Read-only
 * for closed snapshots — popovers stay disabled in that state.
 */
import { computed, ref } from 'vue'
import type { PerioSnapshotDetail, PerioSnapshotSummary, SiteCode } from '../types'
import { usePeriodontogramSession } from '../composables/usePeriodontogramSession'

const props = defineProps<{
  snapshot: PerioSnapshotDetail
  readonly?: boolean
}>()

const emit = defineEmits<{
  refresh: []
  closed: [snapshot: PerioSnapshotDetail]
  discarded: []
}>()

const {
  saving,
  dirty,
  patchTooth,
  patchSite,
  flushPending,
  closeSession,
  discardDraft
} = usePeriodontogramSession()

const isReadOnly = computed(() => props.readonly || props.snapshot.status === 'closed')

const upperTeeth = computed(() =>
  props.snapshot.teeth.filter(t => Math.floor(t.tooth_number / 10) <= 2)
)
const lowerTeeth = computed(() =>
  props.snapshot.teeth.filter(t => Math.floor(t.tooth_number / 10) >= 3)
)

const editingSite = ref<{ toothNumber: number, siteCode: SiteCode } | null>(null)
const sitePopoverOpen = ref(false)
const editingToothNumber = ref<number | null>(null)
const toothModalOpen = ref(false)

const editingSiteValue = computed(() => {
  if (!editingSite.value) return null
  const tooth = props.snapshot.teeth.find(t => t.tooth_number === editingSite.value!.toothNumber)
  return tooth?.sites.find(s => s.site_code === editingSite.value!.siteCode) ?? null
})

const editingTooth = computed(() => {
  if (editingToothNumber.value == null) return null
  return props.snapshot.teeth.find(t => t.tooth_number === editingToothNumber.value) ?? null
})

function handleEditSite(toothNumber: number, siteCode: SiteCode) {
  if (isReadOnly.value) return
  editingSite.value = { toothNumber, siteCode }
  sitePopoverOpen.value = true
}

function handleEditTooth(toothNumber: number) {
  if (isReadOnly.value) return
  editingToothNumber.value = toothNumber
  toothModalOpen.value = true
}

async function handleSaveSite(patch: Record<string, unknown>) {
  if (!editingSite.value) return
  patchSite(
    props.snapshot.id,
    editingSite.value.toothNumber,
    editingSite.value.siteCode,
    patch
  )
  // Optimistic: refresh after the debounce window so totals update.
  setTimeout(() => emit('refresh'), 800)
}

async function handleSaveTooth(patch: Record<string, unknown>) {
  if (editingToothNumber.value == null) return
  patchTooth(props.snapshot.id, editingToothNumber.value, patch)
  setTimeout(() => emit('refresh'), 800)
}

async function handleClose(notes: string | null) {
  await flushPending(props.snapshot.id)
  const closed = await closeSession(props.snapshot.id, notes ?? undefined)
  emit('closed', closed)
}

async function handleDiscard() {
  await discardDraft(props.snapshot.id)
  emit('discarded')
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

    <!--
      Horizontal scroll wrapper: the SEPA chart needs ~960px of width to
      fit all 16 teeth + the 9 metrics rows comfortably. On tablets in
      portrait and on phones the wrapper scrolls instead of cramping
      the layout. A quadrant-by-quadrant swipe variant is queued for a
      later phase.
    -->
    <div class="overflow-x-auto pb-2">
      <div class="min-w-[960px] space-y-4">
        <PerioArchBlock
          arch="upper"
          :teeth="upperTeeth"
          :readonly="isReadOnly"
          @edit-tooth="handleEditTooth"
          @edit-site="handleEditSite"
        />
        <PerioArchBlock
          arch="lower"
          :teeth="lowerTeeth"
          :readonly="isReadOnly"
          @edit-tooth="handleEditTooth"
          @edit-site="handleEditSite"
        />
      </div>
    </div>

    <PerioSiteInputPopover
      v-if="editingSite"
      v-model="sitePopoverOpen"
      :tooth-number="editingSite.toothNumber"
      :site-code="editingSite.siteCode"
      :site="editingSiteValue"
      @save="handleSaveSite"
    />

    <PerioToothInputModal
      v-model="toothModalOpen"
      :tooth="editingTooth"
      @save="handleSaveTooth"
    />

    <PerioSessionActions
      v-if="snapshot.status === 'draft' && !readonly"
      :saving="saving"
      :dirty="dirty"
      @close="handleClose"
      @discard="handleDiscard"
    />
  </div>
</template>
