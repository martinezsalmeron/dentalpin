# Changelog — copilot module

## Unreleased

- feat(copilot): initial backend — conversational agent over DentalPin
  (issue #81 Layer C). Tables `copilot_conversations`, `copilot_messages`,
  `copilot_settings` on the `copilot` Alembic branch. SSE chat
  (`/sessions/{id}/messages`) driving the core orchestrator, inline
  write-confirmation (`/sessions/{id}/confirmations/{call_id}`),
  per-clinic provider/model/budget settings, and per-clinic token budget.
  Conversations link to a core `agent_sessions` row so tool calls audit
  to `agent_audit_logs`. Mandatory PHI redaction; OpenAI provider only in
  v1. Frontend Nuxt layer pending. `auto_install=False`, `removable=True`.
