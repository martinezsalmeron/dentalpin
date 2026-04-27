# Changelog — verifactu module

## Unreleased

- Added per-module `CLAUDE.md` for AI-agent context (2026-04-27).

## 0.1.0 — initial

- AEAT Veri\*Factu submissions with chained SHA-256 hash.
- Per-clinic FNMT certificate, encrypted at rest.
- Producer wizard with declaración responsable signature.
- Test vs prod toggle with admin confirmation.
- Auto-install disabled; `removable=True` with retention guard.
- Subscribes to `invoice.paid`. Hooks into `invoice.issued` via
  `BillingComplianceHook` (synchronous, not event-bus, due to
  chained-hash invariant).
