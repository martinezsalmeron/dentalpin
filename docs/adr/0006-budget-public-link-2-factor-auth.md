# 0006 — Budget public link two-factor authentication

- **Status:** accepted
- **Date:** 2026-04-28
- **Deciders:** Ramon Martinez
- **Tags:** security, privacy, budget, public-api

## Context

When a clinic sends a treatment budget to a patient, the patient receives
an email/SMS with a link to a public web view containing personally
identifiable information (PII): full name, treatments, prices, dates,
clinic identity. Under Spanish LOPD and EU GDPR this is sensitive
sanitary information.

Today the design contemplated a single UUID v4 token in the URL as the
sole access factor. The UUID protects against guessing (≈10³⁸ search
space), but it does **not** protect against link sharing: if the email is
forwarded, the link is pasted in WhatsApp, the URL is screenshotted, or
the patient's email account is compromised, the budget becomes visible
to whoever holds the link.

Concrete risk surfaces:

- Email forwarded to family members on a shared account.
- Browser history / cache on a shared device.
- URL pasted into messaging apps with public previews.
- Search-engine indexing if the URL leaks (mitigated separately with
  `noindex` headers, but not sufficient on its own).
- Compromise of an email account.

We need a second factor of authentication that is cheap, low-friction,
universally available to dental patients (including elderly / low
digital literacy), and does not require a separate channel that the
clinic does not already operate.

## Decision

The public budget link is protected by **two factors**:

1. **Possession factor:** UUID v4 `public_token` embedded in the URL.
2. **Knowledge factor:** a piece of patient data verified through a
   server-side endpoint, with rate limiting and lockout. The method is
   resolved deterministically at send time and stored in
   `budgets.public_auth_method`. Cascade:

   1. **`phone_last4`** — last 4 numeric digits of the patient's phone
      number. Default. Used when the patient record has a phone with
      ≥4 digits.
   2. **`dob`** — patient's date of birth, as ISO date. Used when phone
      is missing.
   3. **`manual_code`** — a 4-6 digit numeric code configured by
      reception staff at send time, hashed with bcrypt/argon2 and
      stored in `budgets.public_auth_secret_hash`. Used when both
      phone and DOB are missing. The clinic communicates this code to
      the patient **verbally**, not through the same channel as the
      link, so a compromised email does not compromise both factors.

   Per-clinic toggle `clinic.settings.budget_public_auth_disabled` (off
   by default) lets a clinic opt out and accept the risk; it sets
   `public_auth_method = "none"` for new budgets.

Successful verification issues an **HttpOnly + Secure + SameSite=Strict
cookie** scoped to `/api/v1/public/budgets/<token>`, signed with a
dedicated secret `BUDGET_PUBLIC_SECRET_KEY` independent of the global
`SECRET_KEY` used for staff JWTs. TTL: 30 minutes, renewed on every
authenticated request.

**Rate limiting and lockout** are enforced server-side over a new
`budget_access_logs` table:

- 5 failed attempts per token in 15 minutes → 429.
- 10 total failed attempts → `budgets.public_locked_at` is set, the
  token becomes invalid, the budget moves to "needs reissue", and
  reception receives a notification. Reissue creates a new budget
  version with a new token; the old token is permanently dead.
- 20 failed attempts per IP per hour → 429 across all public endpoints.

## Consequences

### Good

- Strong protection against link-sharing leaks at zero variable cost
  (no SMS gateway).
- Universally available factors: virtually every dental patient knows
  their phone number or date of birth.
- The `manual_code` fallback gives reception an in-person/phone-call
  channel that is independent from the link's channel — meaningful 2FA.
- Independent secret (`BUDGET_PUBLIC_SECRET_KEY`) limits blast radius
  if one of the keys leaks; allows independent rotation.
- Lockout policy converts brute force into an operational signal
  (reception notified) instead of silently allowing more attempts.
- Auditable: every verification attempt is logged with a hashed IP and
  the method attempted.

### Bad / accepted trade-offs

- Adds a small UX step for the patient before reading the budget.
  Mitigated by a mobile-first verify form with autofocus and clear
  copy.
- If the patient record has stale phone or DOB, the legitimate patient
  may fail verification and need reception to reissue. Operationally
  acceptable.
- The `manual_code` fallback depends on reception following the
  policy of communicating the code verbally. The
  `SetPublicCodeModal.vue` UI explicitly states this in copy; the
  email template never includes the code.
- Logs require a retention policy (90 days, see cron
  `purge_budget_access_logs`) to avoid unbounded growth and to comply
  with privacy expectations.
- Brute-force resistance of the 4-digit `manual_code` relies on the
  lockout, not on the search space alone.

## Alternatives considered

- **UUID-only (status quo of the original draft).** Rejected: does not
  defend against link sharing, which is the dominant real-world threat.
- **Random password sent in the same email.** Rejected: zero security
  gain. Compromise of the email channel exposes both factors.
- **OTP via SMS at link open.** Rejected for MVP: requires SMS gateway
  integration (Twilio/MessageBird), recurring per-message cost in EUR,
  and adds friction without commensurate benefit when phone-last-4 +
  lockout already meets the threat model. Reconsidered for v2 if
  audit data shows the current scheme insufficient.
- **DOB + phone-last-4 multi-factor.** Rejected as default: better
  search space (~3.6 × 10⁷) but doubles friction. The lockout in the
  single-factor design already makes brute force infeasible.
- **Static per-clinic password.** Rejected: not patient-specific,
  shared secret risk, no audit trail.

## How to verify the rule still holds

- Tests:
  - `backend/app/modules/budget/tests/test_public_auth.py`
    exercises the cascade (phone present → phone, no phone → DOB,
    neither → manual_code required), constant-time comparison of
    `manual_code`, lockout after threshold, cookie issuance and
    expiry, expired-token gate, locked-token gate.
  - `backend/app/modules/budget/tests/test_public_endpoints.py`
    covers idempotency (double accept → 409), rate limiting,
    `valid_until` enforcement.
- The endpoint set requires the `public_session` dependency on every
  data-bearing route except `/meta` and `/verify`. A grep in CI:
  `rg -n 'public/budgets/\{token\}' backend/app/modules/budget/router.py`
  must show that all data-bearing routes use the dependency.

## References

- `backend/app/modules/budget/models.py` (Budget public_token,
  public_auth_*, public_locked_at; BudgetAccessLog).
- `backend/app/modules/budget/workflow.py` (resolve_public_auth_method,
  verify_public_access).
- `backend/app/modules/budget/router.py` (public endpoints, cookie
  dependency).
- `backend/app/core/scheduler.py` (purge_budget_access_logs).
- `docs/workflows/plan-budget-flow-tech-plan.md` §1.4, §5.2.
- `docs/workflows/plan-budget-flow.md` (patient verification step).
