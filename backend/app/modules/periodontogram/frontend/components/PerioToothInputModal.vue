<script setup lang="ts">
/**
 * Tooth-level editor.
 *
 * Mobility (0–3 Miller), prognosis (good/fair/poor/hopeless), furcation
 * (0/I/II/III on both buccal and lingual roots — molars only), and
 * keratinized gingiva width. The form mirrors the values currently
 * on the tooth row; emits a partial patch on save.
 */
import { computed, ref, watch } from 'vue'
import type { Furcation, PerioTooth, Prognosis } from '../types'

const props = defineProps<{
  modelValue: boolean
  tooth: PerioTooth | null
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  save: [
    patch: {
      is_present?: boolean
      is_implant?: boolean
      mobility?: number | null
      prognosis?: Prognosis | null
      furcation_buccal?: Furcation | null
      furcation_lingual?: Furcation | null
      keratinized_gingiva_mm?: number | null
    }
  ]
}>()

const isOpen = computed({
  get: () => props.modelValue,
  set: (v: boolean) => emit('update:modelValue', v)
})

const isPresent = ref(true)
const isImplant = ref(false)
const mobility = ref<number | null>(null)
const prognosis = ref<Prognosis | null>(null)
const furcaB = ref<Furcation | null>(null)
const furcaL = ref<Furcation | null>(null)
const kg = ref<number | null>(null)

watch(
  () => props.tooth,
  (tooth) => {
    isPresent.value = tooth?.is_present ?? true
    isImplant.value = tooth?.is_implant ?? false
    mobility.value = tooth?.mobility ?? null
    prognosis.value = tooth?.prognosis ?? null
    furcaB.value = tooth?.furcation_buccal ?? null
    furcaL.value = tooth?.furcation_lingual ?? null
    kg.value = tooth?.keratinized_gingiva_mm ?? null
  },
  { immediate: true }
)

const isMolar = computed(() => {
  if (!props.tooth) return false
  const pos = props.tooth.tooth_number % 10
  return pos >= 6 // 16/17/18, 26/27/28, etc.
})

const prognosisOptions = [
  { value: 'good', label: 'B — Bueno' },
  { value: 'fair', label: 'M — Medio' },
  { value: 'poor', label: 'D — Dudoso' },
  { value: 'hopeless', label: '✕ — Sin esperanza' }
] as const

const furcaOptions = [
  { value: '0', label: '0 — Sin furca' },
  { value: 'I', label: 'I' },
  { value: 'II', label: 'II' },
  { value: 'III', label: 'III' }
] as const

function handleSave() {
  emit('save', {
    is_present: isPresent.value,
    is_implant: isImplant.value,
    mobility: mobility.value,
    prognosis: prognosis.value,
    furcation_buccal: isMolar.value ? furcaB.value : null,
    furcation_lingual: isMolar.value ? furcaL.value : null,
    keratinized_gingiva_mm: kg.value
  })
  isOpen.value = false
}
</script>

<template>
  <UModal v-model="isOpen">
    <UCard v-if="tooth">
      <template #header>
        <div class="flex items-center justify-between">
          <h3 class="text-sm font-semibold text-gray-900">
            Diente {{ tooth.tooth_number }}
          </h3>
          <UButton variant="ghost" icon="i-lucide-x" size="xs" @click="isOpen = false" />
        </div>
      </template>

      <div class="space-y-3">
        <div class="flex items-center gap-4">
          <UCheckbox v-model="isPresent" label="Presente" />
          <UCheckbox v-model="isImplant" label="Implante" />
        </div>

        <div class="grid grid-cols-2 gap-3">
          <UFormField label="Movilidad (0–3)">
            <UInput v-model.number="mobility" type="number" :min="0" :max="3" />
          </UFormField>
          <UFormField label="Anchura encía (mm)">
            <UInput v-model.number="kg" type="number" :min="0" :max="20" />
          </UFormField>
        </div>

        <UFormField label="Pronóstico">
          <USelect v-model="prognosis" :items="prognosisOptions" placeholder="Sin valorar" />
        </UFormField>

        <div v-if="isMolar" class="grid grid-cols-2 gap-3">
          <UFormField label="Furca vestibular">
            <USelect v-model="furcaB" :items="furcaOptions" placeholder="—" />
          </UFormField>
          <UFormField label="Furca lingual/palatina">
            <USelect v-model="furcaL" :items="furcaOptions" placeholder="—" />
          </UFormField>
        </div>
      </div>

      <template #footer>
        <div class="flex justify-end gap-2">
          <UButton variant="outline" @click="isOpen = false">Cancelar</UButton>
          <UButton @click="handleSave">Guardar</UButton>
        </div>
      </template>
    </UCard>
  </UModal>
</template>
