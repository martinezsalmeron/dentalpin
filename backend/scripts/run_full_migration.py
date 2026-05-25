"""Run a real Gesdén → DentalPin migration end-to-end.

Pipeline:
  1. Pick the demo clinic + an admin user already present in the DB
     (use ``./scripts/seed-demo.sh --lang es`` before running this).
  2. Create an ``ImportJob`` against the given .dpm file.
  3. Run ``validate`` → ``execute_in_background`` synchronously.
  4. Print per-entity counts, warning summary, and a sample of what
     landed in the target tables (patients, treatments, budgets,
     invoices, payments).

Usage (inside the backend container):
    python scripts/run_full_migration.py /app/clinica_500.dpm
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from uuid import UUID

from sqlalchemy import func, select

from app.core.auth.models import Clinic, User
from app.database import async_session_maker
from app.modules.billing.models import Invoice
from app.modules.budget.models import Budget
from app.modules.catalog.models import TreatmentCatalogItem
from app.modules.migration_import.models import EntityMapping, ImportWarning
from app.modules.migration_import.service import ImportJobService
from app.modules.odontogram.models import Treatment
from app.modules.patients.models import Patient
from app.modules.payments.models import Payment
from app.modules.treatment_plan.models import TreatmentPlan


async def run(dpmf_path: Path) -> None:
    async with async_session_maker() as db:
        # Pick the first non-system clinic and the first admin.
        clinic = (
            await db.execute(select(Clinic).order_by(Clinic.created_at).limit(1))
        ).scalar_one()
        admin = (await db.execute(select(User).order_by(User.created_at).limit(1))).scalar_one()
        print(f"[clinic] {clinic.name} ({clinic.id})")
        print(f"[admin]  {admin.email} ({admin.id})")

        job = await ImportJobService.create_job(
            db,
            clinic_id=clinic.id,
            user_id=admin.id,
            original_filename=dpmf_path.name,
            staged_path=dpmf_path,
            file_size=dpmf_path.stat().st_size,
        )
        await db.commit()
        print(f"[job]    {job.id} status={job.status}")

        await ImportJobService.validate(db, job, passphrase=None)
        await db.commit()
        print(
            f"[validate] status={job.status} total_entities={job.total_entities} "
            f"source={job.source_system}@{job.source_adapter_version}"
        )
        if job.status != "validated":
            print(f"[validate] FAILED — {job.error}")
            return

    # execute_in_background owns its own session
    await ImportJobService.execute_in_background(
        job_id=job.id,
        clinic_id=clinic.id,
        passphrase=None,
        import_fiscal_compliance=False,
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
        ("Catalog items", await _count(TreatmentCatalogItem)),
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

    # Top warnings by code
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

    # Per-entity-type processed
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

    # Catalog landing breakdown
    print("\n=== Catalog landing (linked seed vs migrated new) ===")
    seed_n = (
        await db.execute(
            select(func.count(TreatmentCatalogItem.id)).where(
                TreatmentCatalogItem.clinic_id == clinic_id,
                TreatmentCatalogItem.is_system.is_(True),
            )
        )
    ).scalar_one()
    mig_n = (
        await db.execute(
            select(func.count(TreatmentCatalogItem.id)).where(
                TreatmentCatalogItem.clinic_id == clinic_id,
                TreatmentCatalogItem.internal_code.like("MIG-%"),
            )
        )
    ).scalar_one()
    print(f"  System seed items: {seed_n}")
    print(f"  Migrated new items (MIG-*): {mig_n}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: run_full_migration.py <dpm-path>")
        sys.exit(2)
    asyncio.run(run(Path(sys.argv[1])))
