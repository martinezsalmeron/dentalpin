<script setup lang="ts">
import { ref, watch } from 'vue'
import type { RecallReason, RecallPriority, Recall } from '../composables/useRecalls'

interface Props {
  open: boolean
  patientId: string
  /** Pre-fill from a treatment-plan / odontogram action. */
  initialReason?: RecallReason
  initialNote?: string
  initialPriority?: RecallPriority
  initialAssignedProfessionalId?: string | null
  initialDueMonth?: string  // YYYY-MM-01
  initialTreatmentId?: string | null
  initialTreatmentCategoryKey?: string | null
}

const props = withDefaults(defineProps<Props>(), {
  initialReason: 'hygiene',
  initialPriority: 'normal'
})

const emit = defineEmits<{
  'update:open': [value: boolean]
  'saved': [recall: Recall]
}>()

const { t } = useI18n()
const toast = useToast()
const recallsApi = useRecalls()

const isSubmitting = ref(false)
const reason = ref<RecallReason>(props.initialReason)
const priority = ref<RecallPriority>(props.initialPriority)
const dueMonth = ref<string>(props.initialDueMonth ?? defaultDueMonth())
const dueDate = ref<string>('')
const note = ref<string>(props.initialNote ?? '')
const assignedProfessionalId = ref<string | null>(props.initialAssignedProfessionalId ?? null)

function defaultDueMonth(): string {
  const today = new Date()
  // Next month, day 1.
  const year = today.getFullYear()
  const month = today.getMonth() + 2  // +1 next month, +1 because Date is 0-indexed when re-creating
  const d = new Date(year, month - 1, 1)
  const yyyy = d.getFullYear()
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  return `${yyyy}-${mm}-01`
}

watch(() => props.open, (v) => {
  if (!v) return
  reason.value = props.initialReason
  priority.value = props.initialPriority
  dueMonth.value = props.initialDueMonth ?? defaultDueMonth()
  dueDate.value = ''
  note.value = props.initialNote ?? ''
  assignedProfessionalId.value = props.initialAssignedProfessionalId ?? null
})

const reasonOptions = computed(() =>
  (['hygiene', 'checkup', 'ortho_review', 'implant_review', 'post_op', 'treatment_followup', 'other'] as RecallReason[])
    .map(r => ({ value: r, label: t(`recalls.reasons.${r}`) }))
)

const priorityOptions = computed(() =>
  (['low', 'normal', 'high'] as RecallPriority[]).map(p => ({
    value: p,
    label: t(`recalls.priority.${p}`)
  }))
)

async function save() {
  if (isSubmitting.value) return
  isSubmitting.value = true
  try {
    const month = dueMonth.value || defaultDueMonth()
    const monthDay1 = month.length === 7 ? `${month}-01` : month
    const res = await recallsApi.create({
      patient_id: props.patientId,
      due_month: monthDay1,
      due_date: dueDate.value || null,
      reason: reason.value,
      reason_note: note.value || null,
      priority: priority.value,
      assigned_professional_id: assignedProfessionalId.value || null,
      linked_treatment_id: props.initialTreatmentId ?? null,
      linked_treatment_category_key: props.initialTreatmentCategoryKey ?? null
    })
    toast.add({ title: t('common.success'), color: 'success' })
    emit('saved', res.data)
    emit('update:open', false)
  } catch (err: unknown) {
    toast.add({
      title: t('common.error'),
      description: (err as { data?: { detail?: string } })?.data?.detail ?? '',
      color: 'error'
    })
  } finally {
    isSubmitting.value = false
  }
}

function close() {
  emit('update:open', false)
}
</script>

<template>
  <UModal
    :open="open"
    :title="t('recalls.modal.title')"
    @update:open="(v: boolean) => emit('update:open', v)"
  >
    <template #body>
      <div class="space-y-3 p-4">
        <UFormField :label="t('recalls.modal.reason')">
          <USelectMenu
            v-model="reason"
            :items="reasonOptions"
            value-key="value"
            label-key="label"
          />
        </UFormField>

        <UFormField :label="t('recalls.modal.month')">
          <UInput
            v-model="dueMonth"
            type="month"
          />
        </UFormField>

        <UFormField :label="t('recalls.modal.preciseDate')">
          <UInput
            v-model="dueDate"
            type="date"
          />
        </UFormField>

        <UFormField :label="t('recalls.modal.priority')">
          <USelectMenu
            v-model="priority"
            :items="priorityOptions"
            value-key="value"
            label-key="label"
          />
        </UFormField>

        <UFormField :label="t('recalls.modal.note')">
          <UTextarea
            v-model="note"
            :rows="3"
            :maxlength="500"
          />
        </UFormField>
      </div>
    </template>
    <template #footer>
      <div class="flex justify-end gap-2 p-2">
        <UButton
          color="neutral"
          variant="ghost"
          :disabled="isSubmitting"
          @click="close"
        >
          {{ t('actions.cancel') }}
        </UButton>
        <UButton
          color="primary"
          :loading="isSubmitting"
          @click="save"
        >
          {{ t('recalls.actions.save') }}
        </UButton>
      </div>
    </template>
  </UModal>
</template>
