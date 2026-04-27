# Verifactu module

Spanish AEAT compliance (Veri\*Factu, RD 1007/2023). The deep
operator-facing guide is `./README.md` — start there for producer
responsibility, deployment models, and the AEAT integration. This
file is the agent quick reference.

## Public API

Routes mounted at `/api/v1/verifactu/`. Settings, certificate
management, queue inspection, records.

## Dependencies

`manifest.depends = ["billing", "catalog"]`.

## Permissions

`verifactu.settings.{read,configure}`,
`verifactu.records.read`,
`verifactu.queue.manage`.

## Events emitted

None.

## Events consumed

- `invoice.paid` → updates `compliance_data['ES']` on the invoice.

The producer reaction to `invoice.issued` happens via
`BillingComplianceHook` (synchronous hook), **not** via the event bus,
because the chained-hash invariant requires deterministic ordering.
See `hook.py` and `README.md` for the architecture.

## Lifecycle

- `auto_install=False` — operator activates from Admin → Modules.
- `removable=True`, but `uninstall()` blocks if any record reached
  `accepted` state (legal retention, 4 years).
- Migrations on the `verifactu` Alembic branch.

## Gotchas

- **Producer wizard must be filled before `prod`.** The backend rejects
  enabling Veri\*Factu in production until the declaración is signed.
- **Chained hash invariant.** Records form a SHA-256 chain. Skipping or
  reordering breaks the chain and AEAT will reject everything after.
  Hence the synchronous `BillingComplianceHook` instead of the event
  bus on `invoice.issued`.
- **Per-clinic FNMT certificate.** Encrypted at rest with Fernet
  derived from `SECRET_KEY` — rotating `SECRET_KEY` requires
  re-encrypting certificates. Document this in any ops runbook change.
- **Test vs prod environments.** `prewww1.aeat.es` for test,
  `www1.agenciatributaria.gob.es` for prod. Flipping requires admin
  confirmation in the wizard.
- **Producer responsibility is per-deployment.** SaaS operator,
  self-hosting clinic, or integrator — they each carry it differently.
  See `README.md` "Producer responsibility".

## Related ADRs

- `docs/adr/0001-modular-plugin-architecture.md`
- `docs/adr/0002-per-module-alembic-branches.md`
- `docs/adr/0003-event-bus-over-direct-imports.md` (and the
  documented exception — `BillingComplianceHook`)
- `docs/adr/0004-bsl-license.md`

## CHANGELOG

See `./CHANGELOG.md`.
