/**
 * Registers the host-owned settings pages with the registry. Modules
 * register their own pages via their own client plugins (same pattern
 * as the existing slot system).
 */
import {
  registerSettingsPage,
  registerGettingStartedRule
} from '~/composables/useSettingsRegistry'

export default defineNuxtPlugin(() => {
  // ---- General -------------------------------------------------------
  registerSettingsPage({
    path: 'clinic',
    category: 'general',
    labelKey: 'settings.clinicInfo',
    descriptionKey: 'settings.clinicInfoDescription',
    icon: 'i-lucide-building-2',
    permission: 'admin.clinic.read',
    component: () => import('~/components/settings/pages/ClinicInfoPage.vue'),
    searchKeywords: ['clinica', 'clinic', 'cif', 'nif', 'razon social', 'direccion', 'address', 'tax id'],
    order: 10
  })

  // ---- Workspace -----------------------------------------------------
  registerSettingsPage({
    path: 'cabinets',
    category: 'workspace',
    labelKey: 'settings.cabinets',
    descriptionKey: 'settings.cabinetsDescription',
    icon: 'i-lucide-door-open',
    component: () => import('~/components/settings/pages/CabinetsPage.vue'),
    searchKeywords: ['gabinete', 'sala', 'box', 'consulta', 'cabinet', 'room'],
    order: 10
  })

  // ---- People --------------------------------------------------------
  registerSettingsPage({
    path: 'users',
    category: 'people',
    labelKey: 'settings.users',
    descriptionKey: 'settings.usersDescription',
    icon: 'i-lucide-users',
    permission: 'admin.users.read',
    component: () => import('~/components/settings/pages/UsersPage.vue'),
    searchKeywords: ['usuarios', 'users', 'roles', 'permisos', 'staff', 'equipo', 'team'],
    order: 10
  })

  // ---- Clinical (stub) ----------------------------------------------
  registerSettingsPage({
    path: 'catalog',
    category: 'clinical',
    labelKey: 'catalog.title',
    descriptionKey: 'catalog.description',
    icon: 'i-lucide-list',
    permission: 'admin.clinic.read',
    to: '/settings/catalog',
    searchKeywords: ['catalogo', 'catalog', 'tratamientos', 'treatments', 'precios', 'prices'],
    order: 10
  })

  // ---- Billing (module-provided pages) ------------------------------
  registerSettingsPage({
    path: 'invoice-series',
    category: 'billing',
    labelKey: 'invoiceSeries.title',
    descriptionKey: 'invoiceSeries.description',
    icon: 'i-lucide-hash',
    permission: 'admin.clinic.read',
    to: '/settings/invoice-series',
    searchKeywords: ['series', 'numeracion', 'invoice', 'numbering', 'factura'],
    order: 10
  })
  registerSettingsPage({
    path: 'vat-types',
    category: 'billing',
    labelKey: 'vatTypes.title',
    descriptionKey: 'vatTypes.description',
    icon: 'i-lucide-percent',
    permission: 'admin.clinic.read',
    to: '/settings/vat-types',
    searchKeywords: ['iva', 'vat', 'impuesto', 'tax'],
    order: 20
  })

  // ---- Communications (module-provided pages) ----------------------
  registerSettingsPage({
    path: 'notifications',
    category: 'communications',
    labelKey: 'notifications.title',
    descriptionKey: 'notifications.description',
    icon: 'i-lucide-mail',
    permission: 'admin.clinic.read',
    to: '/settings/notifications',
    searchKeywords: ['email', 'smtp', 'plantillas', 'templates', 'notificaciones', 'notifications'],
    order: 10
  })

  // ---- Modules (link to existing /settings/modules) -----------------
  registerSettingsPage({
    path: 'manage',
    category: 'modules',
    labelKey: 'settings.modules.title',
    descriptionKey: 'settings.modules.description',
    icon: 'i-lucide-blocks',
    permission: 'admin.clinic.read',
    to: '/settings/modules',
    searchKeywords: ['modulo', 'module', 'plugin', 'instalar', 'install'],
    order: 10
  })

  // ---- Account -------------------------------------------------------
  registerSettingsPage({
    path: 'profile',
    category: 'account',
    labelKey: 'settings.profile',
    descriptionKey: 'settings.profileDescription',
    icon: 'i-lucide-user',
    component: () => import('~/components/settings/pages/ProfilePage.vue'),
    searchKeywords: ['perfil', 'profile', 'cuenta', 'account'],
    order: 10
  })
  registerSettingsPage({
    path: 'language',
    category: 'account',
    labelKey: 'settings.language',
    descriptionKey: 'settings.languageDescription',
    icon: 'i-lucide-languages',
    component: () => import('~/components/settings/pages/LanguagePage.vue'),
    searchKeywords: ['idioma', 'language', 'locale', 'lang'],
    order: 20
  })

  // ---- Onboarding rules ---------------------------------------------
  // Rules read state lazily inside the predicate to stay reactive
  // across login transitions.
  registerGettingStartedRule({
    id: 'clinic-info-incomplete',
    labelKey: 'settings.onboarding.items.clinicInfo.label',
    descriptionKey: 'settings.onboarding.items.clinicInfo.description',
    icon: 'i-lucide-building-2',
    to: '/settings/general/clinic',
    severity: 'warning',
    when: () => {
      const clinic = useClinic()
      const c = clinic.currentClinic.value
      if (!c) return false
      return !c.name || !c.tax_id || !c.address?.street
    }
  })

  registerGettingStartedRule({
    id: 'no-cabinets',
    labelKey: 'settings.onboarding.items.cabinets.label',
    descriptionKey: 'settings.onboarding.items.cabinets.description',
    icon: 'i-lucide-door-open',
    to: '/settings/workspace/cabinets',
    severity: 'info',
    when: () => {
      const clinic = useClinic()
      return clinic.cabinets.value.length === 0
    }
  })
})
