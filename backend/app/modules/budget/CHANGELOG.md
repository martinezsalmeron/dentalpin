# Changelog — budget module

## Unreleased

- Added per-module `CLAUDE.md` for AI-agent context (2026-04-27).

### Added (signed PDF, 2026-04-28)

- Signed-PDF generation: ``BudgetPDFService.generate_pdf`` now
  accepts an optional ``BudgetSignature``. When provided, the PDF
  embeds the captured PNG plus an audit footer (signed_by,
  signed_at, signature_method, document_hash).
- ``BudgetWorkflowService.accept_budget`` renders the signed PDF
  immediately after creating the signature and persists the SHA-
  256 of those bytes on ``BudgetSignature.document_hash`` —
  tamper detection for any future re-render.
- Staff endpoints:
  - ``GET /api/v1/budget/budgets/{id}/pdf/signed`` — 404 when no
    signature exists, otherwise the signed PDF (``Cache-Control:
    private, no-store``).
  - ``GET /api/v1/budget/budgets/{id}/signature`` — signature
    metadata (no raw PNG payload) via the new
    ``SignatureMetaResponse`` schema.
- Public endpoint:
  - ``GET /api/v1/budget/public/budgets/{token}/pdf/signed`` —
    cookie-protected (same per-token JWT cookie as the rest of
    the public flow), 404 when not yet accepted, rate-limited to
    10/minute per token, audit row appended to
    ``BudgetAccessLog`` with ``method_attempted=
    "download_signed_pdf"`` and ``success=True`` (so it never
    contributes to the lockout counter).
- Frontend:
  - Staff: new ``BudgetSignatureCard.vue`` mounted on the budget
    detail page when ``status ∈ {accepted, completed}``. Shows
    signed_by / signed_at / method / relationship / hash and a
    "Download signed PDF" button. Backed by
    ``useBudgets().fetchSignature`` + ``downloadSignedPDF``.
  - Public: download button on the ``already_accepted`` state of
    ``/p/budget/<token>``. On 401 (cookie expired) the page
    shows the verify form again and retries the download once
    the patient re-verifies.
- i18n: ``budget.signature.{signedAt, methodLabel,
  relationshipLabel, documentHash, hashHint, downloadSignedPdf,
  downloadError, notSigned, method.{drawn,clickAccept,external}}``
  and ``budget.public.download.{signedPdf, notSigned, error,
  reauthIntro}`` in ES + EN.

### Removed (2026-04-29)

- ``BudgetWorkflowService.complete_budget`` + ``POST /budgets/{id}/complete``
  endpoint + the "Marcar completado" button. The transition
  ``accepted → completed`` was a bookkeeping flag with no auto-
  trigger and no real consumer (the documented ``budget.completed``
  event was never actually published). Use invoice paid / fully
  invoiced as the financial-closure signal instead. The
  ``InvoiceService.on_budget_completed`` handler in billing is
  also removed.
- Frontend: ``completeBudget`` action and ``canComplete`` helper
  in ``useBudgets``; the ``budget.actions.complete`` and
  ``budget.messages.completed`` i18n keys.

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
