"""Demo data definitions for DentalPin.

This module contains all the seed data used to populate a demo environment.
All UUIDs are fixed to allow consistent references and easier debugging.
"""

from datetime import date, datetime, timedelta
from uuid import UUID

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
# Clinic Configuration
# =============================================================================

CLINIC_DATA = {
    "id": CLINIC_ID,
    "name": "Clínica Dental Demo",
    "tax_id": "B12345678",
    "address": {
        "street": "Calle Gran Vía 123",
        "city": "Madrid",
        "postal_code": "28013",
        "country": "España",
    },
    "phone": "+34 912 345 678",
    "email": "info@demo.clinic",
    "settings": {
        "slot_duration_min": 30,
        "currency": "EUR",
        "timezone": "Europe/Madrid",
        "working_hours": {
            "monday": {"morning": ["09:00", "14:00"], "afternoon": ["16:00", "20:00"]},
            "tuesday": {"morning": ["09:00", "14:00"], "afternoon": ["16:00", "20:00"]},
            "wednesday": {"morning": ["09:00", "14:00"], "afternoon": ["16:00", "20:00"]},
            "thursday": {"morning": ["09:00", "14:00"], "afternoon": ["16:00", "20:00"]},
            "friday": {"morning": ["09:00", "14:00"], "afternoon": ["16:00", "20:00"]},
        },
    },
    "cabinets": [
        {"name": "Gabinete 1", "color": "#3B82F6"},
        {"name": "Gabinete 2", "color": "#10B981"},
    ],
}

# =============================================================================
# Users (all with password: demo1234)
# =============================================================================

USERS_DATA = [
    {
        "id": USER_ADMIN_ID,
        "email": "admin@demo.clinic",
        "first_name": "Admin",
        "last_name": "Demo",
        "role": "admin",
        "membership_id": MEMBERSHIP_ADMIN_ID,
    },
    {
        "id": USER_DENTIST_ID,
        "email": "dentist@demo.clinic",
        "first_name": "María",
        "last_name": "García López",
        "professional_id": "28/12345",  # Colegiado number
        "role": "dentist",
        "membership_id": MEMBERSHIP_DENTIST_ID,
    },
    {
        "id": USER_HYGIENIST_ID,
        "email": "hygienist@demo.clinic",
        "first_name": "Carlos",
        "last_name": "López Martínez",
        "professional_id": "28/54321",
        "role": "hygienist",
        "membership_id": MEMBERSHIP_HYGIENIST_ID,
    },
    {
        "id": USER_ASSISTANT_ID,
        "email": "assistant@demo.clinic",
        "first_name": "Ana",
        "last_name": "Martínez Ruiz",
        "role": "assistant",
        "membership_id": MEMBERSHIP_ASSISTANT_ID,
    },
    {
        "id": USER_RECEPTIONIST_ID,
        "email": "receptionist@demo.clinic",
        "first_name": "Laura",
        "last_name": "Sánchez Pérez",
        "role": "receptionist",
        "membership_id": MEMBERSHIP_RECEPTIONIST_ID,
    },
]

# =============================================================================
# Patients (15 patients with varied ages and data)
# =============================================================================

PATIENTS_DATA = [
    # Children/Teens
    {
        "id": PATIENT_IDS[0],
        "first_name": "Pablo",
        "last_name": "Fernández García",
        "phone": "+34 612 345 001",
        "email": None,
        "date_of_birth": date(2016, 3, 15),
        "notes": "Paciente pediátrico. Primera visita para revisión.",
    },
    {
        "id": PATIENT_IDS[1],
        "first_name": "Lucía",
        "last_name": "Rodríguez Sánchez",
        "phone": "+34 612 345 002",
        "email": "lucia.rodriguez@email.com",
        "date_of_birth": date(2010, 7, 22),
        "notes": "Tratamiento de ortodoncia en curso.",
    },
    # Young Adults
    {
        "id": PATIENT_IDS[2],
        "first_name": "Miguel",
        "last_name": "González Torres",
        "phone": "+34 612 345 003",
        "email": "miguel.gonzalez@email.com",
        "date_of_birth": date(1998, 11, 8),
        "notes": None,
    },
    {
        "id": PATIENT_IDS[3],
        "first_name": "Carmen",
        "last_name": "Díaz Moreno",
        "phone": "+34 612 345 004",
        "email": "carmen.diaz@email.com",
        "date_of_birth": date(1995, 5, 30),
        "notes": "Sensibilidad dental. Usar anestesia con precaución.",
    },
    {
        "id": PATIENT_IDS[4],
        "first_name": "David",
        "last_name": "Martín López",
        "phone": "+34 612 345 005",
        "email": None,
        "date_of_birth": date(1992, 2, 14),
        "notes": None,
    },
    # Adults
    {
        "id": PATIENT_IDS[5],
        "first_name": "Elena",
        "last_name": "Ruiz Hernández",
        "phone": "+34 612 345 006",
        "email": "elena.ruiz@email.com",
        "date_of_birth": date(1985, 9, 3),
        "notes": "Embarazada (tercer trimestre). Evitar radiografías.",
    },
    {
        "id": PATIENT_IDS[6],
        "first_name": "Javier",
        "last_name": "Sánchez Muñoz",
        "phone": "+34 612 345 007",
        "email": "javier.sanchez@email.com",
        "date_of_birth": date(1980, 12, 25),
        "notes": "Diabético tipo 2. Control de cicatrización.",
    },
    {
        "id": PATIENT_IDS[7],
        "first_name": "Isabel",
        "last_name": "López Navarro",
        "phone": "+34 612 345 008",
        "email": None,
        "date_of_birth": date(1978, 6, 17),
        "notes": None,
    },
    {
        "id": PATIENT_IDS[8],
        "first_name": "Francisco",
        "last_name": "García Romero",
        "phone": "+34 612 345 009",
        "email": "francisco.garcia@email.com",
        "date_of_birth": date(1975, 4, 9),
        "notes": "Alérgico a penicilina.",
    },
    {
        "id": PATIENT_IDS[9],
        "first_name": "Rosa",
        "last_name": "Martínez Jiménez",
        "phone": "+34 612 345 010",
        "email": "rosa.martinez@email.com",
        "date_of_birth": date(1970, 8, 21),
        "notes": "Hipertensa. Verificar presión antes de procedimientos.",
    },
    # Older Adults
    {
        "id": PATIENT_IDS[10],
        "first_name": "Antonio",
        "last_name": "Hernández Castro",
        "phone": "+34 612 345 011",
        "email": None,
        "date_of_birth": date(1960, 1, 5),
        "notes": "Prótesis parcial superior.",
    },
    {
        "id": PATIENT_IDS[11],
        "first_name": "María Teresa",
        "last_name": "Romero Vega",
        "phone": "+34 612 345 012",
        "email": None,
        "date_of_birth": date(1955, 10, 12),
        "notes": "Paciente con implantes. Revisión periódica.",
    },
    {
        "id": PATIENT_IDS[12],
        "first_name": "José Luis",
        "last_name": "Muñoz Blanco",
        "phone": "+34 612 345 013",
        "email": "joseluis.munoz@email.com",
        "date_of_birth": date(1950, 3, 28),
        "notes": "Toma anticoagulantes. Coordinar con médico antes de extracciones.",
    },
    {
        "id": PATIENT_IDS[13],
        "first_name": "Dolores",
        "last_name": "Vega Ortiz",
        "phone": "+34 612 345 014",
        "email": None,
        "date_of_birth": date(1948, 7, 7),
        "notes": None,
    },
    {
        "id": PATIENT_IDS[14],
        "first_name": "Manuel",
        "last_name": "Castro Delgado",
        "phone": "+34 612 345 015",
        "email": None,
        "date_of_birth": date(1945, 11, 19),
        "notes": "Prótesis completa. Necesita ajustes frecuentes.",
    },
]

# =============================================================================
# Appointment Templates
# =============================================================================

# Treatment types with typical durations (in minutes)
TREATMENT_TYPES = [
    {"name": "Revisión", "duration": 30, "color": "#3B82F6"},
    {"name": "Limpieza dental", "duration": 45, "color": "#10B981"},
    {"name": "Empaste", "duration": 45, "color": "#F59E0B"},
    {"name": "Extracción", "duration": 60, "color": "#EF4444"},
    {"name": "Endodoncia", "duration": 90, "color": "#8B5CF6"},
    {"name": "Ortodoncia - Revisión", "duration": 30, "color": "#EC4899"},
    {"name": "Blanqueamiento", "duration": 60, "color": "#06B6D4"},
    {"name": "Implante - Consulta", "duration": 45, "color": "#84CC16"},
    {"name": "Urgencia", "duration": 30, "color": "#DC2626"},
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
    appointment_counter = 0

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
    cabinets = ["Gabinete 1", "Gabinete 2"]

    for week_type, week_start in weeks:
        # Determine number of appointments for this week
        if week_type == "past":
            num_appointments = random.randint(10, 12)
        elif week_type == "current":
            num_appointments = random.randint(15, 18)
        else:  # future
            num_appointments = random.randint(10, 12)

        # Generate appointments distributed across weekdays
        for _ in range(num_appointments):
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

            # Pick treatment type
            treatment = random.choice(TREATMENT_TYPES)
            end_time = start_time + timedelta(minutes=treatment["duration"])

            # Pick professional and cabinet
            professional_id = random.choice(professionals)
            cabinet = random.choice(cabinets)

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
            appointment_counter += 1

    return appointments
