/**
 * Registers schedules' settings pages on the host registry. Mounted as
 * cards under ``/settings/workspace`` and as full pages at
 * ``/settings/workspace/<path>`` via the host's dynamic category route.
 *
 * The host is consumed via ``~~`` (frontend root), the same boundary
 * used by the existing slot system. No cross-module import: schedules
 * only depends on the host shell, not on other modules.
 */
import { registerSettingsPage } from '~~/app/composables/useSettingsRegistry'

export default defineNuxtPlugin(() => {
  registerSettingsPage({
    path: 'clinic-hours',
    category: 'workspace',
    labelKey: 'schedules.settingsCards.clinicHoursTitle',
    descriptionKey: 'schedules.settingsCards.clinicHoursDescription',
    icon: 'i-lucide-building-2',
    permission: 'schedules.clinic_hours.read',
    component: () => import('../components/settings/ClinicHoursPage.vue'),
    searchKeywords: ['horario', 'clinica', 'hours', 'clinic', 'agenda', 'apertura'],
    order: 20
  })

  registerSettingsPage({
    path: 'professional-schedules',
    category: 'workspace',
    labelKey: 'schedules.settingsCards.professionalHoursTitle',
    descriptionKey: 'schedules.settingsCards.professionalHoursDescription',
    icon: 'i-lucide-user-cog',
    // canAny: dentist/hygienist hold ``own.read``; assistant/receptionist
    // hold the broader ``professional.read``. Admin matches via ``*``.
    permission: ['schedules.professional.read', 'schedules.professional.own.read'],
    component: () => import('../components/settings/ProfessionalSchedulesPage.vue'),
    searchKeywords: ['profesional', 'professional', 'doctor', 'dentista', 'horario', 'turnos'],
    order: 30
  })
})
