"""india_gst module — initial schema.

Revision ID: igst_0001
Revises: 0001
Create Date: 2026-08-19
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "igst_0001"
# india_gst is ``removable=True``; chain off the core init so the branch
# is truly independent (mirrors verifactu's vfy_0001 exactly). Declares
# a cross-module table requirement on ``invoices``/``invoice_items``
# (created by ``bil_0001``) via ``depends_on`` rather than threading
# into billing's own chain — ``alembic downgrade india_gst@base`` walks
# only india_gst revisions during uninstall.
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = ("india_gst",)
depends_on: str | Sequence[str] | None = "bil_0001"


def upgrade() -> None:
    op.create_table(
        "india_gst_settings",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("trade_name", sa.String(length=200), nullable=True),
        sa.Column("gstin", sa.String(length=15), nullable=True),
        sa.Column(
            "registration_type", sa.String(length=20), nullable=False, server_default="regular"
        ),
        sa.Column("clinic_state", sa.String(length=2), nullable=True),
        sa.Column("turnover_threshold", sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column(
            "show_gstin_on_invoice", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
        sa.Column(
            "show_sac_on_invoice", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("clinic_id", name="uq_india_gst_settings_clinic"),
        sa.CheckConstraint(
            "registration_type IN ('regular','composition','unregistered','exempt')",
            name="ck_india_gst_settings_registration_type",
        ),
    )
    op.create_index(op.f("ix_india_gst_settings_clinic_id"), "india_gst_settings", ["clinic_id"])

    op.create_table(
        "india_gst_catalog_items",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("catalog_item_id", sa.UUID(), nullable=False),
        sa.Column("sac_code", sa.String(length=10), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["catalog_item_id"], ["treatment_catalog_items.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("clinic_id", "catalog_item_id", name="uq_india_gst_catalog_items_item"),
    )
    op.create_index(
        op.f("ix_india_gst_catalog_items_clinic_id"), "india_gst_catalog_items", ["clinic_id"]
    )
    op.create_index(
        op.f("ix_india_gst_catalog_items_catalog_item_id"),
        "india_gst_catalog_items",
        ["catalog_item_id"],
    )

    op.create_table(
        "india_gst_invoice_items",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("invoice_item_id", sa.UUID(), nullable=False),
        sa.Column("sac_code", sa.String(length=10), nullable=True),
        sa.Column("tax_type", sa.String(length=10), nullable=False),
        sa.Column(
            "cgst_rate", sa.Numeric(precision=5, scale=2), nullable=False, server_default="0"
        ),
        sa.Column(
            "cgst_amount", sa.Numeric(precision=12, scale=2), nullable=False, server_default="0"
        ),
        sa.Column(
            "sgst_rate", sa.Numeric(precision=5, scale=2), nullable=False, server_default="0"
        ),
        sa.Column(
            "sgst_amount", sa.Numeric(precision=12, scale=2), nullable=False, server_default="0"
        ),
        sa.Column(
            "igst_rate", sa.Numeric(precision=5, scale=2), nullable=False, server_default="0"
        ),
        sa.Column(
            "igst_amount", sa.Numeric(precision=12, scale=2), nullable=False, server_default="0"
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["invoice_item_id"], ["invoice_items.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("invoice_item_id", name="uq_india_gst_invoice_items_item"),
        sa.CheckConstraint("tax_type IN ('intra','inter')", name="ck_india_gst_invoice_items_type"),
    )
    op.create_index(
        op.f("ix_india_gst_invoice_items_clinic_id"), "india_gst_invoice_items", ["clinic_id"]
    )
    op.create_index(
        op.f("ix_india_gst_invoice_items_invoice_item_id"),
        "india_gst_invoice_items",
        ["invoice_item_id"],
    )

    op.create_table(
        "india_gst_document_sequences",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("prefix", sa.String(length=20), nullable=False),
        sa.Column("fy_label", sa.String(length=8), nullable=False),
        sa.Column("last_number", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "clinic_id", "prefix", "fy_label", name="uq_india_gst_document_sequences"
        ),
    )
    op.create_index(
        op.f("ix_india_gst_document_sequences_clinic_id"),
        "india_gst_document_sequences",
        ["clinic_id"],
    )

    op.create_table(
        "india_gst_einvoice_submissions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("invoice_id", sa.UUID(), nullable=False),
        sa.Column("state", sa.String(length=20), nullable=False, server_default="not_required"),
        sa.Column("provider_error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["invoice_id"], ["invoices.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("invoice_id", name="uq_india_gst_einvoice_invoice"),
        sa.CheckConstraint(
            "state IN ('not_required','not_configured','pending','generated','rejected','error')",
            name="ck_india_gst_einvoice_state",
        ),
    )
    op.create_index(
        op.f("ix_india_gst_einvoice_submissions_clinic_id"),
        "india_gst_einvoice_submissions",
        ["clinic_id"],
    )
    op.create_index(
        "ix_india_gst_einvoice_clinic_state",
        "india_gst_einvoice_submissions",
        ["clinic_id", "state"],
    )


def downgrade() -> None:
    op.drop_index("ix_india_gst_einvoice_clinic_state", table_name="india_gst_einvoice_submissions")
    op.drop_index(
        op.f("ix_india_gst_einvoice_submissions_clinic_id"),
        table_name="india_gst_einvoice_submissions",
    )
    op.drop_table("india_gst_einvoice_submissions")

    op.drop_index(
        op.f("ix_india_gst_document_sequences_clinic_id"),
        table_name="india_gst_document_sequences",
    )
    op.drop_table("india_gst_document_sequences")

    op.drop_index(
        op.f("ix_india_gst_invoice_items_invoice_item_id"),
        table_name="india_gst_invoice_items",
    )
    op.drop_index(
        op.f("ix_india_gst_invoice_items_clinic_id"), table_name="india_gst_invoice_items"
    )
    op.drop_table("india_gst_invoice_items")

    op.drop_index(
        op.f("ix_india_gst_catalog_items_catalog_item_id"),
        table_name="india_gst_catalog_items",
    )
    op.drop_index(
        op.f("ix_india_gst_catalog_items_clinic_id"), table_name="india_gst_catalog_items"
    )
    op.drop_table("india_gst_catalog_items")

    op.drop_index(op.f("ix_india_gst_settings_clinic_id"), table_name="india_gst_settings")
    op.drop_table("india_gst_settings")
