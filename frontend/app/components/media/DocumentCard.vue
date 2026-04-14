<script setup lang="ts">
import type { Document } from '~/types'
import { PERMISSIONS } from '~/config/permissions'

interface Props {
  document: Document
}

const props = defineProps<Props>()

const emit = defineEmits<{
  download: [document: Document]
  delete: [document: Document]
  edit: [document: Document]
}>()

const { t } = useI18n()
const { can } = usePermissions()
const { formatFileSize, getDocumentTypeLabel, getMimeTypeIcon } = useDocuments()

const canWrite = computed(() => can(PERMISSIONS.documents.write))

const formattedDate = computed(() => {
  const date = new Date(props.document.created_at)
  return date.toLocaleDateString()
})

const uploaderName = computed(() => {
  if (props.document.uploader) {
    return `${props.document.uploader.first_name} ${props.document.uploader.last_name}`
  }
  return ''
})

function handleDownload() {
  emit('download', props.document)
}

function handleDelete() {
  emit('delete', props.document)
}

function handleEdit() {
  emit('edit', props.document)
}
</script>

<template>
  <UCard class="group">
    <div class="flex items-start gap-4">
      <!-- Icon -->
      <div class="flex-shrink-0">
        <div class="w-12 h-12 rounded-lg bg-primary-100 dark:bg-primary-900/20 flex items-center justify-center">
          <UIcon
            :name="getMimeTypeIcon(document.mime_type)"
            class="w-6 h-6 text-primary-600 dark:text-primary-400"
          />
        </div>
      </div>

      <!-- Content -->
      <div class="flex-grow min-w-0">
        <div class="flex items-start justify-between gap-2">
          <div class="min-w-0">
            <h4 class="font-medium text-sm truncate">
              {{ document.title }}
            </h4>
            <div class="flex items-center gap-2 mt-1">
              <UBadge
                color="gray"
                variant="subtle"
                size="xs"
              >
                {{ getDocumentTypeLabel(document.document_type as any) }}
              </UBadge>
              <span class="text-xs text-gray-500">{{ formatFileSize(document.file_size) }}</span>
            </div>
          </div>

          <!-- Actions -->
          <div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            <UButton
              icon="i-lucide-download"
              color="gray"
              variant="ghost"
              size="xs"
              :title="t('common.download')"
              @click="handleDownload"
            />
            <UButton
              v-if="canWrite"
              icon="i-lucide-pencil"
              color="gray"
              variant="ghost"
              size="xs"
              :title="t('common.edit')"
              @click="handleEdit"
            />
            <UButton
              v-if="canWrite"
              icon="i-lucide-trash-2"
              color="red"
              variant="ghost"
              size="xs"
              :title="t('common.delete')"
              @click="handleDelete"
            />
          </div>
        </div>

        <!-- Description -->
        <p
          v-if="document.description"
          class="text-xs text-gray-500 mt-2 line-clamp-2"
        >
          {{ document.description }}
        </p>

        <!-- Meta -->
        <div class="flex items-center gap-2 mt-2 text-xs text-gray-400">
          <span>{{ formattedDate }}</span>
          <span v-if="uploaderName">{{ uploaderName }}</span>
        </div>
      </div>
    </div>
  </UCard>
</template>
