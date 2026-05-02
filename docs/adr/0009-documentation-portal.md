# 0009 — Documentation portal: VitePress, filesystem-as-contract, in-app help

- **Status:** accepted
- **Date:** 2026-05-02
- **Deciders:** martinezsalmeron
- **Tags:** documentation, modules, ci, hosting

## Context

`/docs` accumulates ~50 markdown files spread across `technical/`, `user-manual/`,
`modules/`, `adr/`, `features/`, `workflows/`, `checklists/`, `diagrams/` and
`screenshots/`. There is no rendered portal, no convention that maps a screen
to its user-manual page, and no enforcement that keeps docs in sync as the
modular plugin architecture grows.

As more modules ship (each owning models, routes, screens, events, permissions),
the gap between code and docs widens silently. AI agents (Claude) editing this
codebase have no deterministic way to know *which* markdown file to update after
a code change.

The product also needs documentation that is **accessible publicly** (linkable
from the commercial site at `dentalpin.com`) and **available in-app** as
contextual help on every screen — without duplicating content between the
two surfaces.

Issue #75 captures the requirement.

## Decision

Adopt a **VitePress** static portal that builds from the existing `/docs`
markdown without duplication. Six pillars:

1. **Renderer**: VitePress, deployed as a Docker container under Coolify on
   the existing Hetzner host (same infrastructure as backend). The portal
   serves at `docs.dentalpin.com`, public, no auth. TLS via Coolify's
   automatic Let's Encrypt.

2. **Single source of truth**: `/docs/**` markdown is canonical. The portal
   reads it directly. No copy/paste, no separate doc repo.

3. **Per-module + per-screen granularity**:
   - `docs/technical/<module>/{overview,events,permissions}.md` for developer
     reference (English).
   - `docs/user-manual/{en,es}/<module>/{index.md, screens/<slug>.md}` for
     end-user docs (bilingual).

4. **Filesystem + frontmatter as the doc contract** — *not* the module
   manifest. Every screen file declares its `route`, `related_endpoints`,
   `related_permissions`, `last_verified_commit` in YAML frontmatter. The
   portal and CI both walk the filesystem to build the screen→doc lookup.
   The Python `manifest` dict on each module is **not** modified.

5. **Drift detection — two layers**:
   - **CI coverage check** (warning-only first, blocking after backfill):
     extends `backend/scripts/generate_catalogs.py`. Fails when a new screen,
     endpoint, event or permission lacks the corresponding doc artifact, or
     when frontmatter `route` points to a non-existent page.
   - **`last_verified_commit` + stale badge**: portal build runs `git log` on
     paths derived from `related_endpoints` / `related_permissions` (or an
     explicit `related_paths` list) since the verified SHA. If code moved
     past it, the page renders a "stale" badge. Bumping the SHA is part of
     the doc-update PR.

6. **In-app help is a thin client of the portal**:
   - Build script generates `dist/help/<route-slug>.html` per screen file.
   - Frontend adds `<HelpButton />` in the app shell. Drawer fetches the
     pre-rendered HTML over CORS from `docs.dentalpin.com`.
   - **Zero markdown rendering on the FastAPI backend.** App and docs deploys
     are independent.
   - The "Open full manual" link on the drawer goes to the same content on
     the public portal.

### Bilingual rule for user-manual

`docs/user-manual/` is split into `en/` and `es/`. Every new screen ships
markdown in **both** locales. Existing files (currently EN despite the README
claiming ES) move into `user-manual/en/` without re-translation; ES is added
when the module is next touched. `docs/technical/` stays EN-only — it is
developer-facing and CLAUDE.md already establishes that convention.

### What is deliberately **not** built

- No `docs` field in module `manifest`. The filesystem is the single source
  of truth and the plugin system stays untouched.
- No backend MD-serving endpoint. The portal owns rendering.
- No hand-written API reference. The portal embeds Swagger/Stoplight against
  FastAPI's OpenAPI schema. Hand-written prose lives in `overview.md`.
- No translation tooling. Authors write both locales.
- No per-release versioning. Use git history.

## Consequences

### Good

- Authors edit one markdown file in the same PR as the code change. No
  duplicated source.
- Claude (and humans) can grep `docs/user-manual/**/screens/*.md` frontmatter
  by `route`, `related_endpoints` or `related_permissions` to locate the
  exact file to update — no folklore.
- App and docs deploy on independent cadences.
- CI catches drift mechanically; the stale badge surfaces drift even when
  CI passes (e.g., a code change that doesn't add new artifacts but invalidates
  prose).
- Portal is public, so the commercial site (`dentalpin.com`) and the in-app
  help button link to the same URLs.

### Bad / accepted trade-offs

- Bilingual user-manual doubles the authoring cost for end-user docs. Mitigated
  by keeping `docs/technical/` EN-only and by accepting that one locale can lag
  the other (each has its own `last_verified_commit`).
- VitePress is a separate build pipeline (Node + nginx Docker container)
  alongside the FastAPI/Nuxt stack. We accept the small infra footprint in
  exchange for keeping the docs source as plain markdown.
- `last_verified_commit` requires authors to update a SHA on every relevant
  edit. The CI coverage check + the stale badge make forgetting it visible
  rather than silent.
- Hosting docs on Hetzner/Coolify (same host as the app) couples uptime; if
  the host is down both go dark. We accept this — Cloudflare Pages was
  rejected to avoid introducing a second cloud relationship for this small
  benefit.

## Alternatives considered

- **Nuxt Content** — rejected: ties the docs build to the Nuxt app build and
  to the app's deploy cadence. Forces a single deploy artefact.
- **Cloudflare Pages / GitHub Pages hosting** — rejected: introduces a second
  hosting relationship to manage. Coolify on Hetzner already runs the app;
  marginal cost of one more container is near zero.
- **`docs.screens` field in module `manifest` (as proposed in issue #75)** —
  rejected: duplicates the screen→doc mapping (manifest *and* frontmatter),
  guaranteeing silent drift. Filesystem-only mapping is one source of truth.
- **Backend `/api/v1/_meta/help` endpoint serving rendered MD** — rejected:
  forces markdown files to ship inside the backend container, couples app
  and docs deploys, and runs two markdown engines (one in VitePress, one in
  FastAPI) that will eventually render differently.
- **Hand-written API reference markdown** — rejected: drifts from the
  OpenAPI schema. Embed Swagger/Stoplight directly so there is no
  hand-written API surface to maintain.
- **One single-language manual (ES only, as CLAUDE.md previously implied)** —
  rejected: existing `user-manual/` files are in EN and the product needs to
  reach English-speaking users; bilingual was chosen during plan review.

## How to verify the rule still holds

- Portal builds locally: `npm --prefix docs/portal run build` produces
  `docs/portal/.vitepress/dist/`.
- Portal builds in CI: the `docs-portal-build` job in `.github/workflows/ci.yml`
  runs the build on every PR touching `docs/**` or portal config.
- Layout enforcement: `scripts/check_docs_layout.py` allows `portal/` under
  `docs/` and forbids any other folder, preserving the taxonomy.
- The `manifest` dict in each `backend/app/modules/<x>/module.py` MUST NOT
  grow a `docs` field. Grep `manifest.*docs.*=` returns zero matches.
- Backend MUST NOT serve markdown. Grep `backend/app/` for `\.md` MIME or
  `_meta/help` returns zero matches.
- (Future, fase 3) `python backend/scripts/generate_catalogs.py --check`
  fails when a screen, endpoint, event or permission lacks its doc artifact.

## References

- Issue #75
- `docs/README.md` — taxonomy index
- `scripts/check_docs_layout.py` — layout enforcement
- `backend/scripts/generate_catalogs.py` — catalog generator (extension target
  for fase 3 coverage check)
- ADR 0001 — modular plugin architecture (the contract this portal documents)
- Plan: `~/.claude/plans/revisa-la-issue-https-github-com-martine-vectorized-wirth.md`
