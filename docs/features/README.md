# Features

Product feature specs and UX briefs. Audience: product, design, and engineers picking up new work.

## What lives here

- *What* a feature is and *why* it exists. Problem statement, user stories, success criteria.
- UX briefs — flows, wireframes (linked to `../diagrams/`), interaction notes.
- Cross-module feature specs that don't belong to a single module.

## What does NOT belong here

- Implementation plans, architecture, tech specifics → [`../technical/`](../technical/).
- Decisions that lock in a rule or constraint → [`../adr/`](../adr/).
- Single-module deep-dives → [`../modules/`](../modules/).
- End-user how-to → [`../user-manual/`](../user-manual/).

## Style

- Lead with the problem, not the solution.
- One feature per file. Kebab-case filenames.
- If the feature is shipped and stable, mark `status: stable` in frontmatter; if draft, `status: draft`.
- Cross-link the matching tech plan in `../technical/` (and vice versa).
