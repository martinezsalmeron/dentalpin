# 0014 — Copilot proactivity v1: deterministic morning digest email

- **Status:** accepted
- **Date:** 2026-06-11
- **Deciders:** Ramón Martínez + AI pair
- **Tags:** copilot, agents, scheduler, email

## Context

The copilot v1 (issue #81, ADR scope in
`docs/technical/copilot-agentic-architecture.md`) deliberately deferred
proactive behaviour. With the tool surface now covering agenda,
recalls, budgets, billing (read) and payments, the highest-value
proactive feature is a small daily push: today's agenda, overdue
recalls and budgets awaiting response — the same data as the "daily
briefing" playbook, delivered without anyone asking.

Candidate delivery channels considered: a seeded copilot conversation
(costs LLM tokens daily whether or not it is read; no push), a
dashboard card (new UI + API + polling), and email (push, zero LLM
cost, reuses core `EmailService` + per-clinic SMTP).

## Decision

Proactivity v1 is an **opt-in, deterministic (no-LLM) morning digest
email**, one recipient per clinic, built by calling READ tools through
the **tool registry** with the recipient's real role permissions.

Clarifications:

- **RBAC for non-interactive contexts**: the digest task builds an
  `AgentContext` whose `permissions = get_role_permissions(role)` for
  the recipient's membership role, and calls `tool_registry.call()` —
  the same chokepoint as the chat bridge. Tools the recipient cannot
  call are silently omitted. No bespoke data queries.
- **No redaction needed**: the digest is human-space output (same trust
  boundary as any notification email to staff); the redactor only
  guards the cloud-LLM path, which the digest never touches.
- **Scheduling**: one hourly APScheduler job (`CronTrigger(minute=0)`)
  filters clinics where `digest_hour == ` server-local hour. Per-clinic
  timezone handling is an explicit open item; budget reminders share
  the same caveat today.
- **Config**: three columns on `copilot_settings`
  (`digest_enabled`, `digest_hour`, `digest_recipient_user_id`).
  Enabling without a recipient defaults to the user flipping the
  switch. Multi-recipient is v2.
- **Off-books safe by construction**: agenda + recalls + budgets-sent
  only. No invoice/payment juxtaposition, no "outstanding debt".
- **Observability**: each send publishes `copilot.digest.sent`.

## Consequences

### Good

- Zero daily LLM cost; failure mode is a missing email, not a wrong one.
- RBAC parity is mechanical (registry chokepoint), not re-implemented.
- Copilot's `depends = []` holds — email via core, data via registry,
  locale via direct `clinics.settings` read.

### Bad / accepted debt

- ~~`app/core/scheduler.py` imports module task functions (copilot,
  budget, notifications, treatment_plan) even when a module is
  uninstalled.~~ **Resolved.** Modules now declare jobs via
  `BaseModule.get_scheduled_jobs()` (returning
  `app.core.scheduling.ScheduledJob` specs); the scheduler iterates the
  *registered* modules and imports no task functions itself, so an
  uninstalled module contributes no job. Applied to all four modules.
- Server-local `digest_hour` is wrong for clinics in other timezones.
  Acceptable for the current deployment; revisit with multi-tenancy
  (ADR 0012).

## Built since (event-driven nudges)

Event-driven nudges shipped: copilot subscribes to `appointment.cancelled`
and persists a short-lived `copilot_nudges` row; the drawer renders a
contextual banner ("Se canceló la cita de las 10:00…") whose prompt feeds
the fill-gap playbook. Implemented as designed — dedupe per appointment
(`uq_copilot_nudge_dedupe`), same-day expiry (`expires_at` = next
clinic-local midnight, expired rows filtered out), and per-viewer
permission gating (`required_permission`, here `recalls.read`). Text and
prompt are rendered client-side from `kind` + `payload` so the row stores
no locale-specific copy. Only the cancellation trigger ships so far;
further triggers are additional handlers under the same table/contract.
