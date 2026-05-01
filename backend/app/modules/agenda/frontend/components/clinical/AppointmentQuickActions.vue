<script setup lang="ts">
import type { Appointment } from '~~/app/types'
import type { TransitionDescriptor } from '../../composables/useAppointmentStatus'

const props = defineProps<{
  appointment: Appointment
  /** Compact icon-only button (for calendar/daily cards). Default: icon button. */
  dense?: boolean
}>()

const emit = defineEmits<{
  transitioned: [appointment: Appointment, to: TransitionDescriptor['to']]
  failed: [err: unknown]
}>()

const { t } = useI18n()
const toast = useToast()
const { transition } = useAppointments()
const { nextTransitions, statusIcon } = useAppointmentStatus()

const isBusy = ref(false)
const pendingDescriptor = ref<TransitionDescriptor | null>(null)
const pendingNote = ref('')

// Post-completion follow-up slot. After a successful transition to
// "completed", any sibling module registered into the
// `appointment.completed.followup` slot (e.g. `recalls` "Schedule a
// recall?" prompt, issue #62) renders inside this modal.
const followupOpen = ref(false)
const followupAppointment = ref<Appointment | null>(null)
const { resolve } = useModuleSlots()
const followupEntries = computed(() =>
  followupAppointment.value
    ? resolve('appointment.completed.followup', { appointment: followupAppointment.value })
    : []
)

const transitions = computed(() => nextTransitions(props.appointment.status))
const hasActions = computed(() => transitions.value.length > 0)

function dropdownItems() {
  return transitions.value.map((tr, idx) => ({
    label: t(tr.labelKey),
    icon: tr.icon,
    color: tr.destructive ? ('error' as const) : undefined,
    onSelect: (e?: Event) => {
      e?.preventDefault?.()
      if (tr.destructive) {
        pendingDescriptor.value = tr
        pendingNote.value = ''
      } else {
        void runTransition(tr)
      }
    },
    kbd: idx === 0 ? ['enter'] : undefined
  }))
}

async function runTransition(tr: TransitionDescriptor, note?: string) {
  if (isBusy.value) return
  isBusy.value = true
  try {
    await transition(props.appointment.id, tr.to, note?.trim() || undefined)
    emit('transitioned', props.appointment, tr.to)
    if (tr.to === 'completed') {
      followupAppointment.value = { ...props.appointment, status: 'completed' }
      // eslint-disable-next-line no-console
      console.debug('[appointment.completed.followup] entries=', followupEntries.value.length, followupEntries.value.map(e => e.id))
      followupOpen.value = followupEntries.value.length > 0
    }
  } catch (err) {
    toast.add({ title: t('appointments.transitionFailed'), color: 'error' })
    emit('failed', err)
  } finally {
    isBusy.value = false
  }
}

function closeFollowup() {
  followupOpen.value = false
  followupAppointment.value = null
}

function confirmPending() {
  if (!pendingDescriptor.value) return
  const tr = pendingDescriptor.value
  const note = pendingNote.value
  pendingDescriptor.value = null
  void runTransition(tr, note)
}

function cancelPending() {
  pendingDescriptor.value = null
  pendingNote.value = ''
}

const confirmMessage = computed(() => {
  if (!pendingDescriptor.value) return ''
  if (pendingDescriptor.value.to === 'no_show') {
    return t('appointments.confirmNoShowMessage')
  }
  return t('appointments.confirmCancelMessage')
})
</script>

<template>
  <UDropdownMenu
    v-if="hasActions"
    :items="dropdownItems()"
    :ui="{ content: 'min-w-56' }"
  >
    <UButton
      :icon="props.dense ? statusIcon(props.appointment.status) : 'i-lucide-chevrons-right'"
      :size="props.dense ? 'xs' : 'sm'"
      color="neutral"
      variant="ghost"
      :aria-label="t('appointments.transitions.checked_in')"
      :loading="isBusy"
      :disabled="isBusy"
      @click.stop
    />
  </UDropdownMenu>

  <UModal
    :open="!!pendingDescriptor"
    :title="t('appointments.confirmTransitionTitle')"
    @update:open="(v: boolean) => { if (!v) cancelPending() }"
  >
    <template #body>
      <div class="space-y-3 p-4">
        <p class="text-sm text-default">{{ confirmMessage }}</p>
        <UFormField :label="t('appointments.noteLabel')">
          <UTextarea v-model="pendingNote" :rows="2" :maxlength="500" />
        </UFormField>
      </div>
    </template>
    <template #footer>
      <div class="flex justify-end gap-2 p-2">
        <UButton color="neutral" variant="ghost" @click="cancelPending">
          {{ t('actions.cancel') }}
        </UButton>
        <UButton color="error" :loading="isBusy" @click="confirmPending">
          {{ pendingDescriptor ? t(pendingDescriptor.labelKey) : '' }}
        </UButton>
      </div>
    </template>
  </UModal>

  <!-- Post-completion follow-up slot. Renders nothing when no module
       has registered into `appointment.completed.followup`. -->
  <UModal
    :open="followupOpen"
    :title="t('appointments.followup.title')"
    @update:open="(v: boolean) => { if (!v) closeFollowup() }"
  >
    <template #body>
      <div class="space-y-3 p-4">
        <component
          :is="entry.component"
          v-for="entry in followupEntries"
          :key="entry.id"
          :appointment="followupAppointment"
          @done="closeFollowup"
        />
      </div>
    </template>
    <template #footer>
      <div class="flex justify-end gap-2 p-2">
        <UButton color="neutral" variant="ghost" @click="closeFollowup">
          {{ t('actions.close') }}
        </UButton>
      </div>
    </template>
  </UModal>
</template>
