<script setup lang="ts">
import type { TreatmentPlan, TreatmentPlanCreate, TreatmentPlanUpdate } from '~/types'

const props = defineProps<{
  modelValue: boolean
  plan?: TreatmentPlan | null
  patientId: string
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'saved', plan: TreatmentPlan): void
}>()

const { t } = useI18n()
const { createPlan, updatePlan, loading } = useTreatmentPlans()
const { professionals, fetchProfessionals } = useProfessionals()

const isOpen = computed({
  get: () => props.modelValue,
  set: value => emit('update:modelValue', value)
})

const isEditing = computed(() => !!props.plan)

const form = ref<TreatmentPlanCreate | TreatmentPlanUpdate>({
  patient_id: props.patientId,
  title: '',
  assigned_professional_id: undefined,
  diagnosis_notes: '',
  internal_notes: ''
})

// Reset form when modal opens
watch(
  () => props.modelValue,
  async (open) => {
    if (open) {
      await fetchProfessionals()

      if (props.plan) {
        const planDetail = props.plan as TreatmentPlan & { diagnosis_notes?: string, internal_notes?: string }
        form.value = {
          title: props.plan.title || '',
          assigned_professional_id: props.plan.assigned_professional_id || undefined,
          diagnosis_notes: planDetail.diagnosis_notes || '',
          internal_notes: planDetail.internal_notes || ''
        }
      } else {
        form.value = {
          patient_id: props.patientId,
          title: '',
          assigned_professional_id: undefined,
          diagnosis_notes: '',
          internal_notes: ''
        }
      }
    }
  }
)

const professionalOptions = computed(() => {
  return professionals.value.map(p => ({
    label: `${p.first_name} ${p.last_name}`,
    value: p.id
  }))
})

async function handleSubmit() {
  let result: TreatmentPlan | null = null

  if (isEditing.value && props.plan) {
    result = await updatePlan(props.plan.id, form.value as TreatmentPlanUpdate)
  } else {
    result = await createPlan(form.value as TreatmentPlanCreate)
  }

  if (result) {
    emit('saved', result)
    isOpen.value = false
  }
}
</script>

<template>
  <UModal v-model:open="isOpen">
    <template #header>
      <h3 class="text-lg font-semibold">
        {{ isEditing ? t('treatmentPlans.edit') : t('treatmentPlans.create') }}
      </h3>
    </template>

    <template #body>
      <form
        class="space-y-4"
        @submit.prevent="handleSubmit"
      >
        <UFormField :label="t('treatmentPlans.fields.title')">
          <UInput
            v-model="form.title"
            :placeholder="t('treatmentPlans.fields.titlePlaceholder')"
          />
        </UFormField>

        <UFormField :label="t('treatmentPlans.fields.assignedProfessional')">
          <USelect
            v-model="form.assigned_professional_id"
            :items="professionalOptions"
            :placeholder="t('treatmentPlans.fields.selectProfessional')"
            value-key="value"
          />
        </UFormField>

        <UFormField :label="t('treatmentPlans.fields.diagnosisNotes')">
          <UTextarea
            v-model="form.diagnosis_notes"
            :rows="3"
            :placeholder="t('treatmentPlans.fields.diagnosisNotesPlaceholder')"
          />
        </UFormField>

        <UFormField :label="t('treatmentPlans.fields.internalNotes')">
          <UTextarea
            v-model="form.internal_notes"
            :rows="3"
            :placeholder="t('treatmentPlans.fields.internalNotesPlaceholder')"
          />
        </UFormField>
      </form>
    </template>

    <template #footer>
      <div class="flex justify-end gap-2">
        <UButton
          color="gray"
          variant="ghost"
          @click="isOpen = false"
        >
          {{ t('actions.cancel') }}
        </UButton>
        <UButton
          color="primary"
          :loading="loading"
          @click="handleSubmit"
        >
          {{ isEditing ? t('actions.save') : t('actions.create') }}
        </UButton>
      </div>
    </template>
  </UModal>
</template>
