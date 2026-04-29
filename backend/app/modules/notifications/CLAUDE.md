# Notifications module

Email templates, preferences, SMTP, event-driven sending. Heavy
subscriber.

## Public API

Routes mounted at `/api/v1/notifications/` (templates, preferences,
settings, logs).

## Dependencies

`manifest.depends = ["patients", "agenda", "budget", "billing"]`.

## Permissions

`notifications.send`,
`notifications.templates.{read,write}`,
`notifications.preferences.{read,write}`,
`notifications.settings.{read,write}`,
`notifications.logs.read`.

## Events emitted

None.

## Events consumed

- `patient.created`
- `appointment.scheduled` / `appointment.cancelled`
- `budget.sent` / `budget.accepted`
- `invoice.sent`

## Lifecycle

- `removable=False`. Even when SMTP is disabled, the queue/logs surface
  is depended on by the audit feed.

## Gotchas

- **No outbound network calls during a request.** Sending is queued via
  `tasks.py` (APScheduler) so the request transaction can commit
  before the SMTP attempt.
- **Provider abstraction** lives behind `EMAIL_PROVIDER`. `console`
  prints to stdout — use it in dev.
- **Templates are i18n-aware** (Spanish UI strings). Never hardcode
  copy in handlers — use a template.
- **Locale resolution order**:
  1. Patient preference (``NotificationPreference.preferred_locale``).
  2. Clinic-wide default (``clinic.settings.communication_language``).
  3. ``DEFAULT_COMMUNICATION_LOCALE`` ("es") if neither is set.
  Encapsulated in ``service.resolve_clinic_communication_locale``.
  The clinic-wide setting is owned by this module — UI lives at
  ``/settings/communications/language`` (registered via
  ``frontend/plugins/settings.client.ts``).
- **Preferences are per-patient + per-event-type.** Honour them before
  enqueueing.

## Related ADRs

- `docs/adr/0001-modular-plugin-architecture.md`
- `docs/adr/0003-event-bus-over-direct-imports.md`

## CHANGELOG

See `./CHANGELOG.md`.
