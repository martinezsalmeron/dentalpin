/**
 * Polymorphic attachment composable.
 *
 * Wraps the generic `/api/v1/media/attachments` endpoints. Any module
 * can call this to link a Document to one of the registered owner_types
 * (`patient` / `treatment` / `plan` / `plan_item` /
 * `appointment_treatment` / `clinical_note`).
 */

import type { ApiResponse, AttachmentCreate, MediaAttachment } from '~~/app/types'

export function useAttachments() {
  const api = useApi()
  const { t } = useI18n()
  const toast = useToast()

  async function listByOwner(
    ownerType: string,
    ownerId: string
  ): Promise<MediaAttachment[]> {
    try {
      const params = new URLSearchParams({ owner_type: ownerType, owner_id: ownerId })
      const response = await api.get<ApiResponse<MediaAttachment[]>>(
        `/api/v1/media/attachments?${params}`
      )
      return response.data
    } catch (error) {
      console.error('Error listing attachments:', error)
      return []
    }
  }

  async function link(payload: AttachmentCreate): Promise<MediaAttachment | null> {
    try {
      const response = await api.post<ApiResponse<MediaAttachment>>(
        '/api/v1/media/attachments',
        payload
      )
      return response.data
    } catch (error) {
      console.error('Error linking attachment:', error)
      toast.add({
        title: t('common.error'),
        description: t('attachments.linkError', 'Error linking attachment'),
        color: 'error'
      })
      return null
    }
  }

  async function unlink(attachmentId: string): Promise<boolean> {
    try {
      await api.del(`/api/v1/media/attachments/${attachmentId}`)
      return true
    } catch (error) {
      console.error('Error unlinking attachment:', error)
      toast.add({ title: t('common.error'), color: 'error' })
      return false
    }
  }

  return { listByOwner, link, unlink }
}
