# User manual

End-user and administrator guides — how to *use* and *operate* DentalPin.
Audience: clinic staff, self-hosters, on-call admins.

This folder is **bilingual** (Spanish + English). Every screen-level guide
ships in both locales:

- [English (`en/`)](./en/) — original drafts.
- [Spanish (`es/`)](./es/) — translations.

See [ADR 0009](../adr/0009-documentation-portal.md) and
[the documentation portal technical reference](../technical/documentation-portal.md)
for the rule.

## What lives here

- Step-by-step product walkthroughs with screenshots from `../screenshots/`.
- Self-host install / restart / backup / troubleshooting guides.
- Demo data setup, login credentials, role testing.

## What does NOT belong here

- Implementation details → [`../technical/`](../technical/).
- Product specs (what + why) → [`../features/`](../features/).
- Per-module deep-dives → [`../modules/`](../modules/).
- Operational runbooks for incidents or end-to-end workflows → [`../workflows/`](../workflows/).

## Per-module structure

Modules with frontend screens get one subfolder per module:

```
user-manual/
├── en/
│   └── <module>/
│       ├── index.md
│       └── screens/<slug>.md
└── es/
    └── <module>/
        ├── index.md
        └── screens/<slug>.md
```

Modules without frontend screens (backend-only, settings-injecting plugins)
do not need user-manual entries — they live in
`docs/technical/<module>/` only.

## Style

- Both locales: same structure, same screenshots, same frontmatter.
- Show, don't tell — embed screenshots from `../screenshots/`.
- Numbered steps; one screen per step.
- Each screen file starts with the
  [frontmatter contract](../technical/documentation-portal.md#2-frontmatter-contract-the-part-claude-relies-on).
