<script setup lang="ts">
/**
 * One tooth rendered as a lateral silhouette with all six probing
 * sites shown below the SVG.
 *
 * Reuses the odontogram's professional lateral SVG paths
 * (`getLateralPath`, `getToothTransform`) so the tooth orientation
 * matches the anatomy of the arch (roots up for upper, roots down
 * for lower). The six site markers are split into a vestibular
 * triplet (MV V DV) and a palatal/lingual triplet (ML L DL) with a
 * faint divider — keeps the two faces readable in one row instead
 * of duplicating the tooth twice per arch.
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
  readonly?: boolean
}>()

const emit = defineEmits<{
  siteClick: [siteCode: SiteCode]
}>()

const lateralPaths = computed(() => getLateralPath(props.tooth.tooth_number))
const baseTransform = computed(() => getToothTransform(props.tooth.tooth_number))

const siteByCode = computed<Record<string, PerioSite | null>>(() => {
  const map: Record<string, PerioSite | null> = {
    MV: null, V: null, DV: null, ML: null, L: null, DL: null
  }
  for (const site of props.tooth.sites) {
    map[site.site_code] = site
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
        :style="{ transform: baseTransform }"
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

    <!-- Vestibular triplet | Palatal/lingual triplet — both faces in
         one tooth instead of duplicating the SVG twice per arch. -->
    <div class="flex items-center gap-0.5">
      <PerioSiteMarker
        v-for="code in VESTIBULAR_SITES"
        :key="code"
        :site="siteByCode[code]"
        size="sm"
        :disabled="readonly || !tooth.is_present"
        @click="emit('siteClick', code)"
      />
      <span aria-hidden="true" class="mx-0.5 text-gray-300">|</span>
      <PerioSiteMarker
        v-for="code in PALATAL_SITES"
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
