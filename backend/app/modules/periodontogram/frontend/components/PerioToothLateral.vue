<script setup lang="ts">
/**
 * One tooth rendered as a lateral silhouette with three site markers.
 *
 * Reuses the odontogram's professional lateral SVG paths
 * (`getLateralPath`, `getToothTransform`). Periodontogram only needs
 * the silhouette — no treatment overlays, no pulp — so we render the
 * crown + root outlines in a soft stroke and let the site markers
 * sit on top.
 *
 * The container is flipped vertically (`scaleY(-1)`) when the tooth
 * is shown on the palatal/lingual row so the same SVG works for
 * both faces of the same arch.
 */
import { computed } from 'vue'
import type { PerioSite, PerioTooth, SiteCode } from '../types'
import {
  getLateralPath,
  getToothTransform
} from '../../../odontogram/frontend/components/odontogram/ToothSVGPaths'

const props = defineProps<{
  tooth: PerioTooth
  /**
   * Which face we're rendering: vestibular (no flip) or palatal /
   * lingual (vertical flip so the same lateral SVG mirrors).
   */
  face: 'vestibular' | 'palatal' | 'lingual'
  /** Site codes that live on this face, in mesial→distal order. */
  siteCodes: readonly SiteCode[]
  readonly?: boolean
}>()

const emit = defineEmits<{
  siteClick: [siteCode: SiteCode]
}>()

const lateralPaths = computed(() => getLateralPath(props.tooth.tooth_number))
const baseTransform = computed(() => getToothTransform(props.tooth.tooth_number))

const faceTransform = computed(() => {
  // For palatal / lingual rows we mirror the lateral SVG vertically so
  // the crown still points at the metrics table. CSS transforms compose
  // multiplicatively: append the face flip after the quadrant transform.
  if (props.face !== 'vestibular') {
    return `${baseTransform.value} scaleY(-1)`.trim()
  }
  return baseTransform.value
})

const siteByCode = computed<Record<string, PerioSite | null>>(() => {
  const map: Record<string, PerioSite | null> = {}
  for (const code of props.siteCodes) map[code] = null
  for (const site of props.tooth.sites) {
    if (props.siteCodes.includes(site.site_code)) map[site.site_code] = site
  }
  return map
})

const visualOpacity = computed(() => (props.tooth.is_present ? 1 : 0.35))
</script>

<template>
  <div class="perio-tooth-lateral flex flex-col items-center gap-1">
    <div class="perio-tooth-lateral__svg-wrapper relative" :style="{ opacity: visualOpacity }">
      <svg
        :viewBox="lateralPaths.viewBox"
        class="h-20 w-12"
        :style="{ transform: faceTransform }"
        preserveAspectRatio="xMidYMid meet"
      >
        <g fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round" class="text-gray-400">
          <path :d="lateralPaths.crown" />
          <path v-if="lateralPaths.root" :d="lateralPaths.root" />
          <template v-else-if="lateralPaths.roots">
            <path v-for="(d, idx) in lateralPaths.roots" :key="idx" :d="d" />
          </template>
        </g>
        <!-- Soft gum line in red. -->
        <path
          :d="lateralPaths.gumLine"
          fill="none"
          stroke="#ef4444"
          stroke-width="1"
          opacity="0.6"
        />
      </svg>

      <UIcon
        v-if="tooth.is_implant"
        name="i-lucide-anchor"
        class="absolute right-0 top-0 text-emerald-600"
        title="Implante"
      />
      <span
        v-if="!tooth.is_present"
        class="absolute inset-0 flex items-center justify-center text-gray-400"
      >
        <span class="font-mono text-xs">—</span>
      </span>
    </div>

    <div class="flex items-center gap-1">
      <PerioSiteMarker
        v-for="code in siteCodes"
        :key="code"
        :site="siteByCode[code]"
        size="sm"
        :disabled="readonly || !tooth.is_present"
        @click="emit('siteClick', code)"
      />
    </div>

    <span class="font-mono text-[10px] text-gray-500">{{ tooth.tooth_number }}</span>
  </div>
</template>
