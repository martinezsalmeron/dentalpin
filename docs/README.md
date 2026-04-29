# DentalPin Documentation

Index for `/docs`. Pick a folder by **type** of doc, never drop new files at this root.

## Folder taxonomy

| Folder | What lives here |
|--------|-----------------|
| [`user-manual/`](./user-manual/) | End-user / administrator how-to guides (Spanish, screenshots, step-by-step). |
| [`features/`](./features/) | Product feature specs — *what* and *why* (PM-facing). UX briefs, product flows. |
| [`technical/`](./technical/) | Cross-cutting technical reference — *how*. Auth, events, RBAC, API conventions, module-author guide, tech plans. |
| [`modules/`](./modules/) | Per-module deep-dives. One file (or subfolder) per module. |
| [`adr/`](./adr/) | Architecture Decision Records. Immutable, numbered, never deleted (only superseded). |
| [`checklists/`](./checklists/) | Agent / contributor checklists (e.g. new-module bootstrap). |
| [`diagrams/`](./diagrams/) | Mermaid / PlantUML diagram sources. |
| [`screenshots/`](./screenshots/) | Image assets (PNG / SVG). No markdown. |
| [`workflows/`](./workflows/) | Operational runbooks and end-to-end workflow walkthroughs. |

## Files at this root (only these)

| File | Purpose |
|------|---------|
| `README.md` | This index. |
| `glossary.md` | Bilingual ES↔EN domain terms. |
| `events-catalog.md` | Auto-generated event catalog. Do not edit. |
| `modules-catalog.md` | Auto-generated module catalog. Do not edit. |

Adding any other `.md` at this root is a CI failure (see `scripts/check_docs_layout.py`).

## Decision tree — where does my new doc go?

1. **Is it auto-generated?** → `docs/` root, suffix `-catalog.md`. Update `backend/scripts/generate_catalogs.py`.
2. **Is it an architectural decision (rule + rationale + consequences)?** → `adr/NNNN-title.md`.
3. **Is it scoped to one module?** → `modules/<module>.md` (or `modules/<module>/`).
4. **Is it a checklist / bootstrap recipe for contributors?** → `checklists/`.
5. **Is it a diagram source file (Mermaid / PlantUML)?** → `diagrams/`.
6. **Is it an image?** → `screenshots/`.
7. **Is it an operational runbook (deploy, backup, incident, end-to-end workflow)?** → `workflows/`.
8. **Is it written for end-users or admins (how to use the product)?** → `user-manual/`.
9. **Is it a product feature spec or UX brief (what we're building and why)?** → `features/`.
10. **Otherwise — cross-cutting technical reference or implementation plan** → `technical/`.

## See also

- Root [`CLAUDE.md`](../CLAUDE.md) — Documentation policy section restates the routing table for AI agents.
- [`technical/creating-modules.md`](./technical/creating-modules.md) — module author's guide.
