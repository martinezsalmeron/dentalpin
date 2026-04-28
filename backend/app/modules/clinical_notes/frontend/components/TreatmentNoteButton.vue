<script setup lang="ts">
/**
 * TreatmentNoteButton — small note action attached to every Treatment row
 * shown in the odontogram conditions list and the treatment-plan rows.
 *
 * Mounted via the ``odontogram.condition.actions`` slot. Receives
 * ``ctx.treatmentId`` (and optional toothNumber/status). Click opens a
 * popover with the latest treatment notes + an inline composer.
 */

import type { ClinicalNote, RecentNoteEntry } from '~~/app/types'

const props = defineProps<{
  ctx: {
    treatmentId: string
    toothNumber?: number | null
    status?: string
  }
}>()

const { t } = useI18n()
const { can } = usePermissions()
const {
  listForOwner,
  createNote,
  updateNote,
  deleteNote
} = useClinicalNotes()
const { user } = useAuth()

const open = ref(false)
const notes = ref<ClinicalNote[]>([])
const loading = ref(false)
const composerOpen = ref(false)
const editingId = ref<string | null>(null)
const composerBody = ref('')
const saving = ref(false)

const canRead = computed(() => can('clinical_notes.notes.read'))
const canWrite = computed(() => can('clinical_notes.notes.write'))

async function loadCount() {
  if (!canRead.value) return
  try {
    notes.value = await listForOwner('treatment', props.ctx.treatmentId)
  } catch {
    notes.value = []
  }
}

async function refreshFull() {
  loading.value = true
  try {
    notes.value = await listForOwner('treatment', props.ctx.treatmentId)
  } finally {
    loading.value = false
  }
}

function asEntry(note: ClinicalNote): RecentNoteEntry {
  return {
    id: note.id,
    note_type: note.note_type,
    owner_type: note.owner_type,
    owner_id: note.owner_id,
    tooth_number: note.tooth_number,
    body: note.body,
    created_at: note.created_at,
    updated_at: note.updated_at,
    author: { id: note.author_id, full_name: null, email: null },
    linked: { kind: 'treatment', id: note.owner_id, label: null, tooth_number: null },
    attachments: note.attachments
  }
}

function handleOpen(value: boolean) {
  open.value = value
  if (value) refreshFull()
}

function startNew() {
  editingId.value = null
  composerBody.value = ''
  composerOpen.value = true
}

function startEdit(entry: RecentNoteEntry) {
  editingId.value = entry.id
  composerBody.value = entry.body
  composerOpen.value = true
}

async function handleSubmit({ body }: { body: string }) {
  saving.value = true
  try {
    if (editingId.value) {
      await updateNote(editingId.value, body)
    } else {
      await createNote({
        note_type: 'treatment',
        owner_type: 'treatment',
        owner_id: props.ctx.treatmentId,
        body
      })
    }
    composerOpen.value = false
    editingId.value = null
    composerBody.value = ''
    await refreshFull()
  } finally {
    saving.value = false
  }
}

async function handleDelete(entry: RecentNoteEntry) {
  const ok = await deleteNote(entry.id)
  if (ok) await refreshFull()
}

function canEditEntry(entry: RecentNoteEntry): boolean {
  return canWrite.value && !!entry.author?.id && entry.author.id === user.value?.id
}

const visibleCount = computed(() => notes.value.length)

watch(() => props.ctx?.treatmentId, loadCount, { immediate: true })
</script>

<template>
  <UPopover
    v-if="canRead"
    v-model:open="open"
    :ui="{ content: 'w-[min(28rem,90vw)]' }"
    @update:open="handleOpen"
  >
    <UButton
      :icon="visibleCount > 0 ? 'i-lucide-message-square-text' : 'i-lucide-message-square-plus'"
      size="xs"
      variant="ghost"
      :color="visibleCount > 0 ? 'success' : 'neutral'"
      :aria-label="t('clinicalNotes.treatmentButton.aria', { n: visibleCount })"
      :class="{ 'font-medium': visibleCount > 0 }"
    >
      <span
        v-if="visibleCount > 0"
        class="ml-1 text-caption tnum"
      >{{ visibleCount }}</span>
    </UButton>
    <template #content>
      <div class="p-3 space-y-3">
        <header class="flex items-center justify-between">
          <h4 class="font-medium text-sm">
            {{ t('clinicalNotes.treatmentButton.title') }}
            <span
              v-if="ctx?.toothNumber"
              class="text-caption text-muted ml-1"
            >· {{ t('clinicalNotes.linked.tooth', { n: ctx.toothNumber }) }}</span>
          </h4>
          <UButton
            v-if="canWrite && !composerOpen"
            size="xs"
            variant="soft"
            color="primary"
            icon="i-lucide-plus"
            @click="startNew"
          >
            {{ t('clinicalNotes.treatmentButton.add') }}
          </UButton>
        </header>

        <NoteComposer
          v-if="composerOpen && canWrite"
          :note-type="'treatment'"
          :initial-body="composerBody"
          :busy="saving"
          autofocus
          @submit="handleSubmit"
          @cancel="composerOpen = false"
        />

        <div
          v-if="loading"
          class="space-y-2"
        >
          <USkeleton
            v-for="i in 2"
            :key="i"
            class="h-16 w-full"
          />
        </div>
        <div
          v-else-if="notes.length === 0"
          class="text-center py-3 text-sm text-subtle"
        >
          {{ t('clinicalNotes.treatmentButton.empty') }}
        </div>
        <div
          v-else
          class="space-y-2 max-h-[40vh] overflow-y-auto pr-1"
        >
          <NoteCard
            v-for="note in notes"
            :key="note.id"
            :note-id="note.id"
            :note-type="note.note_type"
            :body="note.body"
            :created-at="note.created_at"
            :author="asEntry(note).author"
            :linked="asEntry(note).linked"
            :attachments="note.attachments"
            :can-edit="canEditEntry(asEntry(note))"
            @edit="startEdit(asEntry(note))"
            @delete="handleDelete(asEntry(note))"
          />
        </div>
      </div>
    </template>
  </UPopover>
</template>
