"""Normalize medical_history/emergency_contact/legal_guardian JSONB → tables.

Fase B.4:

* Seven new tables under the ``patients_clinical_*`` prefix.
* Backfill from the JSONB blobs on ``patients``:
  - ``medical_history.allergies`` → ``patients_clinical_allergy``
  - ``medical_history.medications`` → ``patients_clinical_medication``
  - ``medical_history.systemic_diseases`` → ``patients_clinical_systemic_disease``
  - ``medical_history.surgical_history`` → ``patients_clinical_surgical_history``
  - remaining flags → ``patients_clinical_medical_context``
  - ``patients.emergency_contact`` → ``patients_clinical_emergency_contact``
  - ``patients.legal_guardian`` → ``patients_clinical_legal_guardian``
* ``patients.medical_history``, ``emergency_contact``, ``legal_guardian``
  columns are dropped.

Revision ID: w3x4y5z6a7b8
Revises: v2w3x4y5z6a7
Create Date: 2026-04-20

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "w3x4y5z6a7b8"
down_revision: str | None = "v2w3x4y5z6a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- Tables --------------------------------------------------------

    op.create_table(
        "patients_clinical_medical_context",
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("clinic_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("is_pregnant", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("pregnancy_week", sa.Integer(), nullable=True),
        sa.Column("is_lactating", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "is_on_anticoagulants",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column("anticoagulant_medication", sa.String(length=100), nullable=True),
        sa.Column("inr_value", sa.Float(), nullable=True),
        sa.Column("last_inr_date", sa.Date(), nullable=True),
        sa.Column("is_smoker", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("smoking_frequency", sa.String(length=100), nullable=True),
        sa.Column("alcohol_consumption", sa.String(length=100), nullable=True),
        sa.Column("bruxism", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "adverse_reactions_to_anesthesia",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column("anesthesia_reaction_details", sa.String(length=500), nullable=True),
        sa.Column("last_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"]),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("patient_id"),
    )
    op.create_index(
        op.f("ix_patients_clinical_medical_context_clinic_id"),
        "patients_clinical_medical_context",
        ["clinic_id"],
    )

    for table_name, extra_cols, extra_indexes in (
        (
            "patients_clinical_allergy",
            [
                sa.Column("name", sa.String(length=100), nullable=False),
                sa.Column("type", sa.String(length=50), nullable=True),
                sa.Column(
                    "severity",
                    sa.String(length=20),
                    nullable=False,
                    server_default="medium",
                ),
                sa.Column("reaction", sa.String(length=500), nullable=True),
                sa.Column("notes", sa.Text(), nullable=True),
            ],
            [("severity",)],
        ),
        (
            "patients_clinical_medication",
            [
                sa.Column("name", sa.String(length=100), nullable=False),
                sa.Column("dosage", sa.String(length=100), nullable=True),
                sa.Column("frequency", sa.String(length=100), nullable=True),
                sa.Column("start_date", sa.Date(), nullable=True),
                sa.Column("notes", sa.Text(), nullable=True),
            ],
            [],
        ),
        (
            "patients_clinical_systemic_disease",
            [
                sa.Column("name", sa.String(length=100), nullable=False),
                sa.Column("type", sa.String(length=50), nullable=True),
                sa.Column("diagnosis_date", sa.Date(), nullable=True),
                sa.Column(
                    "is_controlled",
                    sa.Boolean(),
                    nullable=False,
                    server_default=sa.true(),
                ),
                sa.Column(
                    "is_critical",
                    sa.Boolean(),
                    nullable=False,
                    server_default=sa.false(),
                ),
                sa.Column("medications", sa.Text(), nullable=True),
                sa.Column("notes", sa.Text(), nullable=True),
            ],
            [("is_critical",)],
        ),
        (
            "patients_clinical_surgical_history",
            [
                sa.Column("procedure", sa.String(length=200), nullable=False),
                sa.Column("surgery_date", sa.Date(), nullable=True),
                sa.Column("complications", sa.Text(), nullable=True),
                sa.Column("notes", sa.Text(), nullable=True),
            ],
            [],
        ),
    ):
        op.create_table(
            table_name,
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("clinic_id", postgresql.UUID(as_uuid=True), nullable=False),
            *extra_cols,
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"]),
            sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            op.f(f"ix_{table_name}_patient_id"), table_name, ["patient_id"]
        )
        op.create_index(op.f(f"ix_{table_name}_clinic_id"), table_name, ["clinic_id"])
        for (col,) in extra_indexes:
            op.create_index(op.f(f"ix_{table_name}_{col}"), table_name, [col])

    op.create_table(
        "patients_clinical_emergency_contact",
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("clinic_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("relationship", sa.String(length=50), nullable=True),
        sa.Column("phone", sa.String(length=20), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column(
            "is_legal_guardian",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"]),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("patient_id"),
    )
    op.create_index(
        op.f("ix_patients_clinical_emergency_contact_clinic_id"),
        "patients_clinical_emergency_contact",
        ["clinic_id"],
    )

    op.create_table(
        "patients_clinical_legal_guardian",
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("clinic_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("relationship", sa.String(length=50), nullable=False),
        sa.Column("dni", sa.String(length=20), nullable=True),
        sa.Column("phone", sa.String(length=20), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("address", sa.String(length=200), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"]),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("patient_id"),
    )
    op.create_index(
        op.f("ix_patients_clinical_legal_guardian_clinic_id"),
        "patients_clinical_legal_guardian",
        ["clinic_id"],
    )

    # --- Backfill ------------------------------------------------------

    op.execute(
        """
        INSERT INTO patients_clinical_medical_context (
            patient_id, clinic_id,
            is_pregnant, pregnancy_week, is_lactating,
            is_on_anticoagulants, anticoagulant_medication, inr_value, last_inr_date,
            is_smoker, smoking_frequency, alcohol_consumption, bruxism,
            adverse_reactions_to_anesthesia, anesthesia_reaction_details,
            last_updated_at, last_updated_by
        )
        SELECT
            p.id,
            p.clinic_id,
            COALESCE((p.medical_history->>'is_pregnant')::boolean, false),
            NULLIF(p.medical_history->>'pregnancy_week', '')::int,
            COALESCE((p.medical_history->>'is_lactating')::boolean, false),
            COALESCE((p.medical_history->>'is_on_anticoagulants')::boolean, false),
            NULLIF(p.medical_history->>'anticoagulant_medication', ''),
            NULLIF(p.medical_history->>'inr_value', '')::float,
            NULLIF(p.medical_history->>'last_inr_date', '')::date,
            COALESCE((p.medical_history->>'is_smoker')::boolean, false),
            NULLIF(p.medical_history->>'smoking_frequency', ''),
            NULLIF(p.medical_history->>'alcohol_consumption', ''),
            COALESCE((p.medical_history->>'bruxism')::boolean, false),
            COALESCE(
                (p.medical_history->>'adverse_reactions_to_anesthesia')::boolean,
                false
            ),
            NULLIF(p.medical_history->>'anesthesia_reaction_details', ''),
            NULLIF(p.medical_history->>'last_updated_at', '')::timestamptz,
            NULLIF(p.medical_history->>'last_updated_by', '')::uuid
        FROM patients p
        WHERE p.medical_history IS NOT NULL
          AND jsonb_typeof(p.medical_history) = 'object'
          AND p.medical_history <> '{}'::jsonb;
        """
    )

    op.execute(
        """
        INSERT INTO patients_clinical_allergy (
            id, patient_id, clinic_id, name, type, severity, reaction, notes
        )
        SELECT
            gen_random_uuid(),
            p.id,
            p.clinic_id,
            COALESCE(entry->>'name', 'Desconocida'),
            NULLIF(entry->>'type', ''),
            COALESCE(NULLIF(entry->>'severity', ''), 'medium'),
            NULLIF(entry->>'reaction', ''),
            NULLIF(entry->>'notes', '')
        FROM patients p,
             jsonb_array_elements(COALESCE(p.medical_history->'allergies', '[]'::jsonb)) AS entry
        WHERE jsonb_typeof(COALESCE(p.medical_history->'allergies', '[]'::jsonb)) = 'array';
        """
    )

    op.execute(
        """
        INSERT INTO patients_clinical_medication (
            id, patient_id, clinic_id, name, dosage, frequency, start_date, notes
        )
        SELECT
            gen_random_uuid(),
            p.id,
            p.clinic_id,
            COALESCE(entry->>'name', 'Desconocido'),
            NULLIF(entry->>'dosage', ''),
            NULLIF(entry->>'frequency', ''),
            NULLIF(entry->>'start_date', '')::date,
            NULLIF(entry->>'notes', '')
        FROM patients p,
             jsonb_array_elements(COALESCE(p.medical_history->'medications', '[]'::jsonb)) AS entry
        WHERE jsonb_typeof(COALESCE(p.medical_history->'medications', '[]'::jsonb)) = 'array';
        """
    )

    op.execute(
        """
        INSERT INTO patients_clinical_systemic_disease (
            id, patient_id, clinic_id, name, type, diagnosis_date,
            is_controlled, is_critical, medications, notes
        )
        SELECT
            gen_random_uuid(),
            p.id,
            p.clinic_id,
            COALESCE(entry->>'name', 'Desconocida'),
            NULLIF(entry->>'type', ''),
            NULLIF(entry->>'diagnosis_date', '')::date,
            COALESCE((entry->>'is_controlled')::boolean, true),
            COALESCE((entry->>'is_critical')::boolean, false),
            NULLIF(entry->>'medications', ''),
            NULLIF(entry->>'notes', '')
        FROM patients p,
             jsonb_array_elements(
                 COALESCE(p.medical_history->'systemic_diseases', '[]'::jsonb)
             ) AS entry
        WHERE jsonb_typeof(
                COALESCE(p.medical_history->'systemic_diseases', '[]'::jsonb)
              ) = 'array';
        """
    )

    op.execute(
        """
        INSERT INTO patients_clinical_surgical_history (
            id, patient_id, clinic_id, procedure, surgery_date, complications, notes
        )
        SELECT
            gen_random_uuid(),
            p.id,
            p.clinic_id,
            COALESCE(entry->>'procedure', 'Sin especificar'),
            NULLIF(entry->>'surgery_date', '')::date,
            NULLIF(entry->>'complications', ''),
            NULLIF(entry->>'notes', '')
        FROM patients p,
             jsonb_array_elements(
                 COALESCE(p.medical_history->'surgical_history', '[]'::jsonb)
             ) AS entry
        WHERE jsonb_typeof(
                COALESCE(p.medical_history->'surgical_history', '[]'::jsonb)
              ) = 'array';
        """
    )

    op.execute(
        """
        INSERT INTO patients_clinical_emergency_contact (
            patient_id, clinic_id, name, relationship, phone, email, is_legal_guardian
        )
        SELECT
            p.id,
            p.clinic_id,
            COALESCE(p.emergency_contact->>'name', ''),
            NULLIF(p.emergency_contact->>'relationship', ''),
            COALESCE(p.emergency_contact->>'phone', ''),
            NULLIF(p.emergency_contact->>'email', ''),
            COALESCE((p.emergency_contact->>'is_legal_guardian')::boolean, false)
        FROM patients p
        WHERE p.emergency_contact IS NOT NULL
          AND jsonb_typeof(p.emergency_contact) = 'object'
          AND COALESCE(p.emergency_contact->>'name', '') <> ''
          AND COALESCE(p.emergency_contact->>'phone', '') <> '';
        """
    )

    op.execute(
        """
        INSERT INTO patients_clinical_legal_guardian (
            patient_id, clinic_id, name, relationship, dni, phone, email, address, notes
        )
        SELECT
            p.id,
            p.clinic_id,
            COALESCE(p.legal_guardian->>'name', ''),
            COALESCE(p.legal_guardian->>'relationship', ''),
            NULLIF(p.legal_guardian->>'dni', ''),
            COALESCE(p.legal_guardian->>'phone', ''),
            NULLIF(p.legal_guardian->>'email', ''),
            NULLIF(p.legal_guardian->>'address', ''),
            NULLIF(p.legal_guardian->>'notes', '')
        FROM patients p
        WHERE p.legal_guardian IS NOT NULL
          AND jsonb_typeof(p.legal_guardian) = 'object'
          AND COALESCE(p.legal_guardian->>'name', '') <> ''
          AND COALESCE(p.legal_guardian->>'relationship', '') <> ''
          AND COALESCE(p.legal_guardian->>'phone', '') <> '';
        """
    )

    # --- Drop legacy JSONB columns -------------------------------------

    op.drop_column("patients", "medical_history")
    op.drop_column("patients", "emergency_contact")
    op.drop_column("patients", "legal_guardian")


def downgrade() -> None:
    op.add_column(
        "patients",
        sa.Column("legal_guardian", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "patients",
        sa.Column("emergency_contact", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "patients",
        sa.Column(
            "medical_history",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )

    for table in (
        "patients_clinical_legal_guardian",
        "patients_clinical_emergency_contact",
        "patients_clinical_surgical_history",
        "patients_clinical_systemic_disease",
        "patients_clinical_medication",
        "patients_clinical_allergy",
        "patients_clinical_medical_context",
    ):
        op.drop_table(table)
