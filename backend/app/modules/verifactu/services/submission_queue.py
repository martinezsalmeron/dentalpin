"""Drain pending VerifactuRecord rows and submit them to AEAT.

Called from a periodic APScheduler job (see ``tasks.py``). Per clinic
with ``enabled=true``:

1. Acquire a Postgres advisory lock keyed by clinic id, so two workers
   don't double-submit and break the hash chain.
2. Honour ``settings.next_send_after`` (AEAT-imposed back-pressure).
3. Take up to ``MAX_BATCH`` records in ``state in ('pending',
   'failed_transient')`` ordered by ``created_at``.
4. Wrap them in a SOAP envelope, submit via :mod:`aeat_client`.
5. Map every ``RespuestaLinea`` back to the originating record using
   ``IDFactura`` + ``CSV`` and update state, codes, timestamps.
6. Update ``settings.next_send_after`` from ``TiempoEsperaEnvio``.
7. On transport failure: mark records ``failed_transient`` and bump
   ``submission_attempt`` for exponential backoff.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.models import Clinic
from app.modules.billing.models import Invoice

from ..models import VerifactuCertificate, VerifactuRecord, VerifactuSettings
from . import aeat_client, encryption, xml_builder

logger = logging.getLogger(__name__)

MAX_BATCH = 1000


async def _try_advisory_lock(db: AsyncSession, clinic_id) -> bool:
    """Acquire a session-scoped advisory lock keyed by clinic id."""

    result = await db.execute(
        text("SELECT pg_try_advisory_xact_lock(hashtextextended(:k, 0))"),
        {"k": f"verifactu:{clinic_id}"},
    )
    return bool(result.scalar())


async def _active_certificate(db: AsyncSession, clinic_id) -> VerifactuCertificate | None:
    result = await db.execute(
        select(VerifactuCertificate).where(
            VerifactuCertificate.clinic_id == clinic_id,
            VerifactuCertificate.is_active.is_(True),
        )
    )
    return result.scalar_one_or_none()


async def _select_pending(
    db: AsyncSession, clinic_id, limit: int
) -> list[VerifactuRecord]:
    result = await db.execute(
        select(VerifactuRecord)
        .where(
            VerifactuRecord.clinic_id == clinic_id,
            VerifactuRecord.state.in_(("pending", "failed_transient")),
        )
        .order_by(VerifactuRecord.created_at.asc())
        .limit(limit)
    )
    return list(result.scalars())


def _build_envelope(
    *,
    nif_emisor: str,
    nombre_razon_emisor: str,
    records: list[VerifactuRecord],
) -> str:
    return xml_builder.render_envelope(
        cabecera_obligado_nif=nif_emisor,
        cabecera_obligado_nombre=nombre_razon_emisor,
        registros_xml=[r.xml_payload for r in records if r.xml_payload],
    )


def _match_line(line: aeat_client.LineResponse, record: VerifactuRecord) -> bool:
    serie = line.id_factura.get("NumSerieFactura") or line.id_factura.get(
        "NumSerieFacturaAnulada"
    )
    if serie is None:
        return False
    return serie == record.serie_numero


async def process_clinic(db: AsyncSession, clinic_id) -> int:
    """Drain pending records for a single clinic. Returns number processed."""

    if not await _try_advisory_lock(db, clinic_id):
        logger.debug("verifactu: clinic %s busy, skip", clinic_id)
        return 0

    settings_q = await db.execute(
        select(VerifactuSettings).where(VerifactuSettings.clinic_id == clinic_id)
    )
    settings = settings_q.scalar_one_or_none()
    if settings is None or not settings.enabled:
        return 0
    now = datetime.now(UTC)
    if settings.next_send_after is not None and now < settings.next_send_after:
        return 0

    cert = await _active_certificate(db, clinic_id)
    if cert is None:
        logger.warning("verifactu: clinic %s has no active certificate", clinic_id)
        return 0

    clinic_q = await db.execute(
        select(Clinic.tax_id, Clinic.legal_name, Clinic.name).where(Clinic.id == clinic_id)
    )
    clinic_row = clinic_q.first()
    if clinic_row is None or not (clinic_row[0] or "").strip():
        logger.warning(
            "verifactu: clinic %s missing tax_id; cannot submit", clinic_id
        )
        return 0
    nif_emisor = clinic_row[0].strip().upper()
    nombre_razon_emisor = (clinic_row[1] or clinic_row[2] or "").strip()

    records = await _select_pending(db, clinic_id, MAX_BATCH)
    if not records:
        return 0

    for r in records:
        r.state = "sending"
        r.submission_attempt += 1
        r.last_attempt_at = now
    await db.flush()

    pfx_bytes = encryption.decrypt_bytes(cert.pfx_encrypted)
    pfx_password = encryption.decrypt_password(cert.password_encrypted)
    if pfx_bytes is None or pfx_password is None:
        logger.error("verifactu: clinic %s cert decryption failed", clinic_id)
        for r in records:
            r.state = "failed_transient"
        await db.flush()
        return 0

    envelope = _build_envelope(
        nif_emisor=nif_emisor,
        nombre_razon_emisor=nombre_razon_emisor,
        records=records,
    )

    try:
        response = await aeat_client.submit(
            environment=settings.environment,
            pfx_bytes=pfx_bytes,
            pfx_password=pfx_password,
            soap_envelope=envelope,
        )
    except aeat_client.AeatClientError as exc:
        logger.warning("verifactu: clinic %s transport error: %s", clinic_id, exc)
        # Surface the transport error to the user via the queue UI.
        # No AEAT response code is available here (the request never made
        # it past mTLS or returned non-2xx), so we only fill the
        # description and the raw response text when present. ``-1`` is
        # used as a sentinel marker so the UI can distinguish transport
        # failures from AEAT business rejections.
        message = str(exc)[:500]
        for r in records:
            r.state = "failed_transient"
            r.aeat_codigo_error = -1
            r.aeat_descripcion_error = message
        await db.flush()
        await db.commit()
        return 0
    finally:
        # Wipe in-memory secrets ASAP.
        del pfx_bytes
        del pfx_password

    settings.last_aeat_response_at = now
    if response.tiempo_espera_envio:
        settings.next_send_after = now + timedelta(seconds=response.tiempo_espera_envio)

    # Detect SOAP Fault responses (HTTP 200 + <env:Fault>). The
    # parse_response can't extract per-record lineas in that case, so
    # we lift the faultstring directly into ``aeat_descripcion_error``
    # for every record in the batch — otherwise the queue UI shows an
    # empty error and the user has no way to know what failed.
    fault_message: str | None = None
    if not response.lineas:
        try:
            from lxml import etree

            root = etree.fromstring(response.raw_xml.encode("utf-8"))
            fault_strings = root.xpath(
                ".//*[local-name()='faultstring']/text()"
            ) or root.xpath(".//*[local-name()='Reason']//text()")
            if fault_strings:
                fault_message = str(fault_strings[0]).strip()[:500]
        except Exception:  # noqa: BLE001 — best-effort surfacing
            fault_message = None

    # Match responses to records.
    for r in records:
        line = next((ln for ln in response.lineas if _match_line(ln, r)), None)
        r.aeat_estado_envio = response.estado_envio
        r.aeat_response_xml = response.raw_xml
        if line is None:
            r.state = "failed_transient"
            if fault_message:
                r.aeat_codigo_error = -2
                r.aeat_descripcion_error = fault_message
            continue
        r.aeat_estado_registro = line.estado_registro
        r.aeat_codigo_error = line.codigo_error
        r.aeat_descripcion_error = line.descripcion_error
        r.aeat_csv = line.csv or response.csv
        r.aeat_timestamp_presentacion = response.timestamp_presentacion

        if line.estado_registro == "Correcto":
            r.state = "accepted"
        elif line.estado_registro == "AceptadoConErrores":
            r.state = "accepted_with_errors"
        elif line.estado_registro == "Incorrecto":
            r.state = "rejected"
        else:
            r.state = "failed_transient"

        # Mirror final state into Invoice.compliance_data.
        if r.state in ("accepted", "accepted_with_errors"):
            inv_q = await db.execute(select(Invoice).where(Invoice.id == r.invoice_id))
            inv = inv_q.scalar_one_or_none()
            if inv is not None:
                cd = dict(inv.compliance_data or {})
                es = dict(cd.get("ES") or {})
                es.update(
                    {
                        "csv": r.aeat_csv,
                        "submitted_at": (
                            r.aeat_timestamp_presentacion.isoformat()
                            if r.aeat_timestamp_presentacion
                            else None
                        ),
                        "state": r.state,
                    }
                )
                cd["ES"] = es
                inv.compliance_data = cd

    await db.commit()
    return len(records)


async def process_all(session_factory) -> dict[str, int]:
    """Iterate clinics with ``enabled=True`` and process each."""

    async with session_factory() as db:
        clinics_q = await db.execute(
            select(VerifactuSettings.clinic_id).where(VerifactuSettings.enabled.is_(True))
        )
        clinic_ids = [row[0] for row in clinics_q.all()]

    counts: dict[str, int] = {}
    for cid in clinic_ids:
        async with session_factory() as db:
            try:
                counts[str(cid)] = await process_clinic(db, cid)
            except Exception as exc:  # noqa: BLE001
                logger.exception("verifactu: clinic %s process failed: %s", cid, exc)
                counts[str(cid)] = -1
    return counts
