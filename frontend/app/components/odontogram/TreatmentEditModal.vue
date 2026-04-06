<script setup lang="ts">
import type { Surface, Treatment, TreatmentStatus } from '~/types'
import { TREATMENT_COLORS, isSurfaceTreatment, getAllowedStatusesForTreatment } from '~/config/odontogramConstants'

const props = defineProps<{
  treatment: Treatment | null
  open: boolean
}>()

const emit = defineEmits<{
  'update:open': [value: boolean]
  'update': [treatmentId: string, data: { status?: TreatmentStatus, surfaces?: Surface[], notes?: string }]
  'delete': [treatmentId: string]
  'perform': [treatmentId: string]
}>()

const { t } = useI18n()

// Local state
const status = ref<TreatmentStatus>('performed')
const selectedSurfaces = ref<Surface[]>([])
const notes = ref('')

// All surfaces
const allSurfaces: Surface[] = ['M', 'D', 'O', 'V', 'L']

// Is surface treatment
const isSurfaceType = computed(() => {
  if (!props.treatment) return false
  return isSurfaceTreatment(props.treatment.treatment_type)
})

// Sync local state with treatment prop
watch(() => props.treatment, (treatment) => {
  if (treatment) {
    status.value = treatment.status
    selectedSurfaces.value = [...(treatment.surfaces || [])]
    notes.value = treatment.notes || ''
  }
}, { immediate: true })

// Treatment label
const treatmentLabel = computed(() => {
  if (!props.treatment) return ''
  return t(`odontogram.treatments.types.${props.treatment.treatment_type}`, props.treatment.treatment_type)
})

// Treatment color
const treatmentColor = computed(() => {
  if (!props.treatment) return '#9CA3AF'
  return TREATMENT_COLORS[props.treatment.treatment_type] || '#9CA3AF'
})

// All status options
const allStatusOptions = [
  { value: 'preexisting' as TreatmentStatus, label: () => t('odontogram.status.preexisting'), color: 'neutral' },
  { value: 'planned' as TreatmentStatus, label: () => t('odontogram.status.planned'), color: 'warning' },
  { value: 'performed' as TreatmentStatus, label: () => t('odontogram.status.performed'), color: 'success' }
]

// Status options filtered by treatment type
const statusOptions = computed(() => {
  if (!props.treatment) return allStatusOptions.map(o => ({ ...o, label: o.label() }))

  const allowedStatuses = getAllowedStatusesForTreatment(props.treatment.treatment_type)
  return allStatusOptions
    .filter(opt => allowedStatuses.includes(opt.value))
    .map(o => ({ ...o, label: o.label() }))
})

function toggleSurface(surface: Surface) {
  const index = selectedSurfaces.value.indexOf(surface)
  if (index === -1) {
    selectedSurfaces.value.push(surface)
  } else {
    selectedSurfaces.value.splice(index, 1)
  }
}

function handleSave() {
  if (!props.treatment) return

  const data: { status?: TreatmentStatus, surfaces?: Surface[], notes?: string } = {}

  if (status.value !== props.treatment.status) {
    data.status = status.value
  }

  if (isSurfaceType.value && JSON.stringify(selectedSurfaces.value.sort()) !== JSON.stringify((props.treatment.surfaces || []).sort())) {
    data.surfaces = selectedSurfaces.value
  }

  if (notes.value !== (props.treatment.notes || '')) {
    data.notes = notes.value
  }

  if (Object.keys(data).length > 0) {
    emit('update', props.treatment.id, data)
  } else {
    // No changes, just close
    emit('update:open', false)
  }
}

function handleDelete() {
  if (!props.treatment) return
  emit('delete', props.treatment.id)
}

function handleMarkPerformed() {
  if (!props.treatment) return
  emit('perform', props.treatment.id)
}

function handleClose() {
  emit('update:open', false)
}
</script>

<template>
  <UModal
    :open="open"
    @update:open="handleClose"
  >
    <template #content>
      <UCard>
        <template #header>
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-3">
              <span
                class="w-4 h-4 rounded-full flex-shrink-0"
                :style="{ backgroundColor: treatmentColor }"
              />
              <span class="font-semibold text-gray-900 dark:text-white">{{ treatmentLabel }}</span>
              <UBadge
                v-if="treatment"
                :color="status === 'performed' ? 'success' : status === 'planned' ? 'warning' : 'neutral'"
                variant="subtle"
                size="xs"
              >
                {{ t('odontogram.tooth') }} {{ treatment.tooth_number }}
              </UBadge>
            </div>
            <UButton
              icon="i-lucide-x"
              color="neutral"
              variant="ghost"
              size="sm"
              @click="handleClose"
            />
          </div>
        </template>

        <div
          v-if="treatment"
          class="space-y-6"
        >
          <!-- Status selection -->
          <div>
            <label class="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">
              {{ t('odontogram.treatments.selectStatus') }}
            </label>
            <div class="flex gap-2">
              <UButton
                v-for="option in statusOptions"
                :key="option.value"
                :color="status === option.value ? option.color : 'neutral'"
                :variant="status === option.value ? 'solid' : 'outline'"
                size="sm"
                @click="status = option.value as TreatmentStatus"
              >
                {{ option.label }}
              </UButton>
            </div>
          </div>

          <!-- Surface selection (only for surface treatments) -->
          <div v-if="isSurfaceType">
            <label class="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">
              {{ t('odontogram.selectSurfaces') }}
            </label>
            <div class="flex gap-2 flex-wrap">
              <UButton
                v-for="surface in allSurfaces"
                :key="surface"
                :color="selectedSurfaces.includes(surface) ? 'primary' : 'neutral'"
                :variant="selectedSurfaces.includes(surface) ? 'solid' : 'outline'"
                size="sm"
                @click="toggleSurface(surface)"
              >
                {{ surface }} - {{ t(`odontogram.surfaces.${surface}`) }}
              </UButton>
            </div>
            <p
              v-if="selectedSurfaces.length > 0"
              class="text-xs text-gray-500 mt-2"
            >
              {{ selectedSurfaces.length }} {{ t('odontogram.surfacesSelected') }}
            </p>
          </div>

          <!-- Notes -->
          <div>
            <label class="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">
              {{ t('patients.notes') }}
            </label>
            <UTextarea
              v-model="notes"
              :placeholder="t('patients.notes')"
              :rows="3"
            />
          </div>

          <!-- Quick action: Mark as performed -->
          <div
            v-if="treatment.status === 'planned'"
            class="pt-4 border-t border-gray-200 dark:border-gray-700"
          >
            <UButton
              color="success"
              variant="soft"
              block
              icon="i-lucide-check"
              @click="handleMarkPerformed"
            >
              {{ t('odontogram.treatments.markPerformed') }}
            </UButton>
          </div>
        </div>

        <template #footer>
          <div class="flex justify-between w-full">
            <UButton
              color="error"
              variant="ghost"
              icon="i-lucide-trash-2"
              @click="handleDelete"
            >
              {{ t('common.delete') }}
            </UButton>
            <div class="flex gap-2">
              <UButton
                color="neutral"
                variant="outline"
                @click="handleClose"
              >
                {{ t('common.cancel') }}
              </UButton>
              <UButton
                color="primary"
                @click="handleSave"
              >
                {{ t('common.save') }}
              </UButton>
            </div>
          </div>
        </template>
      </UCard>
    </template>
  </UModal>
</template>
