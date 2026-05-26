<script setup lang="ts">
/**
 * Compact popover for editing one probing site.
 *
 * Used from `PerioMetricsTable` and `PerioToothLateral`. PR-5 wires
 * the visual shell + values; the autosave + submit handler land in
 * PR-6 alongside the session composable. For now the component emits
 * a `save` event with the patched payload and the parent decides what
 * to do.
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

const { t } = useI18n()

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
  <UModal v-model="isOpen">
    <UCard>
      <template #header>
        <div class="flex items-center justify-between">
          <h3 class="text-sm font-semibold text-gray-900">
            {{ toothNumber }} · {{ siteCode }}
          </h3>
          <UButton variant="ghost" icon="i-lucide-x" size="xs" @click="isOpen = false" />
        </div>
      </template>

      <div class="grid grid-cols-2 gap-3">
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

      <template #footer>
        <div class="flex justify-end gap-2">
          <UButton variant="outline" @click="isOpen = false">Cancelar</UButton>
          <UButton @click="handleSave">{{ t('common.save') }}</UButton>
        </div>
      </template>
    </UCard>
  </UModal>
</template>
