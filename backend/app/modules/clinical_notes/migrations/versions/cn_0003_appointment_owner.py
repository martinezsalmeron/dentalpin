"""Extend clinical_notes matrix with appointment owner.

Adds ``owner_type='appointment'`` plus two ``note_type`` values
(``appointment_clinical``, ``appointment_administrative``) so notes
can attach to ``agenda.Appointment`` rows. Replaces the legacy single
free-text ``appointments.notes`` field (dropped in ``ag_0005``).

Pre-production app: no data backfill — dev environments reset.

Revision ID: cn_0003
Revises: cn_0002
Create Date: 2026-05-24

"""

from collections.abc import Sequence

from alembic import op

revision: str = "cn_0003"
down_revision: str | None = "cn_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint("ck_clinical_notes_note_type", "clinical_notes", type_="check")
    op.create_check_constraint(
        "ck_clinical_notes_note_type",
        "clinical_notes",
        "note_type IN ('administrative', 'diagnosis', 'treatment', "
        "'treatment_plan', 'appointment_clinical', 'appointment_administrative')",
    )

    op.drop_constraint("ck_clinical_notes_owner_type", "clinical_notes", type_="check")
    op.create_check_constraint(
        "ck_clinical_notes_owner_type",
        "clinical_notes",
        "owner_type IN ('patient', 'treatment', 'plan', 'appointment')",
    )

    op.drop_constraint("ck_clinical_notes_type_owner_matrix", "clinical_notes", type_="check")
    op.create_check_constraint(
        "ck_clinical_notes_type_owner_matrix",
        "clinical_notes",
        "(note_type = 'administrative' AND owner_type = 'patient' AND tooth_number IS NULL) "
        "OR (note_type = 'diagnosis' AND owner_type = 'patient') "
        "OR (note_type = 'treatment' AND owner_type = 'treatment' AND tooth_number IS NULL) "
        "OR (note_type = 'treatment_plan' AND owner_type = 'plan' "
        "AND tooth_number IS NULL) "
        "OR (note_type = 'appointment_clinical' AND owner_type = 'appointment' "
        "AND tooth_number IS NULL) "
        "OR (note_type = 'appointment_administrative' AND owner_type = 'appointment' "
        "AND tooth_number IS NULL)",
    )


def downgrade() -> None:
    op.drop_constraint("ck_clinical_notes_type_owner_matrix", "clinical_notes", type_="check")
    op.create_check_constraint(
        "ck_clinical_notes_type_owner_matrix",
        "clinical_notes",
        "(note_type = 'administrative' AND owner_type = 'patient' AND tooth_number IS NULL) "
        "OR (note_type = 'diagnosis' AND owner_type = 'patient') "
        "OR (note_type = 'treatment' AND owner_type = 'treatment' AND tooth_number IS NULL) "
        "OR (note_type = 'treatment_plan' AND owner_type = 'plan' "
        "AND tooth_number IS NULL)",
    )

    op.drop_constraint("ck_clinical_notes_owner_type", "clinical_notes", type_="check")
    op.create_check_constraint(
        "ck_clinical_notes_owner_type",
        "clinical_notes",
        "owner_type IN ('patient', 'treatment', 'plan')",
    )

    op.drop_constraint("ck_clinical_notes_note_type", "clinical_notes", type_="check")
    op.create_check_constraint(
        "ck_clinical_notes_note_type",
        "clinical_notes",
        "note_type IN ('administrative', 'diagnosis', 'treatment', 'treatment_plan')",
    )
