# Updating docs after a code change

Use this checklist whenever your PR changes a module's surface — new
screen, endpoint, event, permission, or major behaviour change. Lives
beside [`new-module.md`](./new-module.md) and is referenced by the
"When adding X, do Y" table in root [`CLAUDE.md`](../../CLAUDE.md).

The full reference is
[`docs/technical/documentation-portal.md`](../technical/documentation-portal.md).

---

## TL;DR

| If you changed… | Touch this | And bump |
|-----------------|------------|----------|
| A page under `<module>/frontend/pages/**` | `docs/user-manual/{en,es}/<module>/screens/<slug>.md` | `last_verified_commit` |
| A `@router.{get,post,...}` decorator path or method | `docs/technical/<module>/permissions.md` *and* the screen MD that uses it | `last_verified_commit` on each touched MD |
| `event_bus.publish(...)` calls or new `EventType` constant | `docs/technical/<module>/events.md` + `docs/events-catalog.md` (regenerate) | `last_verified_commit` |
| `get_permissions()` return value | `docs/technical/<module>/permissions.md` + `frontend/app/config/permissions.ts` | `last_verified_commit` |
| Module purpose, models, services in a non-trivial way | `docs/technical/<module>/overview.md` | `last_verified_commit` |
| Anything user-facing on a screen | The matching screen MD in **both** `en/` and `es/`. New screenshots if the visual changed. | `last_verified_commit` (each locale) |

After the touched files are saved:

```bash
# Regenerate the auto-generated catalogs.
python backend/scripts/generate_catalogs.py

# Run the coverage check (warning-only at first).
python backend/scripts/check_docs_coverage.py
```

Bump the per-module CHANGELOG (`backend/app/modules/<module>/CHANGELOG.md`)
under `## Unreleased`.

---

## Adding a new screen

1. Decide the screen slug (filename stem of the page —
   `index.vue` → `list`, `[id].vue` → `detail`, `new.vue` → `create`).
2. Create both locale files:
   ```
   docs/user-manual/en/<module>/screens/<slug>.md
   docs/user-manual/es/<module>/screens/<slug>.md
   ```
3. Use the
   [frontmatter contract](../technical/documentation-portal.md#2-frontmatter-contract-the-part-claude-relies-on).
4. Take screenshots → `docs/screenshots/<module>/<slug>-<state>.png`.
5. Bump the per-module CHANGELOG.

## Adding a new module

After the standard module bootstrap in [`new-module.md`](./new-module.md):

1. Create `docs/technical/<module>/{overview,events,permissions}.md`.
2. If the module has Nuxt pages, create `docs/user-manual/{en,es}/<module>/`
   with `index.md` plus a screen MD per page.
3. Run `python backend/scripts/generate_catalogs.py`.
4. Run `python backend/scripts/check_docs_coverage.py` to verify.

## Bumping `last_verified_commit`

- **When**: every time you change anything described by the doc, or
  when the doc still reads correctly after a related code change you
  *didn't* author but you happened to verify.
- **What**: the short SHA of the current commit your PR is based on.
  `git rev-parse --short HEAD` after the change is staged.
- **Don't automate it.** Bumping the SHA is an affirmation that you
  read the doc and it still applies. Automation defeats the point.

## Verifying locally

```bash
# Build the portal — confirms the new MDs render and the sidebar picks them up.
cd docs/portal && npm install && npm run build

# Preview at http://localhost:5173
npm run preview
```

If the **stale badge** appears on a page you've just edited, check that
you bumped `last_verified_commit` in the frontmatter.

## When the coverage check complains

The coverage check (warning-only first; blocking after backfill) tells
you exactly which artifact is missing. The most common cases:

- *"`<module>` ships a route `/foo` without a screen MD."* — Create the
  two locale screen files.
- *"Endpoint `GET /api/v1/foo` is not listed in any
  `docs/technical/<m>/permissions.md`."* — Add the row.
- *"Permission `module.read` is unused."* — You removed an endpoint but
  not the permission row.

Don't silence warnings. Either fix the doc or document why the warning
is wrong (the script accepts inline `# ignore: <reason>` comments at
the head of the related MD).
