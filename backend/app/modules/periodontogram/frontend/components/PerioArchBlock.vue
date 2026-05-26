<script setup lang="ts">
/**
 * One arch (upper or lower) of the SEPA layout, rendered as a single
 * fixed-width table so every metric cell aligns with its tooth
 * column.
 *
 * Vertical order:
 *
 *  Upper arch (top → bottom)             Lower arch (top → bottom)
 *  ──────────────────────────────        ──────────────────────────────
 *  FDI numbers                            Palatal-face site metrics
 *  Per-tooth metrics                      Lingual tooth row (flipped)
 *  Vestibular-face site metrics           Vestibular tooth row
 *  Vestibular tooth row                   Vestibular-face site metrics
 *  Palatal tooth row (flipped)            Per-tooth metrics
 *  Palatal-face site metrics              FDI numbers
 *
 * The two arches mirror each other so when stacked vertically the
 * vestibular faces sit on the outside and the palatal/lingual faces
 * meet in the middle — anatomically how the patient's mouth looks
 * from the front.
 */
import { computed } from 'vue'
import type { PerioSite, PerioTooth, SiteCode } from '../types'
import { PALATAL_SITES, VESTIBULAR_SITES } from '../types'

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

const innerFace = computed<'palatal' | 'lingual'>(() =>
  props.arch === 'upper' ? 'palatal' : 'lingual'
)
const innerFaceLabel = computed(() => (props.arch === 'upper' ? 'Palatino' : 'Lingual'))
const innerSites = PALATAL_SITES

function siteValue(tooth: PerioTooth, code: SiteCode): PerioSite | null {
  return tooth.sites.find(s => s.site_code === code) ?? null
}

function pdText(site: PerioSite | null): string {
  if (!site || site.probing_depth_mm == null) return '·'
  return String(site.probing_depth_mm)
}

function gmText(site: PerioSite | null): string {
  if (!site || site.gingival_margin_mm == null) return '·'
  return String(site.gingival_margin_mm)
}

function mobilityText(tooth: PerioTooth): string {
  return tooth.mobility != null ? String(tooth.mobility) : '·'
}

function prognosisText(tooth: PerioTooth): string {
  if (!tooth.prognosis) return '·'
  return ({ good: 'B', fair: 'M', poor: 'D', hopeless: '✕' } as const)[tooth.prognosis]
}

// Rows are declared as data so the upper / lower templates can stay
// short. Each "kind" maps to a render block in the template.
type RowKind =
  | 'implant' | 'mobility' | 'prognosis'
  | 'furca-buccal' | 'furca-lingual' | 'keratinized'
  | 'site-pd' | 'site-gm' | 'site-plaque' | 'site-bop'

interface MetricRow { kind: RowKind, label: string }

const perToothRows: MetricRow[] = [
  { kind: 'implant', label: 'Implante' },
  { kind: 'mobility', label: 'Movilidad' },
  { kind: 'prognosis', label: 'Pronóstico' },
  { kind: 'furca-buccal', label: 'Furca V' },
  { kind: 'furca-lingual', label: 'Furca L/P' },
  { kind: 'keratinized', label: 'Anchura encía' }
]

const perSiteRows: MetricRow[] = [
  { kind: 'site-pd', label: 'Sondaje' },
  { kind: 'site-gm', label: 'Margen' },
  { kind: 'site-plaque', label: 'Placa' },
  { kind: 'site-bop', label: 'Sangrado' }
]
</script>

<template>
  <section class="perio-arch-block rounded-lg border border-gray-200 bg-white">
    <header class="flex items-center justify-between px-3 py-2">
      <h4 class="text-xs font-semibold uppercase tracking-wide text-gray-500">{{ heading }}</h4>
      <span class="text-[10px] text-gray-400">
        Vestibular ↔ {{ innerFaceLabel }}
      </span>
    </header>

    <table class="perio-arch-table w-full table-fixed border-collapse text-center font-mono text-[11px] leading-tight">
      <colgroup>
        <col style="width: 96px" />
        <col v-for="t in orderedTeeth" :key="`col-${t.tooth_number}`" style="width: 60px" />
      </colgroup>

      <!-- FDI header — visible at the top of the upper arch and the
           bottom of the lower arch via tfoot. -->
      <thead v-if="arch === 'upper'">
        <tr>
          <th class="px-1 text-right font-medium text-gray-500"></th>
          <th
            v-for="t in orderedTeeth"
            :key="`fdi-${t.tooth_number}`"
            class="px-1 font-medium text-gray-700"
          >
            {{ t.tooth_number }}
          </th>
        </tr>
      </thead>

      <!-- ============== UPPER ARCH BODY ============== -->
      <tbody v-if="arch === 'upper'" class="divide-y divide-gray-100">
        <!-- Per-tooth metrics -->
        <tr v-for="row in perToothRows" :key="row.kind">
          <th scope="row" class="px-1 text-right font-medium text-gray-500">{{ row.label }}</th>
          <td v-for="t in orderedTeeth" :key="`${row.kind}-${t.tooth_number}`" class="px-1">
            <template v-if="row.kind === 'implant'">
              <span v-if="t.is_implant" class="text-emerald-600" title="Implante">●</span>
              <span v-else class="text-gray-300">·</span>
            </template>
            <button
              v-else
              class="rounded px-1 hover:bg-gray-100 disabled:cursor-not-allowed"
              :disabled="readonly || !t.is_present"
              @click="emit('editTooth', t.tooth_number)"
            >
              <template v-if="row.kind === 'mobility'">{{ mobilityText(t) }}</template>
              <template v-else-if="row.kind === 'prognosis'">{{ prognosisText(t) }}</template>
              <template v-else-if="row.kind === 'furca-buccal'">{{ t.furcation_buccal ?? '·' }}</template>
              <template v-else-if="row.kind === 'furca-lingual'">{{ t.furcation_lingual ?? '·' }}</template>
              <template v-else-if="row.kind === 'keratinized'">{{ t.keratinized_gingiva_mm ?? '·' }}</template>
            </button>
          </td>
        </tr>

        <!-- Vestibular-face site metrics (sit right above the vestibular tooth row) -->
        <tr v-for="row in perSiteRows" :key="`v-${row.kind}`" class="bg-amber-50/40">
          <th scope="row" class="px-1 text-right font-medium text-amber-700">
            {{ row.label }} <span class="text-[9px] text-amber-500">V</span>
          </th>
          <td v-for="t in orderedTeeth" :key="`v-${row.kind}-${t.tooth_number}`" class="px-1">
            <div class="flex items-center justify-center gap-0.5 tabular-nums">
              <template v-for="code in VESTIBULAR_SITES" :key="`v-${row.kind}-${t.tooth_number}-${code}`">
                <button
                  v-if="row.kind === 'site-pd'"
                  class="w-3 rounded font-medium hover:bg-amber-100 disabled:cursor-not-allowed"
                  :disabled="readonly || !t.is_present"
                  :title="`${code} sondaje`"
                  @click="emit('editSite', t.tooth_number, code)"
                >{{ pdText(siteValue(t, code)) }}</button>
                <button
                  v-else-if="row.kind === 'site-gm'"
                  class="w-3 rounded hover:bg-amber-100 disabled:cursor-not-allowed"
                  :disabled="readonly || !t.is_present"
                  :title="`${code} margen`"
                  @click="emit('editSite', t.tooth_number, code)"
                >{{ gmText(siteValue(t, code)) }}</button>
                <button
                  v-else-if="row.kind === 'site-plaque'"
                  class="h-3 w-3 rounded-sm border border-gray-300 transition hover:scale-110"
                  :class="siteValue(t, code)?.plaque ? 'bg-blue-500 border-blue-500' : ''"
                  :disabled="readonly || !t.is_present"
                  :title="`${code} placa`"
                  @click="emit('editSite', t.tooth_number, code)"
                />
                <button
                  v-else-if="row.kind === 'site-bop'"
                  class="h-3 w-3 rounded-sm border border-gray-300 transition hover:scale-110"
                  :class="siteValue(t, code)?.bleeding_on_probing ? 'bg-error-500 border-error-500' : ''"
                  :disabled="readonly || !t.is_present"
                  :title="`${code} sangrado`"
                  @click="emit('editSite', t.tooth_number, code)"
                />
              </template>
            </div>
          </td>
        </tr>

        <!-- Vestibular tooth row -->
        <tr class="tooth-row">
          <th scope="row" class="px-1 text-right text-[10px] font-semibold uppercase tracking-wide text-amber-700">
            Vestibular
          </th>
          <td v-for="t in orderedTeeth" :key="`v-tooth-${t.tooth_number}`" class="px-0 align-bottom">
            <PerioToothLateral
              :tooth="t"
              face="vestibular"
              :readonly="readonly"
              @site-click="(code) => emit('editSite', t.tooth_number, code)"
            />
          </td>
        </tr>

        <!-- Palatal tooth row -->
        <tr class="tooth-row">
          <th scope="row" class="px-1 text-right text-[10px] font-semibold uppercase tracking-wide text-sky-700">
            {{ innerFaceLabel }}
          </th>
          <td v-for="t in orderedTeeth" :key="`p-tooth-${t.tooth_number}`" class="px-0 align-top">
            <PerioToothLateral
              :tooth="t"
              :face="innerFace"
              :readonly="readonly"
              @site-click="(code) => emit('editSite', t.tooth_number, code)"
            />
          </td>
        </tr>

        <!-- Palatal-face site metrics (sit right below the palatal tooth row) -->
        <tr v-for="row in perSiteRows" :key="`p-${row.kind}`" class="bg-sky-50/40">
          <th scope="row" class="px-1 text-right font-medium text-sky-700">
            {{ row.label }} <span class="text-[9px] text-sky-500">{{ innerFaceLabel.charAt(0) }}</span>
          </th>
          <td v-for="t in orderedTeeth" :key="`p-${row.kind}-${t.tooth_number}`" class="px-1">
            <div class="flex items-center justify-center gap-0.5 tabular-nums">
              <template v-for="code in innerSites" :key="`p-${row.kind}-${t.tooth_number}-${code}`">
                <button
                  v-if="row.kind === 'site-pd'"
                  class="w-3 rounded font-medium hover:bg-sky-100 disabled:cursor-not-allowed"
                  :disabled="readonly || !t.is_present"
                  :title="`${code} sondaje`"
                  @click="emit('editSite', t.tooth_number, code)"
                >{{ pdText(siteValue(t, code)) }}</button>
                <button
                  v-else-if="row.kind === 'site-gm'"
                  class="w-3 rounded hover:bg-sky-100 disabled:cursor-not-allowed"
                  :disabled="readonly || !t.is_present"
                  :title="`${code} margen`"
                  @click="emit('editSite', t.tooth_number, code)"
                >{{ gmText(siteValue(t, code)) }}</button>
                <button
                  v-else-if="row.kind === 'site-plaque'"
                  class="h-3 w-3 rounded-sm border border-gray-300 transition hover:scale-110"
                  :class="siteValue(t, code)?.plaque ? 'bg-blue-500 border-blue-500' : ''"
                  :disabled="readonly || !t.is_present"
                  :title="`${code} placa`"
                  @click="emit('editSite', t.tooth_number, code)"
                />
                <button
                  v-else-if="row.kind === 'site-bop'"
                  class="h-3 w-3 rounded-sm border border-gray-300 transition hover:scale-110"
                  :class="siteValue(t, code)?.bleeding_on_probing ? 'bg-error-500 border-error-500' : ''"
                  :disabled="readonly || !t.is_present"
                  :title="`${code} sangrado`"
                  @click="emit('editSite', t.tooth_number, code)"
                />
              </template>
            </div>
          </td>
        </tr>
      </tbody>

      <!-- ============== LOWER ARCH BODY ============== -->
      <tbody v-else class="divide-y divide-gray-100">
        <!-- Lingual-face site metrics on top -->
        <tr v-for="row in perSiteRows" :key="`l-${row.kind}`" class="bg-sky-50/40">
          <th scope="row" class="px-1 text-right font-medium text-sky-700">
            {{ row.label }} <span class="text-[9px] text-sky-500">L</span>
          </th>
          <td v-for="t in orderedTeeth" :key="`l-${row.kind}-${t.tooth_number}`" class="px-1">
            <div class="flex items-center justify-center gap-0.5 tabular-nums">
              <template v-for="code in innerSites" :key="`l-${row.kind}-${t.tooth_number}-${code}`">
                <button
                  v-if="row.kind === 'site-pd'"
                  class="w-3 rounded font-medium hover:bg-sky-100 disabled:cursor-not-allowed"
                  :disabled="readonly || !t.is_present"
                  :title="`${code} sondaje`"
                  @click="emit('editSite', t.tooth_number, code)"
                >{{ pdText(siteValue(t, code)) }}</button>
                <button
                  v-else-if="row.kind === 'site-gm'"
                  class="w-3 rounded hover:bg-sky-100 disabled:cursor-not-allowed"
                  :disabled="readonly || !t.is_present"
                  :title="`${code} margen`"
                  @click="emit('editSite', t.tooth_number, code)"
                >{{ gmText(siteValue(t, code)) }}</button>
                <button
                  v-else-if="row.kind === 'site-plaque'"
                  class="h-3 w-3 rounded-sm border border-gray-300 transition hover:scale-110"
                  :class="siteValue(t, code)?.plaque ? 'bg-blue-500 border-blue-500' : ''"
                  :disabled="readonly || !t.is_present"
                  :title="`${code} placa`"
                  @click="emit('editSite', t.tooth_number, code)"
                />
                <button
                  v-else-if="row.kind === 'site-bop'"
                  class="h-3 w-3 rounded-sm border border-gray-300 transition hover:scale-110"
                  :class="siteValue(t, code)?.bleeding_on_probing ? 'bg-error-500 border-error-500' : ''"
                  :disabled="readonly || !t.is_present"
                  :title="`${code} sangrado`"
                  @click="emit('editSite', t.tooth_number, code)"
                />
              </template>
            </div>
          </td>
        </tr>

        <!-- Lingual tooth row (innerFace='lingual', flipped) -->
        <tr class="tooth-row">
          <th scope="row" class="px-1 text-right text-[10px] font-semibold uppercase tracking-wide text-sky-700">
            {{ innerFaceLabel }}
          </th>
          <td v-for="t in orderedTeeth" :key="`l-tooth-${t.tooth_number}`" class="px-0 align-bottom">
            <PerioToothLateral
              :tooth="t"
              :face="innerFace"
              :readonly="readonly"
              @site-click="(code) => emit('editSite', t.tooth_number, code)"
            />
          </td>
        </tr>

        <!-- Vestibular tooth row -->
        <tr class="tooth-row">
          <th scope="row" class="px-1 text-right text-[10px] font-semibold uppercase tracking-wide text-amber-700">
            Vestibular
          </th>
          <td v-for="t in orderedTeeth" :key="`v-tooth-${t.tooth_number}`" class="px-0 align-top">
            <PerioToothLateral
              :tooth="t"
              face="vestibular"
              :readonly="readonly"
              @site-click="(code) => emit('editSite', t.tooth_number, code)"
            />
          </td>
        </tr>

        <!-- Vestibular-face site metrics directly below the V tooth row -->
        <tr v-for="row in perSiteRows" :key="`v-${row.kind}`" class="bg-amber-50/40">
          <th scope="row" class="px-1 text-right font-medium text-amber-700">
            {{ row.label }} <span class="text-[9px] text-amber-500">V</span>
          </th>
          <td v-for="t in orderedTeeth" :key="`v-${row.kind}-${t.tooth_number}`" class="px-1">
            <div class="flex items-center justify-center gap-0.5 tabular-nums">
              <template v-for="code in VESTIBULAR_SITES" :key="`v-${row.kind}-${t.tooth_number}-${code}`">
                <button
                  v-if="row.kind === 'site-pd'"
                  class="w-3 rounded font-medium hover:bg-amber-100 disabled:cursor-not-allowed"
                  :disabled="readonly || !t.is_present"
                  :title="`${code} sondaje`"
                  @click="emit('editSite', t.tooth_number, code)"
                >{{ pdText(siteValue(t, code)) }}</button>
                <button
                  v-else-if="row.kind === 'site-gm'"
                  class="w-3 rounded hover:bg-amber-100 disabled:cursor-not-allowed"
                  :disabled="readonly || !t.is_present"
                  :title="`${code} margen`"
                  @click="emit('editSite', t.tooth_number, code)"
                >{{ gmText(siteValue(t, code)) }}</button>
                <button
                  v-else-if="row.kind === 'site-plaque'"
                  class="h-3 w-3 rounded-sm border border-gray-300 transition hover:scale-110"
                  :class="siteValue(t, code)?.plaque ? 'bg-blue-500 border-blue-500' : ''"
                  :disabled="readonly || !t.is_present"
                  :title="`${code} placa`"
                  @click="emit('editSite', t.tooth_number, code)"
                />
                <button
                  v-else-if="row.kind === 'site-bop'"
                  class="h-3 w-3 rounded-sm border border-gray-300 transition hover:scale-110"
                  :class="siteValue(t, code)?.bleeding_on_probing ? 'bg-error-500 border-error-500' : ''"
                  :disabled="readonly || !t.is_present"
                  :title="`${code} sangrado`"
                  @click="emit('editSite', t.tooth_number, code)"
                />
              </template>
            </div>
          </td>
        </tr>

        <!-- Per-tooth metrics (inverted order — closest to vestibular) -->
        <tr v-for="row in [...perToothRows].reverse()" :key="row.kind">
          <th scope="row" class="px-1 text-right font-medium text-gray-500">{{ row.label }}</th>
          <td v-for="t in orderedTeeth" :key="`${row.kind}-${t.tooth_number}`" class="px-1">
            <template v-if="row.kind === 'implant'">
              <span v-if="t.is_implant" class="text-emerald-600" title="Implante">●</span>
              <span v-else class="text-gray-300">·</span>
            </template>
            <button
              v-else
              class="rounded px-1 hover:bg-gray-100 disabled:cursor-not-allowed"
              :disabled="readonly || !t.is_present"
              @click="emit('editTooth', t.tooth_number)"
            >
              <template v-if="row.kind === 'mobility'">{{ mobilityText(t) }}</template>
              <template v-else-if="row.kind === 'prognosis'">{{ prognosisText(t) }}</template>
              <template v-else-if="row.kind === 'furca-buccal'">{{ t.furcation_buccal ?? '·' }}</template>
              <template v-else-if="row.kind === 'furca-lingual'">{{ t.furcation_lingual ?? '·' }}</template>
              <template v-else-if="row.kind === 'keratinized'">{{ t.keratinized_gingiva_mm ?? '·' }}</template>
            </button>
          </td>
        </tr>
      </tbody>

      <tfoot v-if="arch === 'lower'">
        <tr>
          <th class="px-1 text-right font-medium text-gray-500"></th>
          <th
            v-for="t in orderedTeeth"
            :key="`fdi-${t.tooth_number}`"
            class="px-1 font-medium text-gray-700"
          >
            {{ t.tooth_number }}
          </th>
        </tr>
      </tfoot>
    </table>
  </section>
</template>

<style scoped>
.perio-arch-table .tooth-row td {
  padding-top: 4px;
  padding-bottom: 4px;
}
</style>
