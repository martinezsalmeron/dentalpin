"""Verifactu implementation of ``BillingComplianceHook``.

Wired in :func:`VerifactuModule.install` via
``BillingHookRegistry.register(VerifactuHook())``. The billing module
discovers it through the registry — no direct import.

Flow on ``on_invoice_issued``:

1. Look up :class:`VerifactuSettings` for the clinic. If missing or
   ``enabled=False`` we return ``{}`` (the module is installed but the
   clinic hasn't activated it).
2. Pessimistically lock the settings row (``SELECT ... FOR UPDATE``)
   to read ``last_huella`` without racing other concurrent issues.
3. Determine the ``TipoFactura`` (F1/F2/R1) and build the XML payload.
4. Compute the ``Huella`` for the chain.
5. Insert a :class:`VerifactuRecord` in ``state="pending"`` with the
   full XML pre-rendered (it will be sent to AEAT by the worker).
6. Update settings ``last_huella``, ``last_record_id`` so the next
   record chains off this one. **Note:** these become the chain head
   immediately even before AEAT confirms — if AEAT rejects we'll need
   ``Subsanación`` resubmits, which use the same hash. This matches
   the AEAT spec (the chain is monotonically growing as records are
   produced, not as records are accepted).
7. Return preliminary compliance data ``{huella, qr_url, state, record_id}``
   to be merged into ``Invoice.compliance_data['ES']``. ``csv`` and
   ``submitted_at`` arrive later when the worker drains the queue.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any
from uuid import uuid4
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.models import Clinic
from app.modules.billing.hooks import BillingComplianceHook

from .models import VerifactuRecord, VerifactuSettings
from .services import hash_chain, iva_classifier, qr, sistema_informatico, vat_mapping, xml_builder

if TYPE_CHECKING:
    from app.modules.billing.models import Invoice

logger = logging.getLogger(__name__)

_TZ = ZoneInfo("Europe/Madrid")


def _now_madrid() -> datetime:
    return datetime.now(_TZ)


async def _get_or_create_settings(db: AsyncSession, clinic_id) -> VerifactuSettings:
    result = await db.execute(
        select(VerifactuSettings)
        .where(VerifactuSettings.clinic_id == clinic_id)
        .with_for_update()
    )
    settings = result.scalar_one_or_none()
    if settings is None:
        settings = VerifactuSettings(
            clinic_id=clinic_id,
            enabled=False,
            environment="test",
            numero_instalacion=str(uuid4()),
        )
        db.add(settings)
        await db.flush()
    return settings


async def _load_emisor(db: AsyncSession, clinic_id) -> tuple[str, str]:
    """Read clinic identity used as fiscal issuer.

    Returns ``(nif_emisor, nombre_razon_emisor)`` derived from
    ``clinics.tax_id`` and ``clinics.legal_name`` (falling back to
    ``clinics.name`` when no separate legal name is set). Both values
    are normalised: NIF uppercased without whitespace, razón social
    stripped.
    """

    result = await db.execute(
        select(Clinic.tax_id, Clinic.legal_name, Clinic.name).where(Clinic.id == clinic_id)
    )
    row = result.first()
    if row is None:
        return "", ""
    tax_id, legal_name, name = row
    nif = (tax_id or "").strip().upper()
    razon = (legal_name or name or "").strip()
    return nif, razon


def _format_amount(d: Decimal | float) -> Decimal:
    if isinstance(d, Decimal):
        return d.quantize(Decimal("0.01"))
    return Decimal(str(d)).quantize(Decimal("0.01"))


def _build_desglose(
    invoice: Invoice,
    overrides: dict | None = None,
) -> tuple[list[xml_builder.DesgloseLine], Decimal, Decimal]:
    """Group line items and produce ``DetalleDesglose``.

    Items are grouped by AEAT classification (``CalificacionOperacion``
    + optional ``CausaExencion``) so each desglose entry maps cleanly
    to one AEAT row. ``overrides`` is the per-clinic
    ``{vat_type_id: ClassificationOverride}`` map loaded by
    :func:`vat_mapping.load_overrides`; lines without an override fall
    back to the rate-based heuristic.
    """

    overrides = overrides or {}

    # First pass: classify every item, then group by (classification,
    # exemption_cause, rate) so the resulting AEAT lines are unique.
    classified: list[tuple[iva_classifier.DesgloseClassification, Decimal, Decimal]] = []
    for item in invoice.items or []:
        vat_rate = Decimal(str(item.vat_rate or 0))
        override = overrides.get(item.vat_type_id) if item.vat_type_id else None
        if override is not None:
            cls = vat_mapping.apply_override(vat_rate=vat_rate, override=override)
        else:
            # Pre-mapping behaviour: heuristic + ``vat_exempt_reason``
            # tag for art. 20 LIVA exemptions.
            is_exento = bool(item.vat_exempt_reason) and vat_rate == 0
            cls = iva_classifier.classify(
                vat_rate=vat_rate, is_exento_sanitario=is_exento
            )
        line_base = Decimal(str(item.line_subtotal or 0)) - Decimal(
            str(item.line_discount or 0)
        )
        line_cuota = Decimal(str(item.line_tax or 0))
        classified.append((cls, line_base, line_cuota))

    groups: dict[tuple[str, str | None, Decimal | None], dict[str, Decimal | iva_classifier.DesgloseClassification]] = {}
    for cls, base, cuota in classified:
        key = (
            cls.calificacion_operacion or "EXENTO",
            cls.causa_exencion,
            cls.tipo_impositivo,
        )
        bucket = groups.setdefault(
            key,
            {"base": Decimal("0"), "cuota": Decimal("0"), "cls": cls},
        )
        bucket["base"] = bucket["base"] + base  # type: ignore[operator]
        bucket["cuota"] = bucket["cuota"] + cuota  # type: ignore[operator]

    lines: list[xml_builder.DesgloseLine] = []
    for bucket in groups.values():
        cls = bucket["cls"]  # type: ignore[assignment]
        # AEAT validation 1237: omit CuotaRepercutida for N1/N2 and
        # exempt operations — only sujeto y no exento (S1/S2) carries
        # the IVA quota.
        is_no_quota = (
            cls.operacion_exenta
            or cls.calificacion_operacion in ("N1", "N2")
        )
        lines.append(
            xml_builder.DesgloseLine(
                impuesto=cls.impuesto,
                clave_regimen=cls.clave_regimen,
                base_imponible=_format_amount(bucket["base"]),  # type: ignore[arg-type]
                calificacion_operacion=cls.calificacion_operacion,
                operacion_exenta=cls.operacion_exenta,
                causa_exencion=cls.causa_exencion,
                tipo_impositivo=cls.tipo_impositivo,
                cuota_repercutida=None if is_no_quota else _format_amount(bucket["cuota"]),  # type: ignore[arg-type]
            )
        )

    cuota_total = sum((b["cuota"] for b in groups.values()), Decimal("0"))  # type: ignore[misc]
    importe_total = _format_amount(Decimal(str(invoice.total or 0)))
    return lines, _format_amount(cuota_total), importe_total


class VerifactuHook(BillingComplianceHook):
    @property
    def country_code(self) -> str:
        return "ES"

    def get_required_fields(self) -> list[str]:
        # We handle NIF/F1-F2 logic ourselves in validate_before_issue.
        return []

    async def validate_before_issue(self, invoice, db) -> tuple[bool, str | None]:
        settings = await db.execute(
            select(VerifactuSettings).where(VerifactuSettings.clinic_id == invoice.clinic_id)
        )
        s = settings.scalar_one_or_none()
        if s is None or not s.enabled:
            return True, None
        nif_emisor, _ = await _load_emisor(db, invoice.clinic_id)
        if not nif_emisor:
            return (
                False,
                "Configura el CIF/NIF de la clínica antes de emitir con Verifactu.",
            )
        if not s.producer_nif or not s.producer_name:
            return (
                False,
                "Configura el productor del SIF en Verifactu antes de emitir.",
            )
        if s.declaracion_responsable_signed_at is None:
            return (
                False,
                "Falta firmar la declaración responsable del productor del SIF.",
            )

        # F2 cap: simplified invoices ≤ 400 €. >400 € requires NIF (F1).
        if not invoice.credit_note_for_id and not invoice.billing_tax_id:
            if Decimal(str(invoice.total or 0)) > Decimal("400"):
                return (
                    False,
                    "Facturas > 400 € requieren NIF del destinatario para Verifactu (F1).",
                )

        return True, None

    async def on_invoice_issued(self, invoice, db) -> dict[str, Any]:
        return await self._build_record(invoice, db, is_credit_note=False)

    async def on_credit_note_issued(self, credit_note, original_invoice, db) -> dict[str, Any]:
        # Rectificativas use R1 + FacturasRectificadas. We pass original
        # via a side channel attribute so _build_record can look it up.
        credit_note._verifactu_original = original_invoice  # noqa: SLF001
        try:
            return await self._build_record(credit_note, db, is_credit_note=True)
        finally:
            try:
                del credit_note._verifactu_original
            except AttributeError:
                pass

    def enhance_pdf_data(self, pdf_data: dict, invoice) -> dict:
        cd = (invoice.compliance_data or {}).get("ES") or {}
        if cd.get("qr_url"):
            pdf_data = dict(pdf_data)
            pdf_data["verifactu_qr_png_b64"] = qr.render_png_base64(cd["qr_url"])
            pdf_data["verifactu_huella"] = cd.get("huella")
            pdf_data["verifactu_csv"] = cd.get("csv")
            notices = list(pdf_data.get("legal_notices", []))
            notices.append("Factura verificable en VERI*FACTU (AEAT)")
            pdf_data["legal_notices"] = notices
        return pdf_data

    async def _build_record(
        self, invoice, db: AsyncSession, *, is_credit_note: bool
    ) -> dict[str, Any]:
        settings = await _get_or_create_settings(db, invoice.clinic_id)
        if not settings.enabled:
            return {}

        nif_emisor, nombre_razon_emisor = await _load_emisor(db, invoice.clinic_id)
        if not nif_emisor:
            raise ValueError(
                "La clínica no tiene CIF/NIF configurado; "
                "imposible firmar el registro Verifactu."
            )

        # Decide TipoFactura.
        importe_total = Decimal(str(invoice.total or 0))
        try:
            tipo_factura = iva_classifier.determine_tipo_factura(
                has_credit_note_for=is_credit_note,
                billing_tax_id=invoice.billing_tax_id,
                importe_total=importe_total,
            )
        except ValueError as exc:
            raise ValueError(str(exc)) from exc

        overrides = await vat_mapping.load_overrides(db, invoice.clinic_id)
        desglose, cuota_total, importe_total_q = _build_desglose(invoice, overrides)
        fecha_expedicion = invoice.issue_date or _now_madrid().date()
        fecha_hora_huso = _now_madrid()

        # Chain link.
        is_first = settings.last_huella is None or settings.last_huella == ""
        huella_anterior = settings.last_huella or ""

        # Build huella.
        huella = hash_chain.fingerprint_alta(
            nif_emisor=nif_emisor,
            num_serie=invoice.invoice_number,
            fecha_expedicion=fecha_expedicion,
            tipo_factura=tipo_factura,
            cuota_total=cuota_total,
            importe_total=importe_total_q,
            huella_anterior=huella_anterior,
            fecha_hora_huso_gen_registro=fecha_hora_huso,
        )

        # Resolve "previous record" identifiers from settings.last_record_id.
        id_factura_anterior = None
        if not is_first and settings.last_record_id:
            prev = await db.execute(
                select(VerifactuRecord).where(VerifactuRecord.id == settings.last_record_id)
            )
            prev_rec = prev.scalar_one_or_none()
            if prev_rec:
                id_factura_anterior = xml_builder.IDFacturaRef(
                    nif=nif_emisor,
                    num_serie=prev_rec.serie_numero,
                    fecha=f"{prev_rec.fecha_expedicion:%d-%m-%Y}",
                )

        # Destinatario for F1; F2 uses FacturaSinIdentif.
        destinatario = None
        if invoice.billing_tax_id:
            destinatario = xml_builder.Destinatario(
                nombre_razon=invoice.billing_name or "",
                nif=invoice.billing_tax_id,
            )

        # Rectificativa metadata.
        facturas_rectificadas: list[xml_builder.IDFacturaRef] = []
        tipo_rectificativa = None
        if is_credit_note:
            tipo_rectificativa = "I"  # incremental — credit note carries delta
            original = getattr(invoice, "_verifactu_original", None)
            if original is not None:
                facturas_rectificadas.append(
                    xml_builder.IDFacturaRef(
                        nif=nif_emisor,
                        num_serie=original.invoice_number or "",
                        fecha=(
                            f"{original.issue_date:%d-%m-%Y}" if original.issue_date else ""
                        ),
                    )
                )

        si = sistema_informatico.from_settings(settings)
        payload = xml_builder.RegistroAltaPayload(
            nif_emisor=nif_emisor,
            nombre_razon_emisor=nombre_razon_emisor,
            serie_numero=invoice.invoice_number or "",
            fecha_expedicion=fecha_expedicion,
            tipo_factura=tipo_factura,
            descripcion_operacion=(
                "Servicios odontológicos" if not is_credit_note else "Rectificativa"
            ),
            desglose=desglose,
            cuota_total=cuota_total,
            importe_total=importe_total_q,
            sistema_informatico=si,
            fecha_hora_huso_gen_registro=fecha_hora_huso,
            huella=huella,
            huella_anterior=huella_anterior,
            is_first_record=is_first,
            id_factura_anterior=id_factura_anterior,
            destinatario=destinatario,
            tipo_rectificativa=tipo_rectificativa,
            facturas_rectificadas=facturas_rectificadas,
        )

        registro_xml = xml_builder.render_registro_alta(payload)

        # Persist record (queued for AEAT submission by worker).
        record = VerifactuRecord(
            clinic_id=invoice.clinic_id,
            invoice_id=invoice.id,
            record_type="alta",
            tipo_factura=tipo_factura,
            tipo_rectificativa=tipo_rectificativa,
            serie_numero=invoice.invoice_number or "",
            fecha_expedicion=fecha_expedicion,
            cuota_total=cuota_total,
            importe_total=importe_total_q,
            huella=huella,
            huella_anterior=huella_anterior or None,
            is_first_record=is_first,
            fecha_hora_huso_gen_registro=fecha_hora_huso.astimezone(UTC),
            xml_payload=registro_xml,
            state="pending",
        )
        db.add(record)
        await db.flush()

        # Advance chain head BEFORE AEAT confirmation. Subsanación reuses
        # the same hash so the chain is stable even on rejection.
        settings.last_huella = huella
        settings.last_record_id = record.id

        qr_url = qr.build_qr_url(
            environment=settings.environment,
            nif=nif_emisor,
            num_serie=invoice.invoice_number or "",
            fecha_expedicion=fecha_expedicion,
            importe_total=importe_total_q,
        )

        return {
            "ES": {
                "record_id": str(record.id),
                "huella": huella,
                "qr_url": qr_url,
                "tipo_factura": tipo_factura,
                "state": "pending",
                "environment": settings.environment,
            }
        }
