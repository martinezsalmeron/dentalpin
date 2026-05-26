import { test, expect } from './_fixtures'

/**
 * Quick patient creation from the agenda's "Nueva cita" modal.
 *
 * Regression case: the receptionist gets a phone call from a brand-new
 * patient and needs to create the patient + book the slot without
 * leaving the calendar. The "+ Crear" row in the patient selector
 * dropdown opens an inline mini-form that POSTs to /api/v1/patients
 * and auto-selects the created patient in the modal.
 *
 * This spec covers the happy path on desktop. Mobile + duplicate-phone
 * banner are covered by component-level unit tests
 * (`tests/components/patientSelectorUtils.test.ts`) and manual QA;
 * the desktop e2e is the cheapest reliable check that the flow is wired
 * end to end (UI → POST → selected card with "Nuevo" badge).
 */

const API_BASE = process.env.E2E_API_BASE || 'http://localhost:8000'

test.describe('agenda — quick patient create', () => {
  test.use({ role: 'receptionist' })

  test('receptionist creates a new patient from inside the New Appointment modal', async ({ loggedIn }) => {
    await loggedIn.goto('/appointments')
    await loggedIn.waitForURL(/\/appointments/, { timeout: 15_000 })
    // Wait for the page to be quiet — the schedule fires
    // ``GET /agenda/appointments?...`` on mount. Vue's ``@click`` handler
    // is bound only after hydration completes; clicking before that lets
    // the event reach the button DOM but the listener never runs, so the
    // modal silently does not open. ``networkidle`` is the cheapest
    // ready signal we have here.
    await loggedIn.waitForLoadState('networkidle')

    // Open "Nueva cita" via the header button. Desktop only — the mobile
    // entry point is a free-slot tap which is brittle to click reliably
    // from outside the layout.
    const newAppointmentBtn = loggedIn.getByRole('button', { name: /Nueva cita|New appointment/i }).first()
    await expect(newAppointmentBtn).toBeEnabled({ timeout: 10_000 })
    await newAppointmentBtn.click()

    // Modal mounts an async chunk — wait for the patient search input
    // to be ready.
    const searchInput = loggedIn.locator('input[data-testid="visual-selector-input"]').first()
    await expect(searchInput).toBeVisible({ timeout: 10_000 })

    // Type a name that is unique enough to not collide with seed data
    // even when this spec runs multiple times against the same DB.
    const suffix = Date.now().toString().slice(-6)
    const firstName = 'Quickcreate'
    const lastName = `Test ${suffix}`
    const fullName = `${firstName} ${lastName}`

    await searchInput.fill(fullName)

    // The "+ Crear" footer row appears as soon as the dropdown reflects
    // the typed query (debounced 300ms server-side, then settled).
    const createRow = loggedIn.locator('[data-testid="patient-selector-create-row"]')
    await expect(createRow).toBeVisible({ timeout: 5_000 })
    await createRow.click()

    // Mini-form replaces the dropdown.
    const createForm = loggedIn.locator('[data-testid="patient-selector-create-form"]')
    await expect(createForm).toBeVisible()

    // The name split heuristic pre-fills first + last name from the typed query.
    const firstNameField = createForm.getByLabel(/Nombre|First name/i)
    const lastNameField = createForm.getByLabel(/Apellidos|Last name/i)
    await expect(firstNameField).toHaveValue(firstName)
    await expect(lastNameField).toHaveValue(lastName)

    // Optional phone — exercise it so we cover the POST payload branch
    // that includes a phone number.
    const phoneField = createForm.getByLabel(/Teléfono|Phone/i)
    await phoneField.fill(`+34 600 ${suffix}`)

    // Submit — the button is disabled until both names are non-empty,
    // which is already the case (pre-filled).
    await createForm.locator('[data-testid="patient-selector-create-submit"]').click()

    // After success: the selected-patient card replaces the selector,
    // and shows the "Nuevo" badge for this session.
    const selectedName = `${lastName}, ${firstName}`
    await expect(loggedIn.getByText(selectedName, { exact: false })).toBeVisible({ timeout: 5_000 })
    await expect(loggedIn.getByText(/Nuevo|New/i).first()).toBeVisible()

    // Persistence: hit the API directly to confirm the patient was
    // actually created (not just optimistic UI). Going through /patients
    // listing would require an additional render race.
    const ctx = loggedIn.context()
    const cookies = await ctx.cookies()
    const token = cookies.find(c => c.name === 'access_token')?.value
    const res = await ctx.request.get(
      `${API_BASE}/api/v1/patients?search=${encodeURIComponent(lastName)}`,
      { headers: token ? { Authorization: `Bearer ${token}` } : {} }
    )
    expect(res.ok()).toBeTruthy()
    const body = (await res.json()) as { data: Array<{ first_name: string, last_name: string }> }
    const match = body.data.find(p => p.first_name === firstName && p.last_name === lastName)
    expect(match, `expected patient ${fullName} to be persisted`).toBeDefined()
  })

  test('the "+ Crear" row is hidden for a role without patients.write', async ({ page }) => {
    // The hygienist role has clinical.patients.read but not patients.write,
    // so the footer slot must not render.
    // We login inline (not via the fixture) to scope the assertion to this
    // narrow check and avoid logging in twice.
    const ctx = page.context()
    const form = new URLSearchParams({
      username: 'hygienist@demo.clinic',
      password: 'demo1234'
    })
    const loginRes = await ctx.request.post(`${API_BASE}/api/v1/auth/login`, {
      data: form.toString(),
      headers: { 'content-type': 'application/x-www-form-urlencoded' }
    })
    if (!loginRes.ok()) test.skip(true, 'hygienist seed user not available')
    const tokens = (await loginRes.json()) as { access_token: string }
    await ctx.addCookies([{
      name: 'access_token',
      value: tokens.access_token,
      url: 'http://localhost:3000'
    }])

    await page.goto('/appointments')
    await page.waitForLoadState('networkidle')

    // Hygienist may not see the create button — skip if so, the gating
    // is enforced anyway by the receptionist case above.
    const createButton = page.getByRole('button', { name: /Nueva cita|New appointment/i }).first()
    if (!(await createButton.isVisible().catch(() => false))) {
      test.skip(true, 'hygienist cannot open the new-appointment modal in this seed')
    }
    await expect(createButton).toBeEnabled({ timeout: 10_000 })
    await createButton.click()

    const searchInput = page.locator('input[data-testid="visual-selector-input"]').first()
    await expect(searchInput).toBeVisible({ timeout: 10_000 })
    await searchInput.fill('Nonexistent Patient X')

    // Wait long enough for both the debounce (300ms) and a search
    // response to settle before asserting absence.
    await page.waitForTimeout(800)
    const createRow = page.locator('[data-testid="patient-selector-create-row"]')
    await expect(createRow).toHaveCount(0)
  })
})
