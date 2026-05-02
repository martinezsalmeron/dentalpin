/**
 * Photo gallery composable — wraps the photo-aware media endpoints.
 *
 * Responsibilities:
 * - List photos / X-rays for a patient with category / subtype / date filters.
 * - Upload a photo (multipart) with classification metadata.
 * - Pair / unpair before/after photos.
 * - Patch photo classification.
 *
 * URLs returned by the backend (`thumb_url` / `medium_url` / `full_url`) are
 * relative paths under `/api/v1/media/...` — the caller fetches them through
 * the same `useApi` instance so authentication is preserved.
 */

import type {
  ApiResponse,
  Document,
  MediaCategory,
  MediaKind,
  PaginatedResponse,
  PhotoMetadataUpdate
} from '~~/app/types'

interface PhotoFilters {
  media_kind?: MediaKind
  media_category?: MediaCategory
  media_subtype?: string
  captured_from?: string
  captured_to?: string
  pair_status?: 'all' | 'paired' | 'unpaired'
  page?: number
  page_size?: number
}

interface PhotoUploadInput {
  file: File
  title: string
  media_kind?: MediaKind
  media_category?: MediaCategory
  media_subtype?: string
  captured_at?: string
  paired_document_id?: string
  description?: string
}

export function usePhotos() {
  const api = useApi()
  const { t } = useI18n()
  const toast = useToast()

  const photos = ref<Document[]>([])
  const total = ref(0)
  const loading = ref(false)
  const uploading = ref(false)

  async function fetchPhotos(patientId: string, filters: PhotoFilters = {}) {
    loading.value = true
    try {
      const params = new URLSearchParams()
      if (filters.media_kind) params.append('media_kind', filters.media_kind)
      if (filters.media_category) params.append('media_category', filters.media_category)
      if (filters.media_subtype) params.append('media_subtype', filters.media_subtype)
      if (filters.captured_from) params.append('captured_from', filters.captured_from)
      if (filters.captured_to) params.append('captured_to', filters.captured_to)
      if (filters.pair_status) params.append('pair_status', filters.pair_status)
      params.append('page', String(filters.page ?? 1))
      params.append('page_size', String(filters.page_size ?? 40))

      const response = await api.get<PaginatedResponse<Document>>(
        `/api/v1/media/patients/${patientId}/photos?${params}`
      )
      photos.value = response.data
      total.value = response.total
    } catch (error) {
      console.error('Error fetching photos:', error)
      toast.add({
        title: t('common.error'),
        description: t('photoGallery.fetchError', 'Error loading photos'),
        color: 'error'
      })
    } finally {
      loading.value = false
    }
  }

  async function uploadPhoto(
    patientId: string,
    input: PhotoUploadInput
  ): Promise<Document | null> {
    uploading.value = true
    try {
      const formData = new FormData()
      formData.append('file', input.file)
      formData.append('title', input.title)
      formData.append('media_kind', input.media_kind ?? 'photo')
      if (input.media_category) formData.append('media_category', input.media_category)
      if (input.media_subtype) formData.append('media_subtype', input.media_subtype)
      if (input.captured_at) formData.append('captured_at', input.captured_at)
      if (input.paired_document_id) {
        formData.append('paired_document_id', input.paired_document_id)
      }
      if (input.description) formData.append('description', input.description)

      const response = await api.post<ApiResponse<Document>>(
        `/api/v1/media/patients/${patientId}/photos`,
        formData
      )
      toast.add({
        title: t('common.success'),
        description: t('photoGallery.uploadSuccess', 'Photo uploaded'),
        color: 'success'
      })
      return response.data
    } catch (error) {
      console.error('Error uploading photo:', error)
      toast.add({
        title: t('common.error'),
        description: t('photoGallery.uploadError', 'Error uploading photo'),
        color: 'error'
      })
      return null
    } finally {
      uploading.value = false
    }
  }

  async function updatePhotoMetadata(
    documentId: string,
    patch: PhotoMetadataUpdate
  ): Promise<Document | null> {
    try {
      const response = await api.patch<ApiResponse<Document>>(
        `/api/v1/media/documents/${documentId}/photo-metadata`,
        patch
      )
      const idx = photos.value.findIndex(p => p.id === documentId)
      if (idx !== -1) photos.value[idx] = response.data
      return response.data
    } catch (error) {
      console.error('Error updating photo metadata:', error)
      toast.add({ title: t('common.error'), color: 'error' })
      return null
    }
  }

  async function pairPhotos(a: string, b: string): Promise<Document | null> {
    try {
      const response = await api.post<ApiResponse<Document>>(
        `/api/v1/media/documents/${a}/pair/${b}`,
        {}
      )
      toast.add({
        title: t('photoGallery.paired', 'Before/after paired'),
        color: 'success'
      })
      return response.data
    } catch (error) {
      console.error('Error pairing photos:', error)
      toast.add({ title: t('common.error'), color: 'error' })
      return null
    }
  }

  async function unpair(documentId: string): Promise<boolean> {
    try {
      await api.del(`/api/v1/media/documents/${documentId}/pair`)
      return true
    } catch (error) {
      console.error('Error unpairing:', error)
      toast.add({ title: t('common.error'), color: 'error' })
      return false
    }
  }

  return {
    photos,
    total,
    loading,
    uploading,
    fetchPhotos,
    uploadPhoto,
    updatePhotoMetadata,
    pairPhotos,
    unpair
  }
}
