# 0007 — Polymorphic attachment owner registry in `media`

- **Status:** accepted
- **Date:** 2026-05-02
- **Deciders:** martinezsalmeron
- **Tags:** modules, media, attachments

## Context

Three modules used to own their own attachment plumbing:

- `media`            — `documents` (the file).
- `clinical_notes`   — `clinical_note_attachments` (polymorphic to
  `patient | treatment | plan | appointment_treatment`, with optional
  `note_id`).
- `treatment_plan`   — `treatment_media` (specific to `plan_item`, with
  a `media_type ∈ {before|after|xray|reference}`).

This was three implementations of the same idea, each with its own
endpoints, validators and migrations. Adding a fourth (consent module
in roadmap, budget module for signed PDFs, …) would have meant a
fourth copy.

The `media` module sits at the bottom of the dependency graph and
cannot import from its consumers without inverting it. We needed a way
for `clinical_notes` / `treatment_plan` / future modules to own the
semantics of their own owner_types while keeping the storage and CRUD
in `media`.

## Decision

`media` owns the schema (`media_attachments`), the endpoints
(`/api/v1/media/attachments`) and the link-time validator. Consumer
modules register their owner_types at import time via a
process-global registry:

```python
from app.modules.media.attachment_registry import OwnerSpec, attachment_registry

attachment_registry.register(
    OwnerSpec(owner_type="plan_item", resolver=_resolve_plan_item),
)
```

The registered resolver is called by `AttachmentService.link()` to
verify (a) the owner exists in the same clinic and (b) it points to
the same patient as the document being attached.

`owner_type` is a free-text `String(40)` — there is **no CHECK
constraint** on it. The taxonomy is dynamic by design: a clinic that
uninstalls `treatment_plan` should not see broken constraints around
`'plan_item'`, and a community module should be able to plug in a new
owner_type without a `media`-side migration.

## Consequences

### Good

- Single source of truth for attachment plumbing.
- Adding a new attachable entity is one file (a resolver) plus one
  `register()` call — no migration in `media`.
- Module dependency direction stays clean: consumers depend on `media`,
  never the other way.
- Tests can re-register with mock resolvers without monkeypatching.

### Bad / accepted trade-offs

- Process-global state. A second worker process re-runs the
  registrations at import time; replication is automatic.
- `owner_id` has no FK. Service-layer guards must catch dangling rows;
  cascade cleanup is the consumer module's responsibility (typically
  via `AttachmentService.unlink_all_for_owner()`).
- Late-loading modules can race with link operations. In practice
  every consumer is loaded at app startup before requests are accepted.

## Alternatives considered

- **Hardcoded enum in `media`.** Rejected: forces every new attachable
  entity to ship via a migration in `media` and creates an awkward
  "module manifest changes a media constant" coupling.
- **One join table per owner module.** Rejected: that's exactly what
  we removed (`clinical_note_attachments`, `treatment_media`).
- **Generic FK with a discriminator and DB CHECK.** Rejected: the
  CHECK constraint becomes a moving target as modules are
  installed/uninstalled and would block upgrades.

## How to verify the rule still holds

- `grep -r "import.*media.attachment_registry" backend/app/modules/`
  must show registrations only in `__init__.py` of consumer modules.
- `media` must NOT import from any of its consumers (test:
  `tests/test_module_isolation.py` already enforces this).
- `media_attachments.owner_type` must remain typed `String(40)` with
  no CHECK constraint in any migration.

## References

- `backend/app/modules/media/attachment_registry.py`
- `backend/app/modules/media/service.py:AttachmentService`
- `backend/app/modules/clinical_notes/owner_resolvers.py`
- `backend/app/modules/treatment_plan/owner_resolvers.py`
- Issue #55
