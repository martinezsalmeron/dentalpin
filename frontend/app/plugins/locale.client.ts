import { STORAGE_KEYS } from '~/constants/storage'

export default defineNuxtPlugin(async (nuxtApp) => {
  const i18n = nuxtApp.$i18n
  const SUPPORTED_LOCALES = ['en', 'es']

  const savedLocale = localStorage.getItem(STORAGE_KEYS.LOCALE)

  if (savedLocale && SUPPORTED_LOCALES.includes(savedLocale) && savedLocale !== i18n.locale.value) {
    await i18n.setLocale(savedLocale)
  }
})
