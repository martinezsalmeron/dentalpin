"""SQLAlchemy models for module lifecycle state.

Three tables:

* ``core_module`` — one row per discovered module with its current state.
* ``core_module_operation_log`` — append-only log of install/uninstall/
  upgrade steps for atomicity and crash recovery.
* ``core_external_id`` — pointers to seed/data records owned by a module,
  so they can be updated on upgrade and removed on uninstall.
"""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ModuleRecord(Base):
    """Persistent record of a module and its lifecycle state."""

    __tablename__ = "core_module"

    name: Mapped[str] = mapped_column(String(100), primary_key=True)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    state: Mapped[str] = mapped_column(String(30), nullable=False)
    category: Mapped[str] = mapped_column(String(20), nullable=False)
    removable: Mapped[bool] = mapped_column(Boolean, nullable=False)
    auto_install: Mapped[bool] = mapped_column(Boolean, nullable=False)
    installed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_state_change: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    base_revision: Mapped[str | None] = mapped_column(String(64))
    applied_revision: Mapped[str | None] = mapped_column(String(64))
    manifest_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    error_message: Mapped[str | None] = mapped_column(Text)
    error_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ModuleOperationLog(Base):
    """Step-level log for install/uninstall/upgrade.

    The lifespan writer inserts ``started`` before each step and updates to
    ``completed`` or ``failed``. On restart after a crash, the registry
    inspects this log to decide what to retry.
    """

    __tablename__ = "core_module_operation_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    module_name: Mapped[str] = mapped_column(
        String(100), ForeignKey("core_module.name", ondelete="CASCADE"), nullable=False
    )
    operation: Mapped[str] = mapped_column(String(30), nullable=False)
    step: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    details: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        Index("ix_core_module_operation_log_module", "module_name"),
        Index("ix_core_module_operation_log_created", "created_at"),
    )


class ExternalId(Base):
    """Pointer from a stable ``xml_id`` to a record owned by a module.

    Allows module upgrades to update seed records by ID and uninstall
    to cascade-delete them.
    """

    __tablename__ = "core_external_id"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    module_name: Mapped[str] = mapped_column(String(100), nullable=False)
    xml_id: Mapped[str] = mapped_column(String(255), nullable=False)
    table_name: Mapped[str] = mapped_column(String(100), nullable=False)
    record_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    noupdate: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("module_name", "xml_id", name="uq_core_external_id_module_xml"),
        Index("ix_core_external_id_module", "module_name"),
        Index("ix_core_external_id_table_record", "table_name", "record_id"),
    )
