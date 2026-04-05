export default defineNuxtPlugin(async (nuxtApp) => {
  const i18n = nuxtApp.$i18n

  const STORAGE_KEY = 'dentalpin:locale'
  const SUPPORTED_LOCALES = ['en', 'es']

  const savedLocale = localStorage.getItem(STORAGE_KEY)

  if (savedLocale && SUPPORTED_LOCALES.includes(savedLocale) && savedLocale !== i18n.locale.value) {
    await i18n.setLocale(savedLocale)
  }
})
