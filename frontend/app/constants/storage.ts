export const STORAGE_KEYS = {
  LOCALE: 'dentalpin:locale',
  DENSITY: 'ui:density',
  onboardingDismissed: (clinicId: string) =>
    `dentalpin.settings.onboarding.dismissed:${clinicId}`,
} as const
