"""whatsapp_kapso models — per-clinic Kapso credentials + template cache.

Secrets (api key, webhook secret) are Fernet-encrypted at rest via the
project-wide ``app.core.email.encryption`` util. Tables live on the module's
own Alembic branch so uninstall drops them cleanly.
"""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, TimestampMixin

if TYPE_CHECKING:
    from app.core.auth.models import Clinic


class WhatsappKapsoSettings(Base, TimestampMixin):
    """Per-clinic Kapso connection: credentials + connected number."""

    __tablename__ = "whatsapp_kapso_settings"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id"), unique=True, index=True)

    api_key_encrypted: Mapped[str] = mapped_column(Text)
    # Kapso/Meta phone number id — the tenant key on every webhook event.
    phone_number_id: Mapped[str] = mapped_column(String(64), index=True)
    business_account_id: Mapped[str | None] = mapped_column(String(64), default=None)
    webhook_secret_encrypted: Mapped[str] = mapped_column(Text)
    display_phone_number: Mapped[str | None] = mapped_column(String(32), default=None)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    last_template_sync_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )

    clinic: Mapped["Clinic"] = relationship(foreign_keys=[clinic_id])

    __table_args__ = (
        Index("idx_whatsapp_kapso_settings_clinic", "clinic_id"),
        Index("idx_whatsapp_kapso_settings_phone_number_id", "phone_number_id"),
    )


class WhatsappKapsoTemplate(Base, TimestampMixin):
    """Cache of the clinic's Meta templates synced from Kapso (for the picker)."""

    __tablename__ = "whatsapp_kapso_templates"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id"), index=True)

    name: Mapped[str] = mapped_column(String(200))
    language: Mapped[str] = mapped_column(String(10))
    status: Mapped[str] = mapped_column(String(20))  # approved | pending | rejected
    category: Mapped[str | None] = mapped_column(String(50), default=None)
    synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)

    clinic: Mapped["Clinic"] = relationship(foreign_keys=[clinic_id])

    __table_args__ = (
        UniqueConstraint("clinic_id", "name", "language", name="uq_whatsapp_kapso_template"),
        Index("idx_whatsapp_kapso_templates_clinic", "clinic_id"),
    )
