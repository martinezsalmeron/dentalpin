<script setup lang="ts">
// One-page wizard for DPMF imports: upload → validate → preview → execute.
// Polls /jobs/{id} every 2s while a background step is running so the
// status, progress and error fields stay current without push.

import { computed, onUnmounted, ref } from 'vue'

const { t } = useI18n()
const api = useApi()
const { can } = usePermissions()

type JobStatus =
  | 'uploaded'
  | 'validating'
  | 'validated'
  | 'previewing'
  | 'executing'
  | 'completed'
  | 'failed'

interface ImportJob {
  id: string
  status: JobStatus
  error: string | null
  original_filename: string
  file_size: number
  source_system: string | null
  format_version: string | null
  tenant_label: string | null
  total_entities: number
  processed_entities: number
}

interface EntityPreview {
  entity_type: string
  declared_count: number
  samples: Array<{ canonical_uuid: string; source_id: string; payload: Record<string, unknown> }>
}

interface PreviewResponse {
  job: ImportJob
  entities: EntityPreview[]
  warnings: Array<{ severity: string; code: string; message: string; entity_type: string | null }>
  files: { total: number; with_sha256: number; without_sha256: number }
  verifactu_data_detected: boolean
  verifactu_module_installed: boolean
}

const file = ref<File | null>(null)
const passphrase = ref('')
const uploading = ref(false)
const uploadError = ref('')

const job = ref<ImportJob | null>(null)
const preview = ref<PreviewResponse | null>(null)
const importFiscal = ref(false)
let pollHandle: ReturnType<typeof setInterval> | null = null

const canExecute = computed(() => can('migration_import.job.execute'))
const verifactuOptInVisible = computed(
  () => !!preview.value?.verifactu_data_detected && !!preview.value?.verifactu_module_installed
)

function onFileChange(evt: Event) {
  const input = evt.target as HTMLInputElement
  file.value = input.files?.[0] ?? null
}

async function startUpload() {
  if (!file.value) return
  uploading.value = true
  uploadError.value = ''
  try {
    const formData = new FormData()
    formData.append('file', file.value)
    const res = await api.post<{ data: ImportJob }>('/api/v1/migration-import/jobs', formData)
    job.value = res.data
    await runValidate()
  } catch (err: any) {
    uploadError.value = err?.message ?? t('migrationImport.upload.error')
  } finally {
    uploading.value = false
  }
}

async function runValidate() {
  if (!job.value) return
  const res = await api.post<{ data: ImportJob }>(
    `/api/v1/migration-import/jobs/${job.value.id}/validate`,
    { passphrase: passphrase.value || null }
  )
  job.value = res.data
  if (job.value.status === 'validated') await loadPreview()
}

async function loadPreview() {
  if (!job.value) return
  const res = await api.post<{ data: PreviewResponse }>(
    `/api/v1/migration-import/jobs/${job.value.id}/preview`,
    { passphrase: passphrase.value || null }
  )
  preview.value = res.data
  job.value = res.data.job
}

async function execute() {
  if (!job.value || !canExecute.value) return
  await api.post(`/api/v1/migration-import/jobs/${job.value.id}/execute`, {
    import_fiscal_compliance: importFiscal.value,
    passphrase: passphrase.value || null
  })
  startPolling()
}

function startPolling() {
  if (pollHandle) clearInterval(pollHandle)
  pollHandle = setInterval(async () => {
    if (!job.value) return
    const res = await api.get<{ data: ImportJob }>(`/api/v1/migration-import/jobs/${job.value.id}`)
    job.value = res.data
    if (job.value.status === 'completed' || job.value.status === 'failed') {
      if (pollHandle) {
        clearInterval(pollHandle)
        pollHandle = null
      }
    }
  }, 2000)
}

onUnmounted(() => {
  if (pollHandle) clearInterval(pollHandle)
})
</script>

<template>
  <div class="space-y-6">
    <header>
      <h2 class="text-xl font-semibold">{{ t('migrationImport.page.title') }}</h2>
      <p class="text-sm text-gray-500">{{ t('migrationImport.page.subtitle') }}</p>
    </header>

    <!-- Upload step -->
    <UCard v-if="!job">
      <div class="space-y-4">
        <UFormField :label="t('migrationImport.upload.dropFile')">
          <UInput type="file" accept=".dpm,.zst,.enc" @change="onFileChange" />
        </UFormField>
        <UFormField :label="t('migrationImport.upload.passphrase')" :help="t('migrationImport.upload.passphraseHelp')">
          <UInput v-model="passphrase" type="password" />
        </UFormField>
        <UAlert v-if="uploadError" color="red" :title="t('migrationImport.upload.error')" :description="uploadError" />
        <UButton :loading="uploading" :disabled="!file" @click="startUpload">
          {{ t('migrationImport.upload.submit') }}
        </UButton>
      </div>
    </UCard>

    <!-- Status + validate/preview/execute -->
    <UCard v-else>
      <div class="space-y-3">
        <div class="flex items-center justify-between">
          <div>
            <p class="font-medium">{{ job.original_filename }}</p>
            <p class="text-xs text-gray-500">
              {{ job.source_system ?? '—' }} · {{ job.format_version ?? '—' }} ·
              {{ (job.file_size / 1024 / 1024).toFixed(1) }} MB
            </p>
          </div>
          <UBadge :color="job.status === 'failed' ? 'red' : job.status === 'completed' ? 'green' : 'blue'">
            {{ t(`migrationImport.status.${job.status}`) }}
          </UBadge>
        </div>
        <UAlert v-if="job.error" color="red" :description="job.error" />
      </div>

      <!-- Preview -->
      <div v-if="preview" class="mt-6 space-y-4">
        <div>
          <h3 class="font-semibold">{{ t('migrationImport.preview.entities') }}</h3>
          <ul class="mt-2 text-sm">
            <li v-for="ent in preview.entities" :key="ent.entity_type" class="flex justify-between border-b py-1">
              <span>{{ ent.entity_type }}</span>
              <span class="font-mono">{{ ent.declared_count }}</span>
            </li>
          </ul>
        </div>

        <div>
          <h3 class="font-semibold">{{ t('migrationImport.preview.files') }}</h3>
          <p class="text-sm">
            {{ t('migrationImport.preview.filesTotal') }}: {{ preview.files.total }} ·
            {{ t('migrationImport.preview.filesWithSha') }}: {{ preview.files.with_sha256 }} ·
            {{ t('migrationImport.preview.filesWithoutSha') }}: {{ preview.files.without_sha256 }}
          </p>
        </div>

        <div v-if="preview.warnings.length">
          <h3 class="font-semibold">{{ t('migrationImport.preview.warnings') }} ({{ preview.warnings.length }})</h3>
          <ul class="mt-2 max-h-48 overflow-y-auto text-xs">
            <li v-for="(w, i) in preview.warnings" :key="i" class="border-b py-1">
              [{{ w.severity }}] {{ w.code }} — {{ w.message }}
            </li>
          </ul>
        </div>

        <UFormField v-if="verifactuOptInVisible" :help="t('migrationImport.preview.verifactuHelp')">
          <UCheckbox v-model="importFiscal" :label="t('migrationImport.preview.verifactuCheckbox')" />
        </UFormField>

        <UAlert color="amber" :description="t('migrationImport.preview.warning')" />

        <UButton
          color="primary"
          :disabled="!canExecute || job.status === 'executing'"
          @click="execute"
        >
          {{ t('migrationImport.preview.confirm') }}
        </UButton>
      </div>

      <!-- Progress -->
      <div v-if="job.status === 'executing'" class="mt-6">
        <p class="text-sm">
          {{ t('migrationImport.execute.progress', { processed: job.processed_entities, total: job.total_entities }) }}
        </p>
      </div>
    </UCard>
  </div>
</template>
