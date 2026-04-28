<script setup lang="ts">
/**
 * NoteCard — shared presentational card for a single clinical note.
 *
 * Renders the color-coded type badge, author + relative timestamp, body
 * (with a "show more" toggle for long entries) and optional linked-entity
 * chip. Edit/delete only render when the parent passes ``can-edit``.
 */

import type { NoteType, ClinicalNoteLinked, ClinicalNoteAuthor, NoteAttachment } from '~~/app/types'

const props = defineProps<{
  noteId: string
  noteType: NoteType
  body: string
  createdAt: string
  author: ClinicalNoteAuthor | { id: string; full_name?: string | null }
  linked?: ClinicalNoteLinked | null
  attachments?: NoteAttachment[]
  /** When true, edit/delete actions are visible. Computed by parent. */
  canEdit?: boolean
  /** Highlight the card (e.g. when matching the current selected tooth). */
  highlight?: boolean
}>()

const emit = defineEmits<{
  edit: []
  delete: []
  'open-linked': [linked: ClinicalNoteLinked]
}>()

const { t } = useI18n()
const { metaFor } = useNoteTypeMeta()

const meta = computed(() => metaFor(props.noteType))
const expanded = ref(false)
const TRUNCATE_AT = 280

const isLong = computed(() => (props.body || '').length > TRUNCATE_AT)
const visibleBody = computed(() => {
  if (!isLong.value || expanded.value) return props.body
  return `${props.body.slice(0, TRUNCATE_AT)}…`
})

function formatRelative(iso: string): string {
  try {
    const then = new Date(iso).getTime()
    const now = Date.now()
    const diffSec = Math.round((now - then) / 1000)
    if (diffSec < 60) return t('clinicalNotes.time.justNow')
    const diffMin = Math.round(diffSec / 60)
    if (diffMin < 60) return t('clinicalNotes.time.minutesAgo', { n: diffMin })
    const diffH = Math.round(diffMin / 60)
    if (diffH < 24) return t('clinicalNotes.time.hoursAgo', { n: diffH })
    const diffD = Math.round(diffH / 24)
    if (diffD < 7) return t('clinicalNotes.time.daysAgo', { n: diffD })
    return new Date(iso).toLocaleDateString()
  } catch {
    return iso
  }
}

function formatAbsolute(iso: string): string {
  try {
    return new Date(iso).toLocaleString()
  } catch {
    return iso
  }
}

const authorLabel = computed(() => {
  const a = props.author as { full_name?: string | null; email?: string | null }
  return a?.full_name || a?.email || t('clinicalNotes.author.unknown')
})

const initials = computed(() => {
  const label = authorLabel.value
  return label
    .split(/\s+/)
    .map(w => w[0])
    .filter(Boolean)
    .slice(0, 2)
    .join('')
    .toUpperCase()
})

const linkedLabel = computed(() => {
  const linked = props.linked
  if (!linked) return null
  if (linked.kind === 'patient' && linked.tooth_number) {
    return t('clinicalNotes.linked.tooth', { n: linked.tooth_number })
  }
  if (linked.kind === 'treatment') {
    if (linked.tooth_number && linked.label) {
      return t('clinicalNotes.linked.treatmentOnTooth', {
        label: linked.label,
        n: linked.tooth_number
      })
    }
    return linked.label || t('clinicalNotes.linked.treatment')
  }
  if (linked.kind === 'plan') {
    return linked.label
      ? t('clinicalNotes.linked.planNamed', { label: linked.label })
      : t('clinicalNotes.linked.plan')
  }
  return null
})
</script>

<template>
  <article
    class="note-card group relative border rounded-token-md p-3 bg-surface transition-colors"
    :class="[
      `note-card--${noteType}`,
      highlight ? 'ring-2 ring-primary' : 'border-default'
    ]"
    :data-note-id="noteId"
  >
    <header class="flex items-start gap-2">
      <UAvatar
        size="xs"
        :alt="authorLabel"
      >
        <span class="text-caption font-semibold">{{ initials }}</span>
      </UAvatar>
      <div class="flex-1 min-w-0">
        <div class="flex flex-wrap items-center gap-x-2 gap-y-1">
          <span class="font-medium text-sm truncate">{{ authorLabel }}</span>
          <UBadge
            :color="meta.color"
            variant="subtle"
            size="xs"
            class="shrink-0"
          >
            <UIcon
              :name="meta.icon"
              class="w-3 h-3 mr-1"
            />
            {{ t(meta.labelKey) }}
          </UBadge>
          <span
            v-if="linkedLabel"
            class="text-caption text-muted truncate"
          >
            · {{ linkedLabel }}
          </span>
        </div>
        <span
          class="text-caption text-subtle"
          :title="formatAbsolute(createdAt)"
        >
          {{ formatRelative(createdAt) }}
        </span>
      </div>
      <div
        v-if="canEdit"
        class="flex gap-1 opacity-0 group-hover:opacity-100 focus-within:opacity-100 transition"
      >
        <UButton
          icon="i-lucide-pencil"
          size="xs"
          variant="ghost"
          :aria-label="t('actions.edit')"
          @click="emit('edit')"
        />
        <UButton
          icon="i-lucide-trash-2"
          size="xs"
          variant="ghost"
          color="error"
          :aria-label="t('actions.delete')"
          @click="emit('delete')"
        />
      </div>
    </header>

    <div class="mt-2 text-sm whitespace-pre-wrap break-words">
      {{ visibleBody }}
    </div>

    <button
      v-if="isLong"
      type="button"
      class="mt-1 text-caption text-primary hover:underline"
      @click="expanded = !expanded"
    >
      {{ expanded ? t('clinicalNotes.actions.showLess') : t('clinicalNotes.actions.showMore') }}
    </button>

    <div
      v-if="attachments?.length"
      class="mt-2 flex flex-wrap gap-1"
    >
      <UBadge
        v-for="att in attachments"
        :key="att.id"
        color="neutral"
        variant="soft"
        size="xs"
      >
        <UIcon
          name="i-lucide-paperclip"
          class="w-3 h-3 mr-1"
        />
        {{ att.document_id.slice(0, 8) }}
      </UBadge>
    </div>

    <button
      v-if="linked && linked.id"
      type="button"
      class="absolute inset-0 rounded-token-md focus:outline-none focus-visible:ring-2 focus-visible:ring-primary"
      :aria-label="t('clinicalNotes.actions.openLinked')"
      @click="emit('open-linked', linked!)"
    />
  </article>
</template>

<style scoped>
.note-card {
  position: relative;
}

.note-card--administrative {
  border-left: 3px solid var(--color-neutral, #94a3b8);
}
.note-card--diagnosis {
  border-left: 3px solid var(--color-info-accent, #3b82f6);
}
.note-card--treatment {
  border-left: 3px solid var(--color-success-accent, #22c55e);
}
.note-card--treatment_plan {
  border-left: 3px solid var(--color-secondary-accent, #a855f7);
}

/* The full-card link button must stay underneath interactive children. */
.note-card button[aria-label]:last-child {
  z-index: 0;
}
.note-card > header,
.note-card > div,
.note-card > button[type='button']:not(:last-child) {
  position: relative;
  z-index: 1;
}
</style>
