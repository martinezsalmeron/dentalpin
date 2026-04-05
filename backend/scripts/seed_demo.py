#!/usr/bin/env python3
"""Seed script to populate DentalPin with demo data.

This script creates a complete demo environment including:
- 1 clinic with full configuration
- 5 users (admin, dentist, hygienist, assistant, receptionist)
- 15 patients of varied ages
- 35-40 appointments across past, current, and next week

Usage:
    docker-compose exec -T backend python scripts/seed_demo.py

All users have password: demo1234
"""

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.models import Clinic, ClinicMembership, User
from app.core.auth.service import hash_password
from app.database import async_session_maker
from app.modules.clinical.models import Appointment, Patient
from app.seeds.demo_data import (
    CLINIC_DATA,
    CLINIC_ID,
    PATIENTS_DATA,
    USERS_DATA,
    generate_appointments,
)


async def check_existing_data(db: AsyncSession) -> bool:
    """Check if demo data already exists."""
    result = await db.execute(select(Clinic).where(Clinic.id == CLINIC_ID))
    return result.scalar_one_or_none() is not None


async def seed_clinic(db: AsyncSession) -> Clinic:
    """Create the demo clinic."""
    clinic = Clinic(
        id=CLINIC_DATA["id"],
        name=CLINIC_DATA["name"],
        tax_id=CLINIC_DATA["tax_id"],
        address=CLINIC_DATA["address"],
        phone=CLINIC_DATA["phone"],
        email=CLINIC_DATA["email"],
        settings=CLINIC_DATA["settings"],
        cabinets=CLINIC_DATA["cabinets"],
    )
    db.add(clinic)
    await db.flush()
    print(f"  Created clinic: {clinic.name}")
    return clinic


async def seed_users(db: AsyncSession, password_hash: str) -> list[User]:
    """Create demo users with their clinic memberships."""
    users = []
    for user_data in USERS_DATA:
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
    for patient_data in PATIENTS_DATA:
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


async def main():
    """Main seed function."""
    print("\n" + "=" * 60)
    print("DentalPin Demo Data Seeder")
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
            print("[1/4] Creating clinic...")
            await seed_clinic(db)

            print("\n[2/4] Creating users...")
            await seed_users(db, password_hash)

            print("\n[3/4] Creating patients...")
            await seed_patients(db)

            print("\n[4/4] Creating appointments...")
            await seed_appointments(db)

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
    print("\n" + "-" * 60)
    print("DEMO CREDENTIALS (all passwords: demo1234)")
    print("-" * 60)
    print(f"{'Email':<30} {'Role':<15} {'Name'}")
    print("-" * 60)
    for user in USERS_DATA:
        print(f"{user['email']:<30} {user['role']:<15} {user['first_name']} {user['last_name']}")
    print("-" * 60)
    print("\nOpen http://localhost:3000 to access the application.\n")


if __name__ == "__main__":
    asyncio.run(main())
