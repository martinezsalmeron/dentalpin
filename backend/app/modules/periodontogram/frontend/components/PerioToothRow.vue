<script setup lang="ts">
/**
 * One anatomical row of teeth for a single arch face.
 *
 * `face='vestibular'` paints the buccal half of the arch, `palatal`
 * the palatal half, and `lingual` the lingual half of the lower arch.
 * Teeth come in FDI order — already sorted by the caller.
 */
import type { PerioTooth, SiteCode } from '../types'
import { PALATAL_SITES, VESTIBULAR_SITES } from '../types'

defineProps<{
  teeth: PerioTooth[]
  face: 'vestibular' | 'palatal' | 'lingual'
  readonly?: boolean
}>()

const emit = defineEmits<{
  siteClick: [toothNumber: number, siteCode: SiteCode]
}>()

function sitesForFace(face: 'vestibular' | 'palatal' | 'lingual'): readonly SiteCode[] {
  return face === 'vestibular' ? VESTIBULAR_SITES : PALATAL_SITES
}
</script>

<template>
  <div class="perio-tooth-row flex items-end justify-center gap-2">
    <PerioToothLateral
      v-for="tooth in teeth"
      :key="tooth.tooth_number"
      :tooth="tooth"
      :face="face"
      :site-codes="sitesForFace(face)"
      :readonly="readonly"
      @site-click="(code) => emit('siteClick', tooth.tooth_number, code)"
    />
  </div>
</template>
