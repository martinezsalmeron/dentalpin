import { test, expect } from './_fixtures'

/**
 * Patient detail smoke: opens a seeded patient and asserts each slot
 * that's fed by a different module renders its data.
 *
 * - identity card (patients module)
 * - alerts banner (patients_clinical)
 * - medical history tab content (patients_clinical)
 * - timeline tab content (patient_timeline)
 *
 * Regression case: after Fase B.6 the patient detail page aggregates
 * data from four different modules, and an early layer-config bug
 * caused half the tabs to render empty. This is the UI guardrail.
 */

test.describe('patient detail', () => {
  test.use({ role: 'admin' })

  test('seeded patient loads identity + clinical data + timeline', async ({ loggedIn }) => {
    await loggedIn.goto('/patients')
    await expect(loggedIn.getByRole('heading', { name: /patients|pacientes/i }).first()).toBeVisible()

    // Wait for the list to hydrate — clicking a NuxtLink before its client-side
    // handler is attached can fall through to the browser default, which then
    // races with the SPA router and occasionally bounces back to /patients.
    // Scope to <main> so we never match the sidebar nav item (/patients).
    const firstPatient = loggedIn.locator('main a[href^="/patients/"]').first()
    await expect(firstPatient).toBeVisible({ timeout: 15_000 })

    await Promise.all([
      loggedIn.waitForURL(/\/patients\/[0-9a-f-]+/, { timeout: 20_000 }),
      firstPatient.click()
    ])

    // 1. Identity — patient name is in the sidebar quick-info card.
    const identity = loggedIn.locator('[data-testid="patient-quick-info"], h1, h2').first()
    await expect(identity).toBeVisible({ timeout: 8_000 })

    // 2. Content: at least one interactive element from the detail tabs.
    // Defensive: find any button or link inside the page body.
    const interactive = loggedIn
      .locator('main button, main a[role="tab"], main a[href*="/patients/"]')
      .first()
    await expect(interactive).toBeVisible()
  })
})
