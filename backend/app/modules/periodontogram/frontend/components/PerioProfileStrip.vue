<script setup lang="ts">
/**
 * SEPA-style sulcus profile strip.
 *
 * Plots two polylines across a row of teeth — gingival margin (calm
 * blue) and probing depth = pocket bottom (calm red) — over a backdrop
 * of horizontal millimetre gridlines so the dentist can read pocket
 * depths as heights, not just numbers.
 *
 * The strip is a flat SVG positioned next to a tooth row, in the
 * direction of the rendered root (the periodontal pocket lives in the
 * root area). Baseline = CEJ ≈ where the gum line of the existing
 * tooth silhouettes lands. Depth grows away from the teeth.
 *
 * Sites without a recorded probing depth are skipped from the
 * polylines — drawing a line at "0" would imply a measurement that
 * wasn't taken. The indices banner anchors the denominator to total
 * present sites separately.
 */
import { computed } from 'vue'
import type { PerioTooth, SiteCode } from '../types'
import { PALATAL_SITES, VESTIBULAR_SITES } from '../types'

const props = defineProps<{
  teeth: PerioTooth[]
  face: 'vestibular' | 'palatal' | 'lingual'
  /**
   * `depth-up`   — baseline at bottom edge, depth grows upward (strip
   *                placed above its tooth row, where the root renders).
   * `depth-down` — baseline at top edge, depth grows downward (strip
   *                placed below its tooth row).
   */
  direction: 'depth-up' | 'depth-down'
  columnWidth?: number
}>()

const COL_W = props.columnWidth ?? 60
// 4 px/mm → strip is 60 px tall for the 15 mm probing range. Matches
// the ~60 px root area visible on the larger `h-20` tooth silhouette,
// so the gridlines + lines paint cleanly across the rendered root.
const MM_PX = 4
const MAX_MM = 15
const STRIP_H = MAX_MM * MM_PX

const sites = computed<readonly SiteCode[]>(() =>
  props.face === 'vestibular' ? VESTIBULAR_SITES : PALATAL_SITES
)

const stripWidth = computed(() => props.teeth.length * COL_W)

function depthToY(mm: number): number {
  // Clamp so a stray big value can't escape the strip area.
  const clamped = Math.max(-3, Math.min(MAX_MM, mm))
  return props.direction === 'depth-up'
    ? STRIP_H - clamped * MM_PX
    : clamped * MM_PX
}

function siteX(toothIdx: number, siteIdx: number): number {
  // Three sites per tooth, evenly spaced across the column at 20/50/80%.
  // The middle site sits over the centre of the tooth silhouette.
  const offsets = [0.2, 0.5, 0.8]
  return toothIdx * COL_W + COL_W * offsets[siteIdx]
}

interface PathPoint { x: number, y: number }

function buildPath(
  getMm: (toothIdx: number, siteIdx: number) => number | null | undefined
): string {
  const pts: PathPoint[] = []
  props.teeth.forEach((_, ti) => {
    sites.value.forEach((_code, si) => {
      const mm = getMm(ti, si)
      if (mm == null) return
      pts.push({ x: siteX(ti, si), y: depthToY(mm) })
    })
  })
  if (pts.length === 0) return ''
  return pts.map((p, i) => (i === 0 ? `M ${p.x},${p.y}` : `L ${p.x},${p.y}`)).join(' ')
}

function siteAt(ti: number, si: number) {
  const tooth = props.teeth[ti]
  return tooth.sites.find(s => s.site_code === sites.value[si])
}

const gmPath = computed(() =>
  buildPath((ti, si) => siteAt(ti, si)?.gingival_margin_mm ?? null)
)

const pdPath = computed(() =>
  buildPath((ti, si) => {
    const s = siteAt(ti, si)
    if (s?.probing_depth_mm == null) return null
    return (s.gingival_margin_mm ?? 0) + s.probing_depth_mm
  })
)

// Pocket band — closed shape between GM (top) and PD (bottom) lines.
// Only drawn over the contiguous run of sites where both values exist.
const bandPath = computed(() => {
  const gm: PathPoint[] = []
  const pd: PathPoint[] = []
  props.teeth.forEach((_, ti) => {
    sites.value.forEach((_code, si) => {
      const s = siteAt(ti, si)
      if (s?.probing_depth_mm == null) return
      const gmMm = s.gingival_margin_mm ?? 0
      const pdMm = gmMm + s.probing_depth_mm
      gm.push({ x: siteX(ti, si), y: depthToY(gmMm) })
      pd.push({ x: siteX(ti, si), y: depthToY(pdMm) })
    })
  })
  if (gm.length < 2) return ''
  const forward = gm.map((p, i) => (i === 0 ? `M ${p.x},${p.y}` : `L ${p.x},${p.y}`)).join(' ')
  const back = pd.slice().reverse().map(p => `L ${p.x},${p.y}`).join(' ')
  return `${forward} ${back} Z`
})

const gridlines = computed(() => {
  const out: Array<{ y: number, mm: number }> = []
  // Include 0 mm (CEJ) — the first millimetre line must pass through
  // the gum line so the dentist can read pocket depth directly off
  // the gridline, without a separate red gum curve on the tooth.
  for (let m = 0; m <= MAX_MM; m++) out.push({ y: depthToY(m), mm: m })
  return out
})
</script>

<template>
  <svg
    :viewBox="`0 0 ${stripWidth} ${STRIP_H}`"
    :width="stripWidth"
    :height="STRIP_H"
    class="perio-profile-strip block"
    preserveAspectRatio="none"
    aria-hidden="true"
  >
    <!-- Millimetre gridlines: hairline gray, bolder at 0/5/10/15.
         The 0 mm line is the CEJ — it doubles as the gum line that
         used to be drawn on the tooth silhouette. -->
    <g>
      <line
        v-for="g in gridlines"
        :key="`grid-${g.mm}`"
        x1="0"
        :x2="stripWidth"
        :y1="g.y"
        :y2="g.y"
        :stroke="g.mm % 5 === 0 ? 'var(--perio-grid-line-bold)' : 'var(--perio-grid-line)'"
        :stroke-width="g.mm % 5 === 0 ? 0.6 : 0.35"
      />
    </g>

    <!-- Pocket band — soft red fill between the two lines. -->
    <path
      v-if="bandPath"
      :d="bandPath"
      fill="var(--perio-pocket-band)"
      style="opacity: var(--perio-pocket-band-opacity)"
    />

    <!-- Gingival margin (calm sky) -->
    <path
      v-if="gmPath"
      :d="gmPath"
      fill="none"
      stroke="var(--perio-gm-stroke)"
      stroke-width="1.4"
      stroke-linejoin="round"
      stroke-linecap="round"
    />

    <!-- Probing depth — pocket bottom (calm red) -->
    <path
      v-if="pdPath"
      :d="pdPath"
      fill="none"
      stroke="var(--perio-pd-stroke)"
      stroke-width="1.4"
      stroke-linejoin="round"
      stroke-linecap="round"
    />
  </svg>
</template>

<style scoped>
.perio-profile-strip {
  width: 100%;
  height: auto;
}
</style>
