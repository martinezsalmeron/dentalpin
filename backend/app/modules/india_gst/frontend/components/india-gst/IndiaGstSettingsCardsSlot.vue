<script setup lang="ts">
import { PERMISSIONS } from '~~/app/config/permissions'

const { t } = useI18n()
const { can } = usePermissions()

const canRead = computed(() => can(PERMISSIONS.indiaGst.settingsRead))
</script>

<template>
  <div
    v-if="canRead"
    class="grid grid-cols-1 md:grid-cols-2 gap-4"
  >
    <SettingsSection
      icon="i-lucide-receipt-indian-rupee"
      :title="t('indiaGst.settingsCards.title')"
      :subtitle="t('indiaGst.settingsCards.description')"
      to="/settings/india-gst"
    />
  </div>
</template>
