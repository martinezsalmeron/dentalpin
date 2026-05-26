<script setup lang="ts">
/**
 * One arch (upper or lower) of the SEPA layout.
 *
 * One tooth row per arch — the per-site markers under each tooth
 * expose both buccal (MV V DV) and palatal/lingual (ML L DL) halves,
 * so we no longer need to duplicate the tooth into two anatomical
 * rows. The metrics table mirrors the same six-site layout.
 *
 * Order: upper arch puts the table on top + teeth below; lower arch
 * inverts — teeth above + table at the bottom — so the two arches
 * meet at their occlusal plane in the middle of the page, matching
 * the SEPA convention.
 */
import { computed } from 'vue'
import type { PerioTooth, SiteCode } from '../types'

const props = defineProps<{
  arch: 'upper' | 'lower'
  teeth: PerioTooth[]
  readonly?: boolean
}>()

const emit = defineEmits<{
  editTooth: [toothNumber: number]
  editSite: [toothNumber: number, siteCode: SiteCode]
}>()

const orderedTeeth = computed(() => {
  // Upper arch order: 18→11, 21→28
  // Lower arch order: 48→41, 31→38 (mirror so the central incisors meet)
  const quadrants = props.arch === 'upper' ? [1, 2] : [4, 3]
  const out: PerioTooth[] = []
  for (const q of quadrants) {
    const quadrantTeeth = props.teeth.filter(t => Math.floor(t.tooth_number / 10) === q)
    quadrantTeeth.sort((a, b) => {
      const pa = a.tooth_number % 10
      const pb = b.tooth_number % 10
      return q === 1 || q === 4 ? pb - pa : pa - pb
    })
    out.push(...quadrantTeeth)
  }
  return out
})

const heading = computed(() => (props.arch === 'upper' ? 'Superior' : 'Inferior'))
</script>

<template>
  <section class="perio-arch-block space-y-2 rounded-lg border border-gray-200 bg-white p-3">
    <header class="flex items-center justify-between">
      <h4 class="text-xs font-semibold uppercase tracking-wide text-gray-500">{{ heading }}</h4>
      <span class="text-[10px] text-gray-400">
        MV V DV · ML L DL
      </span>
    </header>

    <template v-if="arch === 'upper'">
      <PerioMetricsTable
        :teeth="orderedTeeth"
        :readonly="readonly"
        @edit-tooth="(tn) => emit('editTooth', tn)"
        @edit-site="(tn, code) => emit('editSite', tn, code)"
      />
      <PerioToothRow
        :teeth="orderedTeeth"
        :readonly="readonly"
        @site-click="(tn, code) => emit('editSite', tn, code)"
      />
    </template>

    <template v-else>
      <PerioToothRow
        :teeth="orderedTeeth"
        :readonly="readonly"
        @site-click="(tn, code) => emit('editSite', tn, code)"
      />
      <PerioMetricsTable
        :teeth="orderedTeeth"
        :readonly="readonly"
        @edit-tooth="(tn) => emit('editTooth', tn)"
        @edit-site="(tn, code) => emit('editSite', tn, code)"
      />
    </template>
  </section>
</template>
