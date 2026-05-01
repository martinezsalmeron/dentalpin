<script setup lang="ts">
/**
 * Renders the post-completion follow-up modal whose body is filled
 * by every component registered into the ``appointment.completed.followup``
 * slot. Mounted once at the agenda page level so both
 * ``AppointmentQuickActions`` (dropdown) and ``AppointmentKanbanView``
 * (drag-drop) share the same UI surface.
 */
import { computed } from 'vue'

const { t } = useI18n()
const { resolve } = useModuleSlots()
const { open, appointment, dismiss } = useCompletionFollowup()

const entries = computed(() =>
  appointment.value
    ? resolve('appointment.completed.followup', { appointment: appointment.value })
    : []
)

// Hide the modal entirely when no slot entry is registered — keeps
// clinics that don't run recalls from seeing an empty dialog.
const shouldRender = computed(() => open.value && entries.value.length > 0)
</script>

<template>
  <UModal
    :open="shouldRender"
    :title="t('appointments.followup.title')"
    @update:open="(v: boolean) => { if (!v) dismiss() }"
  >
    <template #body>
      <div class="space-y-3 p-4">
        <component
          :is="entry.component"
          v-for="entry in entries"
          :key="entry.id"
          :appointment="appointment"
          @done="dismiss"
        />
      </div>
    </template>
    <template #footer>
      <div class="flex justify-end gap-2 p-2">
        <UButton
          color="neutral"
          variant="ghost"
          @click="dismiss"
        >
          {{ t('actions.close') }}
        </UButton>
      </div>
    </template>
  </UModal>
</template>
