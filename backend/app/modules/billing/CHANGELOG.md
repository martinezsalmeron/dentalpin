# Changelog — billing module

## Unreleased

- Added per-module `CLAUDE.md` for AI-agent context (2026-04-27).

## 0.1.0 — initial

- Invoice + credit note workflow with PDF generation.
- Payment recording (full and partial).
- `BillingComplianceHook` extension point for compliance modules.
- Events: `invoice.issued`, `invoice.sent`, `invoice.paid`.
