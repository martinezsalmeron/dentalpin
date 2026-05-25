"""AppliedTreatmentMapper non-clinical path → ClinicalNote.

Gesdén ``TtosMed`` rows that fail the catalog gate (``IdTto`` null or
``IdTipoOdg`` flagged non-clinical) used to materialise as
``Treatment(scope='global_mouth', clinical_type='migrated')`` +
``PlannedTreatmentItem``. Those rows polluted the BOCA COMPLETA strip
and the per-year catch-all plan view with chips like "Pago a cuenta de
Tratamientos" that aren't really treatments. The mapper now persists
them as ``ClinicalNote(note_type='administrative', owner=patient)``,
and the ``DebtMapper`` skips the earned-ledger entry when a debt
points at one of these.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy import select

from app.core.auth.models import Clinic, User
from app.modules.clinical_notes.models import ClinicalNote
from app.modules.migration_import.mappers.applied_treatment import AppliedTreatmentMapper
from app.modules.migration_import.mappers.base import MapperContext, MappingResolver
from app.modules.migration_import.models import ImportJob, ImportWarning
from app.modules.odontogram.models import Treatment
from app.modules.patients.models import Patient
from app.modules.treatment_plan.models import PlannedTreatmentItem


async def _bootstrap(db_session):
    clinic = Clinic(id=uuid4(), name="C", tax_id=uuid4().hex[:8])
    admin = User(
        id=uuid4(),
        email=f"admin-{uuid4().hex[:8]}@test.local",
        password_hash="x",
        first_name="A",
        last_name="A",
    )
    patient = Patient(
        id=uuid4(),
        clinic_id=clinic.id,
        first_name="Demo",
        last_name="Patient",
        status="active",
    )
    db_session.add_all([clinic, admin, patient])
    await db_session.flush()
    return clinic, admin, patient


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

    class _StubHandle:
        def entity_iter(self, entity_type):
            yield from ()

    ctx = MapperContext(
        db=db_session,
        clinic_id=clinic_id,
        job_id=job.id,
        resolver=resolver,
        import_fiscal_compliance=False,
        created_by=admin_id,
    )
    ctx.handle = _StubHandle()
    return ctx


async def _apply(ctx, *, patient_id, raw, payload, source_id="1", canonical=None):
    canonical = canonical or str(uuid4())
    # Pre-resolve the patient so the mapper finds it.
    await ctx.resolver.set(
        entity_type="patient",
        canonical_uuid=str(patient_id),
        source_system="gesden",
        dentalpin_table="patients",
        dentalpin_id=patient_id,
    )
    payload.setdefault("patient_uuid", str(patient_id))
    await AppliedTreatmentMapper().apply(
        ctx,
        entity_type="applied_treatment",
        payload=payload,
        raw=raw,
        canonical_uuid=canonical,
        source_id=source_id,
        source_system="gesden",
    )
    return canonical


@pytest.mark.asyncio
async def test_no_catalog_variant_lands_as_clinical_note(db_session) -> None:
    clinic, admin, patient = await _bootstrap(db_session)
    ctx = await _ctx(db_session, clinic.id, admin.id)

    canonical = await _apply(
        ctx,
        patient_id=patient.id,
        raw={"IdTipoOdg": None},
        payload={
            "status_code": 5,
            "start_date": "2024-03-01",
            "end_date": "2024-03-01",
            "notes": "Pago a cuenta de Tratamientos",
            "treatment_variant_uuid": None,
        },
    )
    await db_session.flush()

    notes = (
        (
            await db_session.execute(
                select(ClinicalNote).where(
                    ClinicalNote.owner_type == "patient", ClinicalNote.owner_id == patient.id
                )
            )
        )
        .scalars()
        .all()
    )
    assert len(notes) == 1
    note = notes[0]
    assert note.note_type == "administrative"
    assert note.body == "Pago a cuenta de Tratamientos"
    assert note.author_id == admin.id

    treatments = (
        (await db_session.execute(select(Treatment).where(Treatment.patient_id == patient.id)))
        .scalars()
        .all()
    )
    assert treatments == []
    plan_items = (
        (
            await db_session.execute(
                select(PlannedTreatmentItem).where(PlannedTreatmentItem.clinic_id == clinic.id)
            )
        )
        .scalars()
        .all()
    )
    assert plan_items == []

    # Resolver registers the canonical as a clinical_notes target so
    # DebtMapper can detect "no clinical target" downstream.
    table = await ctx.resolver.mapping_table("applied_treatment", canonical)
    assert table == "clinical_notes"


@pytest.mark.asyncio
async def test_non_clinical_tipo_odg_lands_as_clinical_note(db_session) -> None:
    clinic, admin, patient = await _bootstrap(db_session)
    ctx = await _ctx(db_session, clinic.id, admin.id)

    await _apply(
        ctx,
        patient_id=patient.id,
        raw={"IdTipoOdg": 11},  # Anotación
        payload={
            "status_code": 5,
            "start_date": "2024-03-01",
            "end_date": "2024-03-01",
            "notes": "Comentario clínico libre del receptionista",
            # Even with a variant resolved, IdTipoOdg=11 (Anotación)
            # is enforced as non-clinical and routes to a note.
            "treatment_variant_uuid": str(uuid4()),
        },
    )
    await db_session.flush()

    notes = (
        (await db_session.execute(select(ClinicalNote).where(ClinicalNote.owner_id == patient.id)))
        .scalars()
        .all()
    )
    assert len(notes) == 1
    assert notes[0].body == "Comentario clínico libre del receptionista"


@pytest.mark.asyncio
async def test_empty_notes_marks_skipped_no_writes(db_session) -> None:
    clinic, admin, patient = await _bootstrap(db_session)
    ctx = await _ctx(db_session, clinic.id, admin.id)

    canonical = await _apply(
        ctx,
        patient_id=patient.id,
        raw={"IdTipoOdg": 12},  # Nota Económica
        payload={
            "status_code": 5,
            "start_date": "2024-03-01",
            "end_date": "2024-03-01",
            "notes": "   ",  # whitespace only
            "treatment_variant_uuid": None,
        },
    )
    await db_session.flush()

    notes = (
        (await db_session.execute(select(ClinicalNote).where(ClinicalNote.owner_id == patient.id)))
        .scalars()
        .all()
    )
    assert notes == []
    assert await ctx.resolver.was_skipped("applied_treatment", canonical)


@pytest.mark.asyncio
async def test_reimport_is_idempotent(db_session) -> None:
    clinic, admin, patient = await _bootstrap(db_session)
    ctx = await _ctx(db_session, clinic.id, admin.id)

    payload = {
        "status_code": 5,
        "start_date": "2024-03-01",
        "end_date": "2024-03-01",
        "notes": "Pago a cuenta de Tratamientos",
        "treatment_variant_uuid": None,
    }
    canonical = await _apply(ctx, patient_id=patient.id, raw={}, payload=payload)
    await db_session.flush()

    # Re-apply same canonical → short-circuit, no duplicate note.
    await AppliedTreatmentMapper().apply(
        ctx,
        entity_type="applied_treatment",
        payload={**payload, "patient_uuid": str(patient.id)},
        raw={},
        canonical_uuid=canonical,
        source_id="1",
        source_system="gesden",
    )
    await db_session.flush()

    notes = (
        (await db_session.execute(select(ClinicalNote).where(ClinicalNote.owner_id == patient.id)))
        .scalars()
        .all()
    )
    assert len(notes) == 1


@pytest.mark.asyncio
async def test_warning_emitted_for_non_clinical_entry(db_session) -> None:
    clinic, admin, patient = await _bootstrap(db_session)
    ctx = await _ctx(db_session, clinic.id, admin.id)

    await _apply(
        ctx,
        patient_id=patient.id,
        raw={},
        payload={
            "status_code": 5,
            "start_date": "2024-03-01",
            "end_date": "2024-03-01",
            "notes": "Pago a cuenta de Tratamientos",
            "treatment_variant_uuid": None,
        },
    )
    await db_session.flush()

    warnings = (
        (await db_session.execute(select(ImportWarning).where(ImportWarning.job_id == ctx.job_id)))
        .scalars()
        .all()
    )
    codes = {w.code for w in warnings}
    assert "applied_treatment.non_clinical_entry" in codes


@pytest.mark.asyncio
async def test_professional_uuid_becomes_note_author(db_session) -> None:
    clinic, admin, patient = await _bootstrap(db_session)
    ctx = await _ctx(db_session, clinic.id, admin.id)

    dentist = User(
        id=uuid4(),
        email=f"dentist-{uuid4().hex[:8]}@test.local",
        password_hash="x",
        first_name="Dentist",
        last_name="One",
    )
    db_session.add(dentist)
    await db_session.flush()
    prof_canonical = str(uuid4())
    await ctx.resolver.set(
        entity_type="professional",
        canonical_uuid=prof_canonical,
        source_system="gesden",
        dentalpin_table="users",
        dentalpin_id=dentist.id,
    )

    await _apply(
        ctx,
        patient_id=patient.id,
        raw={},
        payload={
            "status_code": 5,
            "start_date": "2024-03-01",
            "end_date": "2024-03-01",
            "notes": "Observación clínica",
            "treatment_variant_uuid": None,
            "professional_uuid": prof_canonical,
        },
    )
    await db_session.flush()

    note = (
        await db_session.execute(select(ClinicalNote).where(ClinicalNote.owner_id == patient.id))
    ).scalar_one()
    assert note.author_id == dentist.id
