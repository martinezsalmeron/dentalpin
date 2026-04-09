"""Demo data definitions for DentalPin.

This module contains all the seed data used to populate a demo environment.
All UUIDs are fixed to allow consistent references and easier debugging.

Supports bilingual data (English and Spanish) via LANG setting.
"""

from datetime import date, datetime, timedelta
from typing import Literal
from uuid import UUID

# =============================================================================
# Language Configuration
# =============================================================================

SupportedLang = Literal["es", "en"]
LANG: SupportedLang = "en"  # Default language


def set_language(lang: SupportedLang) -> None:
    """Set the language for seed data."""
    global LANG
    LANG = lang


def t(translations: dict[str, str]) -> str:
    """Get translated string for current language."""
    return translations.get(LANG, translations.get("en", ""))


# =============================================================================
# Fixed UUIDs for consistent references
# =============================================================================

# Clinic
CLINIC_ID = UUID("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11")

# Users
USER_ADMIN_ID = UUID("b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22")
USER_DENTIST_ID = UUID("b1eebc99-9c0b-4ef8-bb6d-6bb9bd380a23")
USER_HYGIENIST_ID = UUID("b2eebc99-9c0b-4ef8-bb6d-6bb9bd380a24")
USER_ASSISTANT_ID = UUID("b3eebc99-9c0b-4ef8-bb6d-6bb9bd380a25")
USER_RECEPTIONIST_ID = UUID("b4eebc99-9c0b-4ef8-bb6d-6bb9bd380a26")

# Memberships
MEMBERSHIP_ADMIN_ID = UUID("c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a33")
MEMBERSHIP_DENTIST_ID = UUID("c1eebc99-9c0b-4ef8-bb6d-6bb9bd380a34")
MEMBERSHIP_HYGIENIST_ID = UUID("c2eebc99-9c0b-4ef8-bb6d-6bb9bd380a35")
MEMBERSHIP_ASSISTANT_ID = UUID("c3eebc99-9c0b-4ef8-bb6d-6bb9bd380a36")
MEMBERSHIP_RECEPTIONIST_ID = UUID("c4eebc99-9c0b-4ef8-bb6d-6bb9bd380a37")

# Patients (15 patients) - Using hex digits only (0-9, a-f)
PATIENT_IDS = [
    UUID("d0eebc99-9c0b-4ef8-bb6d-6bb9bd380a40"),
    UUID("d1eebc99-9c0b-4ef8-bb6d-6bb9bd380a41"),
    UUID("d2eebc99-9c0b-4ef8-bb6d-6bb9bd380a42"),
    UUID("d3eebc99-9c0b-4ef8-bb6d-6bb9bd380a43"),
    UUID("d4eebc99-9c0b-4ef8-bb6d-6bb9bd380a44"),
    UUID("d5eebc99-9c0b-4ef8-bb6d-6bb9bd380a45"),
    UUID("d6eebc99-9c0b-4ef8-bb6d-6bb9bd380a46"),
    UUID("d7eebc99-9c0b-4ef8-bb6d-6bb9bd380a47"),
    UUID("d8eebc99-9c0b-4ef8-bb6d-6bb9bd380a48"),
    UUID("d9eebc99-9c0b-4ef8-bb6d-6bb9bd380a49"),
    UUID("daeebc99-9c0b-4ef8-bb6d-6bb9bd380a4a"),
    UUID("dbeebc99-9c0b-4ef8-bb6d-6bb9bd380a4b"),
    UUID("dceebc99-9c0b-4ef8-bb6d-6bb9bd380a4c"),
    UUID("ddeebc99-9c0b-4ef8-bb6d-6bb9bd380a4d"),
    UUID("deeebc99-9c0b-4ef8-bb6d-6bb9bd380a4e"),
]


# =============================================================================
# Bilingual Data Definitions
# =============================================================================


# Clinic data with translations
def get_clinic_data() -> dict:
    """Get clinic data in current language."""
    return {
        "id": CLINIC_ID,
        "name": t({"es": "Clínica Dental Demo", "en": "Demo Dental Clinic"}),
        "tax_id": t({"es": "B12345678", "en": "12-3456789"}),
        "address": {
            "street": t({"es": "Calle Gran Vía 123", "en": "123 Main Street"}),
            "city": t({"es": "Madrid", "en": "New York"}),
            "postal_code": t({"es": "28013", "en": "10001"}),
            "country": t({"es": "España", "en": "USA"}),
        },
        "phone": t({"es": "+34 912 345 678", "en": "+1 (212) 555-0100"}),
        "email": "info@demo.clinic",
        "settings": {
            "slot_duration_min": 30,
            "currency": t({"es": "EUR", "en": "USD"}),
            "timezone": t({"es": "Europe/Madrid", "en": "America/New_York"}),
            "working_hours": {
                "monday": {"morning": ["09:00", "14:00"], "afternoon": ["16:00", "20:00"]},
                "tuesday": {"morning": ["09:00", "14:00"], "afternoon": ["16:00", "20:00"]},
                "wednesday": {"morning": ["09:00", "14:00"], "afternoon": ["16:00", "20:00"]},
                "thursday": {"morning": ["09:00", "14:00"], "afternoon": ["16:00", "20:00"]},
                "friday": {"morning": ["09:00", "14:00"], "afternoon": ["16:00", "20:00"]},
            },
        },
        "cabinets": [
            {"name": t({"es": "Gabinete 1", "en": "Room 1"}), "color": "#3B82F6"},
            {"name": t({"es": "Gabinete 2", "en": "Room 2"}), "color": "#10B981"},
        ],
    }


# User names by language
USERS_I18N = {
    "admin": {
        "es": {"first_name": "Admin", "last_name": "Demo"},
        "en": {"first_name": "Admin", "last_name": "Demo"},
    },
    "dentist": {
        "es": {"first_name": "María", "last_name": "García López"},
        "en": {"first_name": "Sarah", "last_name": "Johnson"},
    },
    "hygienist": {
        "es": {"first_name": "Carlos", "last_name": "López Martínez"},
        "en": {"first_name": "Michael", "last_name": "Williams"},
    },
    "assistant": {
        "es": {"first_name": "Ana", "last_name": "Martínez Ruiz"},
        "en": {"first_name": "Emily", "last_name": "Davis"},
    },
    "receptionist": {
        "es": {"first_name": "Laura", "last_name": "Sánchez Pérez"},
        "en": {"first_name": "Jessica", "last_name": "Brown"},
    },
}


def get_users_data() -> list[dict]:
    """Get users data in current language."""
    return [
        {
            "id": USER_ADMIN_ID,
            "email": "admin@demo.clinic",
            "first_name": USERS_I18N["admin"][LANG]["first_name"],
            "last_name": USERS_I18N["admin"][LANG]["last_name"],
            "role": "admin",
            "membership_id": MEMBERSHIP_ADMIN_ID,
        },
        {
            "id": USER_DENTIST_ID,
            "email": "dentist@demo.clinic",
            "first_name": USERS_I18N["dentist"][LANG]["first_name"],
            "last_name": USERS_I18N["dentist"][LANG]["last_name"],
            "professional_id": t({"es": "28/12345", "en": "DDS-12345"}),
            "role": "dentist",
            "membership_id": MEMBERSHIP_DENTIST_ID,
        },
        {
            "id": USER_HYGIENIST_ID,
            "email": "hygienist@demo.clinic",
            "first_name": USERS_I18N["hygienist"][LANG]["first_name"],
            "last_name": USERS_I18N["hygienist"][LANG]["last_name"],
            "professional_id": t({"es": "28/54321", "en": "RDH-54321"}),
            "role": "hygienist",
            "membership_id": MEMBERSHIP_HYGIENIST_ID,
        },
        {
            "id": USER_ASSISTANT_ID,
            "email": "assistant@demo.clinic",
            "first_name": USERS_I18N["assistant"][LANG]["first_name"],
            "last_name": USERS_I18N["assistant"][LANG]["last_name"],
            "role": "assistant",
            "membership_id": MEMBERSHIP_ASSISTANT_ID,
        },
        {
            "id": USER_RECEPTIONIST_ID,
            "email": "receptionist@demo.clinic",
            "first_name": USERS_I18N["receptionist"][LANG]["first_name"],
            "last_name": USERS_I18N["receptionist"][LANG]["last_name"],
            "role": "receptionist",
            "membership_id": MEMBERSHIP_RECEPTIONIST_ID,
        },
    ]


# Patient data by language (phone and email as dicts for lazy translation)
PATIENTS_I18N = [
    # Children/Teens
    {
        "id": PATIENT_IDS[0],
        "es": {
            "first_name": "Pablo",
            "last_name": "Fernández García",
            "notes": "Paciente pediátrico. Primera visita para revisión.",
        },
        "en": {
            "first_name": "Ethan",
            "last_name": "Miller",
            "notes": "Pediatric patient. First visit for checkup.",
        },
        "phone": {"es": "+34 612 345 001", "en": "+1 (212) 555-0001"},
        "email": None,
        "date_of_birth": date(2016, 3, 15),
    },
    {
        "id": PATIENT_IDS[1],
        "es": {
            "first_name": "Lucía",
            "last_name": "Rodríguez Sánchez",
            "notes": "Tratamiento de ortodoncia en curso.",
        },
        "en": {
            "first_name": "Olivia",
            "last_name": "Wilson",
            "notes": "Orthodontic treatment in progress.",
        },
        "phone": {"es": "+34 612 345 002", "en": "+1 (212) 555-0002"},
        "email": {"es": "lucia.rodriguez@email.com", "en": "olivia.wilson@email.com"},
        "date_of_birth": date(2010, 7, 22),
    },
    # Young Adults
    {
        "id": PATIENT_IDS[2],
        "es": {"first_name": "Miguel", "last_name": "González Torres", "notes": None},
        "en": {"first_name": "James", "last_name": "Anderson", "notes": None},
        "phone": {"es": "+34 612 345 003", "en": "+1 (212) 555-0003"},
        "email": {"es": "miguel.gonzalez@email.com", "en": "james.anderson@email.com"},
        "date_of_birth": date(1998, 11, 8),
    },
    {
        "id": PATIENT_IDS[3],
        "es": {
            "first_name": "Carmen",
            "last_name": "Díaz Moreno",
            "notes": "Sensibilidad dental. Usar anestesia con precaución.",
        },
        "en": {
            "first_name": "Emma",
            "last_name": "Taylor",
            "notes": "Dental sensitivity. Use anesthesia with caution.",
        },
        "phone": {"es": "+34 612 345 004", "en": "+1 (212) 555-0004"},
        "email": {"es": "carmen.diaz@email.com", "en": "emma.taylor@email.com"},
        "date_of_birth": date(1995, 5, 30),
    },
    {
        "id": PATIENT_IDS[4],
        "es": {"first_name": "David", "last_name": "Martín López", "notes": None},
        "en": {"first_name": "William", "last_name": "Thomas", "notes": None},
        "phone": {"es": "+34 612 345 005", "en": "+1 (212) 555-0005"},
        "email": None,
        "date_of_birth": date(1992, 2, 14),
    },
    # Adults
    {
        "id": PATIENT_IDS[5],
        "es": {
            "first_name": "Elena",
            "last_name": "Ruiz Hernández",
            "notes": "Embarazada (tercer trimestre). Evitar radiografías.",
        },
        "en": {
            "first_name": "Sophia",
            "last_name": "Martinez",
            "notes": "Pregnant (third trimester). Avoid X-rays.",
        },
        "phone": {"es": "+34 612 345 006", "en": "+1 (212) 555-0006"},
        "email": {"es": "elena.ruiz@email.com", "en": "sophia.martinez@email.com"},
        "date_of_birth": date(1985, 9, 3),
    },
    {
        "id": PATIENT_IDS[6],
        "es": {
            "first_name": "Javier",
            "last_name": "Sánchez Muñoz",
            "notes": "Diabético tipo 2. Control de cicatrización.",
        },
        "en": {
            "first_name": "Daniel",
            "last_name": "Garcia",
            "notes": "Type 2 diabetic. Monitor healing.",
        },
        "phone": {"es": "+34 612 345 007", "en": "+1 (212) 555-0007"},
        "email": {"es": "javier.sanchez@email.com", "en": "daniel.garcia@email.com"},
        "date_of_birth": date(1980, 12, 25),
    },
    {
        "id": PATIENT_IDS[7],
        "es": {"first_name": "Isabel", "last_name": "López Navarro", "notes": None},
        "en": {"first_name": "Mia", "last_name": "Robinson", "notes": None},
        "phone": {"es": "+34 612 345 008", "en": "+1 (212) 555-0008"},
        "email": None,
        "date_of_birth": date(1978, 6, 17),
    },
    {
        "id": PATIENT_IDS[8],
        "es": {
            "first_name": "Francisco",
            "last_name": "García Romero",
            "notes": "Alérgico a penicilina.",
        },
        "en": {
            "first_name": "Alexander",
            "last_name": "Clark",
            "notes": "Allergic to penicillin.",
        },
        "phone": {"es": "+34 612 345 009", "en": "+1 (212) 555-0009"},
        "email": {"es": "francisco.garcia@email.com", "en": "alexander.clark@email.com"},
        "date_of_birth": date(1975, 4, 9),
    },
    {
        "id": PATIENT_IDS[9],
        "es": {
            "first_name": "Rosa",
            "last_name": "Martínez Jiménez",
            "notes": "Hipertensa. Verificar presión antes de procedimientos.",
        },
        "en": {
            "first_name": "Charlotte",
            "last_name": "Lewis",
            "notes": "Hypertensive. Check blood pressure before procedures.",
        },
        "phone": {"es": "+34 612 345 010", "en": "+1 (212) 555-0010"},
        "email": {"es": "rosa.martinez@email.com", "en": "charlotte.lewis@email.com"},
        "date_of_birth": date(1970, 8, 21),
    },
    # Older Adults
    {
        "id": PATIENT_IDS[10],
        "es": {
            "first_name": "Antonio",
            "last_name": "Hernández Castro",
            "notes": "Prótesis parcial superior.",
        },
        "en": {
            "first_name": "Robert",
            "last_name": "Walker",
            "notes": "Upper partial denture.",
        },
        "phone": {"es": "+34 612 345 011", "en": "+1 (212) 555-0011"},
        "email": None,
        "date_of_birth": date(1960, 1, 5),
    },
    {
        "id": PATIENT_IDS[11],
        "es": {
            "first_name": "María Teresa",
            "last_name": "Romero Vega",
            "notes": "Paciente con implantes. Revisión periódica.",
        },
        "en": {
            "first_name": "Patricia",
            "last_name": "Hall",
            "notes": "Patient with implants. Periodic review.",
        },
        "phone": {"es": "+34 612 345 012", "en": "+1 (212) 555-0012"},
        "email": None,
        "date_of_birth": date(1955, 10, 12),
    },
    {
        "id": PATIENT_IDS[12],
        "es": {
            "first_name": "José Luis",
            "last_name": "Muñoz Blanco",
            "notes": "Toma anticoagulantes. Coordinar con médico antes de extracciones.",
        },
        "en": {
            "first_name": "Richard",
            "last_name": "Allen",
            "notes": "On blood thinners. Coordinate with physician before extractions.",
        },
        "phone": {"es": "+34 612 345 013", "en": "+1 (212) 555-0013"},
        "email": {"es": "joseluis.munoz@email.com", "en": "richard.allen@email.com"},
        "date_of_birth": date(1950, 3, 28),
    },
    {
        "id": PATIENT_IDS[13],
        "es": {"first_name": "Dolores", "last_name": "Vega Ortiz", "notes": None},
        "en": {"first_name": "Barbara", "last_name": "Young", "notes": None},
        "phone": {"es": "+34 612 345 014", "en": "+1 (212) 555-0014"},
        "email": None,
        "date_of_birth": date(1948, 7, 7),
    },
    {
        "id": PATIENT_IDS[14],
        "es": {
            "first_name": "Manuel",
            "last_name": "Castro Delgado",
            "notes": "Prótesis completa. Necesita ajustes frecuentes.",
        },
        "en": {
            "first_name": "Charles",
            "last_name": "King",
            "notes": "Complete denture. Requires frequent adjustments.",
        },
        "phone": {"es": "+34 612 345 015", "en": "+1 (212) 555-0015"},
        "email": None,
        "date_of_birth": date(1945, 11, 19),
    },
]


def get_patients_data() -> list[dict]:
    """Get patients data in current language."""
    patients = []
    for p in PATIENTS_I18N:
        # Handle phone: dict with translations or None
        phone = p["phone"]
        if isinstance(phone, dict):
            phone = t(phone)

        # Handle email: dict with translations, string, or None
        email = p["email"]
        if isinstance(email, dict):
            email = t(email)

        patient = {
            "id": p["id"],
            "first_name": p[LANG]["first_name"],
            "last_name": p[LANG]["last_name"],
            "phone": phone,
            "email": email,
            "date_of_birth": p["date_of_birth"],
            "notes": p[LANG]["notes"],
        }
        patients.append(patient)
    return patients


# =============================================================================
# Appointment Templates
# =============================================================================

# Treatment types with typical durations (in minutes)
TREATMENT_TYPES_I18N = [
    {
        "names": {"es": "Revisión", "en": "Checkup"},
        "duration": 30,
        "color": "#3B82F6",
    },
    {
        "names": {"es": "Limpieza dental", "en": "Dental cleaning"},
        "duration": 45,
        "color": "#10B981",
    },
    {
        "names": {"es": "Empaste", "en": "Filling"},
        "duration": 45,
        "color": "#F59E0B",
    },
    {
        "names": {"es": "Extracción", "en": "Extraction"},
        "duration": 60,
        "color": "#EF4444",
    },
    {
        "names": {"es": "Endodoncia", "en": "Root canal"},
        "duration": 90,
        "color": "#8B5CF6",
    },
    {
        "names": {"es": "Ortodoncia - Revisión", "en": "Orthodontics - Checkup"},
        "duration": 30,
        "color": "#EC4899",
    },
    {
        "names": {"es": "Blanqueamiento", "en": "Whitening"},
        "duration": 60,
        "color": "#06B6D4",
    },
    {
        "names": {"es": "Implante - Consulta", "en": "Implant - Consultation"},
        "duration": 45,
        "color": "#84CC16",
    },
    {
        "names": {"es": "Urgencia", "en": "Emergency"},
        "duration": 30,
        "color": "#DC2626",
    },
]


def get_treatment_types() -> list[dict]:
    """Get treatment types in current language."""
    return [
        {"name": t(tt["names"]), "duration": tt["duration"], "color": tt["color"]}
        for tt in TREATMENT_TYPES_I18N
    ]


# Appointment statuses for past appointments
PAST_STATUSES = ["completed", "completed", "completed", "completed", "no_show"]

# Time slots (morning and afternoon)
MORNING_SLOTS = [
    "09:00",
    "09:30",
    "10:00",
    "10:30",
    "11:00",
    "11:30",
    "12:00",
    "12:30",
    "13:00",
    "13:30",
]
AFTERNOON_SLOTS = ["16:00", "16:30", "17:00", "17:30", "18:00", "18:30", "19:00", "19:30"]


def generate_appointments(reference_date: date | None = None) -> list[dict]:
    """Generate realistic appointment data relative to a reference date.

    Args:
        reference_date: The date to use as "today". Defaults to actual today.

    Returns:
        List of appointment dictionaries ready for database insertion.
    """
    import random
    from uuid import uuid4

    if reference_date is None:
        reference_date = date.today()

    appointments = []
    treatment_types = get_treatment_types()
    clinic_data = get_clinic_data()
    cabinets = [c["name"] for c in clinic_data["cabinets"]]

    # Get Monday of current week
    current_monday = reference_date - timedelta(days=reference_date.weekday())

    # Weeks to generate: last week, current week, next week
    weeks = [
        ("past", current_monday - timedelta(days=7)),
        ("current", current_monday),
        ("future", current_monday + timedelta(days=7)),
    ]

    # Professionals to assign appointments to
    professionals = [USER_DENTIST_ID, USER_HYGIENIST_ID]

    # Track used slots to avoid conflicts: (cabinet, professional_id, start_time)
    used_slots: set[tuple[str, str, datetime]] = set()

    for week_type, week_start in weeks:
        # Determine number of appointments for this week
        if week_type == "past":
            num_appointments = random.randint(10, 12)
        elif week_type == "current":
            num_appointments = random.randint(15, 18)
        else:  # future
            num_appointments = random.randint(10, 12)

        # Generate appointments distributed across weekdays
        attempts = 0
        created = 0
        while created < num_appointments and attempts < num_appointments * 10:
            attempts += 1

            # Pick a random weekday (0-4 = Mon-Fri)
            day_offset = random.randint(0, 4)
            appt_date = week_start + timedelta(days=day_offset)

            # Pick morning or afternoon slot
            if random.random() < 0.6:  # 60% morning
                time_str = random.choice(MORNING_SLOTS)
            else:
                time_str = random.choice(AFTERNOON_SLOTS)

            hour, minute = map(int, time_str.split(":"))
            start_time = datetime(appt_date.year, appt_date.month, appt_date.day, hour, minute, 0)

            # Pick professional and cabinet
            professional_id = random.choice(professionals)
            cabinet = random.choice(cabinets)

            # Check for slot conflict
            slot_key = (cabinet, str(professional_id), start_time)
            if slot_key in used_slots:
                continue  # Try again with different slot

            used_slots.add(slot_key)

            # Pick treatment type
            treatment = random.choice(treatment_types)
            end_time = start_time + timedelta(minutes=treatment["duration"])

            # Pick patient
            patient_id = random.choice(PATIENT_IDS)

            # Determine status based on week type
            if week_type == "past":
                status = random.choice(PAST_STATUSES)
            elif week_type == "current":
                # If appointment is before "now", it might be completed
                if appt_date < reference_date:
                    status = random.choice(["completed", "completed", "no_show"])
                elif appt_date == reference_date:
                    status = random.choice(["scheduled", "confirmed", "in_progress"])
                else:
                    status = random.choice(["scheduled", "confirmed"])
            else:  # future
                status = random.choice(["scheduled", "scheduled", "confirmed"])

            appointments.append(
                {
                    "id": uuid4(),
                    "clinic_id": CLINIC_ID,
                    "patient_id": patient_id,
                    "professional_id": professional_id,
                    "cabinet": cabinet,
                    "start_time": start_time,
                    "end_time": end_time,
                    "treatment_type": treatment["name"],
                    "status": status,
                    "notes": None,
                    "color": treatment["color"],
                }
            )
            created += 1

    return appointments


# =============================================================================
# Odontogram Seed Data
# =============================================================================

# Fixed UUIDs for tooth records (for consistent references)
# Using format: e0eebc99-9c0b-4ef8-NNNN-6bb9bd380a00
TOOTH_RECORD_IDS = [
    UUID(f"e0eebc99-9c0b-4ef8-{i:04x}-6bb9bd380a00") for i in range(0xBB6D, 0xBB6D + 500)
]

TREATMENT_IDS = [
    UUID(f"f0eebc99-9c0b-4ef8-{i:04x}-6bb9bd380b00") for i in range(0xBB6D, 0xBB6D + 500)
]

# Permanent teeth numbers (FDI notation)
PERMANENT_TEETH = [
    18,
    17,
    16,
    15,
    14,
    13,
    12,
    11,  # Upper right
    21,
    22,
    23,
    24,
    25,
    26,
    27,
    28,  # Upper left
    38,
    37,
    36,
    35,
    34,
    33,
    32,
    31,  # Lower left
    41,
    42,
    43,
    44,
    45,
    46,
    47,
    48,  # Lower right
]

# Deciduous teeth numbers (for children)
DECIDUOUS_TEETH = [
    55,
    54,
    53,
    52,
    51,  # Upper right
    61,
    62,
    63,
    64,
    65,  # Upper left
    75,
    74,
    73,
    72,
    71,  # Lower left
    81,
    82,
    83,
    84,
    85,  # Lower right
]

SURFACES = ["M", "D", "O", "V", "L"]


def _is_child(patient_dob: date) -> bool:
    """Check if patient is a child (under 12 years old)."""
    age = (date.today() - patient_dob).days // 365
    return age < 12


def _get_patient_teeth(patient_dob: date) -> list[int]:
    """Get appropriate teeth for patient based on age."""
    if _is_child(patient_dob):
        return DECIDUOUS_TEETH
    return PERMANENT_TEETH


# Realistic odontogram scenarios for different patient profiles
ODONTOGRAM_PROFILES = {
    # Profiles for adults with different dental histories
    "healthy_adult": {
        "description": "Adult with good dental health",
        "tooth_conditions": {},  # All healthy
        "treatments": [],
    },
    "adult_with_fillings": {
        "description": "Adult with common fillings",
        "tooth_conditions": {},
        "treatments": [
            # Molars with composite fillings
            {"tooth": 16, "type": "filling_composite", "surfaces": ["O"], "status": "existing"},
            {
                "tooth": 26,
                "type": "filling_composite",
                "surfaces": ["M", "O"],
                "status": "existing",
            },
            {
                "tooth": 36,
                "type": "filling_composite",
                "surfaces": ["O", "D"],
                "status": "existing",
            },
            {"tooth": 46, "type": "filling_amalgam", "surfaces": ["O"], "status": "existing"},
            # Planned treatment
            {"tooth": 47, "type": "caries", "surfaces": ["O"], "status": "planned"},
        ],
    },
    "adult_with_crowns": {
        "description": "Adult with crowns and root canals",
        "tooth_conditions": {},
        "treatments": [
            # Root canal + crown
            {"tooth": 36, "type": "root_canal_full", "surfaces": None, "status": "existing"},
            {"tooth": 36, "type": "crown", "surfaces": None, "status": "existing"},
            # Another crown
            {"tooth": 46, "type": "crown", "surfaces": None, "status": "existing"},
            # Fillings
            {
                "tooth": 17,
                "type": "filling_composite",
                "surfaces": ["O", "D"],
                "status": "existing",
            },
            {
                "tooth": 27,
                "type": "filling_composite",
                "surfaces": ["M", "O"],
                "status": "existing",
            },
            # Planned crown
            {"tooth": 26, "type": "crown", "surfaces": None, "status": "planned"},
        ],
    },
    "adult_with_implant": {
        "description": "Adult with implant",
        "tooth_conditions": {
            36: "missing",  # Missing tooth replaced by implant
        },
        "treatments": [
            {"tooth": 36, "type": "implant", "surfaces": None, "status": "existing"},
            # Other treatments
            {"tooth": 16, "type": "filling_composite", "surfaces": ["O"], "status": "existing"},
            {
                "tooth": 26,
                "type": "filling_composite",
                "surfaces": ["M", "O"],
                "status": "existing",
            },
            {"tooth": 46, "type": "filling_amalgam", "surfaces": ["O", "D"], "status": "existing"},
        ],
    },
    "adult_with_bridge": {
        "description": "Adult with dental bridge",
        "tooth_conditions": {
            35: "missing",  # Pontic location
        },
        "treatments": [
            # Bridge: 34 abutment, 35 pontic, 36 abutment
            {"tooth": 34, "type": "bridge_abutment", "surfaces": None, "status": "existing"},
            {"tooth": 35, "type": "pontic", "surfaces": None, "status": "existing"},
            {"tooth": 36, "type": "bridge_abutment", "surfaces": None, "status": "existing"},
            # Other fillings
            {"tooth": 16, "type": "filling_composite", "surfaces": ["O"], "status": "existing"},
            {
                "tooth": 47,
                "type": "filling_composite",
                "surfaces": ["M", "O", "D"],
                "status": "existing",
            },
        ],
    },
    "adult_needs_work": {
        "description": "Adult needing multiple treatments",
        "tooth_conditions": {},
        "treatments": [
            # Existing treatments
            {"tooth": 16, "type": "filling_composite", "surfaces": ["O"], "status": "existing"},
            {"tooth": 36, "type": "filling_amalgam", "surfaces": ["O", "D"], "status": "existing"},
            # Multiple planned treatments
            {"tooth": 17, "type": "caries", "surfaces": ["O", "D"], "status": "planned"},
            {"tooth": 26, "type": "caries", "surfaces": ["M"], "status": "planned"},
            {"tooth": 37, "type": "crown", "surfaces": None, "status": "planned"},
            {"tooth": 46, "type": "root_canal_full", "surfaces": None, "status": "planned"},
        ],
    },
    "orthodontic_patient": {
        "description": "Patient with orthodontic treatment",
        "tooth_conditions": {},
        "treatments": [
            # Brackets on anterior teeth
            {"tooth": 13, "type": "bracket", "surfaces": None, "status": "existing"},
            {"tooth": 12, "type": "bracket", "surfaces": None, "status": "existing"},
            {"tooth": 11, "type": "bracket", "surfaces": None, "status": "existing"},
            {"tooth": 21, "type": "bracket", "surfaces": None, "status": "existing"},
            {"tooth": 22, "type": "bracket", "surfaces": None, "status": "existing"},
            {"tooth": 23, "type": "bracket", "surfaces": None, "status": "existing"},
            # Tubes on molars
            {"tooth": 16, "type": "tube", "surfaces": None, "status": "existing"},
            {"tooth": 26, "type": "tube", "surfaces": None, "status": "existing"},
            # Lower brackets
            {"tooth": 33, "type": "bracket", "surfaces": None, "status": "existing"},
            {"tooth": 32, "type": "bracket", "surfaces": None, "status": "existing"},
            {"tooth": 31, "type": "bracket", "surfaces": None, "status": "existing"},
            {"tooth": 41, "type": "bracket", "surfaces": None, "status": "existing"},
            {"tooth": 42, "type": "bracket", "surfaces": None, "status": "existing"},
            {"tooth": 43, "type": "bracket", "surfaces": None, "status": "existing"},
            # Displaced teeth markers
            {"tooth": 23, "type": "rotated", "surfaces": None, "status": "existing"},
            {"tooth": 13, "type": "displaced", "surfaces": None, "status": "existing"},
        ],
    },
    # Profiles for children
    "healthy_child": {
        "description": "Child with healthy deciduous teeth",
        "tooth_conditions": {},
        "treatments": [
            # Sealants on molars (preventive)
            {"tooth": 54, "type": "sealant", "surfaces": ["O"], "status": "existing"},
            {"tooth": 64, "type": "sealant", "surfaces": ["O"], "status": "existing"},
            {"tooth": 74, "type": "sealant", "surfaces": ["O"], "status": "existing"},
            {"tooth": 84, "type": "sealant", "surfaces": ["O"], "status": "existing"},
        ],
    },
    "child_with_caries": {
        "description": "Child with some caries and fillings",
        "tooth_conditions": {},
        "treatments": [
            # Existing fillings
            {"tooth": 54, "type": "filling_composite", "surfaces": ["O"], "status": "existing"},
            {
                "tooth": 74,
                "type": "filling_composite",
                "surfaces": ["O", "D"],
                "status": "existing",
            },
            # Planned treatments
            {"tooth": 64, "type": "caries", "surfaces": ["O"], "status": "planned"},
            {"tooth": 84, "type": "caries", "surfaces": ["M", "O"], "status": "planned"},
        ],
    },
}

# Patient ID to profile mapping (deterministic based on patient index)
PATIENT_ODONTOGRAM_MAPPING = [
    # Index 0-1: Children (PATIENT_IDS[0], PATIENT_IDS[1])
    "healthy_child",  # Pablo/Ethan - first visit
    "child_with_caries",  # Lucía/Olivia - orthodontic treatment in progress (has caries)
    # Index 2-14: Adults with various profiles
    "healthy_adult",  # Miguel/James - young adult, healthy
    "adult_with_fillings",  # Carmen/Emma - sensitivity, has fillings
    "adult_with_fillings",  # David/William - simple fillings
    "healthy_adult",  # Elena/Sophia - pregnant, minimal treatment
    "adult_with_crowns",  # Javier/Daniel - diabetic, has crowns
    "adult_with_fillings",  # Isabel/Mia - standard fillings
    "adult_needs_work",  # Francisco/Alexander - allergic, needs work
    "adult_with_crowns",  # Rosa/Charlotte - hypertensive, crowns
    "adult_with_bridge",  # Antonio/Robert - partial denture (bridge)
    "adult_with_implant",  # María Teresa/Patricia - has implants
    "adult_needs_work",  # José Luis/Richard - on blood thinners, needs work
    "adult_with_fillings",  # Dolores/Barbara - standard
    "adult_with_crowns",  # Manuel/Charles - complete denture adjustments
]


def generate_odontogram_data() -> dict:
    """Generate odontogram seed data for all patients.

    Returns:
        Dictionary with:
        - tooth_records: List of ToothRecord data
        - treatments: List of ToothTreatment data
    """
    tooth_records = []
    treatments = []
    patients_data = get_patients_data()

    tooth_record_idx = 0
    treatment_idx = 0

    for patient_idx, patient in enumerate(patients_data):
        patient_id = patient["id"]
        patient_dob = patient["date_of_birth"]

        # Get profile for this patient
        profile_name = PATIENT_ODONTOGRAM_MAPPING[patient_idx]
        profile = ODONTOGRAM_PROFILES[profile_name]

        # Get appropriate teeth based on age
        teeth = _get_patient_teeth(patient_dob)
        tooth_type = "deciduous" if _is_child(patient_dob) else "permanent"

        # Create tooth records for all teeth
        patient_tooth_records = {}  # tooth_number -> record
        for tooth_number in teeth:
            # Check if tooth has specific condition
            general_condition = profile["tooth_conditions"].get(tooth_number, "healthy")

            tooth_record_id = TOOTH_RECORD_IDS[tooth_record_idx]
            tooth_record_idx += 1

            record = {
                "id": tooth_record_id,
                "clinic_id": CLINIC_ID,
                "patient_id": patient_id,
                "tooth_number": tooth_number,
                "tooth_type": tooth_type,
                "general_condition": general_condition,
                "surfaces": {
                    "M": "healthy",
                    "D": "healthy",
                    "O": "healthy",
                    "V": "healthy",
                    "L": "healthy",
                },
                "notes": None,
                "is_displaced": False,
                "is_rotated": False,
                "displacement_notes": None,
            }

            tooth_records.append(record)
            patient_tooth_records[tooth_number] = record

        # Create treatments
        for treatment_data in profile["treatments"]:
            tooth_number = treatment_data["tooth"]

            # Skip if tooth doesn't exist for this patient (e.g., adult treatment for child)
            if tooth_number not in patient_tooth_records:
                continue

            tooth_record = patient_tooth_records[tooth_number]

            # Determine treatment category
            surface_treatments = {
                "caries",
                "incipient_caries",
                "pigmentation",
                "filling_composite",
                "filling_amalgam",
                "filling_temporary",
                "sealant",
                "veneer",
                "inlay",
            }
            treatment_category = (
                "surface" if treatment_data["type"] in surface_treatments else "whole_tooth"
            )

            treatment_id = TREATMENT_IDS[treatment_idx]
            treatment_idx += 1

            treatment = {
                "id": treatment_id,
                "clinic_id": CLINIC_ID,
                "patient_id": patient_id,
                "tooth_record_id": tooth_record["id"],
                "tooth_number": tooth_number,
                "treatment_type": treatment_data["type"],
                "treatment_category": treatment_category,
                "surfaces": treatment_data["surfaces"],
                "status": treatment_data["status"],
                "recorded_at": datetime.now() - timedelta(days=30),
                "performed_at": datetime.now() - timedelta(days=30)
                if treatment_data["status"] == "existing"
                else None,
                "performed_by": USER_DENTIST_ID if treatment_data["status"] == "existing" else None,
                "catalog_item_id": None,
                "budget_item_id": None,
                "source_module": "odontogram",
                "notes": None,
                "deleted_at": None,
            }

            treatments.append(treatment)

            # Update tooth record if treatment modifies markers
            if treatment_data["type"] == "rotated":
                tooth_record["is_rotated"] = True
            elif treatment_data["type"] == "displaced":
                tooth_record["is_displaced"] = True

    return {
        "tooth_records": tooth_records,
        "treatments": treatments,
    }
