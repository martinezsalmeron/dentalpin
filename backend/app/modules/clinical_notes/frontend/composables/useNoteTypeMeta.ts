import type { NoteType } from '~~/app/types'

export interface NoteTypeMeta {
  /** UBadge color for the note type chip. */
  color: 'neutral' | 'info' | 'success' | 'secondary' | 'primary'
  /** Lucide icon used in the badge / sidebar tab. */
  icon: string
  /** i18n key for the localized label. */
  labelKey: string
  /** Static seed category fed to ``useClinicalNotes().listTemplates``. */
  templateCategory: string
}

const META: Record<NoteType, NoteTypeMeta> = {
  administrative: {
    color: 'neutral',
    icon: 'i-lucide-user-cog',
    labelKey: 'clinicalNotes.types.administrative',
    templateCategory: 'administrative'
  },
  diagnosis: {
    color: 'info',
    icon: 'i-lucide-stethoscope',
    labelKey: 'clinicalNotes.types.diagnosis',
    templateCategory: 'diagnosis'
  },
  treatment: {
    color: 'success',
    icon: 'i-lucide-syringe',
    labelKey: 'clinicalNotes.types.treatment',
    templateCategory: 'general'
  },
  treatment_plan: {
    color: 'secondary',
    icon: 'i-lucide-list-checks',
    labelKey: 'clinicalNotes.types.treatment_plan',
    templateCategory: 'general'
  }
}

const ALL_TYPES: NoteType[] = [
  'administrative',
  'diagnosis',
  'treatment',
  'treatment_plan'
]

/**
 * Centralized note-type display metadata. Used by every note-related UI
 * (RecentNotesFeed, NoteCard, DiagnosisNotesSidebar, TreatmentNoteButton)
 * so colors/icons stay consistent.
 */
export function useNoteTypeMeta() {
  function metaFor(type: NoteType): NoteTypeMeta {
    return META[type]
  }
  function allTypes(): NoteType[] {
    return [...ALL_TYPES]
  }
  return { metaFor, allTypes }
}
