<script setup lang="ts">
/**
 * PlanNotesTimeline — merged clinical-notes feed for a single plan.
 *
 * Shows plan-level notes, plan_item notes (captured at completion) and visit
 * notes (AppointmentTreatment.notes) in one chronological list with source
 * badges. Write actions (add/edit/delete) stay scoped to plan-level notes;
 * plan_item and visit entries are read-only here — they are edited from the
 * completion flow and the agenda respectively.
 */

import type {
  ClinicalNoteEntry,
  NoteTemplate,
  PlannedTreatmentItem
} from '~~/app/types'

const props = defineProps<{
  planId: string
  /** Used to resolve treatment names for plan_item / visit entries. */
  items: PlannedTreatmentItem[]
  templateCategory?: string
  readonly?: boolean
}>()

const emit = defineEmits<{
  updated: []
}>()

const { t, locale } = useI18n()
const { user } = useAuth()
const { can } = usePermissions()
const {
  listForPlan,
  createNote,
  updateNote,
  deleteNote,
  listTemplates
} = useClinicalNotes()

const entries = ref<ClinicalNoteEntry[]>([])
const loading = ref(false)
const showEditor = ref(false)
const draftBody = ref('')
const editingId = ref<string | null>(null)
const templates = ref<NoteTemplate[]>([])

const canWrite = computed(() => !props.readonly && can('treatment_plan.notes.write'))

const itemsById = computed(() => {
  const map = new Map<string, PlannedTreatmentItem>()
  for (const it of props.items) map.set(it.id, it)
  return map
})

async function refresh() {
  loading.value = true
  try {
    entries.value = await listForPlan(props.planId)
  } finally {
    loading.value = false
  }
}

async function fetchTemplates() {
  if (!props.templateCategory) return
  templates.value = await listTemplates(props.templateCategory)
}

function startNew() {
  editingId.value = null
  draftBody.value = ''
  showEditor.value = true
}

function startEdit(entry: ClinicalNoteEntry) {
  if (!entry.note_id) return
  editingId.value = entry.note_id
  draftBody.value = entry.body
  showEditor.value = true
}

function applyTemplate(body: string) {
  draftBody.value = body
}

async function save() {
  const body = draftBody.value.trim()
  if (!body) return
  if (editingId.value) {
    await updateNote(editingId.value, body)
  } else {
    await createNote({
      owner_type: 'plan',
      owner_id: props.planId,
      body
    })
  }
  showEditor.value = false
  editingId.value = null
  draftBody.value = ''
  await refresh()
  emit('updated')
}

function cancel() {
  showEditor.value = false
  editingId.value = null
  draftBody.value = ''
}

async function remove(entry: ClinicalNoteEntry) {
  if (!entry.note_id) return
  const ok = await deleteNote(entry.note_id)
  if (ok) {
    await refresh()
    emit('updated')
  }
}

function isOwn(entry: ClinicalNoteEntry): boolean {
  return !!entry.author_id && user.value?.id === entry.author_id
}

function canEdit(entry: ClinicalNoteEntry): boolean {
  return canWrite.value && entry.source === 'plan' && !!entry.note_id && isOwn(entry)
}

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString()
  } catch {
    return iso
  }
}

function sourceBadgeColor(source: 'plan' | 'plan_item' | 'visit'): 'neutral' | 'success' | 'primary' {
  if (source === 'visit') return 'primary'
  if (source === 'plan_item') return 'success'
  return 'neutral'
}

function sourceLabel(entry: ClinicalNoteEntry): string {
  if (entry.source === 'plan') return t('treatmentPlans.filterBy.plan')
  const name = entry.plan_item_id ? treatmentName(entry.plan_item_id) : null
  const base = entry.source === 'visit'
    ? t('treatmentPlans.filterBy.visit')
    : t('treatmentPlans.filterBy.item')
  return name ? `${base}: ${name}` : base
}

function treatmentName(planItemId: string): string | null {
  const item = itemsById.value.get(planItemId)
  if (!item) return null
  const names = item.catalog_item?.names || item.treatment?.catalog_item?.names
  if (names) {
    const localized = names[locale.value] || names.es
    if (localized) return localized
  }
  const clinicalType = item.treatment?.clinical_type
  if (clinicalType) {
    const key = `odontogram.treatments.types.${clinicalType}`
    const translated = t(key)
    if (translated !== key) return translated
    return clinicalType
  }
  return null
}

watch(() => props.planId, refresh, { immediate: true })
onMounted(fetchTemplates)

defineExpose({ refresh })
</script>

<template>
  <div class="space-y-3">
    <div
      v-if="canWrite && !showEditor"
      class="flex justify-end"
    >
      <UButton
        icon="i-lucide-plus"
        size="sm"
        variant="soft"
        @click="startNew"
      >
        {{ t('treatmentPlans.notes.addNote') }}
      </UButton>
    </div>

    <div
      v-if="showEditor"
      class="border border-default rounded-md p-3 space-y-2 bg-surface"
    >
      <div
        v-if="templates.length > 0 && !editingId"
        class="flex items-center gap-2 flex-wrap"
      >
        <span class="text-caption text-muted">
          {{ t('treatmentPlans.notes.templatePicker') }}:
        </span>
        <UButton
          v-for="tpl in templates"
          :key="tpl.id"
          size="xs"
          variant="ghost"
          @click="applyTemplate(tpl.body)"
        >
          {{ t(tpl.i18n_key) }}
        </UButton>
      </div>
      <textarea
        v-model="draftBody"
        :rows="8"
        :placeholder="t('treatmentPlans.notes.bodyPlaceholder')"
        class="clinical-note-textarea"
      />
      <div class="flex justify-end gap-2">
        <UButton
          variant="ghost"
          size="sm"
          @click="cancel"
        >
          {{ t('actions.cancel') }}
        </UButton>
        <UButton
          color="primary"
          size="sm"
          :disabled="!draftBody.trim()"
          @click="save"
        >
          {{ t('actions.save') }}
        </UButton>
      </div>
    </div>

    <div
      v-if="loading"
      class="text-center py-4 text-muted"
    >
      <UIcon
        name="i-lucide-loader-2"
        class="w-5 h-5 animate-spin mx-auto"
      />
    </div>

    <div
      v-else-if="entries.length === 0"
      class="text-center py-4 text-muted text-sm"
    >
      {{ t('treatmentPlans.notes.empty') }}
    </div>

    <div
      v-else
      class="space-y-3"
    >
      <article
        v-for="entry in entries"
        :key="entry.note_id || `${entry.source}-${entry.owner_id}-${entry.created_at}`"
        class="border border-default rounded-md p-3 bg-surface"
      >
        <header class="flex items-center justify-between mb-2 gap-2">
          <div class="flex items-center gap-2 min-w-0">
            <UBadge
              :color="sourceBadgeColor(entry.source)"
              variant="subtle"
              size="xs"
            >
              {{ sourceLabel(entry) }}
            </UBadge>
            <span class="text-caption text-muted truncate">
              {{ formatDate(entry.created_at) }}
            </span>
          </div>
          <div
            v-if="canEdit(entry)"
            class="flex gap-1"
          >
            <UButton
              icon="i-lucide-pencil"
              size="xs"
              variant="ghost"
              @click="startEdit(entry)"
            />
            <UButton
              icon="i-lucide-trash-2"
              size="xs"
              variant="ghost"
              color="error"
              @click="remove(entry)"
            />
          </div>
        </header>
        <div
          class="prose prose-sm max-w-none"
          v-html="entry.body"
        />
        <div
          v-if="entry.attachments.length > 0"
          class="mt-2 flex flex-wrap gap-2"
        >
          <UBadge
            v-for="att in entry.attachments"
            :key="att.id"
            color="neutral"
            variant="soft"
            size="sm"
          >
            <UIcon
              name="i-lucide-paperclip"
              class="w-3 h-3 mr-1"
            />
            {{ att.document_id.slice(0, 8) }}
          </UBadge>
        </div>
      </article>
    </div>
  </div>
</template>

<style scoped>
.clinical-note-textarea {
  display: block;
  width: 100%;
  min-height: 12rem;
  padding: 0.625rem 0.75rem;
  border: 1px solid var(--ui-border);
  border-radius: var(--ui-radius, 6px);
  background: var(--ui-bg);
  color: var(--ui-text);
  font: inherit;
  line-height: 1.5;
  resize: vertical;
}

.clinical-note-textarea:focus {
  outline: none;
  border-color: var(--ui-primary);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--ui-primary) 25%, transparent);
}
</style>
