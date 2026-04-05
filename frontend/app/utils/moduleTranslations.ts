/**
 * Helper for registering module-specific translations.
 *
 * Usage in a module:
 * ```typescript
 * // modules/inventory/translations.ts
 * export const inventoryTranslations = {
 *   es: { inventory: { title: 'Inventario', items: 'Artículos' } },
 *   en: { inventory: { title: 'Inventory', items: 'Items' } }
 * }
 *
 * // In the module's setup
 * registerModuleTranslations(inventoryTranslations)
 * ```
 */
export function registerModuleTranslations(
  translations: Record<string, Record<string, unknown>>
): void {
  const { mergeLocaleMessage } = useI18n()

  for (const [locale, messages] of Object.entries(translations)) {
    mergeLocaleMessage(locale, messages)
  }
}
