"""AppointmentMapper free-text ``notes`` → ClinicalNote (appointment owner).

The legacy ``appointments.notes`` column was dropped (ag_0005). DPMF
appointment payloads that still carry a ``notes`` field now persist as
a polymorphic :class:`ClinicalNote` row with
``owner_type='appointment'`` and ``note_type='appointment_administrative'``.

Idempotency: a second execute on the same job must not duplicate the
note. Tracked under the synthetic ``appointment_note`` entity_type.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy import select

from app.core.auth.models import Clinic, ClinicMembership, User
from app.modules.clinical_notes.models import ClinicalNote
from app.modules.migration_import.mappers.appointment import AppointmentMapper
from app.modules.migration_import.mappers.base import MapperContext, MappingResolver
from app.modules.migration_import.models import ImportJob
from app.modules.patients.models import Patient


async def _bootstrap(db_session):
    clinic = Clinic(id=uuid4(), name="C", tax_id=uuid4().hex[:8])
    admin = User(
        id=uuid4(),
        email=f"admin-{uuid4().hex[:8]}@test.local",
        password_hash="x",
        first_name="A",
        last_name="A",
    )
    professional = User(
        id=uuid4(),
        email=f"prof-{uuid4().hex[:8]}@test.local",
        password_hash="x",
        first_name="P",
        last_name="P",
    )
    patient = Patient(
        id=uuid4(),
        clinic_id=clinic.id,
        first_name="Demo",
        last_name="Patient",
        status="active",
    )
    db_session.add_all([clinic, admin, professional, patient])
    await db_session.flush()
    db_session.add_all(
        [
            ClinicMembership(id=uuid4(), user_id=admin.id, clinic_id=clinic.id, role="admin"),
            ClinicMembership(
                id=uuid4(),
                user_id=professional.id,
                clinic_id=clinic.id,
                role="dentist",
            ),
        ]
    )
    await db_session.flush()
    return clinic, admin, professional, patient


async def _ctx(db_session, clinic_id, admin_id):
    job = ImportJob(
        clinic_id=clinic_id,
        created_by=admin_id,
        status="executing",
        original_filename="t.dpm",
        file_path="/tmp/t.dpm",
        file_size=0,
    )
    db_session.add(job)
    await db_session.flush()
    resolver = MappingResolver(db=db_session, clinic_id=clinic_id, job_id=job.id)
    return MapperContext(
        db=db_session,
        clinic_id=clinic_id,
        job_id=job.id,
        resolver=resolver,
        import_fiscal_compliance=False,
        created_by=admin_id,
    )


async def _apply(ctx, *, patient_id, professional_id, payload, canonical=None):
    canonical = canonical or str(uuid4())
    await ctx.resolver.set(
        entity_type="patient",
        canonical_uuid=str(patient_id),
        source_system="gesden",
        dentalpin_table="patients",
        dentalpin_id=patient_id,
    )
    await ctx.resolver.set(
        entity_type="professional",
        canonical_uuid=str(professional_id),
        source_system="gesden",
        dentalpin_table="users",
        dentalpin_id=professional_id,
    )
    payload.setdefault("patient_uuid", str(patient_id))
    payload.setdefault("professional_uuid", str(professional_id))
    payload.setdefault("scheduled_date", "2024-03-01")
    payload.setdefault("scheduled_time", "10:00:00")
    payload.setdefault("duration_minutes", 30)
    payload.setdefault("coarse_status", "scheduled")
    return await AppointmentMapper().apply(
        ctx,
        entity_type="appointment",
        payload=payload,
        raw={},
        canonical_uuid=canonical,
        source_id="1",
        source_system="gesden",
    ), canonical


@pytest.mark.asyncio
async def test_appointment_with_notes_creates_clinical_note(db_session) -> None:
    clinic, admin, prof, patient = await _bootstrap(db_session)
    ctx = await _ctx(db_session, clinic.id, admin.id)

    apt_id, _ = await _apply(
        ctx,
        patient_id=patient.id,
        professional_id=prof.id,
        payload={"notes": "Llamó para reconfirmar"},
    )
    await db_session.flush()

    notes = (
        (await db_session.execute(select(ClinicalNote).where(ClinicalNote.owner_id == apt_id)))
        .scalars()
        .all()
    )
    assert len(notes) == 1
    note = notes[0]
    assert note.note_type == "appointment_administrative"
    assert note.owner_type == "appointment"
    assert note.body == "Llamó para reconfirmar"
    # Author = resolved professional (resolver hit), not the admin fallback.
    assert note.author_id == prof.id


@pytest.mark.asyncio
async def test_appointment_without_notes_no_clinical_note(db_session) -> None:
    clinic, admin, prof, patient = await _bootstrap(db_session)
    ctx = await _ctx(db_session, clinic.id, admin.id)

    apt_id, canonical = await _apply(
        ctx,
        patient_id=patient.id,
        professional_id=prof.id,
        payload={"notes": "   "},  # whitespace only
    )
    await db_session.flush()

    notes = (
        (await db_session.execute(select(ClinicalNote).where(ClinicalNote.owner_id == apt_id)))
        .scalars()
        .all()
    )
    assert notes == []

    # Resolver marks the synthetic appointment_note canonical as skipped so
    # a re-run does not re-evaluate the same empty payload.
    assert await ctx.resolver.was_skipped("appointment_note", f"{canonical}:note") is True


@pytest.mark.asyncio
async def test_reimport_is_idempotent(db_session) -> None:
    clinic, admin, prof, patient = await _bootstrap(db_session)
    ctx = await _ctx(db_session, clinic.id, admin.id)

    _, canonical = await _apply(
        ctx,
        patient_id=patient.id,
        professional_id=prof.id,
        payload={"notes": "Aviso recogido por recepción"},
    )
    await db_session.flush()

    # Second apply with the same canonical_uuid short-circuits on the
    # appointment AND does not create a second clinical note.
    await _apply(
        ctx,
        patient_id=patient.id,
        professional_id=prof.id,
        payload={"notes": "Aviso recogido por recepción"},
        canonical=canonical,
    )
    await db_session.flush()

    notes = (
        (
            await db_session.execute(
                select(ClinicalNote).where(ClinicalNote.body == "Aviso recogido por recepción")
            )
        )
        .scalars()
        .all()
    )
    assert len(notes) == 1
