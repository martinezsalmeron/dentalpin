<script setup lang="ts">
import { ref } from 'vue'

// Slot entry rendered into `patient.summary.actions`. Receives a
// `patient` ctx prop set by `<ModuleSlot>` in `PatientSummaryHero`.
interface Props {
  patient: { id: string }
}
defineProps<Props>()

const { t } = useI18n()
const open = ref(false)
</script>

<template>
  <div>
    <UButton
      color="primary"
      variant="soft"
      icon="i-lucide-bell"
      size="sm"
      class="w-full"
      @click="open = true"
    >
      {{ t('recalls.setRecall') }}
    </UButton>

    <SetRecallModal
      v-model:open="open"
      :patient-id="patient.id"
    />
  </div>
</template>
