<script setup lang="ts">
/**
 * Modal editor for one probing site.
 *
 * Emits a partial patch through the `save` event when the dentist
 * confirms; the parent (PeriodontogramChart) routes the patch through
 * `usePeriodontogramSession.patchSite` so it joins the autosave
 * queue.
 */
import { computed, ref, watch } from 'vue'
import type { PerioSite, SiteCode } from '../types'

const props = defineProps<{
  modelValue: boolean
  toothNumber: number
  siteCode: SiteCode
  site: PerioSite | null
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  save: [
    patch: {
      probing_depth_mm?: number | null
      gingival_margin_mm?: number | null
      bleeding_on_probing?: boolean
      plaque?: boolean
      suppuration?: boolean
    }
  ]
}>()

const isOpen = computed({
  get: () => props.modelValue,
  set: (v: boolean) => emit('update:modelValue', v)
})

const pd = ref<number | null>(null)
const gm = ref<number | null>(null)
const bop = ref(false)
const plaque = ref(false)
const sup = ref(false)

watch(
  () => props.site,
  (site) => {
    pd.value = site?.probing_depth_mm ?? null
    gm.value = site?.gingival_margin_mm ?? null
    bop.value = site?.bleeding_on_probing ?? false
    plaque.value = site?.plaque ?? false
    sup.value = site?.suppuration ?? false
  },
  { immediate: true }
)

function handleSave() {
  emit('save', {
    probing_depth_mm: pd.value,
    gingival_margin_mm: gm.value,
    bleeding_on_probing: bop.value,
    plaque: plaque.value,
    suppuration: sup.value
  })
  isOpen.value = false
}
</script>

<template>
  <UModal
    :open="isOpen"
    :title="`Diente ${toothNumber} · sitio ${siteCode}`"
    @update:open="(v) => { isOpen = v }"
  >
    <template #body>
      <div class="grid grid-cols-2 gap-3 p-4">
        <UFormField label="Sondaje (mm)">
          <UInput v-model.number="pd" type="number" :min="0" :max="15" />
        </UFormField>
        <UFormField label="Margen gingival (mm)">
          <UInput v-model.number="gm" type="number" :min="-5" :max="10" />
        </UFormField>
        <UCheckbox v-model="bop" label="Sangrado" />
        <UCheckbox v-model="plaque" label="Placa" />
        <UCheckbox v-model="sup" label="Supuración" />
      </div>
    </template>
    <template #footer>
      <div class="flex justify-end gap-2 p-2">
        <UButton variant="outline" color="neutral" @click="isOpen = false">
          Cancelar
        </UButton>
        <UButton color="primary" @click="handleSave">
          Guardar
        </UButton>
      </div>
    </template>
  </UModal>
</template>
