"""Clinical notes module database models.

Polymorphic clinical-notes store. Notes attach to one of four owner types
and carry a ``note_type`` discriminator that the UI uses for filtering and
color-coding.

Owner / type matrix:

| ``note_type``      | ``owner_type`` | ``owner_id`` references          |
|--------------------|----------------|----------------------------------|
| ``administrative`` | ``patient``    | ``patients.id``                  |
| ``diagnosis``      | ``patient``    | ``patients.id`` (optional tooth) |
| ``treatment``      | ``treatment``  | ``treatments.id`` (odontogram)   |
| ``treatment_plan`` | ``plan``       | ``treatment_plans.id``           |

``owner_id`` has no DB-level FK (polymorphic) — the service layer validates
that the owner exists in the same clinic before insert. Visit-level notes
keep living on ``AppointmentTreatment.notes`` in agenda; ``ClinicalNoteAttachment``
still supports ``appointment_treatment`` as an attachment owner so radiographs
can be linked to a visit without going through this module.
"""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, TimestampMixin

# Note types — discriminator surfaced to the UI for filtering + color-coding.
NOTE_TYPE_ADMINISTRATIVE = "administrative"
NOTE_TYPE_DIAGNOSIS = "diagnosis"
NOTE_TYPE_TREATMENT = "treatment"
NOTE_TYPE_TREATMENT_PLAN = "treatment_plan"
NOTE_TYPES = (
    NOTE_TYPE_ADMINISTRATIVE,
    NOTE_TYPE_DIAGNOSIS,
    NOTE_TYPE_TREATMENT,
    NOTE_TYPE_TREATMENT_PLAN,
)

# Owner types — what ``owner_id`` references.
NOTE_OWNER_PATIENT = "patient"
NOTE_OWNER_TREATMENT = "treatment"
NOTE_OWNER_PLAN = "plan"
NOTE_OWNER_TYPES = (NOTE_OWNER_PATIENT, NOTE_OWNER_TREATMENT, NOTE_OWNER_PLAN)

# Attachment owner types — superset, retained ``appointment_treatment`` for
# direct radiograph uploads on visits (consumed by agenda UI).
ATTACHMENT_OWNER_APPOINTMENT_TREATMENT = "appointment_treatment"
ATTACHMENT_OWNER_TYPES = (*NOTE_OWNER_TYPES, ATTACHMENT_OWNER_APPOINTMENT_TREATMENT)


if TYPE_CHECKING:
    from app.core.auth.models import Clinic, User
    from app.modules.media.models import Document


class ClinicalNote(Base, TimestampMixin):
    """Timestamped clinical note.

    Polymorphic on ``owner_type`` (``patient`` / ``treatment`` / ``plan``).
    ``note_type`` adds a UI-facing discriminator independent of the linkage —
    e.g. an ``administrative`` note also sits on a patient owner, but the UI
    treats it differently from a ``diagnosis`` note on the same patient.
    """

    __tablename__ = "clinical_notes"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id"), index=True)

    note_type: Mapped[str] = mapped_column(String(20))
    owner_type: Mapped[str] = mapped_column(String(20))
    owner_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True))

    # Optional tooth pin used by ``diagnosis`` notes that the dentist tied
    # to a specific tooth while exploring with the odontogram. NULL for
    # every other note_type.
    tooth_number: Mapped[int | None] = mapped_column(Integer)

    body: Mapped[str] = mapped_column(Text)
    author_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))

    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    clinic: Mapped["Clinic"] = relationship()
    author: Mapped["User"] = relationship()
    attachments: Mapped[list["ClinicalNoteAttachment"]] = relationship(
        back_populates="note",
    )

    __table_args__ = (
        CheckConstraint(
            "note_type IN ('administrative', 'diagnosis', 'treatment', 'treatment_plan')",
            name="ck_clinical_notes_note_type",
        ),
        CheckConstraint(
            "owner_type IN ('patient', 'treatment', 'plan')",
            name="ck_clinical_notes_owner_type",
        ),
        CheckConstraint(
            "(note_type = 'administrative' AND owner_type = 'patient' AND tooth_number IS NULL) "
            "OR (note_type = 'diagnosis' AND owner_type = 'patient') "
            "OR (note_type = 'treatment' AND owner_type = 'treatment' AND tooth_number IS NULL) "
            "OR (note_type = 'treatment_plan' AND owner_type = 'plan' "
            "AND tooth_number IS NULL)",
            name="ck_clinical_notes_type_owner_matrix",
        ),
        Index(
            "idx_clinical_notes_owner",
            "clinic_id",
            "owner_type",
            "owner_id",
            "deleted_at",
            "created_at",
        ),
        Index(
            "idx_clinical_notes_patient_recent",
            "clinic_id",
            "note_type",
            "owner_id",
            "deleted_at",
            "created_at",
        ),
        Index("idx_clinical_notes_author", "author_id"),
    )


class ClinicalNoteAttachment(Base, TimestampMixin):
    """Polymorphic link between a ``media.Document`` and a notes owner.

    ``owner_type`` extends the note matrix with ``appointment_treatment`` so
    radiographs uploaded directly from the agenda's visit panel keep working.
    """

    __tablename__ = "clinical_note_attachments"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id"), index=True)

    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    owner_type: Mapped[str] = mapped_column(String(30))
    owner_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True))
    note_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("clinical_notes.id", ondelete="SET NULL"), index=True
    )
    display_order: Mapped[int] = mapped_column(Integer, default=0)

    clinic: Mapped["Clinic"] = relationship()
    document: Mapped["Document"] = relationship()
    note: Mapped["ClinicalNote | None"] = relationship(back_populates="attachments")

    __table_args__ = (
        CheckConstraint(
            "owner_type IN ('patient', 'treatment', 'plan', 'appointment_treatment')",
            name="ck_clinical_note_attachments_owner_type",
        ),
        UniqueConstraint(
            "document_id",
            "owner_type",
            "owner_id",
            name="uq_clinical_note_attachments_doc_owner",
        ),
        Index(
            "idx_clinical_note_attachments_owner",
            "clinic_id",
            "owner_type",
            "owner_id",
        ),
    )
