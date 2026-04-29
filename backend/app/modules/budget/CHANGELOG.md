# Changelog — budget module

## Unreleased

- Added per-module `CLAUDE.md` for AI-agent context (2026-04-27).

### Added (patient view, 2026-04-29 — PR3)

- Patient-facing public budget view at ``/p/budget/<token>``
  (frontend route allowlisted in ``auth.global.ts``).
- New ``public`` Nuxt layout — clinic header, mobile-first content,
  no app sidebar.
- ``usePublicBudget`` composable wrapping the six public endpoints
  with ``credentials: 'include'`` so the HttpOnly cookie session
  flows through.
- ``BudgetVerifyForm`` component renders the right input per
  ``meta.method`` (phone_last4 / dob / manual_code) and surfaces
  the error states (invalid, locked, rate_limited, expired).
- Page state machine: cold (locked / expired / already-decided) →
  verify form → budget detail with three CTAs (accept with
  optional signature, reject with reason, "I have questions" /
  request changes).
- i18n strings for the whole patient flow under
  ``budget.public.*`` in ES + EN.

### Added (frontend, 2026-04-29 — PR2)

- Workflow modals (`components/clinical/modals/`):
  `RenegotiateBudgetModal`, `AcceptInClinicModal`,
  `SetPublicCodeModal`. The accept-in-clinic modal includes an
  optional canvas signature pad (PNG-encoded).
- Settings area `/settings/budgets/{,expiry,reminders,public-link}`
  with a new `useBudgetSettings` composable wired to
  `GET / PATCH /api/v1/auth/clinic/settings/budget` (admin-only).
- New i18n strings for the budget workflow + settings copy.

### Added (plan/budget workflow rework, 2026-04-29 — PR1)

- Acceptance / rejection metadata: `accepted_via`, `rejection_reason`,
  `rejection_note` columns. `accept_budget` accepts an
  `accepted_via` argument (`remote_link` / `in_clinic` / `manual`).
- Public-link 2-factor auth (ADR 0006): new columns `public_token`
  (UUID, unique), `public_auth_method`, `public_auth_secret_hash`,
  `public_locked_at`, `viewed_at`, `last_reminder_sent_at`.
- New table `budget_access_logs` for verification audit + rate
  limit + lockout.
- Plan denormalization columns `plan_number_snapshot` /
  `plan_status_snapshot` so endpoints in this module render plan
  context without importing `treatment_plan` ORM models.
- Workflow methods: `cancel_for_renegotiation`, `mark_viewed`,
  `send_reminder`, `set_public_code`, `unlock_public`,
  `clone_to_new_draft`, `resolve_public_auth_method`,
  `verify_public_access`. `BudgetService.create_from_plan_snapshot`
  builds the draft budget when a plan is confirmed (idempotent).
- Six public endpoints under `/api/v1/public/budgets/{token}/`:
  `meta`, `verify`, `GET /`, `accept`, `reject`, `request-changes`.
  Cookie session (HS256, scoped to token, TTL 30min) signed with
  `BUDGET_PUBLIC_SECRET_KEY`.
- Six authenticated endpoints: `renegotiate`, `accept-in-clinic`,
  `resend`, `send-reminder`, `set-public-code`, `unlock-public`.
- Granular permissions `budget.{renegotiate,accept_in_clinic}`.
- New events with snapshot payloads: `budget.expired`,
  `budget.renegotiated`, `budget.viewed`, `budget.reminder_sent`.
  `budget.rejected` now also published with snapshot.
- Cron jobs (`backend/app/modules/budget/tasks.py`):
  `expire_budgets` (daily 02:00), `send_budget_reminders` (daily
  09:00), `purge_budget_access_logs` (daily 04:00, 90-day retention).
- `manifest.depends` now declares `odontogram` to match the existing
  `budget_items.treatment_id` FK.

### Refactored — module isolation (ADR 0003)

- Removed cross-module ORM imports from event handlers
  (`__init__.py`) and `router.py`. Snapshot-based event payloads
  carry the data needed; the budget detail endpoint reads the
  linked plan via raw SQL.
- `budget` no longer imports `app.modules.treatment_plan` or
  `app.modules.odontogram` at runtime.

## 0.1.0 — initial

- Budget creation + versioning + signature workflow.
- PDF generation.
- Events emitted: `budget.sent`, `budget.accepted`.
- Bidirectional sync with `treatment_plan` via events.
