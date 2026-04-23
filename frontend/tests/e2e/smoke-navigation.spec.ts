import { test, expect } from './_fixtures'

/**
 * Sidebar navigation smoke: every module an admin can see must render
 * its landing page without 404 / 500. The minimum bar after the Fase
 * B.6 layer split — catches broken `modules.json`, missing
 * `components:` registration, or a layer page that crashes in SSR.
 */

const ADMIN_ROUTES = [
  // Home renders a time-of-day greeting ("Good morning, X" / "Buenos días, X")
  // or a welcome empty state when no module registers dashboard slots.
  { path: '/', selector: /home|inicio|dashboard|panel|good (morning|afternoon|evening)|buen(os días|as tardes|as noches)|welcome|bienvenid/i },
  { path: '/patients', selector: /patients|pacientes/i },
  { path: '/appointments', selector: /schedule|agenda|appointment|cita/i },
  { path: '/treatment-plans', selector: /plans|planes|treatment/i },
  { path: '/budgets', selector: /quotes|budgets|presupuesto/i },
  { path: '/invoices', selector: /invoices|facturas/i },
  { path: '/reports', selector: /reports|informes/i },
  { path: '/settings', selector: /settings|configuración|configuracion/i },
  { path: '/settings/catalog', selector: /catalog|catálogo|catalogo/i },
  { path: '/settings/vat-types', selector: /vat|iva/i },
  { path: '/settings/invoice-series', selector: /series|serie/i },
  { path: '/settings/notifications', selector: /notifications|notificaciones/i }
]

test.describe('admin navigation smoke', () => {
  test.use({ role: 'admin' })

  for (const { path, selector } of ADMIN_ROUTES) {
    test(`renders ${path}`, async ({ loggedIn }) => {
      const response = await loggedIn.goto(path, { waitUntil: 'domcontentloaded' })
      expect(response?.status() ?? 0).toBeLessThan(400)
      // The route renders *something* matching its section — either a
      // heading, a button, or a link. `toBeVisible` accepts the first
      // hit so the assertion stays independent of component layout
      // churn.
      // Scope to the page main content so the sidebar links don't
      // fire false positives.
      const main = loggedIn.getByRole('main').first()
      const heading = main.getByRole('heading', { name: selector })
      const link = main.getByRole('link', { name: selector })
      const button = main.getByRole('button', { name: selector })
      await expect(heading.or(link).or(button).first()).toBeVisible({ timeout: 8_000 })
    })
  }
})
