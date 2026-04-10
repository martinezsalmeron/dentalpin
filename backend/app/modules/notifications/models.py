"""Notifications module database models."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, TimestampMixin

if TYPE_CHECKING:
    from app.core.auth.models import Clinic
    from app.modules.clinical.models import Patient


class EmailTemplate(Base, TimestampMixin):
    """Customizable email template.

    Templates can be defined at system level (clinic_id=None) or
    customized per clinic. When sending, clinic-specific templates
    take precedence over system templates.
    """

    __tablename__ = "email_templates"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    clinic_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("clinics.id"), index=True, default=None
    )  # NULL = system template

    # Template identification
    template_key: Mapped[str] = mapped_column(
        String(100), index=True
    )  # e.g., "appointment_confirmation"
    locale: Mapped[str] = mapped_column(String(5), default="es")  # es, en

    # Content
    subject: Mapped[str] = mapped_column(String(255))
    body_html: Mapped[str] = mapped_column(Text)
    body_text: Mapped[str | None] = mapped_column(Text, default=None)

    # Metadata
    variables: Mapped[dict | None] = mapped_column(
        JSONB, default=None
    )  # Available template variables
    description: Mapped[str | None] = mapped_column(
        String(500), default=None
    )  # Template description

    # Flags
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)  # System = not editable
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    clinic: Mapped["Clinic | None"] = relationship(foreign_keys=[clinic_id])

    __table_args__ = (
        UniqueConstraint(
            "clinic_id", "template_key", "locale", name="uq_email_template_clinic_key_locale"
        ),
        Index("idx_email_templates_clinic", "clinic_id"),
        Index("idx_email_templates_key", "template_key"),
    )


class NotificationPreference(Base, TimestampMixin):
    """Notification preferences for patients or users.

    Stores opt-in/opt-out settings for different notification types.
    Either patient_id or user_id should be set, not both.
    """

    __tablename__ = "notification_preferences"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id"), index=True)

    # Subject - either patient or user
    patient_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("patients.id"), index=True, default=None
    )
    user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id"), index=True, default=None
    )

    # Global email toggle
    email_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    # Per-type preferences
    preferences: Mapped[dict] = mapped_column(
        JSONB,
        default=lambda: {
            "appointment_confirmation": True,
            "appointment_reminder": True,
            "appointment_cancelled": True,
            "budget_sent": True,
            "budget_accepted": True,
            "welcome": True,
        },
    )

    # Language preference
    preferred_locale: Mapped[str] = mapped_column(String(5), default="es")

    # Relationships
    clinic: Mapped["Clinic"] = relationship(foreign_keys=[clinic_id])
    patient: Mapped["Patient | None"] = relationship(foreign_keys=[patient_id])

    __table_args__ = (
        # A patient can only have one preference record per clinic
        UniqueConstraint(
            "clinic_id", "patient_id", name="uq_notification_pref_clinic_patient"
        ),
        # A user can only have one preference record per clinic
        UniqueConstraint(
            "clinic_id", "user_id", name="uq_notification_pref_clinic_user"
        ),
        Index("idx_notification_preferences_clinic", "clinic_id"),
        Index("idx_notification_preferences_patient", "patient_id"),
        Index("idx_notification_preferences_user", "user_id"),
    )


class ClinicNotificationSettings(Base, TimestampMixin):
    """Clinic-level notification settings.

    Configures which notifications are auto-sent vs manual,
    and general notification behavior for the clinic.
    """

    __tablename__ = "clinic_notification_settings"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    clinic_id: Mapped[UUID] = mapped_column(
        ForeignKey("clinics.id"), unique=True, index=True
    )

    # Per-notification-type settings
    settings: Mapped[dict] = mapped_column(
        JSONB,
        default=lambda: {
            "appointment_confirmation": {"auto_send": True, "enabled": True},
            "appointment_cancelled": {"auto_send": True, "enabled": True},
            "appointment_reminder": {"auto_send": True, "enabled": True, "hours_before": 24},
            "budget_sent": {"auto_send": False, "enabled": True},  # Manual
            "budget_accepted": {"auto_send": True, "enabled": True},
            "welcome": {"auto_send": False, "enabled": True},  # Manual
        },
    )

    # Relationships
    clinic: Mapped["Clinic"] = relationship(foreign_keys=[clinic_id])

    __table_args__ = (Index("idx_clinic_notification_settings_clinic", "clinic_id"),)


class ClinicSmtpSettings(Base, TimestampMixin):
    """SMTP configuration per clinic.

    Stores SMTP server settings for sending emails from a specific clinic.
    Passwords are encrypted using Fernet symmetric encryption.
    """

    __tablename__ = "clinic_smtp_settings"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    clinic_id: Mapped[UUID] = mapped_column(
        ForeignKey("clinics.id"), unique=True, index=True
    )

    # Provider selection: smtp, console, disabled
    provider: Mapped[str] = mapped_column(String(20), default="smtp")

    # SMTP Configuration
    host: Mapped[str | None] = mapped_column(String(255), default=None)
    port: Mapped[int] = mapped_column(Integer, default=587)
    username: Mapped[str | None] = mapped_column(String(255), default=None)
    password_encrypted: Mapped[str | None] = mapped_column(Text, default=None)
    use_tls: Mapped[bool] = mapped_column(Boolean, default=True)
    use_ssl: Mapped[bool] = mapped_column(Boolean, default=False)

    # Sender defaults
    from_email: Mapped[str | None] = mapped_column(String(255), default=None)
    from_name: Mapped[str | None] = mapped_column(String(255), default=None)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    last_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )

    # Relationships
    clinic: Mapped["Clinic"] = relationship(foreign_keys=[clinic_id])

    __table_args__ = (
        Index("idx_clinic_smtp_settings_clinic", "clinic_id"),
    )


class EmailLog(Base):
    """Audit log for sent emails.

    Records all email send attempts for auditing and troubleshooting.
    """

    __tablename__ = "email_logs"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id"), index=True)

    # Recipient info
    recipient_email: Mapped[str] = mapped_column(String(255))
    patient_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("patients.id"), index=True, default=None
    )

    # Template info
    template_key: Mapped[str] = mapped_column(String(100))
    subject: Mapped[str] = mapped_column(String(255))

    # Status
    status: Mapped[str] = mapped_column(
        String(20), index=True
    )  # pending, sent, failed, skipped

    # Provider info
    provider: Mapped[str] = mapped_column(String(50))  # smtp, sendgrid, console
    provider_message_id: Mapped[str | None] = mapped_column(String(255), default=None)

    # Error tracking
    error_message: Mapped[str | None] = mapped_column(Text, default=None)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now()
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)

    # Event tracking
    triggered_by_event: Mapped[str | None] = mapped_column(
        String(100), default=None
    )  # Event that triggered this email
    triggered_by_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id"), index=True, default=None
    )  # User who triggered manual send

    # Context data for debugging
    context_data: Mapped[dict | None] = mapped_column(
        JSONB, default=None
    )  # Template context (sanitized)

    # Relationships
    clinic: Mapped["Clinic"] = relationship(foreign_keys=[clinic_id])
    patient: Mapped["Patient | None"] = relationship(foreign_keys=[patient_id])

    __table_args__ = (
        Index("idx_email_logs_clinic", "clinic_id"),
        Index("idx_email_logs_status", "status"),
        Index("idx_email_logs_created_at", "created_at"),
        Index("idx_email_logs_patient", "patient_id"),
        Index("idx_email_logs_template", "template_key"),
    )
