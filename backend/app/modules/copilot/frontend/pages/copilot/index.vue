<script setup lang="ts">
import { PERMISSIONS } from '~/config/permissions'

const { t } = useI18n()
const { can } = usePermissions()

if (!can(PERMISSIONS.copilot.chat)) {
  throw createError({ statusCode: 403, statusMessage: 'Forbidden' })
}
</script>

<template>
  <div class="mx-auto flex h-[calc(100vh-8rem)] max-w-3xl flex-col">
    <div class="mb-3">
      <h1 class="text-xl font-semibold">
        {{ t('copilot.page.title') }}
      </h1>
      <p class="text-sm text-muted">
        {{ t('copilot.page.subtitle') }}
      </p>
    </div>

    <UCard
      class="flex-1 overflow-hidden"
      :ui="{ body: 'h-full p-3 sm:p-4' }"
    >
      <CopilotDrawer />
    </UCard>
  </div>
</template>
