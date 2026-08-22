<script setup lang="ts">
// Global banner ("app.banners" slot). Self-fetches settings and hides
// itself unless the clinic has installed india_gst but not yet set a
// GSTIN — mirrors verifactu's RejectedGlobalBanner.vue fast-no-op shape.

import { PERMISSIONS } from '~~/app/config/permissions'

const { t } = useI18n()
const { can } = usePermissions()
const { getSettings } = useIndiaGst()

const showBanner = ref(false)
const dismissed = ref(false)

onMounted(async () => {
  if (!can(PERMISSIONS.indiaGst.settingsRead)) return
  try {
    const settings = await getSettings()
    showBanner.value = !settings.gstin
  } catch {
    // Module not installed for this clinic, or not an India clinic —
    // fail closed (no banner) rather than surface a console error.
    showBanner.value = false
  }
})
</script>

<template>
  <UAlert
    v-if="showBanner && !dismissed"
    color="info"
    variant="subtle"
    icon="i-lucide-receipt-indian-rupee"
    :title="t('indiaGst.banner.unregisteredTitle')"
    :description="t('indiaGst.banner.unregisteredDescription')"
    :close-button="{ icon: 'i-lucide-x', color: 'neutral', variant: 'link' }"
    class="mb-4"
    @close="dismissed = true"
  >
    <template #actions>
      <UButton
        to="/settings/india-gst"
        size="xs"
        variant="soft"
      >
        {{ t('indiaGst.banner.configureAction') }}
      </UButton>
    </template>
  </UAlert>
</template>
