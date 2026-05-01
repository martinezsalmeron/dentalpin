<script setup lang="ts">
import { ref } from 'vue'

// Slot entry into `patient.summary.actions`. `<ModuleSlot>` passes
// the slot ctx as a single `ctx` prop; we destructure the patient
// from it here.
const props = defineProps<{
  ctx: { patient: { id: string } }
}>()

const { t } = useI18n()
const open = ref(false)
</script>

<template>
  <div v-if="props.ctx?.patient?.id">
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
      :patient-id="props.ctx.patient.id"
    />
  </div>
</template>
