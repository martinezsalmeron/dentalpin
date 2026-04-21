# End-to-end testing

DentalPin ships a small [Playwright](https://playwright.dev/) suite
under `frontend/tests/e2e/` that drives the live dev stack. It is
deliberately narrow — **smoke only** — because the bulk of the
regression safety comes from the backend `pytest` suite. E2E exists
to catch whole-stack integration regressions that unit tests miss:
broken Nuxt-layer wiring, CORS issues, SSR-only crashes, nav
permission drift.

## Prerequisites

Playwright's precompiled Chromium needs glibc, so the suite runs on
the **host** (macOS / Linux), not inside the Alpine-based frontend
container. One-time setup:

```bash
cd frontend
npm install
npx playwright install chromium
```

## Running

```bash
# From repo root with docker-compose up + demo data seeded:
./scripts/e2e.sh              # full suite
./scripts/e2e.sh rbac         # single file
./scripts/e2e.sh --ui         # open Playwright UI runner
```

The script waits for `http://localhost:3000/login` to respond before
handing off to Playwright.

## What's covered

- `smoke-navigation.spec.ts` — admin visits every route in the
  sidebar and asserts the page renders (status < 400 + a visible
  heading/link/button in main content). Catches broken
  `modules.json`, layer `components:` misconfig, SSR crashes.
- `smoke-patient-detail.spec.ts` — opens the first seeded patient,
  asserts identity + at least one content element. Guards against
  the Fase B.6 "empty tabs" regression class.
- `rbac.spec.ts` — logs in as hygienist / receptionist / dentist and
  asserts the sidebar exposes the expected subset of modules.

## Login strategy

`tests/e2e/_fixtures.ts` logs in by POSTing directly to
`/api/v1/auth/login` and setting the `access_token` cookie. The UI
form works fine in a real browser, but Chromium's cross-origin
fetch from Playwright sometimes flakes on the preflight. Skipping
the form saves a few seconds per test and sidesteps that.

All five seeded roles share `demo1234` as the password.

## Rate limiter

`auth/router.py` disables the rate limiter outside of
`ENVIRONMENT=production`, so local and CI runs don't hit the 5/min
`/login` cap.

## What the suite does NOT do

- CRUD smoke for every entity. The backend pytest suite covers that,
  and duplicating it in the browser is expensive + flaky.
- Visual regression. Out of scope for v1.
- Cross-browser. Chromium only; Firefox / WebKit can be added when
  the suite stabilises.

## Adding a test

```ts
import { test, expect } from './_fixtures'

test.describe('example', () => {
  test.use({ role: 'admin' })   // optional — default is admin

  test('does the thing', async ({ loggedIn }) => {
    await loggedIn.goto('/path')
    await expect(loggedIn.getByRole('heading', { name: /foo/i })).toBeVisible()
  })
})
```

Fixture choices:
- `role: 'dentist' | 'hygienist' | 'assistant' | 'receptionist' | 'admin'`
- `loggedIn: Page` — a Playwright Page already authenticated as
  `role`. Prefer this over raw `page` so specs stay independent.
