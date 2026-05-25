"""ProfessionalMapper — role and is_active wiring.

Guards against the canonical "doctor" role silently falling through to
"assistant" (it must map to DentalPin's "dentist") and against
imported professionals landing inactive in the Users page.
"""

from __future__ import annotations

from datetime import date
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.core.auth.models import Clinic, ClinicMembership, User
from app.modules.migration_import.mappers.base import (
    MapperContext,
    MappingResolver,
    ProfessionalFilterOptions,
)
from app.modules.migration_import.mappers.professional import ProfessionalMapper
from app.modules.migration_import.models import ImportJob, ImportWarning


@pytest.mark.asyncio
async def test_doctor_role_maps_to_dentist(db_session) -> None:
    clinic, admin = await _bootstrap(db_session)
    ctx = await _ctx(db_session, clinic.id, admin.id)
    mapper = ProfessionalMapper()
    canonical = str(uuid4())

    await mapper.apply(
        ctx,
        entity_type="professional",
        payload={
            "email": "doc@example.com",
            "given_name": "Ana",
            "family_name": "García",
            "role": "doctor",
        },
        raw={},
        canonical_uuid=canonical,
        source_id="1",
        source_system="gesden",
    )
    await db_session.flush()

    membership = (
        await db_session.execute(
            select(ClinicMembership).where(ClinicMembership.clinic_id == clinic.id)
        )
    ).scalar_one()
    assert membership.role == "dentist"
    user = (
        await db_session.execute(select(User).where(User.id == membership.user_id))
    ).scalar_one()
    assert user.is_active is True


@pytest.mark.asyncio
async def test_unknown_role_falls_back_to_assistant(db_session) -> None:
    clinic, admin = await _bootstrap(db_session)
    ctx = await _ctx(db_session, clinic.id, admin.id)
    canonical = str(uuid4())

    await ProfessionalMapper().apply(
        ctx,
        entity_type="professional",
        payload={"email": "x@example.com", "role": "other"},
        raw={},
        canonical_uuid=canonical,
        source_id="2",
        source_system="gesden",
    )
    await db_session.flush()

    membership = (
        await db_session.execute(
            select(ClinicMembership).where(ClinicMembership.clinic_id == clinic.id)
        )
    ).scalar_one()
    assert membership.role == "assistant"


@pytest.mark.asyncio
async def test_deactivated_payload_imports_as_inactive(db_session) -> None:
    clinic, admin = await _bootstrap(db_session)
    ctx = await _ctx(db_session, clinic.id, admin.id)
    canonical = str(uuid4())

    await ProfessionalMapper().apply(
        ctx,
        entity_type="professional",
        payload={
            "email": "left@example.com",
            "role": "doctor",
            "deactivated": True,
        },
        raw={},
        canonical_uuid=canonical,
        source_id="3",
        source_system="gesden",
    )
    await db_session.flush()

    user = (
        await db_session.execute(select(User).where(User.email == "left@example.com"))
    ).scalar_one()
    assert user.is_active is False


async def _bootstrap(db_session):
    clinic = Clinic(id=uuid4(), name="C", tax_id="B1")
    admin = User(
        id=uuid4(),
        email=f"admin-{uuid4().hex[:8]}@test.local",
        password_hash="x",
        first_name="A",
        last_name="A",
    )
    db_session.add_all([clinic, admin])
    await db_session.flush()
    return clinic, admin


async def _ctx(
    db_session,
    clinic_id,
    admin_id,
    *,
    filters: ProfessionalFilterOptions | None = None,
):
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
    return MapperContext(
        db=db_session,
        clinic_id=clinic_id,
        job_id=job.id,
        resolver=MappingResolver(db=db_session, clinic_id=clinic_id, job_id=job.id),
        import_fiscal_compliance=False,
        created_by=admin_id,
        professional_filters=filters,
    )


@pytest.mark.asyncio
async def test_filter_orphan_without_activity_is_demoted(db_session) -> None:
    clinic, admin = await _bootstrap(db_session)
    ctx = await _ctx(db_session, clinic.id, admin.id, filters=ProfessionalFilterOptions())

    await ProfessionalMapper().apply(
        ctx,
        entity_type="professional",
        payload={
            "email": "orphan@example.com",
            "given_name": None,
            "family_name": "PLACEHOLDER",
            "role": "other",
            "last_activity_at": None,
        },
        raw={},
        canonical_uuid=str(uuid4()),
        source_id="usuagd:18",
        source_system="gesden",
    )
    await db_session.flush()

    user = (
        await db_session.execute(select(User).where(User.email == "orphan@example.com"))
    ).scalar_one()
    assert user.is_active is False
    membership = (
        await db_session.execute(
            select(ClinicMembership).where(ClinicMembership.user_id == user.id)
        )
    ).scalar_one()
    assert membership.role == "assistant"


@pytest.mark.asyncio
async def test_filter_orphan_with_recent_activity_stays_active(db_session) -> None:
    # Real workers often own an agenda column without a TColabos link;
    # recent appointment traffic on that column overrides the orphan
    # filter so they stay agenda-visible.
    clinic, admin = await _bootstrap(db_session)
    ctx = await _ctx(db_session, clinic.id, admin.id, filters=ProfessionalFilterOptions())

    await ProfessionalMapper().apply(
        ctx,
        entity_type="professional",
        payload={
            "email": "orphan-working@example.com",
            "given_name": None,
            "family_name": "DRA. SAMPLE",
            "role": "other",
            "last_activity_at": date.today().isoformat(),
        },
        raw={},
        canonical_uuid=str(uuid4()),
        source_id="usuagd:18",
        source_system="gesden",
    )
    await db_session.flush()

    user = (
        await db_session.execute(select(User).where(User.email == "orphan-working@example.com"))
    ).scalar_one()
    assert user.is_active is True
    membership = (
        await db_session.execute(
            select(ClinicMembership).where(ClinicMembership.user_id == user.id)
        )
    ).scalar_one()
    # role=other falls back to assistant per _ROLE_MAP — that's expected
    # for TUsuAgd orphans which never carry IdTipoColab.
    assert membership.role == "assistant"


@pytest.mark.asyncio
async def test_filter_stale_activity_demotes(db_session) -> None:
    clinic, admin = await _bootstrap(db_session)
    ctx = await _ctx(
        db_session,
        clinic.id,
        admin.id,
        filters=ProfessionalFilterOptions(min_activity_months=12),
    )
    stale = date(date.today().year - 5, 1, 1).isoformat()

    await ProfessionalMapper().apply(
        ctx,
        entity_type="professional",
        payload={
            "email": "stale@example.com",
            "role": "doctor",
            "last_activity_at": stale,
        },
        raw={},
        canonical_uuid=str(uuid4()),
        source_id="42",
        source_system="gesden",
    )
    await db_session.flush()

    user = (
        await db_session.execute(select(User).where(User.email == "stale@example.com"))
    ).scalar_one()
    assert user.is_active is False
    membership = (
        await db_session.execute(
            select(ClinicMembership).where(ClinicMembership.user_id == user.id)
        )
    ).scalar_one()
    assert membership.role == "assistant"

    warning = (
        await db_session.execute(select(ImportWarning).where(ImportWarning.job_id == ctx.job_id))
    ).scalar_one()
    assert warning.code == "professional.filtered.no_recent_activity"


@pytest.mark.asyncio
async def test_filter_keeps_recent_active_doctor(db_session) -> None:
    clinic, admin = await _bootstrap(db_session)
    ctx = await _ctx(
        db_session,
        clinic.id,
        admin.id,
        filters=ProfessionalFilterOptions(min_activity_months=24),
    )

    await ProfessionalMapper().apply(
        ctx,
        entity_type="professional",
        payload={
            "email": "active@example.com",
            "given_name": "Ana",
            "family_name": "Activa",
            "role": "doctor",
            "last_activity_at": date.today().isoformat(),
        },
        raw={},
        canonical_uuid=str(uuid4()),
        source_id="55",
        source_system="gesden",
    )
    await db_session.flush()

    user = (
        await db_session.execute(select(User).where(User.email == "active@example.com"))
    ).scalar_one()
    assert user.is_active is True
    membership = (
        await db_session.execute(
            select(ClinicMembership).where(ClinicMembership.user_id == user.id)
        )
    ).scalar_one()
    assert membership.role == "dentist"


@pytest.mark.asyncio
async def test_filter_non_clinical_role_opt_in(db_session) -> None:
    clinic, admin = await _bootstrap(db_session)
    ctx = await _ctx(
        db_session,
        clinic.id,
        admin.id,
        filters=ProfessionalFilterOptions(
            min_activity_months=0,
            exclude_non_clinical_roles=True,
        ),
    )

    await ProfessionalMapper().apply(
        ctx,
        entity_type="professional",
        payload={
            "email": "admin-staff@example.com",
            "role": "admin",
            "last_activity_at": date.today().isoformat(),
        },
        raw={},
        canonical_uuid=str(uuid4()),
        source_id="9",
        source_system="gesden",
    )
    await db_session.flush()

    user = (
        await db_session.execute(select(User).where(User.email == "admin-staff@example.com"))
    ).scalar_one()
    assert user.is_active is False
