"""verifactu module — initial schema.

Revision ID: vfy_0001
Revises: tp_0002
Create Date: 2026-04-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "vfy_0001"
down_revision: str | None = "tp_0002"
branch_labels: str | Sequence[str] | None = ("verifactu",)
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "verifactu_settings",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("environment", sa.String(length=10), nullable=False, server_default="test"),
        sa.Column("nif_emisor", sa.String(length=20), nullable=True),
        sa.Column("nombre_razon_emisor", sa.String(length=200), nullable=True),
        sa.Column("numero_instalacion", sa.String(length=60), nullable=False),
        sa.Column("last_huella", sa.String(length=64), nullable=True),
        sa.Column("last_record_id", sa.UUID(), nullable=True),
        sa.Column("next_send_after", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_aeat_response_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("clinic_id", name="uq_verifactu_settings_clinic"),
        sa.CheckConstraint(
            "environment IN ('test','prod')", name="ck_verifactu_settings_environment"
        ),
    )
    op.create_index(
        op.f("ix_verifactu_settings_clinic_id"),
        "verifactu_settings",
        ["clinic_id"],
    )

    op.create_table(
        "verifactu_certificates",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("pfx_encrypted", sa.LargeBinary(), nullable=False),
        sa.Column("password_encrypted", sa.Text(), nullable=False),
        sa.Column("subject_cn", sa.String(length=200), nullable=True),
        sa.Column("issuer_cn", sa.String(length=200), nullable=True),
        sa.Column("nif_titular", sa.String(length=20), nullable=True),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("uploaded_by", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_verifactu_certificates_clinic_id"),
        "verifactu_certificates",
        ["clinic_id"],
    )
    op.create_index(
        "ux_verifactu_certificates_one_active_per_clinic",
        "verifactu_certificates",
        ["clinic_id"],
        unique=True,
        postgresql_where=sa.text("is_active = true"),
    )

    op.create_table(
        "verifactu_records",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("invoice_id", sa.UUID(), nullable=False),
        sa.Column("record_type", sa.String(length=20), nullable=False),
        sa.Column("tipo_factura", sa.String(length=2), nullable=False),
        sa.Column("tipo_rectificativa", sa.String(length=1), nullable=True),
        sa.Column("serie_numero", sa.String(length=60), nullable=False),
        sa.Column("fecha_expedicion", sa.Date(), nullable=False),
        sa.Column("cuota_total", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("importe_total", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("huella", sa.String(length=64), nullable=False),
        sa.Column("huella_anterior", sa.String(length=64), nullable=True),
        sa.Column("is_first_record", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("fecha_hora_huso_gen_registro", sa.DateTime(timezone=True), nullable=False),
        sa.Column("xml_payload", sa.Text(), nullable=True),
        sa.Column("state", sa.String(length=30), nullable=False, server_default="pending"),
        sa.Column("aeat_csv", sa.String(length=60), nullable=True),
        sa.Column("aeat_estado_envio", sa.String(length=30), nullable=True),
        sa.Column("aeat_estado_registro", sa.String(length=30), nullable=True),
        sa.Column("aeat_codigo_error", sa.Integer(), nullable=True),
        sa.Column("aeat_descripcion_error", sa.Text(), nullable=True),
        sa.Column("aeat_timestamp_presentacion", sa.DateTime(timezone=True), nullable=True),
        sa.Column("aeat_response_xml", sa.Text(), nullable=True),
        sa.Column("subsanacion", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("rechazo_previo", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("submission_attempt", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("extra", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["invoice_id"], ["invoices.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("clinic_id", "huella", name="uq_verifactu_record_clinic_huella"),
        sa.CheckConstraint(
            "record_type IN ('alta','anulacion')",
            name="ck_verifactu_record_type",
        ),
        sa.CheckConstraint(
            "tipo_factura IN ('F1','F2','F3','R1','R2','R3','R4','R5')",
            name="ck_verifactu_record_tipo_factura",
        ),
        sa.CheckConstraint(
            "state IN ('pending','sending','accepted','accepted_with_errors',"
            "'rejected','failed_transient','failed_validation')",
            name="ck_verifactu_record_state",
        ),
    )
    op.create_index(
        op.f("ix_verifactu_records_clinic_id"),
        "verifactu_records",
        ["clinic_id"],
    )
    op.create_index(
        op.f("ix_verifactu_records_invoice_id"),
        "verifactu_records",
        ["invoice_id"],
    )
    op.create_index(
        "ix_verifactu_records_clinic_created",
        "verifactu_records",
        ["clinic_id", "created_at"],
    )
    op.create_index(
        "ix_verifactu_records_clinic_state",
        "verifactu_records",
        ["clinic_id", "state"],
    )


def downgrade() -> None:
    op.drop_index("ix_verifactu_records_clinic_state", table_name="verifactu_records")
    op.drop_index("ix_verifactu_records_clinic_created", table_name="verifactu_records")
    op.drop_index(op.f("ix_verifactu_records_invoice_id"), table_name="verifactu_records")
    op.drop_index(op.f("ix_verifactu_records_clinic_id"), table_name="verifactu_records")
    op.drop_table("verifactu_records")

    op.drop_index(
        "ux_verifactu_certificates_one_active_per_clinic",
        table_name="verifactu_certificates",
    )
    op.drop_index(
        op.f("ix_verifactu_certificates_clinic_id"), table_name="verifactu_certificates"
    )
    op.drop_table("verifactu_certificates")

    op.drop_index(op.f("ix_verifactu_settings_clinic_id"), table_name="verifactu_settings")
    op.drop_table("verifactu_settings")
