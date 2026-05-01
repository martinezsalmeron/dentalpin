<script setup lang="ts">
import { computed, ref } from 'vue'

// Slot entry into `appointment.completed.followup`. Receives an
// `appointment` ctx with at least patient_id + treatment_type +
// professional_id. Emits `done` to dismiss the host modal.
interface Props {
  appointment: {
    id: string
    patient_id?: string | null
    professional_id?: string | null
    treatment_type?: string | null
  }
}
const props = defineProps<Props>()
const emit = defineEmits<{ done: [] }>()

const { t } = useI18n()
const open = ref(false)

const patientId = computed(() => props.appointment.patient_id ?? null)
const canPrompt = computed(() => !!patientId.value)

function openModal() {
  open.value = true
}

function onSaved() {
  open.value = false
  emit('done')
}

function skip() {
  emit('done')
}
</script>

<template>
  <div
    v-if="canPrompt"
    class="space-y-3"
  >
    <p class="text-default">
      {{ t('recalls.closeoutPrompt.subtitle') }}
    </p>
    <div class="flex gap-2">
      <UButton
        color="primary"
        icon="i-lucide-bell"
        @click="openModal"
      >
        {{ t('recalls.setRecall') }}
      </UButton>
      <UButton
        color="neutral"
        variant="ghost"
        @click="skip"
      >
        {{ t('recalls.closeoutPrompt.skip') }}
      </UButton>
    </div>

    <SetRecallModal
      v-if="patientId"
      v-model:open="open"
      :patient-id="patientId"
      :initial-assigned-professional-id="appointment.professional_id ?? null"
      @saved="onSaved"
    />
  </div>
</template>
