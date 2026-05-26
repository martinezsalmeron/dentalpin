<script setup lang="ts">
/**
 * One anatomical row of teeth for an arch.
 *
 * Replaces the former vestibular / palatal duplicated rows — each
 * tooth now exposes all six sites itself (see PerioToothLateral),
 * so the arch only needs one row.
 */
import type { PerioTooth, SiteCode } from '../types'

defineProps<{
  teeth: PerioTooth[]
  readonly?: boolean
}>()

const emit = defineEmits<{
  siteClick: [toothNumber: number, siteCode: SiteCode]
}>()
</script>

<template>
  <div class="perio-tooth-row flex items-end justify-center gap-2">
    <PerioToothLateral
      v-for="tooth in teeth"
      :key="tooth.tooth_number"
      :tooth="tooth"
      :readonly="readonly"
      @site-click="(code) => emit('siteClick', tooth.tooth_number, code)"
    />
  </div>
</template>
