<script setup lang="ts">
/**
 * Settings landing — redirects to the first category visible to the
 * current user. URL stays ``/settings`` for incoming links / shortcuts;
 * the category pages own all editor UI.
 *
 * Receptionist → /settings/account
 * Admin → /settings/general
 */

definePageMeta({ middleware: 'auth' })

const router = useRouter()
const { t } = useI18n()
const registry = useSettingsRegistry()
const { isDesktop } = useBreakpoint()

const target = computed(() => registry.firstVisibleCategory())

onMounted(() => {
  // Desktop: jump straight to the first category. Mobile: stay on the
  // hub so the user picks one — landing into "/settings/general" on a
  // small viewport hides the rest of the IA behind a back button.
  if (isDesktop.value && target.value) {
    router.replace(`/settings/${target.value.id}`)
  }
})

watch(isDesktop, (desktop) => {
  if (desktop && target.value) {
    router.replace(`/settings/${target.value.id}`)
  }
})
</script>

<template>
  <SettingsLayout
    :active-id="null"
    :hide-rail="true"
    :title="t('settings.title')"
    :subtitle="t('settings.subtitle')"
  >
    <OnboardingChecklist class="mb-6" />

    <h2 class="text-h2 text-default mb-3">
      {{ t('settings.allCategories') }}
    </h2>

    <SettingsCategoryNav
      :active-id="null"
      :full-width="true"
    />
  </SettingsLayout>
</template>
