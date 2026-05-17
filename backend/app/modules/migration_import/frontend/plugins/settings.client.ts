/**
 * Registers the DPMF migration page under /settings/workspace.
 *
 * Gated on `migration_import.job.read`. The Execute button inside the
 * page checks `migration_import.job.execute` separately so view-only
 * roles (none today by default) can still inspect history.
 */
import { registerSettingsPage } from '~~/app/composables/useSettingsRegistry'

export default defineNuxtPlugin(() => {
  registerSettingsPage({
    path: 'data-migration',
    category: 'workspace',
    labelKey: 'migrationImport.settingsCard.title',
    descriptionKey: 'migrationImport.settingsCard.description',
    icon: 'i-lucide-database-zap',
    permission: 'migration_import.job.read',
    component: () => import('../components/settings/DataMigrationPage.vue'),
    searchKeywords: ['migracion', 'importar', 'gesden', 'dpmf', 'dental-bridge', 'migration', 'import'],
    order: 90
  })
})
