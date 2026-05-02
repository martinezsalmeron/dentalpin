# Changelog — media module

## Unreleased

- Added per-module `CLAUDE.md` for AI-agent context (2026-04-27).
- **0.2.0 (issue #55)** — Photo gallery + generalized polymorphic
  attachments (2026-05-02):
  - `Document` gains `media_kind`, `media_category`, `media_subtype`,
    `captured_at`, `paired_document_id`, `tags` columns. New
    `media_attachments` table replaces both `clinical_note_attachments`
    and `treatment_media`.
  - New endpoints: photo upload (`POST /patients/{id}/photos`) with
    EXIF + Pillow thumbnail generation, gallery list, before/after
    pairing, `/attachments` polymorphic CRUD.
  - Owner-type registry in `attachment_registry.py` — clinical_notes
    and treatment_plan register their owner_types at import time
    (ADR 0007).
  - New permissions `media.attachments.read` / `media.attachments.write`.
  - New events `media.photo_uploaded`, `media.attachment_linked`,
    `media.attachment_unlinked`, `media.pair_created`,
    `media.pair_removed`.
  - Pillow added as a backend dependency.
  - HEIC / HEIF / WebP / GIF added to the photo MIME allowlist.

## 0.1.0 — initial

- Local storage backend with MIME and size validation.
- `document.uploaded`, `document.deleted` events.
- Subscribes to `patient.archived` for cascade.
