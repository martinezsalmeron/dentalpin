#!/usr/bin/env python3
"""Seed script to populate DentalPin with demo data.

This script creates a complete demo environment including:
- 1 clinic with full configuration
- 5 users (admin, dentist, hygienist, assistant, receptionist)
- 15 patients of varied ages
- 35-40 appointments across past, current, and next week
- Odontogram data (tooth records and treatments for each patient)
- Treatment catalog with categories and items
- 7 budgets with various statuses (draft, accepted, completed, etc.)
- 8 invoices with various statuses (draft, issued, partial, paid) and payments

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
from app.modules.billing.models import Invoice, InvoiceItem, InvoiceSeries, Payment
from app.modules.budget.models import Budget, BudgetItem, BudgetSignature
from app.modules.catalog.models import TreatmentCatalogItem
from app.modules.catalog.seed import seed_catalog
from app.modules.clinical.models import Appointment, AppointmentTreatment, Patient
from app.modules.odontogram.models import ToothRecord, ToothTreatment
from app.seeds.demo_data import (
    CLINIC_ID,
    generate_appointments,
    generate_budgets_data,
    generate_invoices_data,
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
            emergency_contact=patient_data.get("emergency_contact"),
            medical_history=patient_data.get("medical_history"),
        )
        db.add(patient)
        patients.append(patient)

    await db.flush()
    print(f"  Created {len(patients)} patients")
    return patients


async def seed_appointments(db: AsyncSession) -> tuple[list[Appointment], list[dict]]:
    """Create demo appointments.

    Returns:
        Tuple of (appointments list, appointments_data for later treatment linking)
    """
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

    return appointments, appointments_data


async def seed_appointment_treatments(db: AsyncSession, appointments_data: list[dict]) -> int:
    """Link appointments to catalog treatments via AppointmentTreatment.

    Args:
        db: Database session
        appointments_data: List of appointment dicts with catalog_codes

    Returns:
        Number of AppointmentTreatment records created
    """
    # Get catalog items map
    result = await db.execute(
        select(TreatmentCatalogItem).where(TreatmentCatalogItem.clinic_id == CLINIC_ID)
    )
    catalog_items = result.scalars().all()

    # Build map of internal_code -> item id
    code_to_id = {item.internal_code: item.id for item in catalog_items}

    created_count = 0
    for appt_data in appointments_data:
        catalog_codes = appt_data.get("catalog_codes", [])
        for order, code in enumerate(catalog_codes):
            catalog_item_id = code_to_id.get(code)
            if catalog_item_id:
                apt_treatment = AppointmentTreatment(
                    appointment_id=appt_data["id"],
                    catalog_item_id=catalog_item_id,
                    display_order=order,
                )
                db.add(apt_treatment)
                created_count += 1

    await db.flush()
    print(f"  Linked {created_count} treatments to appointments")
    return created_count


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


async def seed_budgets(db: AsyncSession) -> dict:
    """Create demo budgets with items and signatures.

    Returns:
        Dictionary with counts of created records.
    """
    # First, get catalog items to reference them in budgets
    result = await db.execute(
        select(TreatmentCatalogItem).where(TreatmentCatalogItem.clinic_id == CLINIC_ID)
    )
    catalog_items = result.scalars().all()

    # Build map of internal_code -> item data
    catalog_items_map = {}
    for item in catalog_items:
        catalog_items_map[item.internal_code] = {
            "id": item.id,
            "default_price": item.default_price,
            "vat_type_id": item.vat_type_id,
            "vat_rate": item.vat_rate or 0.0,
        }

    # Generate budget data
    budget_data = generate_budgets_data(catalog_items_map)

    # Create budgets
    for budget_dict in budget_data["budgets"]:
        budget = Budget(
            id=budget_dict["id"],
            clinic_id=budget_dict["clinic_id"],
            patient_id=budget_dict["patient_id"],
            budget_number=budget_dict["budget_number"],
            version=budget_dict["version"],
            parent_budget_id=budget_dict["parent_budget_id"],
            status=budget_dict["status"],
            valid_from=budget_dict["valid_from"],
            valid_until=budget_dict["valid_until"],
            created_by=budget_dict["created_by"],
            assigned_professional_id=budget_dict["assigned_professional_id"],
            global_discount_type=budget_dict["global_discount_type"],
            global_discount_value=budget_dict["global_discount_value"],
            subtotal=budget_dict["subtotal"],
            total_discount=budget_dict["total_discount"],
            total_tax=budget_dict["total_tax"],
            total=budget_dict["total"],
            currency=budget_dict["currency"],
            internal_notes=budget_dict["internal_notes"],
            patient_notes=budget_dict["patient_notes"],
            insurance_estimate=budget_dict["insurance_estimate"],
            deleted_at=budget_dict["deleted_at"],
        )
        db.add(budget)

    await db.flush()

    # Create budget items
    for item_dict in budget_data["items"]:
        item = BudgetItem(
            id=item_dict["id"],
            clinic_id=item_dict["clinic_id"],
            budget_id=item_dict["budget_id"],
            catalog_item_id=item_dict["catalog_item_id"],
            unit_price=item_dict["unit_price"],
            quantity=item_dict["quantity"],
            discount_type=item_dict["discount_type"],
            discount_value=item_dict["discount_value"],
            vat_type_id=item_dict["vat_type_id"],
            vat_rate=item_dict["vat_rate"],
            line_subtotal=item_dict["line_subtotal"],
            line_discount=item_dict["line_discount"],
            line_tax=item_dict["line_tax"],
            line_total=item_dict["line_total"],
            tooth_number=item_dict["tooth_number"],
            surfaces=item_dict["surfaces"],
            tooth_treatment_id=item_dict["tooth_treatment_id"],
            invoiced_quantity=item_dict.get("invoiced_quantity", 0),
            display_order=item_dict["display_order"],
            notes=item_dict["notes"],
        )
        db.add(item)

    await db.flush()

    # Create signatures
    for sig_dict in budget_data["signatures"]:
        signature = BudgetSignature(
            id=sig_dict["id"],
            clinic_id=sig_dict["clinic_id"],
            budget_id=sig_dict["budget_id"],
            signature_type=sig_dict["signature_type"],
            signed_items=sig_dict["signed_items"],
            signed_by_name=sig_dict["signed_by_name"],
            signed_by_email=sig_dict["signed_by_email"],
            relationship_to_patient=sig_dict["relationship_to_patient"],
            signature_method=sig_dict["signature_method"],
            signature_data=sig_dict["signature_data"],
            ip_address=sig_dict["ip_address"],
            user_agent=sig_dict["user_agent"],
            signed_at=sig_dict["signed_at"],
            external_signature_id=sig_dict["external_signature_id"],
            external_provider=sig_dict["external_provider"],
            document_hash=sig_dict["document_hash"],
        )
        db.add(signature)

    await db.flush()

    # Count by status
    status_counts = {}
    for budget in budget_data["budgets"]:
        status = budget["status"]
        status_counts[status] = status_counts.get(status, 0) + 1

    print(f"  Created {len(budget_data['budgets'])} budgets:")
    for status, count in sorted(status_counts.items()):
        print(f"    - {status}: {count}")
    print(f"  Created {len(budget_data['items'])} budget items")
    print(f"  Created {len(budget_data['signatures'])} signatures")

    return {
        "budgets": len(budget_data["budgets"]),
        "items": len(budget_data["items"]),
        "signatures": len(budget_data["signatures"]),
    }


async def seed_invoices(db: AsyncSession) -> dict:
    """Create demo invoices with items and payments.

    Returns:
        Dictionary with counts of created records.
    """
    # First, get catalog items to reference them in invoices
    result = await db.execute(
        select(TreatmentCatalogItem).where(TreatmentCatalogItem.clinic_id == CLINIC_ID)
    )
    catalog_items = result.scalars().all()

    # Build map of internal_code -> item data
    catalog_items_map = {}
    for item in catalog_items:
        catalog_items_map[item.internal_code] = {
            "id": item.id,
            "default_price": item.default_price,
            "vat_type_id": item.vat_type_id,
            "vat_rate": item.vat_rate or 0.0,
        }

    # Generate invoice data
    invoice_data = generate_invoices_data(catalog_items_map)

    # Create invoice series
    for series_dict in invoice_data["series"]:
        series = InvoiceSeries(
            id=series_dict["id"],
            clinic_id=series_dict["clinic_id"],
            prefix=series_dict["prefix"],
            series_type=series_dict["series_type"],
            description=series_dict["description"],
            current_number=series_dict["current_number"],
            reset_yearly=series_dict["reset_yearly"],
            last_reset_year=series_dict["last_reset_year"],
            is_default=series_dict["is_default"],
            is_active=series_dict["is_active"],
        )
        db.add(series)

    await db.flush()

    # Create invoices
    for invoice_dict in invoice_data["invoices"]:
        invoice = Invoice(
            id=invoice_dict["id"],
            clinic_id=invoice_dict["clinic_id"],
            patient_id=invoice_dict["patient_id"],
            invoice_number=invoice_dict["invoice_number"],
            series_id=invoice_dict["series_id"],
            sequential_number=invoice_dict["sequential_number"],
            budget_id=invoice_dict["budget_id"],
            credit_note_for_id=invoice_dict["credit_note_for_id"],
            status=invoice_dict["status"],
            issue_date=invoice_dict["issue_date"],
            due_date=invoice_dict["due_date"],
            payment_term_days=invoice_dict["payment_term_days"],
            billing_name=invoice_dict["billing_name"],
            billing_tax_id=invoice_dict["billing_tax_id"],
            billing_address=invoice_dict["billing_address"],
            billing_email=invoice_dict["billing_email"],
            subtotal=invoice_dict["subtotal"],
            total_discount=invoice_dict["total_discount"],
            total_tax=invoice_dict["total_tax"],
            total=invoice_dict["total"],
            total_paid=invoice_dict["total_paid"],
            balance_due=invoice_dict["balance_due"],
            currency=invoice_dict["currency"],
            internal_notes=invoice_dict["internal_notes"],
            public_notes=invoice_dict["public_notes"],
            compliance_data=invoice_dict["compliance_data"],
            document_hash=invoice_dict["document_hash"],
            created_by=invoice_dict["created_by"],
            issued_by=invoice_dict["issued_by"],
            deleted_at=invoice_dict["deleted_at"],
        )
        db.add(invoice)

    await db.flush()

    # Create invoice items
    for item_dict in invoice_data["items"]:
        item = InvoiceItem(
            id=item_dict["id"],
            clinic_id=item_dict["clinic_id"],
            invoice_id=item_dict["invoice_id"],
            budget_item_id=item_dict["budget_item_id"],
            catalog_item_id=item_dict["catalog_item_id"],
            description=item_dict["description"],
            internal_code=item_dict["internal_code"],
            unit_price=item_dict["unit_price"],
            quantity=item_dict["quantity"],
            discount_type=item_dict["discount_type"],
            discount_value=item_dict["discount_value"],
            vat_type_id=item_dict["vat_type_id"],
            vat_rate=item_dict["vat_rate"],
            vat_exempt_reason=item_dict["vat_exempt_reason"],
            line_subtotal=item_dict["line_subtotal"],
            line_discount=item_dict["line_discount"],
            line_tax=item_dict["line_tax"],
            line_total=item_dict["line_total"],
            tooth_number=item_dict["tooth_number"],
            surfaces=item_dict["surfaces"],
            display_order=item_dict["display_order"],
        )
        db.add(item)

    await db.flush()

    # Create payments
    for payment_dict in invoice_data["payments"]:
        payment = Payment(
            id=payment_dict["id"],
            clinic_id=payment_dict["clinic_id"],
            invoice_id=payment_dict["invoice_id"],
            amount=payment_dict["amount"],
            payment_method=payment_dict["payment_method"],
            payment_date=payment_dict["payment_date"],
            reference=payment_dict["reference"],
            notes=payment_dict["notes"],
            recorded_by=payment_dict["recorded_by"],
            is_voided=payment_dict["is_voided"],
            voided_at=payment_dict["voided_at"],
            voided_by=payment_dict["voided_by"],
            void_reason=payment_dict["void_reason"],
        )
        db.add(payment)

    await db.flush()

    # Count by status
    status_counts = {}
    for invoice in invoice_data["invoices"]:
        status = invoice["status"]
        status_counts[status] = status_counts.get(status, 0) + 1

    print(f"  Created {len(invoice_data['series'])} invoice series")
    print(f"  Created {len(invoice_data['invoices'])} invoices:")
    for status, count in sorted(status_counts.items()):
        print(f"    - {status}: {count}")
    print(f"  Created {len(invoice_data['items'])} invoice items")
    print(f"  Created {len(invoice_data['payments'])} payments")

    return {
        "series": len(invoice_data["series"]),
        "invoices": len(invoice_data["invoices"]),
        "items": len(invoice_data["items"]),
        "payments": len(invoice_data["payments"]),
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
            print("[1/8] Creating clinic...")
            await seed_clinic(db)

            print("\n[2/8] Creating users...")
            await seed_users(db, password_hash)

            print("\n[3/8] Creating patients...")
            await seed_patients(db)

            print("\n[4/8] Creating appointments...")
            _, appointments_data = await seed_appointments(db)

            print("\n[5/8] Creating odontogram data...")
            await seed_odontogram(db)

            print("\n[6/8] Creating treatment catalog...")
            catalog_result = await seed_catalog(db, CLINIC_ID, lang=lang)
            print(f"  Created {catalog_result['categories']} categories")
            print(f"  Created {catalog_result['items']} catalog items")

            # Link appointments to catalog treatments (must be after catalog creation)
            print("\n[6b/8] Linking appointments to catalog treatments...")
            await seed_appointment_treatments(db, appointments_data)

            print("\n[7/8] Creating budgets...")
            await seed_budgets(db)

            print("\n[8/8] Creating invoices...")
            await seed_invoices(db)

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
