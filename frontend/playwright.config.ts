import { defineConfig, devices } from '@playwright/test'

/**
 * Playwright config for DentalPin browser E2E.
 *
 * Tests drive the live dev stack (Nuxt at :3000, FastAPI at :8000,
 * Postgres seeded via `./scripts/seed-demo.sh`). The suite is
 * deliberately small and focused on smoke + RBAC boundaries; it does
 * NOT exercise every CRUD path (that's the backend pytest suite's
 * job).
 *
 * Run with: `./scripts/e2e.sh`
 */
export default defineConfig({
  testDir: './tests/e2e',
  timeout: 30_000,
  expect: { timeout: 5_000 },
  fullyParallel: false,
  retries: 0,
  workers: 1,
  reporter: [['list']],

  use: {
    baseURL: process.env.E2E_BASE_URL || 'http://localhost:3000',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    actionTimeout: 8_000,
    navigationTimeout: 15_000,
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
})
