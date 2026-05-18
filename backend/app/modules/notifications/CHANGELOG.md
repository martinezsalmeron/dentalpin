# Changelog — notifications module

## Unreleased

- chore(events): subscribe via ``EventType.X`` constants instead of
  string literals — the events were already registered in the enum,
  the handler dict was the last drift site.
- Added per-module `CLAUDE.md` for AI-agent context (2026-04-27).

## 0.1.0 — initial

- Email templates, per-patient preferences, SMTP/console providers.
- APScheduler-backed sending queue (`tasks.py`).
- Subscribes to 6 events across patients, agenda, budget, billing.
