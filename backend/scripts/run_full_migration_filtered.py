"""Run a Gesdén → DentalPin import with the new professional filters.

Mirrors ``run_full_migration.py`` but threads ``execute_options`` so the
operator-tunable professional filter sliders are honoured. Defaults
match the wizard: 24-month activity window, exclude agenda-only
columns, exclude staff inactive in the source, keep non-clinical roles
(they land as deactivated regardless because the activity filter
catches most of them).

Usage (inside the backend container):
    python scripts/run_full_migration_filtered.py /tmp/full_export.dpm
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from uuid import UUID

from sqlalchemy import func, select

from app.core.auth.models import Clinic, ClinicMembership, User
from app.database import async_session_maker
from app.modules.billing.models import Invoice
from app.modules.budget.models import Budget
from app.modules.migration_import.models import EntityMapping, ImportWarning
from app.modules.migration_import.service import ImportJobService
from app.modules.odontogram.models import Treatment
from app.modules.patients.models import Patient
from app.modules.payments.models import Payment
from app.modules.treatment_plan.models import TreatmentPlan

DEFAULT_FILTERS = {
    "professional_min_activity_months": 24,
    "professional_exclude_agenda_orphans": True,
    "professional_exclude_inactive_in_source": True,
    "professional_exclude_non_clinical_roles": False,
}


async def run(dpmf_path: Path) -> None:
    async with async_session_maker() as db:
        clinic = (
            await db.execute(select(Clinic).order_by(Clinic.created_at).limit(1))
        ).scalar_one()
        admin = (await db.execute(select(User).order_by(User.created_at).limit(1))).scalar_one()
        print(f"[clinic] {clinic.name} ({clinic.id})")
        print(f"[admin]  {admin.email} ({admin.id})")
        print(f"[filters] {DEFAULT_FILTERS}")

        job = await ImportJobService.create_job(
            db,
            clinic_id=clinic.id,
            user_id=admin.id,
            original_filename=dpmf_path.name,
            staged_path=dpmf_path,
            file_size=dpmf_path.stat().st_size,
        )
        await db.commit()
        print(f"[job] {job.id} status={job.status}")

        await ImportJobService.validate(db, job, passphrase=None)
        await db.commit()
        print(
            f"[validate] status={job.status} total_entities={job.total_entities} "
            f"source={job.source_system}@{job.source_adapter_version}"
        )
        if job.status != "validated":
            print(f"[validate] FAILED — {job.error}")
            return

    await ImportJobService.execute_in_background(
        job_id=job.id,
        clinic_id=clinic.id,
        passphrase=None,
        import_fiscal_compliance=False,
        execute_options=DEFAULT_FILTERS,
    )

    async with async_session_maker() as db:
        job = await ImportJobService.get_job_unscoped(db, job.id)
        assert job is not None
        print(
            f"[execute] status={job.status} processed={job.processed_entities}/"
            f"{job.total_entities} error={job.error}"
        )
        await _print_target_summary(db, clinic.id, job.id)


async def _print_target_summary(db, clinic_id: UUID, job_id: UUID) -> None:
    async def _count(model, *extra) -> int:
        q = select(func.count()).select_from(model)
        if hasattr(model, "clinic_id"):
            q = q.where(model.clinic_id == clinic_id)
        for clause in extra:
            q = q.where(clause)
        return (await db.execute(q)).scalar_one()

    rows = [
        ("Patients", await _count(Patient)),
        ("Treatments (odontogram)", await _count(Treatment)),
        ("Treatment plans", await _count(TreatmentPlan)),
        ("Budgets", await _count(Budget)),
        ("Invoices", await _count(Invoice)),
        ("Payments", await _count(Payment)),
        ("Entity mappings", await _count(EntityMapping, EntityMapping.job_id == job_id)),
    ]
    print("\n=== Migrated counts ===")
    for label, n in rows:
        print(f"  {label:<28} {n}")

    print("\n=== ClinicMembership by role (this clinic) ===")
    rows = (
        await db.execute(
            select(ClinicMembership.role, func.count())
            .where(ClinicMembership.clinic_id == clinic_id)
            .group_by(ClinicMembership.role)
            .order_by(func.count().desc())
        )
    ).all()
    for role, n in rows:
        print(f"  {role:<28} {n}")

    print("\n=== Active clinicians (agenda-visible) ===")
    n_active_clin = (
        await db.execute(
            select(func.count(User.id))
            .join(ClinicMembership, ClinicMembership.user_id == User.id)
            .where(
                ClinicMembership.clinic_id == clinic_id,
                ClinicMembership.role.in_(["dentist", "hygienist"]),
                User.is_active.is_(True),
            )
        )
    ).scalar_one()
    n_inactive_clin = (
        await db.execute(
            select(func.count(User.id))
            .join(ClinicMembership, ClinicMembership.user_id == User.id)
            .where(
                ClinicMembership.clinic_id == clinic_id,
                ClinicMembership.role == "assistant",
                User.is_active.is_(False),
            )
        )
    ).scalar_one()
    print(f"  Active dentists+hygienists (agenda): {n_active_clin}")
    print(f"  Filtered (inactive assistants):       {n_inactive_clin}")

    print("\n=== Active professionals (name list) ===")
    rows = (
        await db.execute(
            select(User.first_name, User.last_name, ClinicMembership.role)
            .join(ClinicMembership, ClinicMembership.user_id == User.id)
            .where(
                ClinicMembership.clinic_id == clinic_id,
                ClinicMembership.role.in_(["dentist", "hygienist"]),
                User.is_active.is_(True),
            )
            .order_by(User.last_name)
        )
    ).all()
    for fn, ln, role in rows:
        print(f"  {role:<10} {ln}, {fn}")

    print("\n=== Top warnings (code → count) ===")
    rows = (
        await db.execute(
            select(ImportWarning.code, func.count())
            .where(ImportWarning.job_id == job_id)
            .group_by(ImportWarning.code)
            .order_by(func.count().desc())
            .limit(15)
        )
    ).all()
    for code, n in rows:
        print(f"  {code:<40} {n}")

    print("\n=== EntityMapping by type ===")
    rows = (
        await db.execute(
            select(EntityMapping.entity_type, func.count())
            .where(EntityMapping.job_id == job_id)
            .group_by(EntityMapping.entity_type)
            .order_by(func.count().desc())
        )
    ).all()
    for et, n in rows:
        print(f"  {et:<40} {n}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: run_full_migration_filtered.py <dpm-path>")
        sys.exit(2)
    asyncio.run(run(Path(sys.argv[1])))
