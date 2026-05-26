<script setup lang="ts">
/**
 * One arch (upper or lower) of the SEPA layout.
 *
 * Spreadsheet-style inline editing — every cell is directly
 * actionable without a modal:
 *
 * - Numeric fields (Sondaje, Margen, Anchura encía) render as
 *   `<input type="number">` styled to look like a value at rest.
 *   Focus selects the value; Tab advances; blur commits via
 *   `editSite` / `editTooth`.
 * - Toggle fields (Sangrado, Placa) are single-click squares that
 *   flip their boolean.
 * - Enum fields (Movilidad, Pronóstico, Furca V/L) cycle through
 *   their value space on each click — null → first value → next →
 *   wraps back to null.
 * - Implante is a single-click toggle (mostly pre-filled from the
 *   odontogram, override stays local).
 *
 * Alignment is enforced by a `table-fixed` table with an explicit
 * `<colgroup>` — every metric cell shares its column with the tooth
 * directly above or below it, so a vertical scan reads cleanly per
 * FDI number.
 */
import { computed } from 'vue'
import type { Furcation, PerioSite, PerioTooth, Prognosis, SiteCode } from '../types'
import { PALATAL_SITES, VESTIBULAR_SITES } from '../types'

const props = defineProps<{
  arch: 'upper' | 'lower'
  teeth: PerioTooth[]
  readonly?: boolean
}>()

const emit = defineEmits<{
  editTooth: [toothNumber: number, patch: Record<string, unknown>]
  editSite: [toothNumber: number, siteCode: SiteCode, patch: Record<string, unknown>]
}>()

// ---------------------------------------------------------------------------
// Ordering
// ---------------------------------------------------------------------------

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

// ---------------------------------------------------------------------------
// Read helpers
// ---------------------------------------------------------------------------

function siteValue(tooth: PerioTooth, code: SiteCode): PerioSite | null {
  return tooth.sites.find(s => s.site_code === code) ?? null
}

// ---------------------------------------------------------------------------
// Cycle definitions for enum fields. Click cycles forward; null wraps
// back to the head — gives the dentist a single mouse target with
// keyboard friendliness (a value clears via the same button).
// ---------------------------------------------------------------------------

const MOBILITY_CYCLE: Array<number | null> = [null, 0, 1, 2, 3]
const PROGNOSIS_CYCLE: Array<Prognosis | null> = [null, 'good', 'fair', 'poor', 'hopeless']
const FURCA_CYCLE: Array<Furcation | null> = [null, '0', 'I', 'II', 'III']

function nextInCycle<T>(cycle: T[], current: T): T {
  const idx = cycle.findIndex(v => v === current)
  if (idx === -1) return cycle[1] ?? cycle[0]
  return cycle[(idx + 1) % cycle.length]
}

function prognosisGlyph(v: Prognosis | null | undefined): string {
  if (v === 'good') return 'B'
  if (v === 'fair') return 'M'
  if (v === 'poor') return 'D'
  if (v === 'hopeless') return '✕'
  return '·'
}

function mobilityGlyph(v: number | null | undefined): string {
  return v == null ? '·' : String(v)
}

function furcaGlyph(v: Furcation | null | undefined): string {
  return v ?? '·'
}

// ---------------------------------------------------------------------------
// Input parsing for numeric fields. Empty string clears the value.
// ---------------------------------------------------------------------------

function parseIntOrNull(raw: string): number | null {
  if (raw.trim() === '') return null
  const n = Number(raw)
  if (!Number.isFinite(n)) return null
  return Math.round(n)
}

// ---------------------------------------------------------------------------
// Event handlers
// ---------------------------------------------------------------------------

function onSiteNumberInput(
  toothNumber: number,
  code: SiteCode,
  field: 'probing_depth_mm' | 'gingival_margin_mm',
  e: Event
) {
  if (props.readonly) return
  const raw = (e.target as HTMLInputElement).value
  emit('editSite', toothNumber, code, { [field]: parseIntOrNull(raw) })
}

function onSiteToggle(
  toothNumber: number,
  code: SiteCode,
  field: 'bleeding_on_probing' | 'plaque',
  current: boolean | undefined
) {
  if (props.readonly) return
  emit('editSite', toothNumber, code, { [field]: !current })
}

function onToothNumberInput(
  toothNumber: number,
  field: 'keratinized_gingiva_mm',
  e: Event
) {
  if (props.readonly) return
  const raw = (e.target as HTMLInputElement).value
  emit('editTooth', toothNumber, { [field]: parseIntOrNull(raw) })
}

function onToothCycle(
  tooth: PerioTooth,
  field: 'mobility' | 'prognosis' | 'furcation_buccal' | 'furcation_lingual'
) {
  if (props.readonly || !tooth.is_present) return
  if (field === 'mobility') {
    emit('editTooth', tooth.tooth_number, { mobility: nextInCycle(MOBILITY_CYCLE, tooth.mobility ?? null) })
  } else if (field === 'prognosis') {
    emit('editTooth', tooth.tooth_number, { prognosis: nextInCycle(PROGNOSIS_CYCLE, tooth.prognosis ?? null) })
  } else if (field === 'furcation_buccal') {
    emit('editTooth', tooth.tooth_number, { furcation_buccal: nextInCycle(FURCA_CYCLE, tooth.furcation_buccal ?? null) })
  } else {
    emit('editTooth', tooth.tooth_number, { furcation_lingual: nextInCycle(FURCA_CYCLE, tooth.furcation_lingual ?? null) })
  }
}

function onImplantToggle(tooth: PerioTooth) {
  if (props.readonly) return
  emit('editTooth', tooth.tooth_number, { is_implant: !tooth.is_implant })
}

// ---------------------------------------------------------------------------
// Focus auto-select — typing immediately overwrites the previous value
// instead of appending characters.
// ---------------------------------------------------------------------------

function selectOnFocus(e: FocusEvent) {
  const target = e.target as HTMLInputElement
  if (target?.select) target.select()
}
</script>

<template>
  <section class="perio-arch-block rounded-lg border border-gray-200 bg-white">
    <header class="flex items-center justify-between px-3 py-2">
      <h4 class="text-xs font-semibold uppercase tracking-wide text-gray-500">{{ heading }}</h4>
      <span class="text-[10px] text-gray-400">
        Vestibular (MV V DV) ↔ {{ innerFaceLabel }} (ML L DL)
      </span>
    </header>

    <table
      class="perio-arch-table w-full table-fixed border-collapse text-center font-mono text-[11px] leading-tight"
    >
      <colgroup>
        <col style="width: 96px" />
        <col v-for="t in orderedTeeth" :key="`col-${t.tooth_number}`" style="width: 60px" />
      </colgroup>

      <thead v-if="arch === 'upper'">
        <tr>
          <th class="px-1 text-right font-medium text-gray-500"></th>
          <th
            v-for="t in orderedTeeth"
            :key="`fdi-${t.tooth_number}`"
            class="px-1 py-1 font-medium text-gray-700"
          >
            {{ t.tooth_number }}
          </th>
        </tr>
      </thead>

      <!-- ============== UPPER ARCH ============== -->
      <tbody v-if="arch === 'upper'" class="divide-y divide-gray-100">
        <!-- Implante (toggle ● / ·) -->
        <tr>
          <th scope="row" class="px-1 text-right font-medium text-gray-500">Implante</th>
          <td v-for="t in orderedTeeth" :key="`imp-${t.tooth_number}`" class="px-1">
            <button
              class="perio-cell-cycle"
              :class="{ 'text-emerald-600': t.is_implant }"
              :disabled="readonly"
              :title="t.is_implant ? 'Implante (clic para quitar)' : 'Clic para marcar como implante'"
              @click="onImplantToggle(t)"
            >
              {{ t.is_implant ? '●' : '·' }}
            </button>
          </td>
        </tr>

        <!-- Movilidad (cycle 0..3 + null) -->
        <tr>
          <th scope="row" class="px-1 text-right font-medium text-gray-500">Movilidad</th>
          <td v-for="t in orderedTeeth" :key="`mob-${t.tooth_number}`" class="px-1">
            <button
              class="perio-cell-cycle"
              :disabled="readonly || !t.is_present"
              title="Clic para cambiar movilidad (0–3)"
              @click="onToothCycle(t, 'mobility')"
            >
              {{ mobilityGlyph(t.mobility) }}
            </button>
          </td>
        </tr>

        <!-- Pronóstico cycle -->
        <tr>
          <th scope="row" class="px-1 text-right font-medium text-gray-500">Pronóstico</th>
          <td v-for="t in orderedTeeth" :key="`pron-${t.tooth_number}`" class="px-1">
            <button
              class="perio-cell-cycle"
              :disabled="readonly || !t.is_present"
              title="Bueno / Medio / Dudoso / Sin esperanza"
              @click="onToothCycle(t, 'prognosis')"
            >
              {{ prognosisGlyph(t.prognosis) }}
            </button>
          </td>
        </tr>

        <!-- Furca V / L cycles -->
        <tr>
          <th scope="row" class="px-1 text-right font-medium text-gray-500">Furca V</th>
          <td v-for="t in orderedTeeth" :key="`furv-${t.tooth_number}`" class="px-1">
            <button
              class="perio-cell-cycle"
              :disabled="readonly || !t.is_present"
              title="Furca vestibular (0/I/II/III)"
              @click="onToothCycle(t, 'furcation_buccal')"
            >
              {{ furcaGlyph(t.furcation_buccal) }}
            </button>
          </td>
        </tr>
        <tr>
          <th scope="row" class="px-1 text-right font-medium text-gray-500">Furca L/P</th>
          <td v-for="t in orderedTeeth" :key="`furl-${t.tooth_number}`" class="px-1">
            <button
              class="perio-cell-cycle"
              :disabled="readonly || !t.is_present"
              title="Furca lingual/palatina (0/I/II/III)"
              @click="onToothCycle(t, 'furcation_lingual')"
            >
              {{ furcaGlyph(t.furcation_lingual) }}
            </button>
          </td>
        </tr>

        <!-- Anchura encía (numeric input) -->
        <tr>
          <th scope="row" class="px-1 text-right font-medium text-gray-500">Anchura encía</th>
          <td v-for="t in orderedTeeth" :key="`kg-${t.tooth_number}`" class="px-1">
            <input
              type="number"
              min="0"
              max="20"
              :value="t.keratinized_gingiva_mm ?? ''"
              :disabled="readonly || !t.is_present"
              class="perio-cell-input"
              @focus="selectOnFocus"
              @change="(e) => onToothNumberInput(t.tooth_number, 'keratinized_gingiva_mm', e)"
            />
          </td>
        </tr>

        <!-- Vestibular site metrics — amber tint, sits above the V tooth row -->
        <tr v-for="row in [
          { kind: 'site-pd', label: 'Sondaje' },
          { kind: 'site-gm', label: 'Margen' },
          { kind: 'site-plaque', label: 'Placa' },
          { kind: 'site-bop', label: 'Sangrado' }
        ]" :key="`v-${row.kind}`" class="bg-amber-50/40">
          <th scope="row" class="px-1 text-right font-medium text-amber-700">
            {{ row.label }} <span class="text-[9px] text-amber-500">V</span>
          </th>
          <td v-for="t in orderedTeeth" :key="`v-${row.kind}-${t.tooth_number}`" class="px-1">
            <div class="flex items-center justify-center gap-0.5 tabular-nums">
              <template v-for="code in VESTIBULAR_SITES" :key="`v-${row.kind}-${t.tooth_number}-${code}`">
                <input
                  v-if="row.kind === 'site-pd'"
                  type="number"
                  min="0"
                  max="15"
                  :value="siteValue(t, code)?.probing_depth_mm ?? ''"
                  :disabled="readonly || !t.is_present"
                  class="perio-cell-input perio-cell-input--site"
                  :title="`${code} sondaje (0–15 mm)`"
                  @focus="selectOnFocus"
                  @change="(e) => onSiteNumberInput(t.tooth_number, code, 'probing_depth_mm', e)"
                />
                <input
                  v-else-if="row.kind === 'site-gm'"
                  type="number"
                  min="-5"
                  max="10"
                  :value="siteValue(t, code)?.gingival_margin_mm ?? ''"
                  :disabled="readonly || !t.is_present"
                  class="perio-cell-input perio-cell-input--site"
                  :title="`${code} margen gingival (-5 a 10 mm)`"
                  @focus="selectOnFocus"
                  @change="(e) => onSiteNumberInput(t.tooth_number, code, 'gingival_margin_mm', e)"
                />
                <button
                  v-else-if="row.kind === 'site-plaque'"
                  type="button"
                  class="perio-cell-toggle perio-cell-toggle--plaque"
                  :class="{ 'is-on': siteValue(t, code)?.plaque }"
                  :disabled="readonly || !t.is_present"
                  :title="`${code} placa (clic para alternar)`"
                  @click="onSiteToggle(t.tooth_number, code, 'plaque', siteValue(t, code)?.plaque)"
                />
                <button
                  v-else-if="row.kind === 'site-bop'"
                  type="button"
                  class="perio-cell-toggle perio-cell-toggle--bop"
                  :class="{ 'is-on': siteValue(t, code)?.bleeding_on_probing }"
                  :disabled="readonly || !t.is_present"
                  :title="`${code} sangrado (clic para alternar)`"
                  @click="onSiteToggle(t.tooth_number, code, 'bleeding_on_probing', siteValue(t, code)?.bleeding_on_probing)"
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
            <PerioToothLateral :tooth="t" face="vestibular" :readonly="readonly" />
          </td>
        </tr>

        <!-- Palatal tooth row -->
        <tr class="tooth-row">
          <th scope="row" class="px-1 text-right text-[10px] font-semibold uppercase tracking-wide text-sky-700">
            {{ innerFaceLabel }}
          </th>
          <td v-for="t in orderedTeeth" :key="`p-tooth-${t.tooth_number}`" class="px-0 align-top">
            <PerioToothLateral :tooth="t" :face="innerFace" :readonly="readonly" />
          </td>
        </tr>

        <!-- Palatal site metrics — sky tint -->
        <tr v-for="row in [
          { kind: 'site-bop', label: 'Sangrado' },
          { kind: 'site-plaque', label: 'Placa' },
          { kind: 'site-gm', label: 'Margen' },
          { kind: 'site-pd', label: 'Sondaje' }
        ]" :key="`p-${row.kind}`" class="bg-sky-50/40">
          <th scope="row" class="px-1 text-right font-medium text-sky-700">
            {{ row.label }} <span class="text-[9px] text-sky-500">{{ innerFaceLabel.charAt(0) }}</span>
          </th>
          <td v-for="t in orderedTeeth" :key="`p-${row.kind}-${t.tooth_number}`" class="px-1">
            <div class="flex items-center justify-center gap-0.5 tabular-nums">
              <template v-for="code in innerSites" :key="`p-${row.kind}-${t.tooth_number}-${code}`">
                <input
                  v-if="row.kind === 'site-pd'"
                  type="number"
                  min="0"
                  max="15"
                  :value="siteValue(t, code)?.probing_depth_mm ?? ''"
                  :disabled="readonly || !t.is_present"
                  class="perio-cell-input perio-cell-input--site"
                  :title="`${code} sondaje (0–15 mm)`"
                  @focus="selectOnFocus"
                  @change="(e) => onSiteNumberInput(t.tooth_number, code, 'probing_depth_mm', e)"
                />
                <input
                  v-else-if="row.kind === 'site-gm'"
                  type="number"
                  min="-5"
                  max="10"
                  :value="siteValue(t, code)?.gingival_margin_mm ?? ''"
                  :disabled="readonly || !t.is_present"
                  class="perio-cell-input perio-cell-input--site"
                  :title="`${code} margen gingival (-5 a 10 mm)`"
                  @focus="selectOnFocus"
                  @change="(e) => onSiteNumberInput(t.tooth_number, code, 'gingival_margin_mm', e)"
                />
                <button
                  v-else-if="row.kind === 'site-plaque'"
                  type="button"
                  class="perio-cell-toggle perio-cell-toggle--plaque"
                  :class="{ 'is-on': siteValue(t, code)?.plaque }"
                  :disabled="readonly || !t.is_present"
                  :title="`${code} placa (clic para alternar)`"
                  @click="onSiteToggle(t.tooth_number, code, 'plaque', siteValue(t, code)?.plaque)"
                />
                <button
                  v-else-if="row.kind === 'site-bop'"
                  type="button"
                  class="perio-cell-toggle perio-cell-toggle--bop"
                  :class="{ 'is-on': siteValue(t, code)?.bleeding_on_probing }"
                  :disabled="readonly || !t.is_present"
                  :title="`${code} sangrado (clic para alternar)`"
                  @click="onSiteToggle(t.tooth_number, code, 'bleeding_on_probing', siteValue(t, code)?.bleeding_on_probing)"
                />
              </template>
            </div>
          </td>
        </tr>
      </tbody>

      <!-- ============== LOWER ARCH (mirror) ============== -->
      <tbody v-else class="divide-y divide-gray-100">
        <!-- Lingual site metrics on top -->
        <tr v-for="row in [
          { kind: 'site-pd', label: 'Sondaje' },
          { kind: 'site-gm', label: 'Margen' },
          { kind: 'site-plaque', label: 'Placa' },
          { kind: 'site-bop', label: 'Sangrado' }
        ]" :key="`l-${row.kind}`" class="bg-sky-50/40">
          <th scope="row" class="px-1 text-right font-medium text-sky-700">
            {{ row.label }} <span class="text-[9px] text-sky-500">L</span>
          </th>
          <td v-for="t in orderedTeeth" :key="`l-${row.kind}-${t.tooth_number}`" class="px-1">
            <div class="flex items-center justify-center gap-0.5 tabular-nums">
              <template v-for="code in innerSites" :key="`l-${row.kind}-${t.tooth_number}-${code}`">
                <input
                  v-if="row.kind === 'site-pd'"
                  type="number"
                  min="0"
                  max="15"
                  :value="siteValue(t, code)?.probing_depth_mm ?? ''"
                  :disabled="readonly || !t.is_present"
                  class="perio-cell-input perio-cell-input--site"
                  :title="`${code} sondaje (0–15 mm)`"
                  @focus="selectOnFocus"
                  @change="(e) => onSiteNumberInput(t.tooth_number, code, 'probing_depth_mm', e)"
                />
                <input
                  v-else-if="row.kind === 'site-gm'"
                  type="number"
                  min="-5"
                  max="10"
                  :value="siteValue(t, code)?.gingival_margin_mm ?? ''"
                  :disabled="readonly || !t.is_present"
                  class="perio-cell-input perio-cell-input--site"
                  :title="`${code} margen gingival (-5 a 10 mm)`"
                  @focus="selectOnFocus"
                  @change="(e) => onSiteNumberInput(t.tooth_number, code, 'gingival_margin_mm', e)"
                />
                <button
                  v-else-if="row.kind === 'site-plaque'"
                  type="button"
                  class="perio-cell-toggle perio-cell-toggle--plaque"
                  :class="{ 'is-on': siteValue(t, code)?.plaque }"
                  :disabled="readonly || !t.is_present"
                  :title="`${code} placa (clic para alternar)`"
                  @click="onSiteToggle(t.tooth_number, code, 'plaque', siteValue(t, code)?.plaque)"
                />
                <button
                  v-else-if="row.kind === 'site-bop'"
                  type="button"
                  class="perio-cell-toggle perio-cell-toggle--bop"
                  :class="{ 'is-on': siteValue(t, code)?.bleeding_on_probing }"
                  :disabled="readonly || !t.is_present"
                  :title="`${code} sangrado (clic para alternar)`"
                  @click="onSiteToggle(t.tooth_number, code, 'bleeding_on_probing', siteValue(t, code)?.bleeding_on_probing)"
                />
              </template>
            </div>
          </td>
        </tr>

        <!-- Lingual tooth row -->
        <tr class="tooth-row">
          <th scope="row" class="px-1 text-right text-[10px] font-semibold uppercase tracking-wide text-sky-700">
            {{ innerFaceLabel }}
          </th>
          <td v-for="t in orderedTeeth" :key="`l-tooth-${t.tooth_number}`" class="px-0 align-bottom">
            <PerioToothLateral :tooth="t" :face="innerFace" :readonly="readonly" />
          </td>
        </tr>

        <!-- Vestibular tooth row -->
        <tr class="tooth-row">
          <th scope="row" class="px-1 text-right text-[10px] font-semibold uppercase tracking-wide text-amber-700">
            Vestibular
          </th>
          <td v-for="t in orderedTeeth" :key="`v-tooth-${t.tooth_number}`" class="px-0 align-top">
            <PerioToothLateral :tooth="t" face="vestibular" :readonly="readonly" />
          </td>
        </tr>

        <!-- Vestibular site metrics directly below the V tooth row -->
        <tr v-for="row in [
          { kind: 'site-bop', label: 'Sangrado' },
          { kind: 'site-plaque', label: 'Placa' },
          { kind: 'site-gm', label: 'Margen' },
          { kind: 'site-pd', label: 'Sondaje' }
        ]" :key="`v-${row.kind}`" class="bg-amber-50/40">
          <th scope="row" class="px-1 text-right font-medium text-amber-700">
            {{ row.label }} <span class="text-[9px] text-amber-500">V</span>
          </th>
          <td v-for="t in orderedTeeth" :key="`v-${row.kind}-${t.tooth_number}`" class="px-1">
            <div class="flex items-center justify-center gap-0.5 tabular-nums">
              <template v-for="code in VESTIBULAR_SITES" :key="`v-${row.kind}-${t.tooth_number}-${code}`">
                <input
                  v-if="row.kind === 'site-pd'"
                  type="number"
                  min="0"
                  max="15"
                  :value="siteValue(t, code)?.probing_depth_mm ?? ''"
                  :disabled="readonly || !t.is_present"
                  class="perio-cell-input perio-cell-input--site"
                  :title="`${code} sondaje (0–15 mm)`"
                  @focus="selectOnFocus"
                  @change="(e) => onSiteNumberInput(t.tooth_number, code, 'probing_depth_mm', e)"
                />
                <input
                  v-else-if="row.kind === 'site-gm'"
                  type="number"
                  min="-5"
                  max="10"
                  :value="siteValue(t, code)?.gingival_margin_mm ?? ''"
                  :disabled="readonly || !t.is_present"
                  class="perio-cell-input perio-cell-input--site"
                  :title="`${code} margen gingival (-5 a 10 mm)`"
                  @focus="selectOnFocus"
                  @change="(e) => onSiteNumberInput(t.tooth_number, code, 'gingival_margin_mm', e)"
                />
                <button
                  v-else-if="row.kind === 'site-plaque'"
                  type="button"
                  class="perio-cell-toggle perio-cell-toggle--plaque"
                  :class="{ 'is-on': siteValue(t, code)?.plaque }"
                  :disabled="readonly || !t.is_present"
                  :title="`${code} placa (clic para alternar)`"
                  @click="onSiteToggle(t.tooth_number, code, 'plaque', siteValue(t, code)?.plaque)"
                />
                <button
                  v-else-if="row.kind === 'site-bop'"
                  type="button"
                  class="perio-cell-toggle perio-cell-toggle--bop"
                  :class="{ 'is-on': siteValue(t, code)?.bleeding_on_probing }"
                  :disabled="readonly || !t.is_present"
                  :title="`${code} sangrado (clic para alternar)`"
                  @click="onSiteToggle(t.tooth_number, code, 'bleeding_on_probing', siteValue(t, code)?.bleeding_on_probing)"
                />
              </template>
            </div>
          </td>
        </tr>

        <!-- Per-tooth metrics (reversed — closest to vestibular row) -->
        <tr>
          <th scope="row" class="px-1 text-right font-medium text-gray-500">Anchura encía</th>
          <td v-for="t in orderedTeeth" :key="`kg-${t.tooth_number}`" class="px-1">
            <input
              type="number"
              min="0"
              max="20"
              :value="t.keratinized_gingiva_mm ?? ''"
              :disabled="readonly || !t.is_present"
              class="perio-cell-input"
              @focus="selectOnFocus"
              @change="(e) => onToothNumberInput(t.tooth_number, 'keratinized_gingiva_mm', e)"
            />
          </td>
        </tr>
        <tr>
          <th scope="row" class="px-1 text-right font-medium text-gray-500">Furca L/P</th>
          <td v-for="t in orderedTeeth" :key="`furl-${t.tooth_number}`" class="px-1">
            <button
              class="perio-cell-cycle"
              :disabled="readonly || !t.is_present"
              title="Furca lingual/palatina (0/I/II/III)"
              @click="onToothCycle(t, 'furcation_lingual')"
            >{{ furcaGlyph(t.furcation_lingual) }}</button>
          </td>
        </tr>
        <tr>
          <th scope="row" class="px-1 text-right font-medium text-gray-500">Furca V</th>
          <td v-for="t in orderedTeeth" :key="`furv-${t.tooth_number}`" class="px-1">
            <button
              class="perio-cell-cycle"
              :disabled="readonly || !t.is_present"
              title="Furca vestibular (0/I/II/III)"
              @click="onToothCycle(t, 'furcation_buccal')"
            >{{ furcaGlyph(t.furcation_buccal) }}</button>
          </td>
        </tr>
        <tr>
          <th scope="row" class="px-1 text-right font-medium text-gray-500">Pronóstico</th>
          <td v-for="t in orderedTeeth" :key="`pron-${t.tooth_number}`" class="px-1">
            <button
              class="perio-cell-cycle"
              :disabled="readonly || !t.is_present"
              title="Bueno / Medio / Dudoso / Sin esperanza"
              @click="onToothCycle(t, 'prognosis')"
            >{{ prognosisGlyph(t.prognosis) }}</button>
          </td>
        </tr>
        <tr>
          <th scope="row" class="px-1 text-right font-medium text-gray-500">Movilidad</th>
          <td v-for="t in orderedTeeth" :key="`mob-${t.tooth_number}`" class="px-1">
            <button
              class="perio-cell-cycle"
              :disabled="readonly || !t.is_present"
              title="Clic para cambiar movilidad (0–3)"
              @click="onToothCycle(t, 'mobility')"
            >{{ mobilityGlyph(t.mobility) }}</button>
          </td>
        </tr>
        <tr>
          <th scope="row" class="px-1 text-right font-medium text-gray-500">Implante</th>
          <td v-for="t in orderedTeeth" :key="`imp-${t.tooth_number}`" class="px-1">
            <button
              class="perio-cell-cycle"
              :class="{ 'text-emerald-600': t.is_implant }"
              :disabled="readonly"
              :title="t.is_implant ? 'Implante (clic para quitar)' : 'Clic para marcar como implante'"
              @click="onImplantToggle(t)"
            >{{ t.is_implant ? '●' : '·' }}</button>
          </td>
        </tr>
      </tbody>

      <tfoot v-if="arch === 'lower'">
        <tr>
          <th class="px-1 text-right font-medium text-gray-500"></th>
          <th
            v-for="t in orderedTeeth"
            :key="`fdi-${t.tooth_number}`"
            class="px-1 py-1 font-medium text-gray-700"
          >
            {{ t.tooth_number }}
          </th>
        </tr>
      </tfoot>
    </table>
  </section>
</template>

<style scoped>
/* Cell-level inline editors. Keep the visual chrome minimal so the
   chart still reads like a SEPA paper chart, but surface every cell
   as a single-click target. */

.perio-cell-cycle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  padding: 0 4px;
  border-radius: 4px;
  border: 1px solid transparent;
  background: transparent;
  font-family: inherit;
  font-size: inherit;
  color: inherit;
  cursor: pointer;
  transition: background-color 100ms ease, border-color 100ms ease;
}

.perio-cell-cycle:hover:not(:disabled) {
  background-color: rgb(243 244 246); /* gray-100 */
}

.perio-cell-cycle:focus-visible {
  outline: none;
  border-color: rgb(59 130 246); /* primary-500 */
  box-shadow: 0 0 0 1px rgb(59 130 246);
}

.perio-cell-cycle:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.perio-cell-input {
  width: 100%;
  padding: 0 2px;
  border: 1px solid transparent;
  background: transparent;
  font-family: inherit;
  font-size: inherit;
  text-align: center;
  font-variant-numeric: tabular-nums;
  appearance: textfield;
  -moz-appearance: textfield;
  border-radius: 3px;
  transition: background-color 100ms ease, border-color 100ms ease;
}

.perio-cell-input::-webkit-outer-spin-button,
.perio-cell-input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

.perio-cell-input:hover:not(:disabled) {
  background-color: rgb(249 250 251);
}

.perio-cell-input:focus {
  outline: none;
  background-color: white;
  border-color: rgb(245 158 11); /* amber-500 */
  box-shadow: 0 0 0 1px rgb(245 158 11);
}

.perio-cell-input:disabled {
  cursor: not-allowed;
  color: rgb(156 163 175);
}

.perio-cell-input--site {
  width: 14px;
  padding: 0;
  font-weight: 600;
}

.perio-cell-toggle {
  width: 14px;
  height: 14px;
  border-radius: 3px;
  border: 1px solid rgb(209 213 219);
  background: white;
  cursor: pointer;
  transition: transform 100ms ease, background-color 100ms ease;
}

.perio-cell-toggle:hover:not(:disabled) {
  transform: scale(1.1);
}

.perio-cell-toggle:focus-visible {
  outline: none;
  box-shadow: 0 0 0 2px rgb(59 130 246);
}

.perio-cell-toggle--bop.is-on {
  background-color: rgb(239 68 68);
  border-color: rgb(239 68 68);
}

.perio-cell-toggle--plaque.is-on {
  background-color: rgb(59 130 246);
  border-color: rgb(59 130 246);
}

.perio-cell-toggle:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.perio-arch-table .tooth-row td {
  padding-top: 4px;
  padding-bottom: 4px;
}
</style>
