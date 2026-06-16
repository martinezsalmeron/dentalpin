# Copilot proactivity — morning digest (v1)

Decision record: [ADR 0014](../../adr/0014-copilot-proactivity.md).
Architecture context: [copilot-agentic-architecture.md](../copilot-agentic-architecture.md).

## What ships

v1: an opt-in daily email per clinic ("Briefing del día"). v2 (migration
`cop_0003`) makes it **multi-recipient** — `digest_recipient_user_ids` is
a list, one email per recipient, each scoped to that recipient's role —
and makes `digest_hour` **clinic-timezone aware** (`clinics.timezone`).

Three sections, each omitted when empty or when the recipient lacks the
permission:

| Section | Tool called | Permission |
|---|---|---|
| Today's appointments | `agenda.get_day_overview` | `agenda.appointments.read` |
| Overdue recalls | `recalls.list_due_recalls(overdue=true)` | `recalls.read` |
| Budgets awaiting response | `budget.list_budgets(status=['sent'])` | `budget.read` |

No LLM involved: the digest is rendered from a fixed Jinja template
(`templates/email/{es,en}/copilot_morning_digest.html`), subject and
locale resolved from `clinics.settings.communication_language`.

## Moving parts

| Piece | Where |
|---|---|
| Settings columns | `copilot_settings.digest_enabled / digest_hour / digest_recipient_user_ids` (migrations `cop_0002`, `cop_0003`) |
| Task | `backend/app/modules/copilot/tasks.py` → `send_morning_digests()` |
| Scheduling | declared via `CopilotModule.get_scheduled_jobs()` (job `copilot_morning_digests`, hourly at minute 0); the task matches `digest_hour` against the **clinic's local hour** (`clinics.timezone`) |
| Config UI | `/settings/integrations/copilot` (`CopilotSettingsPanel.vue`, registered via `useSettingsRegistry`) |
| Event | `copilot.digest.sent` `{clinic_id, recipient_user_id, date, email_status}` |

## Invariants

- **Data only via `tool_registry.call()`** with an `AgentContext` whose
  permissions are `get_role_permissions(recipient role)`. Never query
  other modules' tables from the task. This is what keeps RBAC parity
  and `depends = []` true for free.
- **Off-books**: the digest contains agenda + recalls + budgets-sent.
  Do not add paid/invoiced sections or any "outstanding" figure.
- **Idempotency**: the hourly gate means at most one send per clinic
  per day per hour value; re-running the task re-sends (acceptable —
  the email is informational).

## Open items

- ~~Clinic-timezone-aware `digest_hour`~~ — done (v2). The task converts
  "now" into each clinic's `clinics.timezone` before matching the hour,
  and passes the clinic-local date to the digest.
- ~~Multi-recipient / per-role digests~~ — done (v2). Recipients are a
  JSONB list (no FK; the task skips ids that no longer resolve to an
  active member). Each recipient gets a digest scoped to their role.
- Per-recipient hour / per-recipient section selection — not built; one
  `digest_hour` per clinic still.
- ~~Event-driven nudges~~ — built. `appointment.cancelled` →
  `copilot_nudges` ("fill the freed slot from recalls?"), surfaced as a
  drawer banner. See the `copilot_nudges` table, `events.py`, and
  `CopilotNudges.vue`. Only the cancellation nudge ships so far; other
  triggers (e.g. cash mismatch, due recalls) can be added as handlers.
