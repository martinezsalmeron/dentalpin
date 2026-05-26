<script setup lang="ts">
/**
 * One arch (upper or lower) of the SEPA layout.
 *
 * For the upper arch the metrics table sits on top and two tooth rows
 * (vestibular ↓ / palatal ↑) follow below. For the lower arch the
 * order flips: lingual ↓ / vestibular ↑ first, then the metrics table.
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
      // First quadrant of each side goes 8→1; second 1→8.
      return q === 1 || q === 4 ? pb - pa : pa - pb
    })
    out.push(...quadrantTeeth)
  }
  return out
})

const heading = computed(() => (props.arch === 'upper' ? 'Superior' : 'Inferior'))

const facePrimary = computed<'vestibular' | 'lingual'>(() =>
  props.arch === 'upper' ? 'vestibular' : 'lingual'
)

const faceSecondary = computed<'palatal' | 'vestibular'>(() =>
  props.arch === 'upper' ? 'palatal' : 'vestibular'
)
</script>

<template>
  <section class="perio-arch-block space-y-2 rounded-lg border border-gray-200 bg-white p-3">
    <header class="flex items-center justify-between">
      <h4 class="text-xs font-semibold uppercase tracking-wide text-gray-500">{{ heading }}</h4>
      <span class="text-[10px] text-gray-400">
        {{ arch === 'upper' ? 'Vestibular / Palatino' : 'Lingual / Vestibular' }}
      </span>
    </header>

    <!-- Upper arch: metrics table first, then teeth -->
    <template v-if="arch === 'upper'">
      <PerioMetricsTable
        :teeth="orderedTeeth"
        face="vestibular"
        :readonly="readonly"
        @edit-tooth="(tn) => emit('editTooth', tn)"
        @edit-site="(tn, code) => emit('editSite', tn, code)"
      />
      <PerioToothRow
        :teeth="orderedTeeth"
        :face="facePrimary"
        :readonly="readonly"
        @site-click="(tn, code) => emit('editSite', tn, code)"
      />
      <PerioToothRow
        :teeth="orderedTeeth"
        :face="faceSecondary"
        :readonly="readonly"
        @site-click="(tn, code) => emit('editSite', tn, code)"
      />
    </template>

    <!-- Lower arch: teeth first, then metrics table -->
    <template v-else>
      <PerioToothRow
        :teeth="orderedTeeth"
        :face="facePrimary"
        :readonly="readonly"
        @site-click="(tn, code) => emit('editSite', tn, code)"
      />
      <PerioToothRow
        :teeth="orderedTeeth"
        :face="faceSecondary"
        :readonly="readonly"
        @site-click="(tn, code) => emit('editSite', tn, code)"
      />
      <PerioMetricsTable
        :teeth="orderedTeeth"
        face="vestibular"
        :readonly="readonly"
        @edit-tooth="(tn) => emit('editTooth', tn)"
        @edit-site="(tn, code) => emit('editSite', tn, code)"
      />
    </template>
  </section>
</template>
