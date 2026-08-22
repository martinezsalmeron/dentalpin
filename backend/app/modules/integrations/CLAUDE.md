# integrations module

Webhook subscriptions (REST Hooks) for third-party automations — issue
#65. Phase 1 (narrow first slice, approved by Ramón 2026-08-21, see
`notes/dentalpin/65-integrations-api.md` in the contributor's own
notes repo): subscription CRUD, outbox-backed delivery with retry/
backoff/auto-disable, Stripe-style HMAC signing, and exactly one
working trigger (`patient.created`). Public data-read API, API-token
auth, the full trigger catalog, and the Zapier/Make/n8n integrations
are follow-up PRs, not in this module yet.

## What it does

Admin-authenticated CRUD under `/api/v1/integrations/webhooks/
subscriptions` (JWT + `require_permission`, gated behind
`integrations.subscriptions.read`/`.write`). A clinic subscribes to
one or more event types with a target URL; the module signs and
delivers a JSON payload to that URL whenever a subscribed event fires.

## Outbox

`WebhookDelivery` is both the outbox queue row and the audit record
for one delivery attempt — same split as
`notifications.models.CommunicationMessage`. `gateway.py`'s
`WebhookGateway` mirrors `NotificationGateway`'s shape 1:1: `enqueue_
for_event` is DB-only (no network I/O, so a rolled-back publisher
transaction queues nothing), the scheduled `dispatch_outbox` tick
(every 45s) sends with `FOR UPDATE SKIP LOCKED` batching and commits
before each network call so no row lock is held across I/O. Backoff:
`min(60 * 2**(attempts-1), 3600)`, same formula as
`CommunicationMessage`. A subscription auto-disables after
`MAX_CONSECUTIVE_FAILURES` (10) consecutive delivery failures —
`CommunicationMessage` has no equivalent, since it tracks per-message
terminal state, not a per-subscriber circuit breaker.

## Signing

`signing.py` — Stripe's exact scheme. Header
`X-Integrations-Signature`: `t=<unix_ts>,v1=<hex_hmac>`. Signed string
is `f"{timestamp}.{payload}"` over the raw body bytes (never a
re-serialized copy). 5-minute tolerance on verify. A receiver already
carrying a Stripe webhook verifier can reuse it unmodified, minus the
header name.

## Secrets

`WebhookSubscription.secret_encrypted` is Fernet-derived-from-
`SECRET_KEY` (`app.core.email.encryption`) — the 5th consumer of that
scheme (SMTP password, Verifactu PFX password, `whatsapp_kapso`'s API
key and webhook secret, now this). Decided by Ramón 2026-08-21: a
second encryption key wouldn't meaningfully shrink blast radius over
`SECRET_KEY` already signing every JWT. The plaintext secret is
generated server-side (`secrets.token_urlsafe(32)`) and returned
**once**, in the create response only (`WebhookSubscriptionCreated`) —
never logged, never returned again, only decrypted internally to sign
a delivery.

## SSRF guard (`url_safety.py`)

Not in the original issue scoping — `target_url` is clinic-supplied
and the server POSTs to it directly, so it needed the same treatment
as any other server-side-request-forgery surface. Two checkpoints:
`validate_new_url` runs at subscription create/update
(`schemas.py`'s `target_url` validator) — requires `https`, resolves
the hostname, rejects private/loopback/link-local/reserved/multicast
addresses (covers `169.254.169.254` cloud metadata, `127.0.0.1`,
RFC1918, etc.), and rejects a raw IP literal in those ranges directly.
`validate_before_dispatch` runs again in `client.post_webhook`,
immediately before every send — a hostname can be repointed after the
subscription was created (DNS rebinding, or just a delayed re-point),
so validating only once at creation isn't enough. `client.py` also
sets `follow_redirects=False` explicitly, so a receiver can't bounce
a validated request to an unvalidated internal URL via a 3xx.

## Tenancy

Every `WebhookSubscription`/`WebhookDelivery` query filters on
`clinic_id`. `_get_owned_subscription` (router.py) 404s rather than
403s on a cross-clinic subscription id, same as the rest of the repo's
convention for not confirming another clinic's row exists.

## Dependencies

`manifest.depends = ["patients"]` — the one Phase 1 trigger is
`patient.created`.

## Lifecycle

- `installable=True`, `auto_install=False` (repo policy for optional
  modules), `removable=True`.
- Own Alembic branch (`integrations`), rooted on core `"0001"` —
  `int_0001` (initial schema: `webhook_subscriptions`,
  `webhook_deliveries`).

## CHANGELOG

See `./CHANGELOG.md`.
