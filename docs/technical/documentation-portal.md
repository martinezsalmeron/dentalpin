# Documentation portal — technical reference

Implementation reference for the documentation portal introduced by
[ADR 0009](../adr/0009-documentation-portal.md) (issue #75). This is the
durable plan: how the contract works, how Claude and humans add docs, and
how each fase wires together.

The design plan that motivates the work lives in the conversation history;
this document is the technical companion.

---

## 1. What ships and where

```
docs/
├── technical/                          # EN, developer reference
│   ├── <cross-cutting files>
│   └── <module>/                       # per-module deep-dive
│       ├── overview.md                 # arch, data model, services
│       ├── events.md                   # publishes / subscribes
│       └── permissions.md              # one row per permission
├── user-manual/                        # bilingual end-user docs
│   ├── en/<module>/
│   │   ├── index.md                    # module landing page
│   │   └── screens/<slug>.md           # one file per route
│   └── es/<module>/
│       ├── index.md
│       └── screens/<slug>.md
├── modules/, adr/, checklists/,
│   features/, workflows/,
│   diagrams/, screenshots/              # unchanged
└── portal/                              # VitePress build pipeline
    ├── .vitepress/
    │   ├── config.ts                    # srcDir: '..', auto sidebar
    │   └── sidebar.ts                   # walks /docs filesystem
    ├── package.json
    ├── Dockerfile + nginx.conf
    └── README.md
```

The portal is a static site built by VitePress and served by nginx in a
Docker container deployed via Coolify on Hetzner. Source is `/docs/**`,
single source of truth, no copies.

Modules **without** screens (backend-only, settings-injecting plugins, etc.)
get `docs/technical/<module>/` only — no `user-manual/<lang>/<module>/`
required. Modules **with** screens MUST ship both.

---

## 2. Frontmatter contract (the part Claude relies on)

Every screen file under `docs/user-manual/<lang>/<module>/screens/<slug>.md`
ships YAML frontmatter:

```yaml
---
module: patients                        # backend module name
screen: list                            # short slug, matches filename
route: /patients                        # Nuxt route this doc covers
related_endpoints:
  - GET /api/v1/patients
  - POST /api/v1/patients
  - GET /api/v1/patients/recent
related_permissions:
  - clinical.patients.read
  - clinical.patients.write
related_paths:                          # optional; inferred when absent
  - backend/app/modules/patients/router.py
  - backend/app/modules/patients/frontend/pages/patients/index.vue
last_verified_commit: 0e9a0acf12        # short SHA, bumped per edit
screenshots:
  - patients/list-empty.png
  - patients/list-populated.png
---
```

### Required fields

- `module` — must match a directory under `backend/app/modules/`.
- `route` — the user-visible Nuxt route. May contain `[id]`, `[...slug]`.
- `last_verified_commit` — git SHA (full or short) the author confirmed the
  doc against. Stale-badge logic compares against `git log` for the
  related paths.

### Recommended fields

- `screen` — short slug; should equal the filename stem.
- `related_endpoints` — `METHOD /path` strings. Drives the CI coverage
  check and the inferred related-paths fallback.
- `related_permissions` — `module.resource.action` strings.
- `screenshots` — paths relative to `docs/screenshots/`.
- `related_paths` — explicit list of code paths whose mtime/git-history is
  used for stale detection. Falls back to inference from
  `related_endpoints` and `related_permissions` when omitted.

### Module-level technical pages

`docs/technical/<module>/overview.md` opens with simpler frontmatter:

```yaml
---
module: patients
last_verified_commit: 0e9a0acf12
---
```

Events and permissions tables live in `events.md` and `permissions.md`
respectively — see Fase 3 for the rules the CI check enforces.

---

## 3. Single source of truth for screen→doc mapping

The `module.manifest` Python dict is **not** modified. The portal and CI
both **walk the filesystem**:

```
glob docs/user-manual/*/<module>/screens/*.md  → parse frontmatter
                                              → key by `route`
```

Helpers (Fase 3 introduces them):

- `backend/scripts/docs_index.py` — discovery + frontmatter parsing,
  shared by the CI coverage check and (later) the in-app help endpoint.
- `docs/portal/.vitepress/help.ts` (Fase 5) — same logic in TypeScript so
  the portal build emits `dist/help/<route-slug>.html` for the drawer.

Both use the **same parser** and the **same conventions**. Any divergence
is a bug.

---

## 4. Sidebar generation (already shipped, fase 1)

`docs/portal/.vitepress/sidebar.ts` walks the docs root at build time:

- One sidebar group per top-level section (`technical`, `user-manual`,
  `modules`, `adr`, `features`, `workflows`, `checklists`, `diagrams`).
- Folders become collapsible groups; markdown files become leaves.
- README.md hoists as the section's "Overview" link.
- Skips: `portal/`, `screenshots/`, `node_modules/`, dotfiles.
- Skips author templates: `TEMPLATE.md`, `*-template.md`,
  `CHANGELOG.md` (kept in sync with `srcExclude` in `config.ts`).

Section order is hardcoded to put user-manual first; unknown sections
sort alphabetically at the end.

There is no hand-maintained `nav` or `sidebar` array.

---

## 5. CI coverage check (Fase 3)

`backend/scripts/check_docs_coverage.py` (new — sibling to
`generate_catalogs.py`) runs in the existing `catalog-freshness` CI job
and validates:

| Rule | Failure example |
|------|------------------|
| Every module has `docs/technical/<module>/overview.md`. | `patients_clinical` missing overview. |
| Every module has `docs/technical/<module>/events.md` if it publishes or subscribes events. | `patients` publishes `patient.created` but file missing. |
| Every event published or subscribed appears as a row in the module's `events.md`. | New `patient.merged` event not yet listed. |
| Every module has `docs/technical/<module>/permissions.md` if `get_permissions()` returns ≥1 permission. | new `clinical.patients.delete` not listed. |
| Every Nuxt route under `<module>/frontend/pages/**` has a screen file in **both** `user-manual/en/<module>/screens/` and `user-manual/es/<module>/screens/`. | New `pages/patients/merge.vue` lacks `screens/merge.md`. |
| Every screen file's frontmatter `route` resolves to an actual page. | `route: /old-route` no longer in `pages/`. |
| Every `related_endpoints` entry resolves to a registered endpoint. | Typo'd path. |
| Every `related_permissions` entry is a registered permission. | Typo'd permission. |

**Modes:**

- Default (run from `catalog-freshness` job): warning-only. Prints findings,
  exits 0.
- `--strict`: blocking. Used after the backfill (Fase 6) to gate merges.

The check shares module discovery and event/permission resolution with
`generate_catalogs.py` — keep the helpers in `backend/scripts/_docs_lib.py`
so both scripts import the same source of truth.

---

## 6. `last_verified_commit` and the stale badge (Fase 4)

A frontmatter SHA tells the portal "this doc was confirmed accurate at this
commit." The build computes staleness:

```
related_paths = frontmatter.related_paths
              or paths_from_endpoints(related_endpoints)
              + paths_from_permissions(related_permissions)
              + [docs/user-manual/<lang>/<module>/screens/<slug>.md]
              + [backend/app/modules/<module>/]    # fallback

stale = git log --oneline last_verified_commit..HEAD -- <related_paths>
```

If `stale` is non-empty, the page renders a badge **at the top of the
content** with:

- "⚠ This page may be out of date" (translated to the page's locale).
- A link to the GitHub diff for the related paths since the verified SHA.

**Implementation:** a VitePress `transformPageData` hook in `config.ts`
mutates `frontmatter.staleSince` and `frontmatter.staleDiffUrl`. A small
custom Vue component in `.vitepress/theme/StaleBadge.vue` reads those
fields and renders the badge. The default theme is extended via
`.vitepress/theme/index.ts`.

`paths_from_endpoints` resolves a `METHOD /api/v1/...` string to the file
that registers it (typically `backend/app/modules/<module>/router.py`).
`paths_from_permissions` resolves `module.resource.action` to
`backend/app/modules/<module>/module.py` (where `get_permissions()` lives).
Both helpers are shared with the CI check.

The build runs `git log` once per related-paths set; cached per build to
keep total time under 10s for ~100 docs.

---

## 7. In-app help (Fase 5)

The portal build emits one **standalone HTML fragment per screen** at
`dist/help/<route-slug>.html`. Fragments contain only the screen body —
no portal chrome, no sidebar — wrapped in a minimal stylesheet that
matches the app's typography.

`<route-slug>` is the route with `/` → `_` and `[param]` left literal:

| Route | Fragment URL |
|-------|--------------|
| `/patients` | `https://docs.dentalpin.com/help/patients.html` |
| `/patients/[id]` | `https://docs.dentalpin.com/help/patients_[id].html` |
| `/treatment-plans/new` | `https://docs.dentalpin.com/help/treatment-plans_new.html` |

The frontend ships a `<HelpButton />` component in the app shell. It reads
the current route from Vue Router and constructs the fragment URL with the
user's locale prefix (`/en/help/...` or `/es/help/...`).

Drawer behaviour:

1. Click `?` → drawer opens.
2. Frontend `fetch('https://docs.dentalpin.com/<lang>/help/<slug>.html')`.
3. On 200, render the HTML inside the drawer (sanitised — content comes
   from our own portal so DOMPurify is belt-and-braces only).
4. On 404, render fallback "No help available for this screen yet" with
   a link to the user-manual root.
5. The drawer footer always has "Open full manual →" linking to the same
   doc on the portal at full-page width.

CORS is set in `nginx.conf` on the `/help/` location — allow GET/OPTIONS
from `app.dentalpin.com` (tighten from `*` once the production app
origin is known).

The frontend route → slug helper lives in `frontend/app/composables/
useHelp.ts`. Its sole job is the URL construction; rendering is the
drawer component's responsibility.

---

## 8. Bilingual rule for user-manual

`docs/technical/` is **EN-only**. `docs/user-manual/` is **bilingual**:

- Every screen file MUST exist in both `user-manual/en/<module>/screens/`
  and `user-manual/es/<module>/screens/`.
- Each locale has its own frontmatter `last_verified_commit` — they can
  go stale independently.
- Existing user-manual files (currently EN despite the README claim) move
  into `user-manual/en/` during fase 2 without re-translation. ES is
  added when the module is next touched.
- `docs/technical/<module>/` is created without a locale split.

VitePress' `locales` config (Fase 2.A) mounts EN at `/en/...` and ES at
`/es/...`, with the default landing page detecting the browser's
`Accept-Language`.

---

## 9. Recipe — adding a new screen's docs

When you add a new Nuxt page under `backend/app/modules/<module>/frontend/
pages/`:

1. Decide the screen slug — usually the page's filename stem
   (`index.vue` → `list`, `[id].vue` → `detail`, `new.vue` → `create`).
2. Create both locale files:
   ```
   docs/user-manual/en/<module>/screens/<slug>.md
   docs/user-manual/es/<module>/screens/<slug>.md
   ```
3. Fill frontmatter (see §2). `last_verified_commit` = current `git rev-parse --short HEAD`.
4. Take screenshots, commit them under
   `docs/screenshots/<module>/<slug>-<state>.png`.
5. Bump the per-module CHANGELOG (`backend/app/modules/<module>/CHANGELOG.md`)
   under `## Unreleased`.

The CI coverage check (warning-only at first, blocking after backfill)
fails if either locale is missing.

---

## 10. Recipe — adding a new module

After the standard module bootstrap in
[`docs/checklists/new-module.md`](../checklists/new-module.md):

1. Create `docs/technical/<module>/`:
   - `overview.md` — module purpose, models, services. Frontmatter only
     needs `module:` and `last_verified_commit:`.
   - `events.md` — one row per event, even if the table starts empty.
   - `permissions.md` — one row per permission.
2. If the module has Nuxt pages, create `docs/user-manual/{en,es}/<module>/`:
   - `index.md` — module landing page (overview for end users).
   - `screens/<slug>.md` per page (see §9).
3. Run `python backend/scripts/generate_catalogs.py` to refresh
   `docs/modules-catalog.md`.
4. Run `python backend/scripts/check_docs_coverage.py` to confirm the
   coverage check is happy (or knows what's still missing).

---

## 11. Hosting and deploy

| Aspect | Decision |
|--------|----------|
| Build | `npm run build` inside `docs/portal/` produces `.vitepress/dist/`. |
| Container | Multi-stage `Dockerfile` (Node builder → `nginx:alpine` runtime). |
| Build context | Repo root (the portal needs `/docs/**`). The repo-root `.dockerignore` excludes `docs/`, but `docs/portal/Dockerfile.dockerignore` overrides that for BuildKit per-Dockerfile ignore. |
| Hosting | Coolify on the existing Hetzner host. Same infra as backend. |
| Domain | `docs.dentalpin.com`. Public, no auth. |
| TLS | Coolify-managed Let's Encrypt. |
| CI smoke test | `.github/workflows/ci.yml` job `docs-portal-build` runs `npm install && npm run build` on every PR. |

Coolify configuration:

- Repo: `martinezsalmeron/dentalpin`
- Build context: `/`
- Dockerfile path: `docs/portal/Dockerfile`
- Exposed port: `80`

The portal deploy is **independent** of the backend/frontend deploy
cadence. A docs-only PR rebuilds and ships only the portal container.

---

## 12. What is deliberately not built

These are tempting but rejected; revisit only with a concrete need.

| Tempting | Why we skipped it |
|----------|-------------------|
| `docs` field in module `manifest` | Two sources of truth for the screen→doc mapping. Filesystem is enough. |
| Backend `/api/v1/_meta/help` endpoint | Couples app and docs deploys, runs two markdown engines. The portal owns rendering. |
| Hand-written API reference per module | Drifts from OpenAPI. Embed Swagger/Stoplight directly in `docs/technical/<module>/api.md` (or skip the file entirely). |
| `last_verified_commit` automation that bumps SHAs in PRs | Authors must affirm the doc still applies to the change. Automation defeats the point. |
| Portal as Nuxt Content / inside the main app | Couples docs build to app build. Use a static portal. |
| Cloudflare Pages / GitHub Pages | Adds a second cloud relationship for marginal benefit; Coolify on Hetzner is already there. |

---

## 13. Phase status

| Fase | What | Status |
|------|------|--------|
| 1 | ADR 0009, VitePress scaffold, Dockerfile, CI smoke test | **shipped** (this PR) |
| 2 | Frontmatter contract, EN/ES split, patients + schedules reference modules, checklist, CLAUDE.md update | in this PR |
| 3 | `check_docs_coverage.py` (warning-only) | in this PR |
| 4 | Stale badge from `last_verified_commit` | in this PR |
| 5 | In-app help drawer, `<HelpButton />`, CORS | next session (frontend integration) |
| 6 | Backfill remaining modules, flip coverage check to blocking | rolling, one PR per module |
| 7 | Link `docs.dentalpin.com` from the commercial site | external (out of repo) |

---

## 14. References

- [ADR 0009](../adr/0009-documentation-portal.md) — the architectural decision.
- [`docs/portal/README.md`](../portal/README.md) — how to dev/build/deploy
  the portal locally.
- [`backend/scripts/generate_catalogs.py`](../../backend/scripts/generate_catalogs.py)
  — the existing catalog generator the coverage check extends.
- [`scripts/check_docs_layout.py`](../../scripts/check_docs_layout.py) —
  the layout enforcer that already polices the `/docs` taxonomy.
- Issue #75.
