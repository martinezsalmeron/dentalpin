"""Demo seed for clinical notes.

Derives notes from already-seeded patients, treatment plans and
treatments. Inserts ``ClinicalNote`` rows directly without firing
``clinical_notes.*_created`` events so re-seed remains idempotent —
``patient_timeline`` re-derives its own rows from the source data and
firing events here would have it double-record entries that its seed
later wipes.

Only invoked by ``backend/scripts/seed_demo.py`` after treatment plans
exist (notes need their owners). Idempotent for the given clinic:
wipes the clinic's clinical_notes rows, then repopulates.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.odontogram.models import Treatment, TreatmentTooth
from app.modules.patients.models import Patient
from app.modules.treatment_plan.models import TreatmentPlan

from .models import (
    NOTE_OWNER_PATIENT,
    NOTE_OWNER_PLAN,
    NOTE_OWNER_TREATMENT,
    NOTE_TYPE_ADMINISTRATIVE,
    NOTE_TYPE_DIAGNOSIS,
    NOTE_TYPE_TREATMENT,
    NOTE_TYPE_TREATMENT_PLAN,
    ClinicalNote,
)

# UI strings stay in Spanish per project convention (CLAUDE.md).
_ADMIN_BODIES = (
    "Prefiere citas por la tarde. Avisar 24h antes para confirmar.",
    "Llamar siempre al móvil; no responde al fijo.",
    "Pago habitual con tarjeta. Solicita factura simplificada.",
    "Acude acompañado/a de un familiar; documentar consentimiento.",
    "Idioma preferido para comunicaciones: español.",
    "Solicita recordatorio por WhatsApp el día anterior.",
    "Tiene movilidad reducida; reservar cabinete accesible.",
)

_DIAGNOSIS_BODIES = (
    "Caries oclusal incipiente; valorar empaste en próxima visita.",
    "Movilidad grado I y sospecha de absceso periapical. Solicitar radiografía periapical.",
    "Sensibilidad al frío en el cuadrante; descartar recesión gingival.",
    "Bruxismo evidente con desgaste oclusal generalizado. Considerar férula de descarga.",
    "Encía inflamada con sangrado al sondaje. Refuerzo de higiene oral.",
    "Restauración antigua filtrada; recomendar sustitución.",
    "Tercer molar incluido sin sintomatología actual; mantener en observación.",
)

_TREATMENT_BODIES = (
    "Se aplica anestesia local (articaína 4% con epinefrina 1:100.000) sin incidencias.",
    "Apertura cameral e irrigación con hipoclorito sódico al 5,25%. Localizados 3 conductos.",
    "Adaptación marginal correcta tras pulido. Paciente refiere ausencia de molestias.",
    "Se coloca dique de goma para aislamiento absoluto. Buena cooperación del paciente.",
    "Se recomienda cita de control en dos semanas para revisar oclusión.",
    "Procedimiento sin complicaciones. Indicaciones postoperatorias entregadas.",
    "Cementado definitivo con cemento de ionómero de vidrio. Ajuste oclusal verificado.",
)

_PLAN_BODIES = (
    "Plan acordado con el paciente. Priorizar tratamientos urgentes en cuadrante superior derecho.",
    "Paciente solicita financiación; gestionar opción a 6 meses sin intereses.",
    "Se acuerda iniciar fase higiénica antes de los tratamientos restauradores.",
    "Pendiente de presentación al cónyuge; confirmará aceptación tras consulta familiar.",
    "Se aplica descuento del 10% por tratamiento integral.",
    "Paciente prefiere posponer la fase estética hasta después del verano.",
)


async def seed_clinical_notes_demo(
    db: AsyncSession,
    clinic_id: UUID,
    dentist_id: UUID,
    hygienist_id: UUID,
) -> dict[str, int]:
    """Populate clinical_notes for the demo clinic.

    Returns ``{"administrative": n, "diagnosis": n, "treatment": n,
    "treatment_plan": n}`` for the seed-demo summary line.
    """
    await db.execute(delete(ClinicalNote).where(ClinicalNote.clinic_id == clinic_id))

    stats = {"administrative": 0, "diagnosis": 0, "treatment": 0, "treatment_plan": 0}
    now = datetime.now(UTC)
    cursor = 0

    def author(idx: int) -> UUID:
        return dentist_id if idx % 2 == 0 else hygienist_id

    # --- Per-patient: administrative + diagnosis -------------------------
    patients_res = await db.execute(
        select(Patient).where(Patient.clinic_id == clinic_id).order_by(Patient.created_at)
    )
    patient_list = list(patients_res.scalars().all())

    # First tooth per patient from seeded TreatmentTooth — gives diagnosis
    # notes a realistic tooth pin where the odontogram already has data.
    tt_rows = await db.execute(
        select(TreatmentTooth.tooth_number, Treatment.patient_id)
        .join(Treatment, TreatmentTooth.treatment_id == Treatment.id)
        .where(Treatment.clinic_id == clinic_id)
    )
    tooth_by_patient: dict[UUID, int] = {}
    for tooth_number, patient_id in tt_rows.all():
        tooth_by_patient.setdefault(patient_id, tooth_number)

    for i, patient in enumerate(patient_list):
        admin_at = now - timedelta(days=80 + (i % 14))
        db.add(
            ClinicalNote(
                clinic_id=clinic_id,
                note_type=NOTE_TYPE_ADMINISTRATIVE,
                owner_type=NOTE_OWNER_PATIENT,
                owner_id=patient.id,
                tooth_number=None,
                body=_ADMIN_BODIES[cursor % len(_ADMIN_BODIES)],
                author_id=author(cursor),
                created_at=admin_at,
                updated_at=admin_at,
            )
        )
        cursor += 1
        stats["administrative"] += 1

        diag_at = now - timedelta(days=55 + (i % 14))
        db.add(
            ClinicalNote(
                clinic_id=clinic_id,
                note_type=NOTE_TYPE_DIAGNOSIS,
                owner_type=NOTE_OWNER_PATIENT,
                owner_id=patient.id,
                tooth_number=tooth_by_patient.get(patient.id),
                body=_DIAGNOSIS_BODIES[cursor % len(_DIAGNOSIS_BODIES)],
                author_id=author(cursor),
                created_at=diag_at,
                updated_at=diag_at,
            )
        )
        cursor += 1
        stats["diagnosis"] += 1

    # --- Per-plan: treatment_plan note (~2 of every 3 plans) -------------
    plans_res = await db.execute(
        select(TreatmentPlan)
        .where(TreatmentPlan.clinic_id == clinic_id)
        .order_by(TreatmentPlan.created_at)
    )
    for i, plan in enumerate(plans_res.scalars().all()):
        if i % 3 == 0:
            continue
        plan_at = now - timedelta(days=30 + (i % 14))
        db.add(
            ClinicalNote(
                clinic_id=clinic_id,
                note_type=NOTE_TYPE_TREATMENT_PLAN,
                owner_type=NOTE_OWNER_PLAN,
                owner_id=plan.id,
                tooth_number=None,
                body=_PLAN_BODIES[cursor % len(_PLAN_BODIES)],
                author_id=author(cursor),
                created_at=plan_at,
                updated_at=plan_at,
            )
        )
        cursor += 1
        stats["treatment_plan"] += 1

    # --- Per-performed-treatment: treatment note (every other one) -------
    performed_res = await db.execute(
        select(Treatment).where(
            Treatment.clinic_id == clinic_id,
            Treatment.status == "performed",
        )
    )
    for i, t in enumerate(performed_res.scalars().all()):
        if i % 2 == 1:
            continue
        tx_at = now - timedelta(days=10 + (i % 18))
        db.add(
            ClinicalNote(
                clinic_id=clinic_id,
                note_type=NOTE_TYPE_TREATMENT,
                owner_type=NOTE_OWNER_TREATMENT,
                owner_id=t.id,
                tooth_number=None,
                body=_TREATMENT_BODIES[cursor % len(_TREATMENT_BODIES)],
                author_id=author(cursor),
                created_at=tx_at,
                updated_at=tx_at,
            )
        )
        cursor += 1
        stats["treatment"] += 1

    await db.flush()
    return stats
