import type {
  ApiResponse,
  AppointmentTreatmentNoteResponse,
  AppointmentTreatmentNoteUpdate,
  AttachmentOwnerType,
  ClinicalNote,
  ClinicalNoteCreate,
  ClinicalNoteEntry,
  ClinicalNoteOwnerType,
  ClinicalNoteUpdate,
  NoteAttachment,
  NoteAttachmentCreate,
  NoteTemplate,
  PlanNotesGroup
} from '~~/app/types'

/**
 * Clinical notes + polymorphic attachments for treatment plans.
 *
 * Notes live at two levels (plan, plan_item). Visit-level notes reuse
 * `AppointmentTreatment.notes` (agenda module) and are updated via
 * {@link patchVisitNote}.
 */
export function useClinicalNotes() {
  const api = useApi()
  const toast = useToast()
  const { t } = useI18n()

  const notes = ref<ClinicalNote[]>([])
  const loading = ref(false)

  async function listNotes(ownerType: ClinicalNoteOwnerType, ownerId: string) {
    loading.value = true
    try {
      const qs = new URLSearchParams({ owner_type: ownerType, owner_id: ownerId })
      const response = await api.get<ApiResponse<ClinicalNote[]>>(
        `/api/v1/treatment_plan/notes?${qs}`
      )
      notes.value = response.data
      return response.data
    } finally {
      loading.value = false
    }
  }

  async function listForPlan(planId: string): Promise<ClinicalNoteEntry[]> {
    const response = await api.get<ApiResponse<ClinicalNoteEntry[]>>(
      `/api/v1/treatment_plan/treatment-plans/${planId}/clinical-notes`
    )
    return response.data
  }

  async function listGroupedForPatient(patientId: string): Promise<PlanNotesGroup[]> {
    const response = await api.get<ApiResponse<PlanNotesGroup[]>>(
      `/api/v1/treatment_plan/patients/${patientId}/clinical-notes`
    )
    return response.data
  }

  async function listTemplates(category?: string): Promise<NoteTemplate[]> {
    const qs = new URLSearchParams()
    if (category) qs.append('category', category)
    const url = `/api/v1/treatment_plan/note-templates${qs.toString() ? `?${qs}` : ''}`
    const response = await api.get<ApiResponse<NoteTemplate[]>>(url)
    return response.data
  }

  async function createNote(input: ClinicalNoteCreate): Promise<ClinicalNote | null> {
    try {
      const response = await api.post<ApiResponse<ClinicalNote>>(
        '/api/v1/treatment_plan/notes',
        input
      )
      toast.add({ title: t('treatmentPlans.notes.saved'), color: 'green' })
      return response.data
    } catch (error) {
      console.error('Error creating clinical note:', error)
      return null
    }
  }

  async function updateNote(noteId: string, body: string): Promise<ClinicalNote | null> {
    try {
      const payload: ClinicalNoteUpdate = { body }
      const response = await api.patch<ApiResponse<ClinicalNote>>(
        `/api/v1/treatment_plan/notes/${noteId}`,
        payload
      )
      toast.add({ title: t('treatmentPlans.notes.saved'), color: 'green' })
      return response.data
    } catch (error) {
      console.error('Error updating clinical note:', error)
      return null
    }
  }

  async function deleteNote(noteId: string): Promise<boolean> {
    try {
      await api.del(`/api/v1/treatment_plan/notes/${noteId}`)
      toast.add({ title: t('treatmentPlans.notes.deleted'), color: 'green' })
      return true
    } catch (error) {
      console.error('Error deleting clinical note:', error)
      return false
    }
  }

  async function linkAttachment(input: NoteAttachmentCreate): Promise<NoteAttachment | null> {
    try {
      const response = await api.post<ApiResponse<NoteAttachment>>(
        '/api/v1/treatment_plan/attachments',
        input
      )
      return response.data
    } catch (error) {
      console.error('Error linking attachment:', error)
      return null
    }
  }

  async function unlinkAttachment(attachmentId: string): Promise<boolean> {
    try {
      await api.del(`/api/v1/treatment_plan/attachments/${attachmentId}`)
      return true
    } catch (error) {
      console.error('Error unlinking attachment:', error)
      return false
    }
  }

  async function listAttachments(
    ownerType: AttachmentOwnerType,
    ownerId: string
  ): Promise<NoteAttachment[]> {
    const qs = new URLSearchParams({ owner_type: ownerType, owner_id: ownerId })
    const response = await api.get<ApiResponse<NoteAttachment[]>>(
      `/api/v1/treatment_plan/attachments?${qs}`
    )
    return response.data
  }

  async function patchVisitNote(
    appointmentTreatmentId: string,
    payload: AppointmentTreatmentNoteUpdate
  ): Promise<AppointmentTreatmentNoteResponse | null> {
    try {
      const response = await api.patch<ApiResponse<AppointmentTreatmentNoteResponse>>(
        `/api/v1/agenda/appointment-treatments/${appointmentTreatmentId}`,
        payload
      )
      toast.add({ title: t('treatmentPlans.notes.saved'), color: 'green' })
      return response.data
    } catch (error) {
      console.error('Error updating visit note:', error)
      return null
    }
  }

  return {
    notes,
    loading,
    listNotes,
    listForPlan,
    listGroupedForPatient,
    listTemplates,
    createNote,
    updateNote,
    deleteNote,
    linkAttachment,
    unlinkAttachment,
    listAttachments,
    patchVisitNote
  }
}
