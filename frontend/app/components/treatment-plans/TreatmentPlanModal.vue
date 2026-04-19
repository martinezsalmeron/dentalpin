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
const auth = useAuth()
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

// Show/hide notes section
const showNotes = ref(false)

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
        // Show notes section if there are existing notes
        showNotes.value = !!(planDetail.diagnosis_notes || planDetail.internal_notes)
      } else {
        // Auto-select current user if they're a professional
        const currentUserId = auth.user.value?.id
        const isCurrentUserProfessional = professionals.value.some(p => p.id === currentUserId)

        form.value = {
          patient_id: props.patientId,
          title: '',
          assigned_professional_id: isCurrentUserProfessional ? currentUserId : undefined,
          diagnosis_notes: '',
          internal_notes: ''
        }
        showNotes.value = false
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

function closeModal() {
  isOpen.value = false
}
</script>

<template>
  <UModal
    v-model:open="isOpen"
    :ui="{ width: 'sm:max-w-lg' }"
  >
    <template #content>
      <UCard>
        <!-- Header -->
        <template #header>
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-3">
              <div class="flex h-10 w-10 items-center justify-center rounded-lg bg-[var(--color-primary-soft)]">
                <UIcon
                  name="i-lucide-clipboard-list"
                  class="h-5 w-5 text-primary-accent"
                />
              </div>
              <div>
                <h2 class="text-h1 text-default text-default">
                  {{ isEditing ? t('treatmentPlans.edit') : t('treatmentPlans.create') }}
                </h2>
                <p class="text-sm text-muted">
                  {{ t('treatmentPlans.modal.subtitle') }}
                </p>
              </div>
            </div>
            <UButton
              variant="ghost"
              color="neutral"
              icon="i-lucide-x"
              size="sm"
              @click="closeModal"
            />
          </div>
        </template>

        <!-- Body -->
        <div class="space-y-5">
          <form
            class="space-y-5"
            @submit.prevent="handleSubmit"
          >
            <!-- Main info section -->
            <div class="space-y-4">
              <!-- Title -->
              <UFormField :label="t('treatmentPlans.fields.title')">
                <UInput
                  v-model="form.title"
                  :placeholder="t('treatmentPlans.fields.titlePlaceholder')"
                  size="lg"
                  autofocus
                />
              </UFormField>

              <!-- Professional -->
              <UFormField :label="t('treatmentPlans.fields.assignedProfessional')">
                <USelect
                  v-model="form.assigned_professional_id"
                  :items="professionalOptions"
                  :placeholder="t('treatmentPlans.fields.selectProfessional')"
                  value-key="value"
                  size="lg"
                />
              </UFormField>
            </div>

            <!-- Notes section (collapsible) -->
            <div class="border-t border-default pt-4">
              <button
                type="button"
                class="flex w-full items-center justify-between text-sm font-medium text-muted hover:text-default dark:text-subtle dark:hover:text-white"
                @click="showNotes = !showNotes"
              >
                <span class="flex items-center gap-2">
                  <UIcon
                    name="i-lucide-file-text"
                    class="h-4 w-4"
                  />
                  {{ t('treatmentPlans.modal.additionalNotes') }}
                </span>
                <UIcon
                  :name="showNotes ? 'i-lucide-chevron-up' : 'i-lucide-chevron-down'"
                  class="h-4 w-4"
                />
              </button>

              <Transition
                enter-active-class="transition duration-200 ease-out"
                enter-from-class="opacity-0 -translate-y-2"
                enter-to-class="opacity-100 translate-y-0"
                leave-active-class="transition duration-150 ease-in"
                leave-from-class="opacity-100 translate-y-0"
                leave-to-class="opacity-0 -translate-y-2"
              >
                <div
                  v-show="showNotes"
                  class="mt-4 space-y-4"
                >
                  <UFormField :label="t('treatmentPlans.fields.diagnosisNotes')">
                    <UTextarea
                      v-model="form.diagnosis_notes"
                      :rows="2"
                      :placeholder="t('treatmentPlans.fields.diagnosisNotesPlaceholder')"
                    />
                  </UFormField>

                  <UFormField :label="t('treatmentPlans.fields.internalNotes')">
                    <UTextarea
                      v-model="form.internal_notes"
                      :rows="2"
                      :placeholder="t('treatmentPlans.fields.internalNotesPlaceholder')"
                    />
                  </UFormField>
                </div>
              </Transition>
            </div>
          </form>

          <!-- Quick info -->
          <div class="rounded-token-md alert-surface-info px-3 py-2">
            <div class="flex gap-2">
              <UIcon
                name="i-lucide-lightbulb"
                class="mt-0.5 h-4 w-4 flex-shrink-0 text-info-accent"
              />
              <p class="text-sm text-info">
                {{ t('treatmentPlans.modal.quickTip') }}
              </p>
            </div>
          </div>
        </div>

        <!-- Footer -->
        <template #footer>
          <div class="flex justify-end gap-3">
            <UButton
              variant="outline"
              color="neutral"
              @click="closeModal"
            >
              {{ t('actions.cancel') }}
            </UButton>
            <UButton
              :loading="loading"
              icon="i-lucide-plus"
              @click="handleSubmit"
            >
              {{ isEditing ? t('actions.save') : t('treatmentPlans.modal.createButton') }}
            </UButton>
          </div>
        </template>
      </UCard>
    </template>
  </UModal>
</template>
