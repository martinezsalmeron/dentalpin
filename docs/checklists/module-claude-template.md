# Per-module `CLAUDE.md` template

Copy this into `backend/app/modules/<name>/CLAUDE.md` when you create or
document a module. Target ≤2 KB — agents load this in addition to the
root `CLAUDE.md`, so keep it tight.

Fill every section. Delete sections that genuinely don't apply (and
delete this guidance line too).

```markdown
# <Module name> module

<One-line purpose. e.g. "Owns patient identity (name, contact, demographics, status).">

## Public API

- Routes mounted at `/api/v1/<module>/`.
- Key endpoints:
  - `GET    /<module>/foo`        — list; permission `<module>.foo.read`
  - `POST   /<module>/foo`        — create; permission `<module>.foo.write`
  - <add the rest. Verbs + path + permission. No example payloads — they belong in OpenAPI.>

## Dependencies

`manifest.depends = [...]`. Cross-module reads/imports are only allowed
against these modules. Cross-module FKs only against these.

## Permissions

`<module>.foo.read`, `<module>.foo.write`, ...

(Mirror `get_permissions()`. Roles → permissions live in the manifest.)

## Events emitted

| Event | When | Payload keys |
|---|---|---|
| `<entity>.<action>` | <trigger> | `<key1>`, `<key2>` |

## Events consumed

| Event | Handler | Effect |
|---|---|---|
| `<entity>.<action>` | `_on_xxx` | <one line> |

## Lifecycle

- `installable` / `auto_install` / `removable` from manifest.
- If removable: what `uninstall()` blocks on (e.g. legal retention).

## Gotchas / non-obvious invariants

- <list things an agent will get wrong without this hint>
- <e.g. "this module must NOT depend on agenda — data flows the other way via events">
- <e.g. "every query must filter by clinic_id, including inside agent tools">

## Related ADRs

- `docs/adr/NNNN-title.md` — <why it applies here>

## CHANGELOG

See `./CHANGELOG.md`.
```

## CHANGELOG.md template

```markdown
# Changelog — <module> module

## Unreleased

- ...

## 0.1.0 — <YYYY-MM-DD>

- Initial release.
```

Format: per-module Keep-a-Changelog, dates ISO. Append under
`## Unreleased` while you work; cut a version when you ship.
