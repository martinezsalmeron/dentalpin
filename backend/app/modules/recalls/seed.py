"""Demo seed for the recalls module.

Generates a realistic monthly call list across the seeded patients:
mix of statuses (pending / no answer / scheduled / done / needs
review / cancelled), reasons, priorities, and a sprinkle of contact
attempts so the receptionist UX has something to work through on a
fresh demo. Lazily seeds ``RecallSettings`` with the documented
defaults (already handled by the service, so we just call it once).

Idempotent for the given clinic: wipes the clinic's recalls +
attempts, then repopulates. ``recall.*`` events are NOT published
during seeding — listeners would re-seed off-cycle data.

Only invoked by ``backend/scripts/seed_demo.py`` after patients +
appointments exist (recalls reference both).
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.agenda.models import Appointment
from app.modules.patients.models import Patient

from .models import Recall, RecallContactAttempt
from .service import RecallSettingsService


def _normalize_due_month(d: date) -> date:
    return date(d.year, d.month, 1)


def _add_months(d: date, months: int) -> date:
    base = _normalize_due_month(d)
    total = base.year * 12 + (base.month - 1) + months
    year, month = divmod(total, 12)
    return date(year, month + 1, 1)


# Eight scenario templates, cycled across patients. Together they
# cover every status the call-list filters can show, plus enough
# reasons and priorities for the dashboard counters to be non-trivial.
_SCENARIOS = (
    {
        "key": "pending_due_this_month_hygiene",
        "month_offset": 0,
        "reason": "hygiene",
        "priority": "normal",
        "status": "pending",
        "attempts": 0,
        "note": "Recordatorio de higiene anual.",
    },
    {
        "key": "no_answer_overdue_checkup",
        "month_offset": -1,
        "reason": "checkup",
        "priority": "normal",
        "status": "contacted_no_answer",
        "attempts": 2,
        "note": "Revisión anual; no contesta al teléfono fijo.",
    },
    {
        "key": "scheduled_postop_high",
        "month_offset": 0,
        "reason": "post_op",
        "priority": "high",
        "status": "contacted_scheduled",
        "attempts": 1,
        "note": "Postoperatorio de cirugía 36; cita confirmada.",
    },
    {
        "key": "done_last_month_hygiene",
        "month_offset": -1,
        "reason": "hygiene",
        "priority": "normal",
        "status": "done",
        "attempts": 1,
        "note": "Higiene completada en visita previa.",
    },
    {
        "key": "pending_next_month_ortho",
        "month_offset": 1,
        "reason": "ortho_review",
        "priority": "normal",
        "status": "pending",
        "attempts": 0,
        "note": "Revisión mensual de ortodoncia.",
    },
    {
        "key": "needs_review_implant",
        "month_offset": -2,
        "reason": "implant_review",
        "priority": "high",
        "status": "needs_review",
        "attempts": 0,
        "note": "Revisión de implante 46; revisar contacto.",
    },
    {
        "key": "cancelled_treatment_followup",
        "month_offset": -1,
        "reason": "treatment_followup",
        "priority": "low",
        "status": "cancelled",
        "attempts": 1,
        "note": "Paciente declina seguimiento.",
    },
    {
        "key": "pending_three_months_implant",
        "month_offset": 3,
        "reason": "implant_review",
        "priority": "normal",
        "status": "pending",
        "attempts": 0,
        "note": "Control de implante a los 3 meses.",
    },
)


_ATTEMPT_NOTES = (
    "Llamada al móvil sin respuesta.",
    "Buzón de voz; mensaje dejado.",
    "Indica que llamemos la próxima semana.",
    "Acuerda agendar tras revisar agenda laboral.",
)


async def seed_recalls_demo(
    db: AsyncSession,
    clinic_id: UUID,
    dentist_id: UUID,
    hygienist_id: UUID,
    receptionist_id: UUID,
) -> dict[str, int]:
    """Populate the recalls module for the demo clinic.

    Returns ``{<status>: count}`` plus a top-level ``total`` for the
    summary line printed by ``seed_demo.py``.
    """
    # Wipe — attempts cascade via FK ondelete=CASCADE.
    await db.execute(delete(Recall).where(Recall.clinic_id == clinic_id))
    await db.flush()

    # Lazy-seed settings (idempotent — fetches the row or inserts the
    # documented defaults).
    await RecallSettingsService.get_or_create(db, clinic_id)

    patients_res = await db.execute(
        select(Patient).where(Patient.clinic_id == clinic_id).order_by(Patient.created_at)
    )
    patient_list = list(patients_res.scalars().all())

    # Map patient -> earliest scheduled appointment (used to give
    # ``contacted_scheduled`` recalls a real linked_appointment_id when
    # one exists; falls back to None otherwise).
    appt_res = await db.execute(
        select(Appointment)
        .where(Appointment.clinic_id == clinic_id)
        .order_by(Appointment.start_time)
    )
    appt_by_patient: dict[UUID, UUID] = {}
    for appt in appt_res.scalars().all():
        if appt.patient_id and appt.patient_id not in appt_by_patient:
            appt_by_patient[appt.patient_id] = appt.id

    today = date.today()
    now = datetime.now(UTC)

    stats: dict[str, int] = {
        "pending": 0,
        "contacted_no_answer": 0,
        "contacted_scheduled": 0,
        "done": 0,
        "cancelled": 0,
        "needs_review": 0,
        "attempts": 0,
        "total": 0,
    }

    for i, patient in enumerate(patient_list):
        scenario = _SCENARIOS[i % len(_SCENARIOS)]
        due_month = _add_months(today, scenario["month_offset"])
        created_at = now - timedelta(days=14 + (i % 21))

        completed_at = None
        if scenario["status"] == "done":
            completed_at = now - timedelta(days=5 + (i % 10))

        professional_id = (
            dentist_id
            if scenario["reason"]
            in (
                "post_op",
                "implant_review",
                "ortho_review",
                "treatment_followup",
            )
            else hygienist_id
        )

        recall = Recall(
            clinic_id=clinic_id,
            patient_id=patient.id,
            due_month=due_month,
            due_date=None,
            reason=scenario["reason"],
            reason_note=scenario["note"],
            priority=scenario["priority"],
            status=scenario["status"],
            recommended_by=dentist_id,
            assigned_professional_id=professional_id,
            contact_attempt_count=scenario["attempts"],
            last_contact_attempt_at=(
                now - timedelta(days=2 + (i % 5)) if scenario["attempts"] > 0 else None
            ),
            completed_at=completed_at,
            created_at=created_at,
            updated_at=created_at,
        )
        if scenario["status"] == "contacted_scheduled":
            recall.linked_appointment_id = appt_by_patient.get(patient.id)

        db.add(recall)
        await db.flush()  # need recall.id to attach attempts

        # Attempts: one per N declared by the scenario, channels +
        # outcomes mixed so the call-list shows variety.
        for k in range(scenario["attempts"]):
            channel = "phone" if k == 0 else ("whatsapp" if k == 1 else "sms")
            outcome = (
                "scheduled"
                if scenario["status"] == "contacted_scheduled" and k == scenario["attempts"] - 1
                else (
                    "declined"
                    if scenario["status"] == "cancelled"
                    else ("voicemail" if k == 1 else "no_answer")
                )
            )
            db.add(
                RecallContactAttempt(
                    recall_id=recall.id,
                    clinic_id=clinic_id,
                    attempted_by=receptionist_id,
                    channel=channel,
                    outcome=outcome,
                    attempted_at=now - timedelta(days=k + 1, hours=2 * k),
                    note=_ATTEMPT_NOTES[(i + k) % len(_ATTEMPT_NOTES)],
                )
            )
            stats["attempts"] += 1

        stats[scenario["status"]] += 1
        stats["total"] += 1

    await db.flush()
    return stats
