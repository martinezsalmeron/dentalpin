<script setup lang="ts">
/**
 * SEPA metrics table for one arch.
 *
 * Renders the nine canonical rows (Implante, Movilidad, Pronóstico,
 * Furca, Sangrado, Placa, Anchura encía, Margen gingival, Profundidad
 * sondaje) across the 16 teeth in FDI order. Each cell is a button
 * that emits an edit event so the parent can open the right editor.
 *
 * Rows for site-level metrics (sangrado, placa, margen, sondaje)
 * show three sub-cells per tooth (vestibular face only — the
 * palatal/lingual face is shown on the matching arch's lower table).
 */
import { computed } from 'vue'
import type { PerioSite, PerioTooth, SiteCode } from '../types'
import { PALATAL_SITES, VESTIBULAR_SITES } from '../types'

const props = defineProps<{
  teeth: PerioTooth[]
  /** Which set of three sites we display on the per-site rows. */
  face: 'vestibular' | 'palatal' | 'lingual'
  readonly?: boolean
}>()

const emit = defineEmits<{
  editTooth: [toothNumber: number]
  editSite: [toothNumber: number, siteCode: SiteCode]
}>()

const siteCodes = computed(() =>
  props.face === 'vestibular' ? VESTIBULAR_SITES : PALATAL_SITES
)

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

function furcaText(tooth: PerioTooth): string {
  if (props.face === 'vestibular') return tooth.furcation_buccal ?? '·'
  return tooth.furcation_lingual ?? '·'
}

function mobilityText(tooth: PerioTooth): string {
  return tooth.mobility != null ? String(tooth.mobility) : '·'
}

function prognosisText(tooth: PerioTooth): string {
  if (!tooth.prognosis) return '·'
  // SEPA shorthand mapping (Bueno / Medio / Malo / Sin esperanza).
  return ({ good: 'B', fair: 'M', poor: 'D', hopeless: '✕' } as const)[tooth.prognosis]
}
</script>

<template>
  <table class="perio-metrics-table w-full text-center font-mono text-[11px] leading-tight">
    <thead>
      <tr>
        <th class="px-1 text-right font-medium text-gray-500"> </th>
        <th
          v-for="tooth in teeth"
          :key="`th-${tooth.tooth_number}`"
          class="px-1 font-medium text-gray-500"
        >
          {{ tooth.tooth_number }}
        </th>
      </tr>
    </thead>
    <tbody class="divide-y divide-gray-100">
      <tr>
        <th scope="row" class="px-1 text-right font-medium text-gray-500">Implante</th>
        <td v-for="t in teeth" :key="`imp-${t.tooth_number}`" class="px-1">
          <span v-if="t.is_implant" class="text-emerald-600" title="Implante">●</span>
          <span v-else class="text-gray-300">·</span>
        </td>
      </tr>
      <tr>
        <th scope="row" class="px-1 text-right font-medium text-gray-500">Movilidad</th>
        <td v-for="t in teeth" :key="`mob-${t.tooth_number}`" class="px-1">
          <button
            class="rounded px-1 hover:bg-gray-100 disabled:cursor-not-allowed"
            :disabled="readonly || !t.is_present"
            @click="emit('editTooth', t.tooth_number)"
          >
            {{ mobilityText(t) }}
          </button>
        </td>
      </tr>
      <tr>
        <th scope="row" class="px-1 text-right font-medium text-gray-500">Pronóstico</th>
        <td v-for="t in teeth" :key="`pron-${t.tooth_number}`" class="px-1">
          <button
            class="rounded px-1 hover:bg-gray-100 disabled:cursor-not-allowed"
            :disabled="readonly || !t.is_present"
            @click="emit('editTooth', t.tooth_number)"
          >
            {{ prognosisText(t) }}
          </button>
        </td>
      </tr>
      <tr>
        <th scope="row" class="px-1 text-right font-medium text-gray-500">Furca</th>
        <td v-for="t in teeth" :key="`fur-${t.tooth_number}`" class="px-1">
          <button
            class="rounded px-1 hover:bg-gray-100 disabled:cursor-not-allowed"
            :disabled="readonly || !t.is_present"
            @click="emit('editTooth', t.tooth_number)"
          >
            {{ furcaText(t) }}
          </button>
        </td>
      </tr>
      <tr>
        <th scope="row" class="px-1 text-right font-medium text-gray-500">Sangrado</th>
        <td v-for="t in teeth" :key="`bop-${t.tooth_number}`" class="px-1">
          <div class="flex justify-center gap-0.5">
            <button
              v-for="code in siteCodes"
              :key="`bop-${t.tooth_number}-${code}`"
              class="h-3 w-3 rounded-sm border border-gray-300 transition hover:scale-110"
              :class="siteValue(t, code)?.bleeding_on_probing ? 'bg-error-500 border-error-500' : ''"
              :disabled="readonly || !t.is_present"
              :title="`${code} sangrado`"
              @click="emit('editSite', t.tooth_number, code)"
            />
          </div>
        </td>
      </tr>
      <tr>
        <th scope="row" class="px-1 text-right font-medium text-gray-500">Placa</th>
        <td v-for="t in teeth" :key="`pi-${t.tooth_number}`" class="px-1">
          <div class="flex justify-center gap-0.5">
            <button
              v-for="code in siteCodes"
              :key="`pi-${t.tooth_number}-${code}`"
              class="h-3 w-3 rounded-sm border border-gray-300 transition hover:scale-110"
              :class="siteValue(t, code)?.plaque ? 'bg-blue-500 border-blue-500' : ''"
              :disabled="readonly || !t.is_present"
              :title="`${code} placa`"
              @click="emit('editSite', t.tooth_number, code)"
            />
          </div>
        </td>
      </tr>
      <tr>
        <th scope="row" class="px-1 text-right font-medium text-gray-500">Anchura encía</th>
        <td v-for="t in teeth" :key="`kg-${t.tooth_number}`" class="px-1">
          <button
            class="rounded px-1 hover:bg-gray-100 disabled:cursor-not-allowed"
            :disabled="readonly || !t.is_present"
            @click="emit('editTooth', t.tooth_number)"
          >
            {{ t.keratinized_gingiva_mm ?? '·' }}
          </button>
        </td>
      </tr>
      <tr>
        <th scope="row" class="px-1 text-right font-medium text-gray-500">Margen gingival</th>
        <td v-for="t in teeth" :key="`gm-${t.tooth_number}`" class="px-1">
          <div class="flex justify-center gap-0.5 tabular-nums">
            <button
              v-for="code in siteCodes"
              :key="`gm-${t.tooth_number}-${code}`"
              class="w-3 rounded hover:bg-gray-100 disabled:cursor-not-allowed"
              :disabled="readonly || !t.is_present"
              :title="`${code} margen`"
              @click="emit('editSite', t.tooth_number, code)"
            >
              {{ gmText(siteValue(t, code)) }}
            </button>
          </div>
        </td>
      </tr>
      <tr>
        <th scope="row" class="px-1 text-right font-medium text-gray-500">Sondaje</th>
        <td v-for="t in teeth" :key="`pd-${t.tooth_number}`" class="px-1">
          <div class="flex justify-center gap-0.5 tabular-nums font-medium">
            <button
              v-for="code in siteCodes"
              :key="`pd-${t.tooth_number}-${code}`"
              class="w-3 rounded hover:bg-gray-100 disabled:cursor-not-allowed"
              :disabled="readonly || !t.is_present"
              :title="`${code} sondaje`"
              @click="emit('editSite', t.tooth_number, code)"
            >
              {{ pdText(siteValue(t, code)) }}
            </button>
          </div>
        </td>
      </tr>
    </tbody>
  </table>
</template>
