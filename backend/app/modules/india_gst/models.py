"""India GST module database models.

Tables:

* ``india_gst_settings`` — per-clinic supplier GST profile, e-invoice
  config, display prefs (one row per clinic).
* ``india_gst_catalog_items`` — per-treatment SAC code defaults.
* ``india_gst_invoice_items`` — CGST/SGST/IGST split for an issued
  invoice line, derived from (never recomputed against)
  ``InvoiceItem.line_tax``.
* ``india_gst_einvoice_submissions`` — e-invoice scaffolding state
  (one row per invoice; no live GSP/IRP submission in v1).

None of these add columns to billing's own ``invoices``/``invoice_items``
tables — see ``hook.py`` and the module ``CLAUDE.md`` for the extension
strategy via ``Invoice.compliance_data['IN']``.
"""

from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, TimestampMixin

if TYPE_CHECKING:
    from app.core.auth.models import Clinic
    from app.modules.billing.models import Invoice, InvoiceItem
    from app.modules.catalog.models import TreatmentCatalogItem


class IndiaGstSettings(Base, TimestampMixin):
    """Per-clinic India GST supplier profile. Exactly one row per clinic."""

    __tablename__ = "india_gst_settings"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    clinic_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clinics.id", ondelete="CASCADE"), unique=True, index=True
    )

    trade_name: Mapped[str | None] = mapped_column(String(200), default=None)
    # Supplier (clinic's own) GSTIN. NEVER the recipient's — that lives
    # on ``Invoice.billing_tax_id`` (billing-owned, generic column).
    gstin: Mapped[str | None] = mapped_column(String(15), default=None)
    registration_type: Mapped[str] = mapped_column(String(20), default="regular", nullable=False)
    # State/UT code (see constants.INDIA_STATES), not a display string.
    clinic_state: Mapped[str | None] = mapped_column(String(2), default=None)

    # Above this yearly-turnover threshold e-invoicing applies; the hook
    # then marks issued invoices "not_configured" (no provider in v1).
    turnover_threshold: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), default=None)

    show_gstin_on_invoice: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    show_sac_on_invoice: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    clinic: Mapped["Clinic"] = relationship()

    __table_args__ = (Index("ix_india_gst_settings_clinic", "clinic_id"),)


class IndiaGstCatalogItem(Base, TimestampMixin):
    """Per-treatment SAC code default, overriding the catalog item's own.

    When no row exists for a catalog item, the invoice line has no SAC
    default and the settings "missing SAC" review table flags it.
    """

    __tablename__ = "india_gst_catalog_items"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    clinic_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clinics.id", ondelete="CASCADE"), index=True
    )
    catalog_item_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("treatment_catalog_items.id", ondelete="CASCADE"),
        index=True,
    )

    sac_code: Mapped[str] = mapped_column(String(10), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, default=None)

    catalog_item: Mapped["TreatmentCatalogItem"] = relationship()

    __table_args__ = (
        Index("ix_india_gst_catalog_items_clinic", "clinic_id"),
        UniqueConstraint("clinic_id", "catalog_item_id", name="uq_india_gst_catalog_items_item"),
    )


class IndiaGstInvoiceItem(Base, TimestampMixin):
    """CGST/SGST/IGST split for one issued invoice line.

    Written once by :func:`hook.compute_gst_breakdown` at issue time
    (upserted — idempotent on re-run). Splits ``InvoiceItem.line_tax``
    after the fact; never recomputes tax independently. CGST and SGST
    are always EQUAL (each = line tax / 2, rounded HALF_UP per head);
    on odd-paise lines the pair may differ from ``line_tax`` by ±0.01 —
    head-wise rounding, expected under GST. Sign-agnostic: credit-note
    amounts arrive already negative and are not re-negated.
    """

    __tablename__ = "india_gst_invoice_items"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    clinic_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clinics.id", ondelete="RESTRICT"), index=True
    )
    invoice_item_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoice_items.id", ondelete="RESTRICT"),
        unique=True,
        index=True,
    )

    sac_code: Mapped[str | None] = mapped_column(String(10), default=None)
    tax_type: Mapped[str] = mapped_column(String(10), nullable=False)  # intra | inter

    cgst_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0"))
    cgst_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))
    sgst_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0"))
    sgst_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))
    igst_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0"))
    igst_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))

    invoice_item: Mapped["InvoiceItem"] = relationship()

    __table_args__ = (Index("ix_india_gst_invoice_items_clinic", "clinic_id"),)


class IndiaGstDocumentSequence(Base, TimestampMixin):
    """Per-(clinic, prefix, financial-year) GST serial counter.

    GST Rule 46(b) requires a consecutive serial number unique within the
    financial year (April–March). Billing's ``InvoiceSeries`` counter
    resets on the *calendar* year, so between January and March its
    numbers repeat inside one FY — this table is the FY-scoped source of
    truth instead. Rows are incremented under ``SELECT … FOR UPDATE``
    (see :func:`service.allocate_fy_document_number`), and the unique
    constraint makes duplicate GST document numbers impossible.
    """

    __tablename__ = "india_gst_document_sequences"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    clinic_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clinics.id", ondelete="RESTRICT"), index=True
    )
    prefix: Mapped[str] = mapped_column(String(20), nullable=False)
    fy_label: Mapped[str] = mapped_column(String(8), nullable=False)  # e.g. "FY26-27"
    last_number: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    __table_args__ = (
        UniqueConstraint("clinic_id", "prefix", "fy_label", name="uq_india_gst_document_sequences"),
    )


class IndiaGstEinvoiceSubmission(Base, TimestampMixin):
    """E-invoice applicability state for one invoice. One row per invoice.

    v1 has no live GSP/IRP provider wired in. The hook writes
    ``not_required`` (below the turnover threshold) or
    ``not_configured`` (above it, no provider); the retry endpoint
    always answers 409. IRN/acknowledgement columns arrive with a real
    provider adapter, not before.
    """

    __tablename__ = "india_gst_einvoice_submissions"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    clinic_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clinics.id", ondelete="RESTRICT"), index=True
    )
    invoice_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="RESTRICT"), unique=True, index=True
    )

    state: Mapped[str] = mapped_column(String(20), default="not_required", nullable=False)
    provider_error_message: Mapped[str | None] = mapped_column(Text, default=None)

    clinic: Mapped["Clinic"] = relationship()
    invoice: Mapped["Invoice"] = relationship()

    __table_args__ = (
        Index("ix_india_gst_einvoice_clinic", "clinic_id"),
        Index("ix_india_gst_einvoice_state", "clinic_id", "state"),
    )
