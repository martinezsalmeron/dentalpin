<script setup lang="ts">
/**
 * One tooth rendered as a lateral silhouette plus three site markers
 * for the requested face.
 *
 * When `tooth.is_implant` is true, the natural root paths are
 * suppressed and the odontogram's `ImplantSVG` component is layered
 * into the root area instead — same visual language as the
 * odontogram so the dentist sees consistent iconography across
 * modules. Crown + gum line stay drawn so the clinical context
 * (carious crown, deep recession, etc.) survives the implant
 * placement.
 *
 * Reuses the odontogram's professional lateral SVG paths
 * (`getLateralPath`, `getToothTransform`). For palatal/lingual rows
 * we compose a vertical flip on top of the quadrant transform so the
 * same SVG can stand in for the other face of the tooth — the
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
        <!-- Z-order matches the odontogram: root or implant first
             (back layer), crown on top so its bottom edge overlaps
             the implant neck cleanly, gum line on top of everything. -->

        <!-- Natural root paths (back layer when no implant). -->
        <g
          v-if="!tooth.is_implant"
          fill="none"
          stroke="currentColor"
          stroke-width="1.5"
          stroke-linejoin="round"
          class="text-gray-400"
        >
          <path v-if="lateralPaths.root" :d="lateralPaths.root" />
          <template v-else-if="lateralPaths.roots">
            <path v-for="(d, idx) in lateralPaths.roots" :key="idx" :d="d" />
          </template>
        </g>

        <!-- Implant fixture replaces the natural root area. Drawn
             before the crown so the crown's bottom edge covers the
             implant neck — same visual seal the odontogram produces. -->
        <ImplantSVG
          v-if="tooth.is_implant && tooth.is_present"
          :view-box="lateralPaths.viewBox"
          :tooth-number="tooth.tooth_number"
          fill="#10b981"
          status="existing"
        />

        <!-- Crown on top of root/implant. Solid white fill so the
             crown's footprint occludes the implant neck — gives the
             same clean seal the odontogram produces between fixture
             and crown. -->
        <g
          fill="white"
          stroke="currentColor"
          stroke-width="1.5"
          stroke-linejoin="round"
          class="text-gray-400"
        >
          <path :d="lateralPaths.crown" />
        </g>

        <!-- Soft gum line in red — outermost layer. Skipped on
             implant teeth: the periodontal "gum line" concept on a
             natural root doesn't map to the peri-implant soft tissue
             interface, and drawing it would slash across the
             implant fixture / crown junction. Matches how the
             odontogram renders implants. -->
        <path
          v-if="!tooth.is_implant"
          :d="lateralPaths.gumLine"
          fill="none"
          stroke="#ef4444"
          stroke-width="1"
          opacity="0.6"
        />
      </svg>

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
