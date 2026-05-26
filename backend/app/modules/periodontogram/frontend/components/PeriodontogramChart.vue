<script setup lang="ts">
/**
 * SEPA chart orchestrator.
 *
 * Wires the inline edits emitted by `PerioArchBlock` (per-tooth and
 * per-site patches) into the autosave queue, plus the sticky session
 * actions for close / discard. No modal popovers — every cell in the
 * chart edits in place.
 */
import { computed, onBeforeUnmount, onMounted, watch } from 'vue'
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

const toast = useToast()

const {
  saving,
  dirty,
  lastError,
  patchTooth,
  patchSite,
  flushPending,
  closeSession,
  discardDraft
} = usePeriodontogramSession()

watch(lastError, (err) => {
  if (err) {
    toast.add({
      title: 'No se pudo guardar el cambio',
      description: 'Comprueba tu conexión e intenta de nuevo.',
      color: 'error',
      icon: 'i-lucide-alert-triangle'
    })
  }
})

function _beforeUnload(event: BeforeUnloadEvent) {
  if (dirty.value || saving.value) {
    event.preventDefault()
    event.returnValue = ''
  }
}

onMounted(() => {
  if (typeof window !== 'undefined') {
    window.addEventListener('beforeunload', _beforeUnload)
  }
})

onBeforeUnmount(() => {
  if (typeof window !== 'undefined') {
    window.removeEventListener('beforeunload', _beforeUnload)
  }
})

const isReadOnly = computed(() => props.readonly || props.snapshot.status === 'closed')

const upperTeeth = computed(() =>
  props.snapshot.teeth.filter(t => Math.floor(t.tooth_number / 10) <= 2)
)
const lowerTeeth = computed(() =>
  props.snapshot.teeth.filter(t => Math.floor(t.tooth_number / 10) >= 3)
)

function handleEditSite(toothNumber: number, siteCode: SiteCode, patch: Record<string, unknown>) {
  if (isReadOnly.value) return
  patchSite(props.snapshot.id, toothNumber, siteCode, patch)
  setTimeout(() => emit('refresh'), 800)
}

function handleEditTooth(toothNumber: number, patch: Record<string, unknown>) {
  if (isReadOnly.value) return
  patchTooth(props.snapshot.id, toothNumber, patch)
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

    <div
      class="overflow-x-auto pb-2"
      role="region"
      aria-label="Periodontograma — arcadas superior e inferior"
    >
      <div class="min-w-[1100px] space-y-4">
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

    <PerioSessionActions
      v-if="snapshot.status === 'draft' && !readonly"
      :saving="saving"
      :dirty="dirty"
      @close="handleClose"
      @discard="handleDiscard"
    />
  </div>
</template>
