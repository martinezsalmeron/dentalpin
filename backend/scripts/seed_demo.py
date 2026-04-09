#!/usr/bin/env python3
"""Seed script to populate DentalPin with demo data.

This script creates a complete demo environment including:
- 1 clinic with full configuration
- 5 users (admin, dentist, hygienist, assistant, receptionist)
- 15 patients of varied ages
- 35-40 appointments across past, current, and next week
- Odontogram data (tooth records and treatments for each patient)
- Treatment catalog with categories and items

Usage:
    # Default (English)
    docker-compose exec -T backend python scripts/seed_demo.py

    # Spanish
    docker-compose exec -T backend python scripts/seed_demo.py --lang es

    # English (explicit)
    docker-compose exec -T backend python scripts/seed_demo.py --lang en

All users have password: demo1234
"""

import argparse
import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.models import Clinic, ClinicMembership, User
from app.core.auth.service import hash_password
from app.database import async_session_maker
from app.modules.catalog.seed import seed_catalog
from app.modules.clinical.models import Appointment, Patient
from app.modules.odontogram.models import ToothRecord, ToothTreatment
from app.seeds.demo_data import (
    CLINIC_ID,
    generate_appointments,
    generate_odontogram_data,
    get_clinic_data,
    get_patients_data,
    get_users_data,
    set_language,
)


async def check_existing_data(db: AsyncSession) -> bool:
    """Check if demo data already exists."""
    result = await db.execute(select(Clinic).where(Clinic.id == CLINIC_ID))
    return result.scalar_one_or_none() is not None


async def seed_clinic(db: AsyncSession) -> Clinic:
    """Create the demo clinic."""
    clinic_data = get_clinic_data()
    clinic = Clinic(
        id=clinic_data["id"],
        name=clinic_data["name"],
        tax_id=clinic_data["tax_id"],
        address=clinic_data["address"],
        phone=clinic_data["phone"],
        email=clinic_data["email"],
        settings=clinic_data["settings"],
        cabinets=clinic_data["cabinets"],
    )
    db.add(clinic)
    await db.flush()
    print(f"  Created clinic: {clinic.name}")
    return clinic


async def seed_users(db: AsyncSession, password_hash: str) -> list[User]:
    """Create demo users with their clinic memberships."""
    users = []
    users_data = get_users_data()
    for user_data in users_data:
        user = User(
            id=user_data["id"],
            email=user_data["email"],
            password_hash=password_hash,
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            professional_id=user_data.get("professional_id"),
            is_active=True,
            token_version=0,
        )
        db.add(user)
        users.append(user)

        # Create membership
        membership = ClinicMembership(
            id=user_data["membership_id"],
            user_id=user_data["id"],
            clinic_id=CLINIC_ID,
            role=user_data["role"],
        )
        db.add(membership)
        print(f"  Created user: {user.email} ({user_data['role']})")

    await db.flush()
    return users


async def seed_patients(db: AsyncSession) -> list[Patient]:
    """Create demo patients."""
    patients = []
    patients_data = get_patients_data()
    for patient_data in patients_data:
        patient = Patient(
            id=patient_data["id"],
            clinic_id=CLINIC_ID,
            first_name=patient_data["first_name"],
            last_name=patient_data["last_name"],
            phone=patient_data["phone"],
            email=patient_data["email"],
            date_of_birth=patient_data["date_of_birth"],
            notes=patient_data["notes"],
            status="active",
        )
        db.add(patient)
        patients.append(patient)

    await db.flush()
    print(f"  Created {len(patients)} patients")
    return patients


async def seed_appointments(db: AsyncSession) -> list[Appointment]:
    """Create demo appointments."""
    appointments_data = generate_appointments()
    appointments = []

    for appt_data in appointments_data:
        appointment = Appointment(
            id=appt_data["id"],
            clinic_id=appt_data["clinic_id"],
            patient_id=appt_data["patient_id"],
            professional_id=appt_data["professional_id"],
            cabinet=appt_data["cabinet"],
            start_time=appt_data["start_time"],
            end_time=appt_data["end_time"],
            treatment_type=appt_data["treatment_type"],
            status=appt_data["status"],
            notes=appt_data["notes"],
            color=appt_data["color"],
        )
        db.add(appointment)
        appointments.append(appointment)

    await db.flush()

    # Count by status
    status_counts = {}
    for appt in appointments:
        status_counts[appt.status] = status_counts.get(appt.status, 0) + 1

    print(f"  Created {len(appointments)} appointments:")
    for status, count in sorted(status_counts.items()):
        print(f"    - {status}: {count}")

    return appointments


async def seed_odontogram(db: AsyncSession) -> dict:
    """Create demo odontogram data (tooth records and treatments).

    Returns:
        Dictionary with counts of created records.
    """
    odontogram_data = generate_odontogram_data()

    # Create tooth records
    tooth_records = []
    for record_data in odontogram_data["tooth_records"]:
        record = ToothRecord(
            id=record_data["id"],
            clinic_id=record_data["clinic_id"],
            patient_id=record_data["patient_id"],
            tooth_number=record_data["tooth_number"],
            tooth_type=record_data["tooth_type"],
            general_condition=record_data["general_condition"],
            surfaces=record_data["surfaces"],
            notes=record_data["notes"],
            is_displaced=record_data["is_displaced"],
            is_rotated=record_data["is_rotated"],
            displacement_notes=record_data["displacement_notes"],
        )
        db.add(record)
        tooth_records.append(record)

    await db.flush()

    # Create treatments
    treatments = []
    for treatment_data in odontogram_data["treatments"]:
        treatment = ToothTreatment(
            id=treatment_data["id"],
            clinic_id=treatment_data["clinic_id"],
            patient_id=treatment_data["patient_id"],
            tooth_record_id=treatment_data["tooth_record_id"],
            tooth_number=treatment_data["tooth_number"],
            treatment_type=treatment_data["treatment_type"],
            treatment_category=treatment_data["treatment_category"],
            surfaces=treatment_data["surfaces"],
            status=treatment_data["status"],
            recorded_at=treatment_data["recorded_at"],
            performed_at=treatment_data["performed_at"],
            performed_by=treatment_data["performed_by"],
            catalog_item_id=treatment_data["catalog_item_id"],
            budget_item_id=treatment_data["budget_item_id"],
            source_module=treatment_data["source_module"],
            notes=treatment_data["notes"],
            deleted_at=treatment_data["deleted_at"],
        )
        db.add(treatment)
        treatments.append(treatment)

    await db.flush()

    # Count patients with odontogram data
    patient_ids = set(r.patient_id for r in tooth_records)

    # Count by status
    existing_count = sum(1 for t in treatments if t.status == "existing")
    planned_count = sum(1 for t in treatments if t.status == "planned")

    print(f"  Created {len(tooth_records)} tooth records for {len(patient_ids)} patients")
    print(f"  Created {len(treatments)} treatments:")
    print(f"    - existing: {existing_count}")
    print(f"    - planned: {planned_count}")

    return {
        "tooth_records": len(tooth_records),
        "treatments": len(treatments),
        "patients": len(patient_ids),
    }


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Seed DentalPin with demo data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/seed_demo.py              # Default (English)
  python scripts/seed_demo.py --lang es    # Spanish
  python scripts/seed_demo.py --lang en    # English (explicit)
        """,
    )
    parser.add_argument(
        "--lang",
        "-l",
        choices=["en", "es"],
        default="en",
        help="Language for demo data (default: en)",
    )
    return parser.parse_args()


async def main(lang: str = "en"):
    """Main seed function."""
    # Set language for demo data
    set_language(lang)
    lang_name = "English" if lang == "en" else "Spanish"

    print("\n" + "=" * 60)
    print(f"DentalPin Demo Data Seeder ({lang_name})")
    print("=" * 60 + "\n")

    async with async_session_maker() as db:
        # Check for existing data
        if await check_existing_data(db):
            print("Demo data already exists!")
            print("To reset, run: ./scripts/reset-db.sh")
            print("Then run this script again.\n")
            return

        print("Creating demo data...\n")

        # Generate password hash once
        password_hash = hash_password("demo1234")

        try:
            # Seed in order (respecting foreign keys)
            print("[1/6] Creating clinic...")
            await seed_clinic(db)

            print("\n[2/6] Creating users...")
            await seed_users(db, password_hash)

            print("\n[3/6] Creating patients...")
            await seed_patients(db)

            print("\n[4/6] Creating appointments...")
            await seed_appointments(db)

            print("\n[5/6] Creating odontogram data...")
            await seed_odontogram(db)

            print("\n[6/6] Creating treatment catalog...")
            catalog_result = await seed_catalog(db, CLINIC_ID, lang=lang)
            print(f"  Created {catalog_result['categories']} categories")
            print(f"  Created {catalog_result['items']} catalog items")

            # Commit all changes
            await db.commit()
            print("\n" + "=" * 60)
            print("Demo data created successfully!")
            print("=" * 60)

        except Exception as e:
            await db.rollback()
            print(f"\nError creating demo data: {e}")
            raise

    # Print credentials summary
    users_data = get_users_data()
    print("\n" + "-" * 60)
    print("DEMO CREDENTIALS (all passwords: demo1234)")
    print("-" * 60)
    print(f"{'Email':<30} {'Role':<15} {'Name'}")
    print("-" * 60)
    for user in users_data:
        print(f"{user['email']:<30} {user['role']:<15} {user['first_name']} {user['last_name']}")
    print("-" * 60)
    print("\nOpen http://localhost:3000 to access the application.\n")


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(main(lang=args.lang))
