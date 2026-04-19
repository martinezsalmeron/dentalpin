<script setup lang="ts">
import type { DocumentType } from '~/types'

interface Props {
  patientId: string
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false
})

const emit = defineEmits<{
  uploaded: [document: Document]
}>()

const { t } = useI18n()
const { uploadDocument, uploading, uploadProgress } = useDocuments()

const isDragging = ref(false)
const selectedFile = ref<File | null>(null)
const title = ref('')
const description = ref('')
const documentType = ref<DocumentType>('other')

const fileInputRef = ref<HTMLInputElement>()

const documentTypes: DocumentType[] = ['consent', 'id_scan', 'insurance', 'report', 'referral', 'other']
const documentTypeLabels: Record<DocumentType, string> = {
  consent: 'documents.types.consent',
  id_scan: 'documents.types.id_scan',
  insurance: 'documents.types.insurance',
  report: 'documents.types.report',
  referral: 'documents.types.referral',
  other: 'documents.types.other'
}

const documentTypeOptions = computed(() =>
  documentTypes.map(type => ({
    label: t(documentTypeLabels[type]),
    value: type
  }))
)

const canSubmit = computed(() =>
  selectedFile.value !== null && title.value.trim().length > 0 && !uploading.value
)

function handleDragEnter(e: DragEvent) {
  e.preventDefault()
  isDragging.value = true
}

function handleDragLeave(e: DragEvent) {
  e.preventDefault()
  isDragging.value = false
}

function handleDragOver(e: DragEvent) {
  e.preventDefault()
}

function handleDrop(e: DragEvent) {
  e.preventDefault()
  isDragging.value = false

  const files = e.dataTransfer?.files
  if (files && files.length > 0) {
    selectFile(files[0])
  }
}

function handleFileSelect(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files && input.files.length > 0) {
    selectFile(input.files[0])
  }
}

function selectFile(file: File) {
  // Validate file type
  const allowedTypes = ['application/pdf', 'image/jpeg', 'image/png']
  if (!allowedTypes.includes(file.type)) {
    return
  }

  // Validate file size (10MB)
  if (file.size > 10 * 1024 * 1024) {
    return
  }

  selectedFile.value = file
  // Auto-fill title from filename
  if (!title.value) {
    title.value = file.name.replace(/\.[^/.]+$/, '')
  }
}

function clearFile() {
  selectedFile.value = null
  title.value = ''
  description.value = ''
  documentType.value = 'other'
  if (fileInputRef.value) {
    fileInputRef.value.value = ''
  }
}

function triggerFileSelect() {
  fileInputRef.value?.click()
}

async function handleSubmit() {
  if (!canSubmit.value || !selectedFile.value) return

  const doc = await uploadDocument(
    props.patientId,
    selectedFile.value,
    documentType.value,
    title.value.trim(),
    description.value.trim() || undefined
  )

  if (doc) {
    emit('uploaded', doc)
    clearFile()
  }
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}
</script>

<template>
  <div class="space-y-4">
    <!-- Drop zone -->
    <div
      :class="[
        'border-2 border-dashed rounded-lg p-6 text-center transition-colors cursor-pointer',
        isDragging ? 'border-[var(--color-primary)] bg-[var(--color-primary-soft)]' : 'border-default ',
        disabled ? 'opacity-50 cursor-not-allowed' : 'hover:border-[var(--color-primary)]'
      ]"
      @dragenter="handleDragEnter"
      @dragleave="handleDragLeave"
      @dragover="handleDragOver"
      @drop="handleDrop"
      @click="!disabled && triggerFileSelect()"
    >
      <input
        ref="fileInputRef"
        type="file"
        accept=".pdf,.jpg,.jpeg,.png"
        class="hidden"
        :disabled="disabled"
        @change="handleFileSelect"
      >

      <template v-if="!selectedFile">
        <UIcon
          name="i-lucide-upload-cloud"
          class="w-12 h-12 mx-auto text-subtle mb-3"
        />
        <p class="text-sm text-muted">
          {{ t('documents.dropzone.hint', 'Drag and drop a file here, or click to select') }}
        </p>
        <p class="text-caption text-subtle mt-1">
          PDF, JPG, PNG (max 10MB)
        </p>
      </template>

      <template v-else>
        <div class="flex items-center justify-center gap-3">
          <UIcon
            name="i-lucide-file"
            class="w-8 h-8 text-primary-accent"
          />
          <div class="text-left">
            <p class="text-sm font-medium">
              {{ selectedFile.name }}
            </p>
            <p class="text-caption text-subtle">
              {{ formatFileSize(selectedFile.size) }}
            </p>
          </div>
          <UButton
            icon="i-lucide-x"
            color="neutral"
            variant="ghost"
            size="xs"
            @click.stop="clearFile"
          />
        </div>
      </template>
    </div>

    <!-- Form fields (shown when file selected) -->
    <template v-if="selectedFile">
      <UFormField :label="t('documents.fields.type', 'Type')">
        <USelectMenu
          v-model="documentType"
          :items="documentTypeOptions"
          value-key="value"
        />
      </UFormField>

      <UFormField
        :label="t('documents.fields.title', 'Title')"
        required
      >
        <UInput
          v-model="title"
          :placeholder="t('documents.fields.titlePlaceholder', 'Document title')"
        />
      </UFormField>

      <UFormField :label="t('documents.fields.description', 'Description')">
        <UTextarea
          v-model="description"
          :placeholder="t('documents.fields.descriptionPlaceholder', 'Optional notes')"
          :rows="2"
        />
      </UFormField>

      <!-- Upload progress -->
      <div
        v-if="uploading && uploadProgress"
        class="space-y-1"
      >
        <div class="flex justify-between text-caption text-subtle">
          <span>{{ t('documents.uploading', 'Uploading...') }}</span>
          <span>{{ uploadProgress.percentage }}%</span>
        </div>
        <UProgress :value="uploadProgress.percentage" />
      </div>

      <!-- Submit button -->
      <UButton
        :disabled="!canSubmit"
        :loading="uploading"
        icon="i-lucide-upload"
        class="w-full"
        @click="handleSubmit"
      >
        {{ t('documents.upload', 'Upload Document') }}
      </UButton>
    </template>
  </div>
</template>
