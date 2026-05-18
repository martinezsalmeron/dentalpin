import { STORAGE_KEYS } from '~/constants/storage'

export function useLocale() {
  const { locale, setLocale, locales } = useI18n()

  const availableLocales = computed(() =>
    (locales.value as Array<{ code: string, name: string }>).map(l => ({
      code: l.code,
      name: l.name
    }))
  )

  async function changeLocale(code: string): Promise<void> {
    if (import.meta.client) {
      localStorage.setItem(STORAGE_KEYS.LOCALE, code)
    }
    await setLocale(code)
  }

  return {
    currentLocale: computed(() => locale.value),
    availableLocales,
    changeLocale
  }
}
