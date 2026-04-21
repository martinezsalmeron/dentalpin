"""v2 squash — patients_clinical initial.

Initial schema for the `patients_clinical` module.

Revision ID: pc_0001
Revises:
Create Date: 2026-04-21

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "pc_0001"
down_revision: str | None = "tp_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "patients_clinical_allergy",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("patient_id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=True),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("reaction", sa.String(length=500), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinics.id"],
        ),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_patients_clinical_allergy_clinic_id"),
        "patients_clinical_allergy",
        ["clinic_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_patients_clinical_allergy_patient_id"),
        "patients_clinical_allergy",
        ["patient_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_patients_clinical_allergy_severity"),
        "patients_clinical_allergy",
        ["severity"],
        unique=False,
    )

    op.create_table(
        "patients_clinical_emergency_contact",
        sa.Column("patient_id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("relationship", sa.String(length=50), nullable=True),
        sa.Column("phone", sa.String(length=20), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("is_legal_guardian", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinics.id"],
        ),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("patient_id"),
    )
    op.create_index(
        op.f("ix_patients_clinical_emergency_contact_clinic_id"),
        "patients_clinical_emergency_contact",
        ["clinic_id"],
        unique=False,
    )

    op.create_table(
        "patients_clinical_legal_guardian",
        sa.Column("patient_id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("relationship", sa.String(length=50), nullable=False),
        sa.Column("dni", sa.String(length=20), nullable=True),
        sa.Column("phone", sa.String(length=20), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("address", sa.String(length=200), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinics.id"],
        ),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("patient_id"),
    )
    op.create_index(
        op.f("ix_patients_clinical_legal_guardian_clinic_id"),
        "patients_clinical_legal_guardian",
        ["clinic_id"],
        unique=False,
    )

    op.create_table(
        "patients_clinical_medical_context",
        sa.Column("patient_id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("is_pregnant", sa.Boolean(), nullable=False),
        sa.Column("pregnancy_week", sa.Integer(), nullable=True),
        sa.Column("is_lactating", sa.Boolean(), nullable=False),
        sa.Column("is_on_anticoagulants", sa.Boolean(), nullable=False),
        sa.Column("anticoagulant_medication", sa.String(length=100), nullable=True),
        sa.Column("inr_value", sa.Float(), nullable=True),
        sa.Column("last_inr_date", sa.Date(), nullable=True),
        sa.Column("is_smoker", sa.Boolean(), nullable=False),
        sa.Column("smoking_frequency", sa.String(length=100), nullable=True),
        sa.Column("alcohol_consumption", sa.String(length=100), nullable=True),
        sa.Column("bruxism", sa.Boolean(), nullable=False),
        sa.Column("adverse_reactions_to_anesthesia", sa.Boolean(), nullable=False),
        sa.Column("anesthesia_reaction_details", sa.String(length=500), nullable=True),
        sa.Column("last_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_updated_by", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinics.id"],
        ),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("patient_id"),
    )
    op.create_index(
        op.f("ix_patients_clinical_medical_context_clinic_id"),
        "patients_clinical_medical_context",
        ["clinic_id"],
        unique=False,
    )

    op.create_table(
        "patients_clinical_medication",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("patient_id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("dosage", sa.String(length=100), nullable=True),
        sa.Column("frequency", sa.String(length=100), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinics.id"],
        ),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_patients_clinical_medication_clinic_id"),
        "patients_clinical_medication",
        ["clinic_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_patients_clinical_medication_patient_id"),
        "patients_clinical_medication",
        ["patient_id"],
        unique=False,
    )

    op.create_table(
        "patients_clinical_surgical_history",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("patient_id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("procedure", sa.String(length=200), nullable=False),
        sa.Column("surgery_date", sa.Date(), nullable=True),
        sa.Column("complications", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinics.id"],
        ),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_patients_clinical_surgical_history_clinic_id"),
        "patients_clinical_surgical_history",
        ["clinic_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_patients_clinical_surgical_history_patient_id"),
        "patients_clinical_surgical_history",
        ["patient_id"],
        unique=False,
    )

    op.create_table(
        "patients_clinical_systemic_disease",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("patient_id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=True),
        sa.Column("diagnosis_date", sa.Date(), nullable=True),
        sa.Column("is_controlled", sa.Boolean(), nullable=False),
        sa.Column("is_critical", sa.Boolean(), nullable=False),
        sa.Column("medications", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinics.id"],
        ),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_patients_clinical_systemic_disease_clinic_id"),
        "patients_clinical_systemic_disease",
        ["clinic_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_patients_clinical_systemic_disease_is_critical"),
        "patients_clinical_systemic_disease",
        ["is_critical"],
        unique=False,
    )
    op.create_index(
        op.f("ix_patients_clinical_systemic_disease_patient_id"),
        "patients_clinical_systemic_disease",
        ["patient_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("patients_clinical_systemic_disease")
    op.drop_table("patients_clinical_surgical_history")
    op.drop_table("patients_clinical_medication")
    op.drop_table("patients_clinical_medical_context")
    op.drop_table("patients_clinical_legal_guardian")
    op.drop_table("patients_clinical_emergency_contact")
    op.drop_table("patients_clinical_allergy")
