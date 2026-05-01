<script setup lang="ts">
import { computed, ref } from 'vue'

// Slot entry into `patient.summary.actions`. `<ModuleSlot>` passes
// the slot ctx as a single `ctx` prop; we destructure the patient
// from it here. We read ``do_not_contact`` to hide the CTA and
// show the opt-out banner instead — receptionists must never
// schedule a recall against a patient flagged as no-contact.
const props = defineProps<{
  ctx: {
    patient: {
      id: string
      do_not_contact?: boolean
      status?: string
    }
  }
}>()

const { t } = useI18n()
const open = ref(false)

const patient = computed(() => props.ctx?.patient)
const doNotContact = computed(() => patient.value?.do_not_contact === true)
const isArchived = computed(() => patient.value?.status === 'archived')
const canSchedule = computed(
  () => !!patient.value?.id && !doNotContact.value && !isArchived.value
)
</script>

<template>
  <div v-if="patient?.id">
    <!-- Opt-out banner: replaces the CTA when the patient is flagged
         do_not_contact (and reuses the same surface for archived). -->
    <div
      v-if="doNotContact"
      class="alert-surface-warning rounded-token-md px-3 py-2 flex items-start gap-2"
      role="status"
    >
      <UIcon
        name="i-lucide-phone-off"
        class="w-4 h-4 mt-0.5 shrink-0"
        :style="{ color: 'var(--color-warning-accent)' }"
        aria-hidden="true"
      />
      <div class="text-sm leading-snug">
        <p class="font-medium text-default">
          {{ t('patients.doNotContact.badge') }}
        </p>
        <p class="text-subtle text-caption mt-0.5">
          {{ t('recalls.doNotContact.cannotSchedule') }}
        </p>
      </div>
    </div>

    <UButton
      v-else-if="canSchedule"
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
      v-if="canSchedule"
      v-model:open="open"
      :patient-id="patient.id"
    />
  </div>
</template>
