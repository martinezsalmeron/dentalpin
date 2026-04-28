"""Clinical notes — initial.

Owns the ``clinical_notes`` + ``clinical_note_attachments`` tables. The
treatment_plan module created earlier versions of these tables in
``tp_0002_clinical_notes`` (see ADR 0002). This revision:

- Adds ``note_type`` (NOT NULL) and ``tooth_number`` columns.
- Backfills ``note_type`` from the legacy ``owner_type`` discriminator
  (``plan`` → ``treatment_plan``).
- Migrates ``owner_type='plan_item'`` notes to the underlying
  ``treatment`` so notes follow the Treatment across diagnosis → plan
  → completion (issue #60).
- Replaces the ``owner_type`` CHECK and adds the type/owner matrix
  CHECK enforcing the four note_type / owner_type pairings.
- Reindexes the table for the recent-feed query.

Sits on its own branch (``branch_labels=("clinical_notes",)``) and
declares ``depends_on=("tp_0002",)`` so the table exists before we
ALTER it on fresh installs.

Revision ID: cn_0001
Revises:
Create Date: 2026-04-28

"""

from collections.abc import Sequence

from alembic import op

revision: str = "cn_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = ("clinical_notes",)
depends_on: str | Sequence[str] | None = ("tp_0002",)


def upgrade() -> None:
    # ------------------------------------------------------------------
    # New columns
    # ------------------------------------------------------------------
    op.execute("ALTER TABLE clinical_notes ADD COLUMN IF NOT EXISTS note_type VARCHAR(20)")
    op.execute("ALTER TABLE clinical_notes ADD COLUMN IF NOT EXISTS tooth_number INTEGER")

    # ------------------------------------------------------------------
    # Backfill note_type from legacy owner_type
    # ------------------------------------------------------------------
    op.execute(
        "UPDATE clinical_notes SET note_type = 'treatment_plan' "
        "WHERE owner_type = 'plan' AND note_type IS NULL"
    )
    # Migrate plan_item notes onto the underlying Treatment row so they
    # travel with the treatment regardless of plan status.
    op.execute(
        """
        UPDATE clinical_notes c
           SET note_type = 'treatment',
               owner_type = 'treatment',
               owner_id = pti.treatment_id
          FROM planned_treatment_items pti
         WHERE c.owner_type = 'plan_item'
           AND c.owner_id = pti.id
           AND c.note_type IS NULL
        """
    )

    # ------------------------------------------------------------------
    # Attachments — same plan_item → treatment remap
    # ------------------------------------------------------------------
    op.execute(
        """
        UPDATE clinical_note_attachments a
           SET owner_type = 'treatment',
               owner_id = pti.treatment_id
          FROM planned_treatment_items pti
         WHERE a.owner_type = 'plan_item'
           AND a.owner_id = pti.id
        """
    )

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    op.execute("ALTER TABLE clinical_notes ALTER COLUMN note_type SET NOT NULL")

    op.execute("ALTER TABLE clinical_notes DROP CONSTRAINT IF EXISTS ck_clinical_notes_owner_type")
    op.execute(
        "ALTER TABLE clinical_notes ADD CONSTRAINT ck_clinical_notes_owner_type "
        "CHECK (owner_type IN ('patient', 'treatment', 'plan'))"
    )
    op.execute("ALTER TABLE clinical_notes DROP CONSTRAINT IF EXISTS ck_clinical_notes_note_type")
    op.execute(
        "ALTER TABLE clinical_notes ADD CONSTRAINT ck_clinical_notes_note_type "
        "CHECK (note_type IN ('administrative', 'diagnosis', 'treatment', 'treatment_plan'))"
    )
    op.execute(
        "ALTER TABLE clinical_notes DROP CONSTRAINT IF EXISTS ck_clinical_notes_type_owner_matrix"
    )
    op.execute(
        """
        ALTER TABLE clinical_notes ADD CONSTRAINT ck_clinical_notes_type_owner_matrix
        CHECK (
            (note_type = 'administrative' AND owner_type = 'patient' AND tooth_number IS NULL)
         OR (note_type = 'diagnosis'      AND owner_type = 'patient')
         OR (note_type = 'treatment'      AND owner_type = 'treatment'
             AND tooth_number IS NULL)
         OR (note_type = 'treatment_plan' AND owner_type = 'plan'
             AND tooth_number IS NULL)
        )
        """
    )

    # Attachments: owner_type now allows the new note owners + keep
    # appointment_treatment for direct radiograph uploads.
    op.execute(
        "ALTER TABLE clinical_note_attachments DROP CONSTRAINT IF EXISTS "
        "ck_clinical_note_attachments_owner_type"
    )
    op.execute(
        "ALTER TABLE clinical_note_attachments ADD CONSTRAINT "
        "ck_clinical_note_attachments_owner_type CHECK ("
        "owner_type IN ('patient', 'treatment', 'plan', 'appointment_treatment'))"
    )

    # ------------------------------------------------------------------
    # Reindex
    # ------------------------------------------------------------------
    op.execute("DROP INDEX IF EXISTS idx_clinical_notes_owner")
    op.create_index(
        "idx_clinical_notes_owner",
        "clinical_notes",
        ["clinic_id", "owner_type", "owner_id", "deleted_at", "created_at"],
        unique=False,
    )
    op.create_index(
        "idx_clinical_notes_patient_recent",
        "clinical_notes",
        ["clinic_id", "note_type", "owner_id", "deleted_at", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    # Best-effort revert. We recreate the legacy ``owner_type`` CHECK and
    # drop the new columns/indexes; we do NOT attempt to restore the
    # plan_item linkage that was rewritten in upgrade(), because the
    # planned_treatment_items row is what we joined through and the
    # backfill is one-way.
    op.execute("DROP INDEX IF EXISTS idx_clinical_notes_patient_recent")
    op.execute("DROP INDEX IF EXISTS idx_clinical_notes_owner")
    op.create_index(
        "idx_clinical_notes_owner",
        "clinical_notes",
        ["clinic_id", "owner_type", "owner_id", "created_at"],
        unique=False,
    )

    op.execute(
        "ALTER TABLE clinical_note_attachments DROP CONSTRAINT IF EXISTS "
        "ck_clinical_note_attachments_owner_type"
    )
    op.execute(
        "ALTER TABLE clinical_note_attachments ADD CONSTRAINT "
        "ck_clinical_note_attachments_owner_type CHECK ("
        "owner_type IN ('plan', 'plan_item', 'appointment_treatment'))"
    )

    op.execute(
        "ALTER TABLE clinical_notes DROP CONSTRAINT IF EXISTS ck_clinical_notes_type_owner_matrix"
    )
    op.execute("ALTER TABLE clinical_notes DROP CONSTRAINT IF EXISTS ck_clinical_notes_note_type")
    op.execute("ALTER TABLE clinical_notes DROP CONSTRAINT IF EXISTS ck_clinical_notes_owner_type")
    op.execute(
        "ALTER TABLE clinical_notes ADD CONSTRAINT ck_clinical_notes_owner_type "
        "CHECK (owner_type IN ('plan', 'plan_item'))"
    )

    op.execute("ALTER TABLE clinical_notes DROP COLUMN IF EXISTS tooth_number")
    op.execute("ALTER TABLE clinical_notes DROP COLUMN IF EXISTS note_type")
