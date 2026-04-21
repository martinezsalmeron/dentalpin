"""Event handlers for the patient_timeline module.

Every handler follows the same contract:

- Signature ``async def on_*(data: dict) -> None`` — matches the event bus
  calling convention (``handler(data)``).
- Opens its own DB session via :func:`async_session_maker`.
- Commits on success, rolls back on failure.
- Never imports models from other modules. Everything it needs must come in
  the ``data`` dict. Keeps the timeline module removable in isolation — the
  whole point of the patient_timeline split in Fase B.3.
- Skips events without a ``patient_id`` (administrative/clinic-scoped events
  have nowhere to land in the ficha del paciente).
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from app.core.events import EventType
from app.database import async_session_maker

from .service import TimelineService

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_dt(value: Any) -> datetime:
    """Parse an ISO timestamp; fall back to now if missing/invalid."""
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            pass
    return datetime.now(UTC)


def _required_ids(data: dict, *keys: str) -> tuple[UUID, ...] | None:
    """Return tuple of UUIDs for the given keys, or None if any are missing/invalid."""
    try:
        return tuple(UUID(data[k]) for k in keys)
    except (KeyError, TypeError, ValueError):
        return None


async def _record(
    event_type: str,
    event_category: str,
    source_table: str,
    data: dict,
    *,
    source_id_key: str,
    title: str,
    description: str | None = None,
    event_data: dict | None = None,
    occurred_at_key: str = "occurred_at",
    created_by_key: str | None = None,
) -> None:
    """Generic helper: insert one timeline row and commit.

    Centralizes session management + error handling so each specific handler
    stays declarative.
    """
    ids = _required_ids(data, "clinic_id", "patient_id", source_id_key)
    if ids is None:
        # Not enough info to attach to a patient — silently skip. These events
        # are valid at the clinic level (e.g. admin emails without a patient)
        # and simply don't belong on any single ficha.
        return
    clinic_id, patient_id, source_id = ids

    created_by: UUID | None = None
    if created_by_key and data.get(created_by_key):
        try:
            created_by = UUID(data[created_by_key])
        except (TypeError, ValueError):
            created_by = None

    async with async_session_maker() as db:
        try:
            await TimelineService.add_entry(
                db=db,
                clinic_id=clinic_id,
                patient_id=patient_id,
                event_type=event_type,
                event_category=event_category,
                source_table=source_table,
                source_id=source_id,
                title=title,
                description=description,
                event_data=event_data,
                occurred_at=_parse_dt(data.get(occurred_at_key)),
                created_by=created_by,
            )
            await db.commit()
        except Exception:
            await db.rollback()
            logger.exception("patient_timeline: failed to record %s", event_type)


# ---------------------------------------------------------------------------
# Visits
# ---------------------------------------------------------------------------


async def on_appointment_scheduled(data: dict) -> None:
    treatment = data.get("treatment_type") or "Consulta"
    await _record(
        event_type=EventType.APPOINTMENT_SCHEDULED,
        event_category="visit",
        source_table="appointments",
        data=data,
        source_id_key="appointment_id",
        title=f"Cita programada: {treatment}",
        event_data={
            "cabinet": data.get("cabinet"),
            "professional_id": data.get("professional_id"),
            "start_time": data.get("start_time"),
        },
        occurred_at_key="start_time",
    )


async def on_appointment_completed(data: dict) -> None:
    treatment = data.get("treatment_type") or "Consulta"
    await _record(
        event_type=EventType.APPOINTMENT_COMPLETED,
        event_category="visit",
        source_table="appointments",
        data=data,
        source_id_key="appointment_id",
        title=f"Cita completada: {treatment}",
        description=data.get("notes"),
        event_data={
            "cabinet": data.get("cabinet"),
            "professional_id": data.get("professional_id"),
        },
        occurred_at_key="end_time",
    )


async def on_appointment_cancelled(data: dict) -> None:
    treatment = data.get("treatment_type") or "Consulta"
    await _record(
        event_type=EventType.APPOINTMENT_CANCELLED,
        event_category="visit",
        source_table="appointments",
        data=data,
        source_id_key="appointment_id",
        title=f"Cita cancelada: {treatment}",
        event_data={"professional_id": data.get("professional_id")},
    )


async def on_appointment_no_show(data: dict) -> None:
    treatment = data.get("treatment_type") or "Consulta"
    await _record(
        event_type=EventType.APPOINTMENT_NO_SHOW,
        event_category="visit",
        source_table="appointments",
        data=data,
        source_id_key="appointment_id",
        title=f"Paciente no asistió: {treatment}",
        event_data={
            "cabinet": data.get("cabinet"),
            "professional_id": data.get("professional_id"),
        },
        occurred_at_key="start_time",
    )


# ---------------------------------------------------------------------------
# Treatments
# ---------------------------------------------------------------------------


async def on_tooth_treatment_performed(data: dict) -> None:
    name = data.get("treatment_name") or data.get("clinical_type") or "tratamiento"
    teeth = data.get("tooth_numbers") or []
    teeth_label = ", ".join(str(t) for t in teeth) if teeth else None
    await _record(
        event_type=EventType.ODONTOGRAM_TREATMENT_PERFORMED,
        event_category="treatment",
        source_table="treatments",
        data=data,
        source_id_key="treatment_id",
        title=f"Tratamiento realizado: {name}",
        description=f"Dientes: {teeth_label}" if teeth_label else None,
        event_data={
            "clinical_type": data.get("clinical_type"),
            "tooth_numbers": teeth,
        },
        occurred_at_key="performed_at",
        created_by_key="performed_by",
    )


async def on_plan_created(data: dict) -> None:
    plan_name = data.get("plan_name") or f"Plan {data.get('plan_number', '')}".strip()
    await _record(
        event_type=EventType.TREATMENT_PLAN_CREATED,
        event_category="treatment",
        source_table="treatment_plans",
        data=data,
        source_id_key="plan_id",
        title=f"Plan de tratamiento creado: {plan_name}"
        if plan_name
        else "Plan de tratamiento creado",
        event_data={"plan_number": data.get("plan_number")},
        created_by_key="created_by",
    )


async def on_plan_item_completed(data: dict) -> None:
    item_name = data.get("item_name")
    title = (
        f"Tratamiento del plan completado: {item_name}"
        if item_name
        else "Tratamiento del plan completado"
    )
    await _record(
        event_type=EventType.TREATMENT_PLAN_TREATMENT_COMPLETED,
        event_category="treatment",
        source_table="planned_treatment_items",
        data=data,
        source_id_key="item_id",
        title=title,
        event_data={"plan_id": data.get("plan_id")},
        created_by_key="completed_by",
    )


# ---------------------------------------------------------------------------
# Financial
# ---------------------------------------------------------------------------


async def on_budget_sent(data: dict) -> None:
    number = data.get("budget_number")
    await _record(
        event_type=EventType.BUDGET_SENT,
        event_category="financial",
        source_table="budgets",
        data=data,
        source_id_key="budget_id",
        title=f"Presupuesto enviado: {number}" if number else "Presupuesto enviado",
        event_data={
            "budget_number": number,
            "total": data.get("total"),
            "send_method": data.get("send_method"),
        },
    )


async def on_budget_accepted(data: dict) -> None:
    number = data.get("budget_number")
    await _record(
        event_type=EventType.BUDGET_ACCEPTED,
        event_category="financial",
        source_table="budgets",
        data=data,
        source_id_key="budget_id",
        title=f"Presupuesto aceptado: {number}" if number else "Presupuesto aceptado",
        event_data={"budget_number": number, "total": data.get("total")},
    )


async def on_invoice_issued(data: dict) -> None:
    number = data.get("invoice_number")
    await _record(
        event_type=EventType.INVOICE_ISSUED,
        event_category="financial",
        source_table="invoices",
        data=data,
        source_id_key="invoice_id",
        title=f"Factura emitida: {number}" if number else "Factura emitida",
        event_data={"invoice_number": number, "total": data.get("total")},
    )


async def on_invoice_paid(data: dict) -> None:
    number = data.get("invoice_number")
    await _record(
        event_type=EventType.INVOICE_PAID,
        event_category="financial",
        source_table="invoices",
        data=data,
        source_id_key="invoice_id",
        title=f"Factura pagada: {number}" if number else "Factura pagada",
        event_data={"invoice_number": number, "total": data.get("total")},
    )


# ---------------------------------------------------------------------------
# Communications
# ---------------------------------------------------------------------------


async def on_email_sent(data: dict) -> None:
    subject = data.get("subject") or data.get("template_key") or "email"
    await _record(
        event_type=EventType.EMAIL_SENT,
        event_category="communication",
        source_table="email_logs",
        data=data,
        source_id_key="email_log_id",
        title=f"Email enviado: {subject}",
        description=data.get("recipient_email"),
        event_data={
            "template_key": data.get("template_key"),
            "recipient_email": data.get("recipient_email"),
        },
    )


async def on_email_failed(data: dict) -> None:
    subject = data.get("subject") or data.get("template_key") or "email"
    await _record(
        event_type=EventType.EMAIL_FAILED,
        event_category="communication",
        source_table="email_logs",
        data=data,
        source_id_key="email_log_id",
        title=f"Email fallido: {subject}",
        description=data.get("error_message") or data.get("recipient_email"),
        event_data={
            "template_key": data.get("template_key"),
            "recipient_email": data.get("recipient_email"),
            "error_message": data.get("error_message"),
        },
    )


# ---------------------------------------------------------------------------
# Medical history
# ---------------------------------------------------------------------------


async def on_medical_updated(data: dict) -> None:
    # patient_timeline uses patient_id as the source_id for medical updates —
    # there is no per-update row to point to. Inject it so the generic helper
    # passes the required-ids check.
    data = {**data, "source_id": data.get("patient_id")}
    section = data.get("section")
    # The event_category badge already shows "Historial médico" and the
    # description carries the human summary — keep the title short and
    # avoid leaking internal section slugs like "history" / "context".
    title = data.get("summary") or "Historia clínica actualizada"
    await _record(
        event_type=EventType.PATIENT_MEDICAL_UPDATED,
        event_category="medical",
        source_table="patients",
        data=data,
        source_id_key="source_id",
        title=title,
        event_data={"section": section},
        created_by_key="user_id",
    )


# ---------------------------------------------------------------------------
# Documents
# ---------------------------------------------------------------------------


async def on_document_uploaded(data: dict) -> None:
    title = data.get("title") or "Documento"
    await _record(
        event_type=EventType.DOCUMENT_UPLOADED,
        event_category="document",
        source_table="documents",
        data=data,
        source_id_key="document_id",
        title=f"Documento: {title}",
        event_data={"document_type": data.get("document_type")},
    )
