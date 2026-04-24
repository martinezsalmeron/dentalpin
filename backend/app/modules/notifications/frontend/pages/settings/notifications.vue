<script setup lang="ts">
import type { NotificationTypeSettings, SmtpSettingsUpdate, SmtpTestRequest } from '~~/app/types'

const { t } = useI18n()
const { isAdmin } = usePermissions()
const auth = useAuth()
const {
  settings,
  smtpSettings,
  isLoading,
  isSaving,
  isTesting,
  isSmtpLoading,
  isSmtpSaving,
  isSmtpTesting,
  notificationTypes,
  fetchSettings,
  updateSettings,
  testEmailConnection,
  fetchSmtpSettings,
  updateSmtpSettings,
  testSmtpConnection
} = useNotificationSettings()

// Local state for editing
const localSettings = ref<Record<string, NotificationTypeSettings>>({})
const hasChanges = ref(false)
const showTestEmailModal = ref(false)
const testEmail = ref('')

// SMTP Configuration state
const showSmtpModal = ref(false)
const smtpForm = ref<SmtpSettingsUpdate>({
  provider: 'disabled',
  host: '',
  port: 587,
  username: '',
  password: '',
  use_tls: true,
  use_ssl: false,
  from_email: '',
  from_name: ''
})
const smtpTestEmail = ref('')

// Provider options
const providerOptions = [
  { value: 'smtp', label: 'SMTP' },
  { value: 'console', label: 'Console (desarrollo)' },
  { value: 'disabled', label: 'Deshabilitado' }
]

// Initialize local settings from fetched settings
watch(settings, (newSettings) => {
  if (newSettings?.settings) {
    localSettings.value = JSON.parse(JSON.stringify(newSettings.settings))
    hasChanges.value = false
  }
}, { immediate: true })

// Initialize SMTP form from fetched settings
watch(smtpSettings, (newSettings) => {
  if (newSettings) {
    smtpForm.value = {
      provider: newSettings.provider,
      host: newSettings.host || '',
      port: newSettings.port || 587,
      username: newSettings.username || '',
      password: '', // Never populate password from server
      use_tls: newSettings.use_tls,
      use_ssl: newSettings.use_ssl,
      from_email: newSettings.from_email || '',
      from_name: newSettings.from_name || ''
    }
  }
}, { immediate: true })

// Fetch settings on mount
onMounted(() => {
  fetchSettings()
  fetchSmtpSettings()
  // Default test email to user's email
  if (auth.user.value?.email) {
    testEmail.value = auth.user.value.email
    smtpTestEmail.value = auth.user.value.email
  }
})

// Track changes
function onSettingChange() {
  hasChanges.value = true
}

// Get setting value with fallback
function getSettingValue(key: string, field: keyof NotificationTypeSettings): boolean | number {
  const setting = localSettings.value[key]
  if (!setting) {
    // Return defaults
    if (field === 'enabled') return true
    if (field === 'auto_send') return true
    if (field === 'hours_before') return 24
  }
  return setting[field] as boolean | number
}

// Update local setting
function updateLocalSetting(key: string, field: keyof NotificationTypeSettings, value: boolean | number) {
  if (!localSettings.value[key]) {
    localSettings.value[key] = { auto_send: true, enabled: true }
  }
  (localSettings.value[key] as Record<string, boolean | number>)[field] = value
  onSettingChange()
}

// Save all settings
async function saveSettings() {
  const success = await updateSettings({ settings: localSettings.value })
  if (success) {
    hasChanges.value = false
  }
}

// Test email connection
async function handleTestEmail() {
  if (!testEmail.value) return
  await testEmailConnection(testEmail.value)
  showTestEmailModal.value = false
}

// Open SMTP configuration modal
function openSmtpModal() {
  // Reset form with current values
  if (smtpSettings.value) {
    smtpForm.value = {
      provider: smtpSettings.value.provider,
      host: smtpSettings.value.host || '',
      port: smtpSettings.value.port || 587,
      username: smtpSettings.value.username || '',
      password: '',
      use_tls: smtpSettings.value.use_tls,
      use_ssl: smtpSettings.value.use_ssl,
      from_email: smtpSettings.value.from_email || '',
      from_name: smtpSettings.value.from_name || ''
    }
  }
  showSmtpModal.value = true
}

// Test SMTP connection
async function handleSmtpTest() {
  if (!smtpForm.value.host || !smtpForm.value.from_email || !smtpTestEmail.value) return

  const request: SmtpTestRequest = {
    host: smtpForm.value.host,
    port: smtpForm.value.port || 587,
    username: smtpForm.value.username,
    password: smtpForm.value.password,
    use_tls: smtpForm.value.use_tls ?? true,
    use_ssl: smtpForm.value.use_ssl ?? false,
    from_email: smtpForm.value.from_email,
    to_email: smtpTestEmail.value
  }

  await testSmtpConnection(request)
}

// Save SMTP settings
async function handleSmtpSave() {
  const dataToSave: SmtpSettingsUpdate = {
    provider: smtpForm.value.provider,
    host: smtpForm.value.host,
    port: smtpForm.value.port,
    username: smtpForm.value.username,
    use_tls: smtpForm.value.use_tls,
    use_ssl: smtpForm.value.use_ssl,
    from_email: smtpForm.value.from_email,
    from_name: smtpForm.value.from_name
  }

  // Only include password if it was entered
  if (smtpForm.value.password) {
    dataToSave.password = smtpForm.value.password
  }

  const success = await updateSmtpSettings(dataToSave)
  if (success) {
    showSmtpModal.value = false
  }
}

// Get status color for SMTP
const smtpStatusColor = computed(() => {
  if (!smtpSettings.value) return 'bg-[var(--color-text-subtle)]'
  if (smtpSettings.value.provider === 'disabled') return 'bg-[var(--color-text-subtle)]'
  if (smtpSettings.value.is_verified) return 'bg-[var(--color-success-accent)]'
  if (smtpSettings.value.host) return 'bg-[var(--color-warning-accent)]'
  return 'bg-[var(--color-text-subtle)]'
})

// Get status text for SMTP
const smtpStatusText = computed(() => {
  if (!smtpSettings.value) return t('notifications.smtp.status.not_configured')
  if (smtpSettings.value.provider === 'disabled') return t('notifications.smtp.status.disabled')
  if (smtpSettings.value.provider === 'console') return t('notifications.smtp.status.console')
  if (smtpSettings.value.is_verified) return t('notifications.smtp.status.verified')
  if (smtpSettings.value.host) return t('notifications.smtp.status.not_verified')
  return t('notifications.smtp.status.not_configured')
})

// Redirect non-admins
if (!isAdmin.value) {
  navigateTo('/settings')
}
</script>

<template>
  <div class="space-y-6">
    <!-- Page header -->
    <div class="flex items-center justify-between">
      <div>
        <div class="flex items-center gap-2 mb-1">
          <NuxtLink
            to="/settings"
            class="text-subtle hover:text-muted dark:text-subtle dark:hover:text-subtle"
          >
            <UIcon
              name="i-lucide-arrow-left"
              class="w-5 h-5"
            />
          </NuxtLink>
          <h1 class="text-display text-default">
            {{ t('notifications.title') }}
          </h1>
        </div>
        <p class="text-muted">
          {{ t('notifications.pageDescription') }}
        </p>
      </div>

      <div class="flex gap-2">
        <UButton
          variant="outline"
          icon="i-lucide-mail-check"
          :loading="isTesting"
          @click="showTestEmailModal = true"
        >
          {{ t('notifications.testConnection') }}
        </UButton>
        <UButton
          v-if="hasChanges"
          icon="i-lucide-save"
          :loading="isSaving"
          @click="saveSettings"
        >
          {{ t('common.save') }}
        </UButton>
      </div>
    </div>

    <!-- Loading state -->
    <div
      v-if="isLoading"
      class="space-y-4"
    >
      <USkeleton class="h-32 w-full" />
      <USkeleton class="h-64 w-full" />
    </div>

    <!-- Settings content -->
    <template v-else>
      <!-- Notification Types Configuration -->
      <UCard>
        <template #header>
          <div class="flex items-center gap-2">
            <UIcon
              name="i-lucide-bell"
              class="w-5 h-5 text-primary-accent"
            />
            <h2 class="font-semibold text-default">
              {{ t('notifications.autoVsManual') }}
            </h2>
          </div>
        </template>

        <p class="text-caption text-subtle mb-6">
          {{ t('notifications.autoVsManualDescription') }}
        </p>

        <div class="overflow-x-auto">
          <table class="w-full">
            <thead>
              <tr class="border-b border-default">
                <th class="text-left py-3 px-4 font-medium text-muted dark:text-subtle">
                  {{ t('notifications.notificationType') }}
                </th>
                <th class="text-center py-3 px-4 font-medium text-muted dark:text-subtle w-24">
                  {{ t('notifications.enabled') }}
                </th>
                <th class="text-center py-3 px-4 font-medium text-muted dark:text-subtle w-32">
                  {{ t('notifications.autoSend') }}
                </th>
                <th class="text-center py-3 px-4 font-medium text-muted dark:text-subtle w-32">
                  {{ t('notifications.options') }}
                </th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="type in notificationTypes"
                :key="type.key"
                class="border-b border-subtle"
              >
                <td class="py-4 px-4">
                  <div>
                    <p class="font-medium text-default">
                      {{ type.label }}
                    </p>
                    <p class="text-caption text-subtle">
                      {{ type.description }}
                    </p>
                  </div>
                </td>
                <td class="py-4 px-4 text-center">
                  <USwitch
                    :model-value="getSettingValue(type.key, 'enabled') as boolean"
                    @update:model-value="(v: boolean) => updateLocalSetting(type.key, 'enabled', v)"
                  />
                </td>
                <td class="py-4 px-4 text-center">
                  <USwitch
                    :model-value="getSettingValue(type.key, 'auto_send') as boolean"
                    :disabled="!getSettingValue(type.key, 'enabled')"
                    @update:model-value="(v: boolean) => updateLocalSetting(type.key, 'auto_send', v)"
                  />
                </td>
                <td class="py-4 px-4 text-center">
                  <div
                    v-if="type.supportsHoursBefore"
                    class="flex items-center justify-center gap-2"
                  >
                    <UInput
                      :model-value="getSettingValue(type.key, 'hours_before') as number"
                      type="number"
                      min="1"
                      max="168"
                      class="w-16"
                      :disabled="!getSettingValue(type.key, 'enabled')"
                      @update:model-value="(v: string | number) => updateLocalSetting(type.key, 'hours_before', Number(v))"
                    />
                    <span class="text-caption text-subtle">{{ t('notifications.hoursBefore') }}</span>
                  </div>
                  <span
                    v-else
                    class="text-subtle"
                  >-</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="mt-6 p-4 alert-surface-info rounded-lg">
          <div class="flex gap-3">
            <UIcon
              name="i-lucide-info"
              class="w-5 h-5 text-info-accent flex-shrink-0 mt-0.5"
            />
            <div class="text-sm text-info">
              <p class="font-medium mb-1">
                {{ t('notifications.infoTitle') }}
              </p>
              <ul class="list-disc list-inside space-y-1">
                <li>{{ t('notifications.infoAutoSend') }}</li>
                <li>{{ t('notifications.infoManualSend') }}</li>
                <li>{{ t('notifications.infoDisabled') }}</li>
              </ul>
            </div>
          </div>
        </div>
      </UCard>

      <!-- SMTP Configuration -->
      <UCard>
        <template #header>
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <UIcon
                name="i-lucide-server"
                class="w-5 h-5 text-primary-accent"
              />
              <h2 class="font-semibold text-default">
                {{ t('notifications.smtp.title') }}
              </h2>
            </div>
            <UButton
              variant="outline"
              size="sm"
              icon="i-lucide-settings"
              :loading="isSmtpLoading"
              @click="openSmtpModal"
            >
              {{ t('notifications.smtp.configure') }}
            </UButton>
          </div>
        </template>

        <div
          v-if="isSmtpLoading"
          class="space-y-3"
        >
          <USkeleton class="h-6 w-48" />
          <USkeleton class="h-4 w-64" />
        </div>

        <div
          v-else
          class="space-y-4"
        >
          <!-- Status indicator -->
          <div class="flex items-center gap-3">
            <div
              class="w-3 h-3 rounded-full"
              :class="smtpStatusColor"
            />
            <span class="text-muted">
              {{ smtpStatusText }}
            </span>
            <UBadge
              v-if="smtpSettings?.is_verified && smtpSettings?.last_verified_at"
              color="neutral"
              variant="subtle"
              size="xs"
            >
              {{ new Date(smtpSettings.last_verified_at).toLocaleDateString() }}
            </UBadge>
          </div>

          <!-- SMTP details if configured -->
          <div
            v-if="smtpSettings?.host && smtpSettings.provider === 'smtp'"
            class="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm"
          >
            <div>
              <span class="text-muted">{{ t('notifications.smtp.host') }}:</span>
              <span class="ml-2 text-default">{{ smtpSettings.host }}:{{ smtpSettings.port }}</span>
            </div>
            <div>
              <span class="text-muted">{{ t('notifications.smtp.fromEmail') }}:</span>
              <span class="ml-2 text-default">{{ smtpSettings.from_email || '-' }}</span>
            </div>
            <div>
              <span class="text-muted">{{ t('notifications.smtp.security') }}:</span>
              <span class="ml-2 text-default">
                {{ smtpSettings.use_ssl ? 'SSL' : smtpSettings.use_tls ? 'TLS' : 'None' }}
              </span>
            </div>
            <div>
              <span class="text-muted">{{ t('notifications.smtp.username') }}:</span>
              <span class="ml-2 text-default">{{ smtpSettings.username || '-' }}</span>
            </div>
          </div>

          <!-- Info message -->
          <p class="text-caption text-subtle">
            {{ t('notifications.smtp.description') }}
          </p>
        </div>
      </UCard>
    </template>

    <!-- Test Email Modal -->
    <UModal v-model:open="showTestEmailModal">
      <template #content>
        <UCard>
          <template #header>
            <div class="flex items-center gap-2">
              <UIcon
                name="i-lucide-mail-check"
                class="w-5 h-5 text-primary-accent"
              />
              <h3 class="font-semibold text-default">
                {{ t('notifications.testEmailTitle') }}
              </h3>
            </div>
          </template>

          <form
            class="space-y-4"
            @submit.prevent="handleTestEmail"
          >
            <p class="text-caption text-subtle">
              {{ t('notifications.testEmailDescription') }}
            </p>

            <UFormField :label="t('common.email')">
              <UInput
                v-model="testEmail"
                type="email"
                required
              />
            </UFormField>

            <div class="flex justify-end gap-2 pt-4">
              <UButton
                variant="ghost"
                @click="showTestEmailModal = false"
              >
                {{ t('common.cancel') }}
              </UButton>
              <UButton
                type="submit"
                :loading="isTesting"
              >
                {{ t('notifications.sendTestEmail') }}
              </UButton>
            </div>
          </form>
        </UCard>
      </template>
    </UModal>

    <!-- SMTP Configuration Modal -->
    <UModal
      v-model:open="showSmtpModal"
      :ui="{ width: 'max-w-2xl' }"
    >
      <template #content>
        <UCard>
          <template #header>
            <div class="flex items-center gap-2">
              <UIcon
                name="i-lucide-server"
                class="w-5 h-5 text-primary-accent"
              />
              <h3 class="font-semibold text-default">
                {{ t('notifications.smtp.title') }}
              </h3>
            </div>
          </template>

          <form
            class="space-y-6"
            @submit.prevent="handleSmtpSave"
          >
            <!-- Provider selection -->
            <UFormField :label="t('notifications.smtp.provider')">
              <USelect
                v-model="smtpForm.provider"
                :items="providerOptions"
                value-key="value"
                label-key="label"
              />
            </UFormField>

            <!-- SMTP Configuration (only shown when provider is smtp) -->
            <template v-if="smtpForm.provider === 'smtp'">
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <UFormField :label="t('notifications.smtp.host')">
                  <UInput
                    v-model="smtpForm.host"
                    placeholder="smtp.example.com"
                    required
                  />
                </UFormField>

                <UFormField :label="t('notifications.smtp.port')">
                  <UInput
                    v-model.number="smtpForm.port"
                    type="number"
                    min="1"
                    max="65535"
                    required
                  />
                </UFormField>
              </div>

              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <UFormField :label="t('notifications.smtp.username')">
                  <UInput
                    v-model="smtpForm.username"
                    placeholder="user@example.com"
                  />
                </UFormField>

                <UFormField :label="t('notifications.smtp.password')">
                  <UInput
                    v-model="smtpForm.password"
                    type="password"
                    :placeholder="smtpSettings?.has_password ? '••••••••' : ''"
                  />
                  <p
                    v-if="smtpSettings?.has_password"
                    class="text-caption text-subtle mt-1"
                  >
                    {{ t('notifications.smtp.passwordHint') }}
                  </p>
                </UFormField>
              </div>

              <div class="flex gap-6">
                <UFormField>
                  <div class="flex items-center gap-2">
                    <USwitch v-model="smtpForm.use_tls" />
                    <span class="text-sm text-muted">{{ t('notifications.smtp.useTls') }}</span>
                  </div>
                </UFormField>

                <UFormField>
                  <div class="flex items-center gap-2">
                    <USwitch v-model="smtpForm.use_ssl" />
                    <span class="text-sm text-muted">{{ t('notifications.smtp.useSsl') }}</span>
                  </div>
                </UFormField>
              </div>

              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <UFormField :label="t('notifications.smtp.fromEmail')">
                  <UInput
                    v-model="smtpForm.from_email"
                    type="email"
                    placeholder="noreply@clinic.com"
                    required
                  />
                </UFormField>

                <UFormField :label="t('notifications.smtp.fromName')">
                  <UInput
                    v-model="smtpForm.from_name"
                    placeholder="Mi Clinica Dental"
                  />
                </UFormField>
              </div>

              <!-- Test connection section -->
              <div class="p-4 bg-surface-muted rounded-lg space-y-3">
                <p class="text-sm font-medium text-muted">
                  {{ t('notifications.smtp.testConnectionTitle') }}
                </p>
                <div class="flex gap-3">
                  <UInput
                    v-model="smtpTestEmail"
                    type="email"
                    :placeholder="t('notifications.smtp.testEmailPlaceholder')"
                    class="flex-1"
                  />
                  <UButton
                    type="button"
                    variant="outline"
                    :loading="isSmtpTesting"
                    :disabled="!smtpForm.host || !smtpForm.from_email || !smtpTestEmail"
                    @click="handleSmtpTest"
                  >
                    {{ t('notifications.smtp.testConnection') }}
                  </UButton>
                </div>
              </div>
            </template>

            <!-- Console mode info -->
            <div
              v-else-if="smtpForm.provider === 'console'"
              class="p-4 alert-surface-info rounded-lg"
            >
              <p class="text-sm text-info">
                {{ t('notifications.smtp.consoleNote') }}
              </p>
            </div>

            <!-- Disabled mode info -->
            <div
              v-else-if="smtpForm.provider === 'disabled'"
              class="p-4 alert-surface-warning rounded-lg"
            >
              <p class="text-sm text-yellow-700">
                {{ t('notifications.smtp.disabledNote') }}
              </p>
            </div>

            <div class="flex justify-end gap-2 pt-4 border-t border-default">
              <UButton
                type="button"
                variant="ghost"
                @click="showSmtpModal = false"
              >
                {{ t('common.cancel') }}
              </UButton>
              <UButton
                type="submit"
                :loading="isSmtpSaving"
              >
                {{ t('common.save') }}
              </UButton>
            </div>
          </form>
        </UCard>
      </template>
    </UModal>
  </div>
</template>
