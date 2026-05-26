<script setup lang="ts">
/**
 * One tooth rendered as a lateral silhouette plus three site markers
 * for the requested face.
 *
 * Reuses the odontogram's professional lateral SVG paths
 * (`getLateralPath`, `getToothTransform`). For palatal/lingual rows
 * we compose a vertical flip on top of the quadrant transform so
 * the same SVG can stand in for the other face of the tooth — the
 * established SEPA convention for showing both faces of an arch
 * stacked vertically.
 */
import { computed } from 'vue'
import type { PerioSite, PerioTooth, SiteCode } from '../types'
import { PALATAL_SITES, VESTIBULAR_SITES } from '../types'
import {
  getLateralPath,
  getToothTransform
} from '../../../odontogram/frontend/components/odontogram/ToothSVGPaths'

const props = defineProps<{
  tooth: PerioTooth
  /** Anatomical face this row represents. */
  face: 'vestibular' | 'palatal' | 'lingual'
  readonly?: boolean
}>()

// Markers are display-only — editing happens via the inline table
// cells in PerioArchBlock. Keeping the markers as decorative dots
// avoids two competing edit affordances on the same data.

const lateralPaths = computed(() => getLateralPath(props.tooth.tooth_number))
const baseTransform = computed(() => getToothTransform(props.tooth.tooth_number))

const faceTransform = computed(() => {
  if (props.face !== 'vestibular') {
    return `${baseTransform.value} scaleY(-1)`.trim()
  }
  return baseTransform.value
})

const visibleSites = computed<readonly SiteCode[]>(() =>
  props.face === 'vestibular' ? VESTIBULAR_SITES : PALATAL_SITES
)

const siteByCode = computed<Record<string, PerioSite | null>>(() => {
  const map: Record<string, PerioSite | null> = {}
  for (const code of visibleSites.value) map[code] = null
  for (const site of props.tooth.sites) {
    if (visibleSites.value.includes(site.site_code)) map[site.site_code] = site
  }
  return map
})

const visualOpacity = computed(() => (props.tooth.is_present ? 1 : 0.35))
</script>

<template>
  <div class="perio-tooth-lateral flex flex-col items-center gap-0.5">
    <div class="perio-tooth-lateral__svg-wrapper relative" :style="{ opacity: visualOpacity }">
      <svg
        :viewBox="lateralPaths.viewBox"
        class="h-16 w-10"
        :style="{ transform: faceTransform }"
        preserveAspectRatio="xMidYMid meet"
      >
        <g
          fill="none"
          stroke="currentColor"
          stroke-width="1.5"
          stroke-linejoin="round"
          class="text-gray-400"
        >
          <path :d="lateralPaths.crown" />
          <path v-if="lateralPaths.root" :d="lateralPaths.root" />
          <template v-else-if="lateralPaths.roots">
            <path v-for="(d, idx) in lateralPaths.roots" :key="idx" :d="d" />
          </template>
        </g>
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

    <!-- Three site markers for THIS face only — decorative heatmap
         under the tooth so the dentist can spot deep pockets at a
         glance. Editing happens in the metric table rows. -->
    <div class="flex items-center gap-0.5">
      <PerioSiteMarker
        v-for="code in visibleSites"
        :key="code"
        :site="siteByCode[code]"
        size="sm"
        readonly
      />
    </div>
  </div>
</template>
