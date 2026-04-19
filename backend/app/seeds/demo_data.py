"""Demo data definitions for DentalPin.

This module contains all the seed data used to populate a demo environment.
All UUIDs are fixed to allow consistent references and easier debugging.

Supports bilingual data (English and Spanish) via LANG setting.
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
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
# emergency_contact: {name, relationship, phone, email, is_legal_guardian}
# medical_history: {allergies[], is_pregnant, pregnancy_week, is_lactating,
#                   is_on_anticoagulants, anticoagulant_medication, inr_value,
#                   adverse_reactions_to_anesthesia, anesthesia_reaction_details,
#                   systemic_diseases[]}
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
        "emergency_contact": {
            "es": {
                "name": "Carlos Fernández",
                "relationship": "Padre",
                "phone": "+34 612 345 100",
                "email": "carlos.fernandez@email.com",
                "is_legal_guardian": True,
            },
            "en": {
                "name": "John Miller",
                "relationship": "Father",
                "phone": "+1 (212) 555-0100",
                "email": "john.miller@email.com",
                "is_legal_guardian": True,
            },
        },
        "medical_history": {
            "allergies": [],
            "systemic_diseases": [],
        },
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
        "emergency_contact": {
            "es": {
                "name": "María Sánchez",
                "relationship": "Madre",
                "phone": "+34 612 345 101",
                "email": "maria.sanchez@email.com",
                "is_legal_guardian": True,
            },
            "en": {
                "name": "Sarah Wilson",
                "relationship": "Mother",
                "phone": "+1 (212) 555-0101",
                "email": "sarah.wilson@email.com",
                "is_legal_guardian": True,
            },
        },
        "medical_history": {
            "allergies": [],
            "systemic_diseases": [],
        },
    },
    # Young Adults
    {
        "id": PATIENT_IDS[2],
        "es": {"first_name": "Miguel", "last_name": "González Torres", "notes": None},
        "en": {"first_name": "James", "last_name": "Anderson", "notes": None},
        "phone": {"es": "+34 612 345 003", "en": "+1 (212) 555-0003"},
        "email": {"es": "miguel.gonzalez@email.com", "en": "james.anderson@email.com"},
        "date_of_birth": date(1998, 11, 8),
        "emergency_contact": {
            "es": {
                "name": "Laura González",
                "relationship": "Hermana",
                "phone": "+34 612 345 102",
                "email": None,
                "is_legal_guardian": False,
            },
            "en": {
                "name": "Laura Anderson",
                "relationship": "Sister",
                "phone": "+1 (212) 555-0102",
                "email": None,
                "is_legal_guardian": False,
            },
        },
        "medical_history": {
            "allergies": [],
            "systemic_diseases": [],
        },
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
        "emergency_contact": {
            "es": {
                "name": "Pedro Díaz",
                "relationship": "Esposo",
                "phone": "+34 612 345 103",
                "email": "pedro.diaz@email.com",
                "is_legal_guardian": False,
            },
            "en": {
                "name": "Peter Taylor",
                "relationship": "Husband",
                "phone": "+1 (212) 555-0103",
                "email": "peter.taylor@email.com",
                "is_legal_guardian": False,
            },
        },
        "medical_history": {
            "allergies": [
                {
                    "name": {"es": "Látex", "en": "Latex"},
                    "severity": "medium",
                    "reaction": {"es": "Irritación cutánea", "en": "Skin irritation"},
                },
            ],
            "adverse_reactions_to_anesthesia": True,
            "anesthesia_reaction_details": {
                "es": "Mareos y náuseas post-anestesia",
                "en": "Dizziness and nausea post-anesthesia",
            },
            "systemic_diseases": [],
        },
    },
    {
        "id": PATIENT_IDS[4],
        "es": {"first_name": "David", "last_name": "Martín López", "notes": None},
        "en": {"first_name": "William", "last_name": "Thomas", "notes": None},
        "phone": {"es": "+34 612 345 005", "en": "+1 (212) 555-0005"},
        "email": None,
        "date_of_birth": date(1992, 2, 14),
        "emergency_contact": None,
        "medical_history": {
            "allergies": [],
            "systemic_diseases": [],
        },
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
        "emergency_contact": {
            "es": {
                "name": "Andrés Ruiz",
                "relationship": "Esposo",
                "phone": "+34 612 345 104",
                "email": "andres.ruiz@email.com",
                "is_legal_guardian": False,
            },
            "en": {
                "name": "Andrew Martinez",
                "relationship": "Husband",
                "phone": "+1 (212) 555-0104",
                "email": "andrew.martinez@email.com",
                "is_legal_guardian": False,
            },
        },
        "medical_history": {
            "allergies": [],
            "is_pregnant": True,
            "pregnancy_week": 32,
            "systemic_diseases": [],
        },
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
        "emergency_contact": {
            "es": {
                "name": "Ana Muñoz",
                "relationship": "Esposa",
                "phone": "+34 612 345 105",
                "email": "ana.munoz@email.com",
                "is_legal_guardian": False,
            },
            "en": {
                "name": "Anna Garcia",
                "relationship": "Wife",
                "phone": "+1 (212) 555-0105",
                "email": "anna.garcia@email.com",
                "is_legal_guardian": False,
            },
        },
        "medical_history": {
            "allergies": [],
            "systemic_diseases": [
                {
                    "name": {"es": "Diabetes Mellitus Tipo 2", "en": "Type 2 Diabetes Mellitus"},
                    "is_critical": True,
                    "notes": {
                        "es": "Controlada con metformina. HbA1c: 7.2%",
                        "en": "Controlled with metformin. HbA1c: 7.2%",
                    },
                },
            ],
        },
    },
    {
        "id": PATIENT_IDS[7],
        "es": {"first_name": "Isabel", "last_name": "López Navarro", "notes": None},
        "en": {"first_name": "Mia", "last_name": "Robinson", "notes": None},
        "phone": {"es": "+34 612 345 008", "en": "+1 (212) 555-0008"},
        "email": None,
        "date_of_birth": date(1978, 6, 17),
        "emergency_contact": {
            "es": {
                "name": "Roberto López",
                "relationship": "Hermano",
                "phone": "+34 612 345 106",
                "email": None,
                "is_legal_guardian": False,
            },
            "en": {
                "name": "Robert Robinson",
                "relationship": "Brother",
                "phone": "+1 (212) 555-0106",
                "email": None,
                "is_legal_guardian": False,
            },
        },
        "medical_history": {
            "allergies": [],
            "is_lactating": True,
            "systemic_diseases": [],
        },
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
        "emergency_contact": {
            "es": {
                "name": "Marta Romero",
                "relationship": "Esposa",
                "phone": "+34 612 345 107",
                "email": "marta.romero@email.com",
                "is_legal_guardian": False,
            },
            "en": {
                "name": "Martha Clark",
                "relationship": "Wife",
                "phone": "+1 (212) 555-0107",
                "email": "martha.clark@email.com",
                "is_legal_guardian": False,
            },
        },
        "medical_history": {
            "allergies": [
                {
                    "name": {"es": "Penicilina", "en": "Penicillin"},
                    "severity": "critical",
                    "reaction": {"es": "Anafilaxia", "en": "Anaphylaxis"},
                },
                {
                    "name": {"es": "Amoxicilina", "en": "Amoxicillin"},
                    "severity": "high",
                    "reaction": {"es": "Urticaria severa", "en": "Severe urticaria"},
                },
            ],
            "systemic_diseases": [],
        },
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
        "emergency_contact": {
            "es": {
                "name": "Luis Jiménez",
                "relationship": "Esposo",
                "phone": "+34 612 345 108",
                "email": None,
                "is_legal_guardian": False,
            },
            "en": {
                "name": "Louis Lewis",
                "relationship": "Husband",
                "phone": "+1 (212) 555-0108",
                "email": None,
                "is_legal_guardian": False,
            },
        },
        "medical_history": {
            "allergies": [],
            "systemic_diseases": [
                {
                    "name": {"es": "Hipertensión Arterial", "en": "Arterial Hypertension"},
                    "is_critical": True,
                    "notes": {
                        "es": "Tratamiento con enalapril 10mg/día. PA habitual: 130/85",
                        "en": "Treatment with enalapril 10mg/day. Usual BP: 130/85",
                    },
                },
            ],
        },
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
        "emergency_contact": {
            "es": {
                "name": "Carmen Castro",
                "relationship": "Hija",
                "phone": "+34 612 345 109",
                "email": "carmen.castro@email.com",
                "is_legal_guardian": False,
            },
            "en": {
                "name": "Carmen Walker",
                "relationship": "Daughter",
                "phone": "+1 (212) 555-0109",
                "email": "carmen.walker@email.com",
                "is_legal_guardian": False,
            },
        },
        "medical_history": {
            "allergies": [
                {
                    "name": {"es": "Yodo", "en": "Iodine"},
                    "severity": "medium",
                    "reaction": {"es": "Erupción cutánea", "en": "Skin rash"},
                },
            ],
            "systemic_diseases": [
                {
                    "name": {"es": "Artrosis", "en": "Osteoarthritis"},
                    "is_critical": False,
                    "notes": {"es": "Afecta movilidad cervical", "en": "Affects cervical mobility"},
                },
            ],
        },
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
        "emergency_contact": {
            "es": {
                "name": "Fernando Vega",
                "relationship": "Hijo",
                "phone": "+34 612 345 110",
                "email": "fernando.vega@email.com",
                "is_legal_guardian": False,
            },
            "en": {
                "name": "Fernando Hall",
                "relationship": "Son",
                "phone": "+1 (212) 555-0110",
                "email": "fernando.hall@email.com",
                "is_legal_guardian": False,
            },
        },
        "medical_history": {
            "allergies": [],
            "systemic_diseases": [
                {
                    "name": {"es": "Osteoporosis", "en": "Osteoporosis"},
                    "is_critical": False,
                    "notes": {
                        "es": "Tratamiento con bisfosfonatos. Precaución con extracciones.",
                        "en": "Treatment with bisphosphonates. Caution with extractions.",
                    },
                },
            ],
        },
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
        "emergency_contact": {
            "es": {
                "name": "Pilar Blanco",
                "relationship": "Esposa",
                "phone": "+34 612 345 111",
                "email": None,
                "is_legal_guardian": False,
            },
            "en": {
                "name": "Patricia Allen",
                "relationship": "Wife",
                "phone": "+1 (212) 555-0111",
                "email": None,
                "is_legal_guardian": False,
            },
        },
        "medical_history": {
            "allergies": [],
            "is_on_anticoagulants": True,
            "anticoagulant_medication": "Sintrom (Acenocumarol)",
            "inr_value": 2.5,
            "systemic_diseases": [
                {
                    "name": {"es": "Fibrilación Auricular", "en": "Atrial Fibrillation"},
                    "is_critical": True,
                    "notes": {
                        "es": "Anticoagulado. Requiere control INR antes de procedimientos.",
                        "en": "Anticoagulated. Requires INR control before procedures.",
                    },
                },
            ],
        },
    },
    {
        "id": PATIENT_IDS[13],
        "es": {"first_name": "Dolores", "last_name": "Vega Ortiz", "notes": None},
        "en": {"first_name": "Barbara", "last_name": "Young", "notes": None},
        "phone": {"es": "+34 612 345 014", "en": "+1 (212) 555-0014"},
        "email": None,
        "date_of_birth": date(1948, 7, 7),
        "emergency_contact": {
            "es": {
                "name": "Jorge Vega",
                "relationship": "Hijo",
                "phone": "+34 612 345 112",
                "email": "jorge.vega@email.com",
                "is_legal_guardian": False,
            },
            "en": {
                "name": "George Young",
                "relationship": "Son",
                "phone": "+1 (212) 555-0112",
                "email": "george.young@email.com",
                "is_legal_guardian": False,
            },
        },
        "medical_history": {
            "allergies": [],
            "systemic_diseases": [],
        },
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
        "emergency_contact": {
            "es": {
                "name": "Teresa Delgado",
                "relationship": "Hija",
                "phone": "+34 612 345 113",
                "email": "teresa.delgado@email.com",
                "is_legal_guardian": False,
            },
            "en": {
                "name": "Teresa King",
                "relationship": "Daughter",
                "phone": "+1 (212) 555-0113",
                "email": "teresa.king@email.com",
                "is_legal_guardian": False,
            },
        },
        "medical_history": {
            "allergies": [
                {
                    "name": {"es": "AINEs", "en": "NSAIDs"},
                    "severity": "high",
                    "reaction": {
                        "es": "Problemas gástricos severos",
                        "en": "Severe gastric problems",
                    },
                },
            ],
            "systemic_diseases": [
                {
                    "name": {"es": "Insuficiencia Renal Crónica", "en": "Chronic Kidney Disease"},
                    "is_critical": True,
                    "notes": {
                        "es": "Estadio 3. Ajustar dosis de medicamentos.",
                        "en": "Stage 3. Adjust medication doses.",
                    },
                },
                {
                    "name": {"es": "Diabetes Mellitus Tipo 2", "en": "Type 2 Diabetes Mellitus"},
                    "is_critical": True,
                    "notes": {"es": "Insulinodependiente", "en": "Insulin-dependent"},
                },
            ],
        },
    },
]


def _translate_medical_history(mh: dict | None) -> dict | None:
    """Translate medical history fields that have language variants."""
    if not mh:
        return None

    result = {}

    # Copy simple fields
    for key in [
        "is_pregnant",
        "pregnancy_week",
        "is_lactating",
        "is_on_anticoagulants",
        "anticoagulant_medication",
        "inr_value",
        "adverse_reactions_to_anesthesia",
    ]:
        if key in mh:
            result[key] = mh[key]

    # Translate anesthesia_reaction_details
    if "anesthesia_reaction_details" in mh:
        details = mh["anesthesia_reaction_details"]
        result["anesthesia_reaction_details"] = t(details) if isinstance(details, dict) else details

    # Translate allergies
    if "allergies" in mh:
        result["allergies"] = []
        for allergy in mh["allergies"]:
            translated = {
                "name": t(allergy["name"])
                if isinstance(allergy["name"], dict)
                else allergy["name"],
                "severity": allergy["severity"],
            }
            if "reaction" in allergy:
                reaction = allergy["reaction"]
                translated["reaction"] = t(reaction) if isinstance(reaction, dict) else reaction
            result["allergies"].append(translated)

    # Translate systemic_diseases
    if "systemic_diseases" in mh:
        result["systemic_diseases"] = []
        for disease in mh["systemic_diseases"]:
            translated = {
                "name": t(disease["name"])
                if isinstance(disease["name"], dict)
                else disease["name"],
                "is_critical": disease.get("is_critical", False),
            }
            if "notes" in disease:
                notes = disease["notes"]
                translated["notes"] = t(notes) if isinstance(notes, dict) else notes
            result["systemic_diseases"].append(translated)

    return result


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

        # Handle emergency_contact: dict with language keys or None
        emergency_contact = p.get("emergency_contact")
        if isinstance(emergency_contact, dict) and LANG in emergency_contact:
            emergency_contact = emergency_contact[LANG]

        # Handle medical_history: translate nested fields
        medical_history = _translate_medical_history(p.get("medical_history"))

        patient = {
            "id": p["id"],
            "first_name": p[LANG]["first_name"],
            "last_name": p[LANG]["last_name"],
            "phone": phone,
            "email": email,
            "date_of_birth": p["date_of_birth"],
            "notes": p[LANG]["notes"],
            "emergency_contact": emergency_contact,
            "medical_history": medical_history,
        }
        patients.append(patient)
    return patients


# =============================================================================
# Scheduling helpers
# =============================================================================

# Time slots (morning and afternoon) used by the appointment generator.
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
def _single(
    clinical_type: str, tooth: int, *, surfaces: list[str] | None = None, status: str = "performed"
) -> dict:
    """Shortcut for single-tooth Treatment dicts in ODONTOGRAM_PROFILES."""
    return {
        "clinical_type": clinical_type,
        "status": status,
        "teeth": [{"tooth": tooth, "role": None, "surfaces": surfaces}],
    }


ODONTOGRAM_PROFILES = {
    # Each profile holds:
    #   tooth_conditions: {tooth_number: condition} — applied to ToothRecord.general_condition.
    #   treatments: list of {clinical_type, status, teeth: [{tooth, role, surfaces}]}.
    "healthy_adult": {
        "description": "Adult with good dental health",
        "tooth_conditions": {},
        "treatments": [],
    },
    "adult_with_fillings": {
        "description": "Adult with common fillings",
        "tooth_conditions": {},
        "treatments": [
            _single("filling_composite", 16, surfaces=["O"]),
            _single("filling_composite", 26, surfaces=["M", "O"]),
            _single("filling_composite", 36, surfaces=["O", "D"]),
            _single("filling_amalgam", 46, surfaces=["O"]),
            _single("filling_composite", 47, surfaces=["O"], status="planned"),
        ],
    },
    "adult_with_crowns": {
        "description": "Adult with crowns and root canals",
        "tooth_conditions": {},
        "treatments": [
            _single("root_canal_full", 36),
            _single("crown", 36),
            _single("crown", 46),
            _single("filling_composite", 17, surfaces=["O", "D"]),
            _single("filling_composite", 27, surfaces=["M", "O"]),
            _single("crown", 26, status="planned"),
        ],
    },
    "adult_with_implant": {
        "description": "Adult with implant",
        "tooth_conditions": {36: "missing"},
        "treatments": [
            _single("implant", 36),
            _single("filling_composite", 16, surfaces=["O"]),
            _single("filling_composite", 26, surfaces=["M", "O"]),
            _single("filling_amalgam", 46, surfaces=["O", "D"]),
        ],
    },
    "adult_with_bridge": {
        "description": "Adult with dental bridge 34-35-36",
        "tooth_conditions": {35: "missing"},
        "treatments": [
            {
                "clinical_type": "bridge",
                "status": "performed",
                "teeth": [
                    {"tooth": 34, "role": "pillar", "surfaces": None},
                    {"tooth": 35, "role": "pontic", "surfaces": None},
                    {"tooth": 36, "role": "pillar", "surfaces": None},
                ],
            },
            _single("filling_composite", 16, surfaces=["O"]),
            _single("filling_composite", 47, surfaces=["M", "O", "D"]),
        ],
    },
    "adult_needs_work": {
        "description": "Adult needing multiple treatments",
        "tooth_conditions": {},
        "treatments": [
            _single("filling_composite", 16, surfaces=["O"]),
            _single("filling_amalgam", 36, surfaces=["O", "D"]),
            _single("filling_composite", 17, surfaces=["O", "D"], status="planned"),
            _single("filling_composite", 26, surfaces=["M"], status="planned"),
            _single("crown", 37, status="planned"),
            _single("root_canal_full", 46, status="planned"),
        ],
    },
    "orthodontic_patient": {
        "description": "Patient with orthodontic treatment",
        "tooth_conditions": {},
        "treatments": [
            _single("bracket", 13),
            _single("bracket", 12),
            _single("bracket", 11),
            _single("bracket", 21),
            _single("bracket", 22),
            _single("bracket", 23),
            _single("tube", 16),
            _single("tube", 26),
            _single("bracket", 33),
            _single("bracket", 32),
            _single("bracket", 31),
            _single("bracket", 41),
            _single("bracket", 42),
            _single("bracket", 43),
        ],
        # Positional flags are handled via tooth_conditions — no need to emit
        # pseudo-treatments for 'rotated'/'displaced'.
        "positional": {23: {"is_rotated": True}, 13: {"is_displaced": True}},
    },
    "healthy_child": {
        "description": "Child with healthy deciduous teeth",
        "tooth_conditions": {},
        "treatments": [
            _single("sealant", 54, surfaces=["O"]),
            _single("sealant", 64, surfaces=["O"]),
            _single("sealant", 74, surfaces=["O"]),
            _single("sealant", 84, surfaces=["O"]),
        ],
    },
    "child_with_caries": {
        "description": "Child with fillings and planned restorations",
        "tooth_conditions": {},
        "treatments": [
            _single("filling_composite", 54, surfaces=["O"]),
            _single("filling_composite", 74, surfaces=["O", "D"]),
            _single("filling_composite", 64, surfaces=["O"], status="planned"),
            _single("filling_composite", 84, surfaces=["M", "O"], status="planned"),
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
        - treatments: List of Treatment headers
        - treatment_teeth: List of TreatmentTooth children
    """
    tooth_records = []
    treatments = []
    treatment_teeth = []
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
        # Apply explicit positional flags if the profile sets them.
        for tooth_num, flags in profile.get("positional", {}).items():
            rec = patient_tooth_records.get(tooth_num)
            if rec:
                rec.update(flags)

        for treatment_def in profile["treatments"]:
            # Skip treatments whose teeth don't exist for this patient.
            teeth_defs = treatment_def["teeth"]
            if any(t["tooth"] not in patient_tooth_records for t in teeth_defs):
                continue

            treatment_id = TREATMENT_IDS[treatment_idx]
            treatment_idx += 1

            status = treatment_def["status"]
            recorded_at = datetime.now() - timedelta(days=30)
            performed_at = recorded_at if status == "performed" else None

            treatments.append(
                {
                    "id": treatment_id,
                    "clinic_id": CLINIC_ID,
                    "patient_id": patient_id,
                    "clinical_type": treatment_def["clinical_type"],
                    "catalog_item_id": None,
                    "status": status,
                    "recorded_at": recorded_at,
                    "performed_at": performed_at,
                    "performed_by": USER_DENTIST_ID if status == "performed" else None,
                    "price_snapshot": None,
                    "currency_snapshot": None,
                    "duration_snapshot": None,
                    "vat_rate_snapshot": None,
                    "budget_item_id": None,
                    "notes": None,
                    "source_module": "odontogram",
                    "deleted_at": None,
                }
            )

            for t in teeth_defs:
                treatment_teeth.append(
                    {
                        "treatment_id": treatment_id,
                        "tooth_record_id": patient_tooth_records[t["tooth"]]["id"],
                        "tooth_number": t["tooth"],
                        "role": t.get("role"),
                        "surfaces": t.get("surfaces"),
                    }
                )

    return {
        "tooth_records": tooth_records,
        "treatments": treatments,
        "treatment_teeth": treatment_teeth,
    }


# =============================================================================
# Patient Journey Data — single source of truth for plan/budget/appointment/invoice
# =============================================================================

# Fixed UUID pools for clinical journey entities.
TREATMENT_PLAN_IDS = [UUID(f"fe00bc99-9c0b-4ef8-bb6d-6bb9bd380{i:03x}") for i in range(20)]
PLAN_TREATMENT_IDS = [UUID(f"fa00bc99-9c0b-4ef8-bb6d-6bb9bd381{i:03x}") for i in range(200)]
PLANNED_ITEM_IDS = [UUID(f"ff00bc99-9c0b-4ef8-bb6d-6bb9bd380{i:03x}") for i in range(200)]

BUDGET_IDS = [UUID(f"aa00bc99-9c0b-4ef8-bb6d-6bb9bd380b{i:02x}") for i in range(10)]
BUDGET_ITEM_IDS = [UUID(f"bb00bc99-9c0b-4ef8-bb6d-6bb9bd380c{i:02x}") for i in range(50)]
BUDGET_SIGNATURE_IDS = [UUID(f"cc00bc99-9c0b-4ef8-bb6d-6bb9bd380d{i:02x}") for i in range(10)]

INVOICE_SERIES_IDS = [UUID(f"fa00bc99-9c0b-4ef8-bb6d-6bb9bd380e{i:02x}") for i in range(5)]
INVOICE_IDS = [UUID(f"fb00bc99-9c0b-4ef8-bb6d-6bb9bd380f{i:02x}") for i in range(20)]
INVOICE_ITEM_IDS = [UUID(f"fc00bc99-9c0b-4ef8-bb6d-6bb9bd380{i:03x}") for i in range(100)]
PAYMENT_IDS = [UUID(f"fd00bc99-9c0b-4ef8-bb6d-6bb9bd380{i:03x}") for i in range(30)]


# Appointment visuals + duration by catalog_code prefix. Ordered most-specific first.
_APPT_LOOK_BY_PREFIX: list[tuple[str, dict]] = [
    ("DX-VISIT", {"name": {"es": "Revisión", "en": "Checkup"}, "duration": 30, "color": "#3B82F6"}),
    ("DX-RX", {"name": {"es": "Radiografía", "en": "X-ray"}, "duration": 30, "color": "#60A5FA"}),
    ("DX", {"name": {"es": "Diagnóstico", "en": "Diagnosis"}, "duration": 30, "color": "#3B82F6"}),
    (
        "PREV",
        {
            "name": {"es": "Limpieza dental", "en": "Dental cleaning"},
            "duration": 45,
            "color": "#10B981",
        },
    ),
    ("REST-CROWN", {"name": {"es": "Corona", "en": "Crown"}, "duration": 60, "color": "#A855F7"}),
    ("REST-VEN", {"name": {"es": "Carilla", "en": "Veneer"}, "duration": 60, "color": "#F472B6"}),
    ("REST-COMP", {"name": {"es": "Empaste", "en": "Filling"}, "duration": 45, "color": "#F59E0B"}),
    (
        "REST",
        {"name": {"es": "Restauración", "en": "Restoration"}, "duration": 45, "color": "#F59E0B"},
    ),
    (
        "SURG-EXT",
        {"name": {"es": "Extracción", "en": "Extraction"}, "duration": 60, "color": "#EF4444"},
    ),
    ("SURG", {"name": {"es": "Cirugía", "en": "Surgery"}, "duration": 60, "color": "#DC2626"}),
    (
        "ENDO-MULTI",
        {
            "name": {"es": "Endodoncia multirradicular", "en": "Multi-root canal"},
            "duration": 90,
            "color": "#8B5CF6",
        },
    ),
    (
        "ENDO",
        {"name": {"es": "Endodoncia", "en": "Root canal"}, "duration": 75, "color": "#8B5CF6"},
    ),
    (
        "PERIO",
        {"name": {"es": "Periodoncia", "en": "Periodontics"}, "duration": 60, "color": "#14B8A6"},
    ),
    (
        "EST-BLAN",
        {"name": {"es": "Blanqueamiento", "en": "Whitening"}, "duration": 60, "color": "#06B6D4"},
    ),
    ("EST", {"name": {"es": "Estética", "en": "Aesthetics"}, "duration": 45, "color": "#06B6D4"}),
    ("PROT", {"name": {"es": "Prótesis", "en": "Prosthesis"}, "duration": 90, "color": "#84CC16"}),
]


def _appt_look_for(code: str) -> dict:
    """Map a catalog internal_code to its display (name/duration/color) for appointments."""
    for prefix, meta in _APPT_LOOK_BY_PREFIX:
        if code.startswith(prefix):
            return meta
    return {"name": {"es": "Tratamiento", "en": "Treatment"}, "duration": 45, "color": "#64748B"}


# PATIENT_JOURNEYS: one entry per patient captures the full clinical narrative.
#
#   plan.items       : the items the patient needs. Both the budget and the appointments
#                      draw from this list (by index). Mark "completed": True for items
#                      already performed — this flips the backing Treatment to performed
#                      and the PlannedTreatmentItem to completed.
#   budget (opt.)    : financial materialization of the plan. items are 1-to-1 with
#                      plan.items and snap each item's unit_price / vat from catalog.
#   appointments     : 2-3 per patient. `covers` holds plan.items indexes this visit
#                      performs. `week` is past/current/future relative to "today".
#   invoice (opt.)   : bills a subset of budget items. `covers` lists the budget-item
#                      indexes (= plan-item indexes) this invoice invoices.
PATIENT_JOURNEYS = [
    # Patient 0 — Pablo / Ethan (pediatric, first visit)
    {
        "patient_idx": 0,
        "plan": {
            "id_idx": 0,
            "status": "active",
            "title": {"es": "Plan preventivo infantil", "en": "Pediatric preventive plan"},
            "diagnosis_notes": {
                "es": "Primera visita. Revisión pediátrica.",
                "en": "First visit. Pediatric checkup.",
            },
            "items": [
                {"catalog_code": "DX-VISIT", "is_global": True},
                {"catalog_code": "PREV-CLEAN", "is_global": True},
                {"catalog_code": "REST-COMP", "tooth": 54, "is_global": False},
            ],
        },
        "appointments": [
            {"week": "past", "covers": [0], "status": "completed"},
            {"week": "current", "covers": [1], "status": "confirmed"},
            {"week": "future", "covers": [2], "status": "scheduled"},
        ],
    },
    # Patient 1 — Lucía / Olivia (ortho + caries in deciduous molars)
    {
        "patient_idx": 1,
        "plan": {
            "id_idx": 1,
            "status": "active",
            "title": {"es": "Tratamiento conservador", "en": "Conservative treatment"},
            "diagnosis_notes": {
                "es": "Caries en molares inferiores deciduos.",
                "en": "Caries on lower deciduous molars.",
            },
            "items": [
                {"catalog_code": "DX-VISIT", "is_global": True},
                {"catalog_code": "REST-COMP", "tooth": 74, "is_global": False},
                {"catalog_code": "REST-COMP", "tooth": 84, "is_global": False},
            ],
        },
        "appointments": [
            {"week": "past", "covers": [0], "status": "completed"},
            {"week": "current", "covers": [1], "status": "confirmed"},
            {"week": "future", "covers": [2], "status": "scheduled"},
        ],
    },
    # Patient 2 — Miguel / James (young adult; draft plan + draft budget + draft invoice)
    {
        "patient_idx": 2,
        "plan": {
            "id_idx": 2,
            "status": "draft",
            "title": {"es": "Revisión y limpieza", "en": "Checkup and cleaning"},
            "diagnosis_notes": {
                "es": "Paciente joven, buen estado general.",
                "en": "Young patient, good general condition.",
            },
            "items": [
                {"catalog_code": "DX-VISIT", "is_global": True},
                {"catalog_code": "PREV-CLEAN", "is_global": True},
            ],
        },
        "budget": {
            "id_idx": 0,
            "status": "draft",
            "global_discount": None,
            "signature": False,
            "notes": {"es": "Borrador pendiente de revisión", "en": "Draft pending review"},
        },
        "appointments": [
            {"week": "future", "covers": [0], "status": "scheduled"},
            {"week": "future", "covers": [1], "status": "scheduled"},
        ],
        "invoice": {
            "id_idx": 0,
            "status": "draft",
            "payments": [],
            "covers": [0, 1],
            "notes": {"es": "Borrador - pendiente de emitir", "en": "Draft - pending issuance"},
        },
    },
    # Patient 3 — Carmen / Emma (sensitivity; draft budget + issued invoice for done items)
    {
        "patient_idx": 3,
        "plan": {
            "id_idx": 3,
            "status": "draft",
            "title": {"es": "Plan de tratamiento inicial", "en": "Initial treatment plan"},
            "diagnosis_notes": {
                "es": "Paciente con sensibilidad dental. Requiere empaste en molar.",
                "en": "Patient with dental sensitivity. Requires filling on molar.",
            },
            "items": [
                {"catalog_code": "DX-VISIT", "is_global": True, "completed": True},
                {"catalog_code": "DX-RXPAN", "is_global": True, "completed": True},
                {"catalog_code": "REST-COMP", "tooth": 16, "is_global": False},
            ],
        },
        "budget": {
            "id_idx": 1,
            "status": "draft",
            "global_discount": None,
            "signature": False,
            "notes": {
                "es": "Presupuesto pendiente de aceptación",
                "en": "Budget pending acceptance",
            },
        },
        "appointments": [
            {"week": "past", "covers": [0, 1], "status": "completed"},
            {"week": "future", "covers": [2], "status": "scheduled"},
        ],
        "invoice": {
            "id_idx": 1,
            "status": "issued",
            "payments": [],
            "covers": [0, 1],
            "notes": {"es": "Emitida - pendiente de pago", "en": "Issued - pending payment"},
        },
    },
    # Patient 4 — David / William (aesthetic; draft budget, no invoice yet)
    {
        "patient_idx": 4,
        "plan": {
            "id_idx": 4,
            "status": "active",
            "title": {"es": "Plan estético", "en": "Aesthetic plan"},
            "diagnosis_notes": {
                "es": "Paciente interesado en blanqueamiento.",
                "en": "Patient interested in whitening.",
            },
            "items": [
                {"catalog_code": "DX-VISIT", "is_global": True, "completed": True},
                {"catalog_code": "PREV-CLEAN", "is_global": True},
                {"catalog_code": "EST-BLAN-CLIN", "is_global": True},
            ],
        },
        "budget": {
            "id_idx": 2,
            "status": "draft",
            "global_discount": {"type": "percentage", "value": 5},
            "signature": False,
            "notes": {"es": "Pendiente de aceptación", "en": "Pending acceptance"},
        },
        "appointments": [
            {"week": "past", "covers": [0], "status": "completed"},
            {"week": "future", "covers": [1], "status": "scheduled"},
            {"week": "future", "covers": [2], "status": "scheduled"},
        ],
    },
    # Patient 5 — Elena / Sophia (pregnant; accepted budget with signature, partial invoice)
    {
        "patient_idx": 5,
        "plan": {
            "id_idx": 5,
            "status": "active",
            "title": {"es": "Diagnóstico y restauración", "en": "Diagnosis and restoration"},
            "diagnosis_notes": {
                "es": "Embarazada. Evitar radiografías no esenciales.",
                "en": "Pregnant. Avoid non-essential x-rays.",
            },
            "items": [
                {"catalog_code": "DX-VISIT", "is_global": True, "completed": True},
                {"catalog_code": "DX-RXPAN", "is_global": True, "completed": True},
                {"catalog_code": "REST-COMP", "tooth": 26, "is_global": False},
            ],
        },
        "budget": {
            "id_idx": 3,
            "status": "accepted",
            "global_discount": None,
            "signature": True,
            "notes": {
                "es": "Paciente embarazada - tratamiento en curso",
                "en": "Pregnant patient - treatment in progress",
            },
        },
        "appointments": [
            {"week": "past", "covers": [0, 1], "status": "completed"},
            {"week": "current", "covers": [2], "status": "confirmed"},
        ],
        "invoice": {
            "id_idx": 2,
            "status": "partial",
            "payments": [{"method": "card", "percent": 50}],
            "covers": [0, 1, 2],
            "notes": {"es": "Pago parcial recibido", "en": "Partial payment received"},
        },
    },
    # Patient 6 — Javier / Daniel (diabetic; accepted+signed budget, paid invoice)
    {
        "patient_idx": 6,
        "plan": {
            "id_idx": 6,
            "status": "active",
            "title": {"es": "Endodoncia y corona", "en": "Root canal and crown"},
            "diagnosis_notes": {
                "es": "Paciente diabético. Control especial de cicatrización.",
                "en": "Diabetic patient. Special healing monitoring.",
            },
            "items": [
                {"catalog_code": "DX-VISIT", "is_global": True, "completed": True},
                {"catalog_code": "ENDO-MULTI", "tooth": 36, "is_global": False, "completed": True},
                {"catalog_code": "REST-CROWN-MC", "tooth": 36, "is_global": False},
            ],
        },
        "budget": {
            "id_idx": 4,
            "status": "accepted",
            "global_discount": None,
            "signature": True,
            "notes": {
                "es": "Paciente diabético - control especial",
                "en": "Diabetic patient - special care",
            },
        },
        "appointments": [
            {"week": "past", "covers": [0], "status": "completed"},
            {"week": "past", "covers": [1], "status": "completed"},
            {"week": "future", "covers": [2], "status": "scheduled"},
        ],
        "invoice": {
            "id_idx": 3,
            "status": "paid",
            "payments": [{"method": "bank_transfer", "percent": 100}],
            "covers": [0, 1],
            "notes": {"es": "Pagado por transferencia", "en": "Paid by bank transfer"},
        },
    },
    # Patient 7 — Isabel / Mia (rejected budget, no invoice)
    {
        "patient_idx": 7,
        "plan": {
            "id_idx": 7,
            "status": "active",
            "title": {"es": "Revisión periódica", "en": "Periodic checkup"},
            "diagnosis_notes": {
                "es": "Control semestral. Paciente rechazó carillas estéticas.",
                "en": "Bi-annual checkup. Patient rejected aesthetic veneers.",
            },
            "items": [
                {"catalog_code": "DX-VISIT", "is_global": True, "completed": True},
                {"catalog_code": "PREV-CLEAN", "is_global": True},
                {"catalog_code": "REST-VEN-COMP", "tooth": 11, "is_global": False},
            ],
        },
        "budget": {
            "id_idx": 5,
            "status": "rejected",
            "global_discount": None,
            "signature": False,
            "notes": {
                "es": "Rechazado por precio de carillas",
                "en": "Rejected due to veneer pricing",
            },
        },
        "appointments": [
            {"week": "past", "covers": [0], "status": "completed"},
            {"week": "current", "covers": [1], "status": "confirmed"},
        ],
    },
    # Patient 8 — Francisco / Alexander (penicillin allergic; accepted, paid split)
    {
        "patient_idx": 8,
        "plan": {
            "id_idx": 8,
            "status": "active",
            "title": {"es": "Tratamiento periodontal", "en": "Periodontal treatment"},
            "diagnosis_notes": {
                "es": "ALÉRGICO A PENICILINA. Usar alternativas.",
                "en": "ALLERGIC TO PENICILLIN. Use alternatives.",
            },
            "items": [
                {"catalog_code": "PERIO-RAR", "is_global": True, "completed": True},
                {"catalog_code": "REST-COMP", "tooth": 17, "is_global": False, "completed": True},
                {"catalog_code": "REST-COMP", "tooth": 26, "is_global": False},
            ],
        },
        "budget": {
            "id_idx": 6,
            "status": "accepted",
            "global_discount": {"type": "absolute", "value": 50},
            "signature": True,
            "notes": {"es": "Alérgico a penicilina", "en": "Allergic to penicillin"},
        },
        "appointments": [
            {"week": "past", "covers": [0], "status": "completed"},
            {"week": "past", "covers": [1], "status": "completed"},
            {"week": "future", "covers": [2], "status": "scheduled"},
        ],
        "invoice": {
            "id_idx": 4,
            "status": "paid",
            "payments": [
                {"method": "cash", "percent": 40},
                {"method": "card", "percent": 60},
            ],
            "covers": [0, 1],
            "notes": {"es": "Pagado en dos plazos", "en": "Paid in two installments"},
        },
    },
    # Patient 9 — Rosa / Charlotte (hypertensive; accepted+signed, paid invoice)
    {
        "patient_idx": 9,
        "plan": {
            "id_idx": 9,
            "status": "active",
            "title": {"es": "Rehabilitación oral", "en": "Oral rehabilitation"},
            "diagnosis_notes": {
                "es": "Hipertensa - verificar presión antes de procedimientos.",
                "en": "Hypertensive - check blood pressure before procedures.",
            },
            "items": [
                {"catalog_code": "DX-VISIT", "is_global": True, "completed": True},
                {
                    "catalog_code": "REST-CROWN-MC",
                    "tooth": 46,
                    "is_global": False,
                    "completed": True,
                },
                {"catalog_code": "ENDO-MULTI", "tooth": 36, "is_global": False},
                {"catalog_code": "REST-CROWN-MC", "tooth": 36, "is_global": False},
            ],
        },
        "budget": {
            "id_idx": 7,
            "status": "accepted",
            "global_discount": {"type": "percentage", "value": 10},
            "signature": True,
            "notes": {"es": "Tratamiento en curso", "en": "Treatment in progress"},
        },
        "appointments": [
            {"week": "past", "covers": [0], "status": "completed"},
            {"week": "past", "covers": [1], "status": "completed"},
            {"week": "future", "covers": [2, 3], "status": "scheduled"},
        ],
        "invoice": {
            "id_idx": 5,
            "status": "paid",
            "payments": [{"method": "card", "percent": 100}],
            "covers": [0, 1],
            "notes": {"es": "Primera fase facturada", "en": "First phase billed"},
        },
    },
    # Patient 10 — Antonio / Robert (completed prosthetic workflow)
    {
        "patient_idx": 10,
        "plan": {
            "id_idx": 10,
            "status": "completed",
            "title": {"es": "Prótesis parcial superior", "en": "Upper partial denture"},
            "diagnosis_notes": {
                "es": "Prótesis parcial superior entregada y ajustada.",
                "en": "Upper partial denture delivered and adjusted.",
            },
            "items": [
                {"catalog_code": "DX-VISIT", "is_global": True, "completed": True},
                {"catalog_code": "PROT-PART-METAL", "is_global": True, "completed": True},
            ],
        },
        "budget": {
            "id_idx": 8,
            "status": "completed",
            "global_discount": None,
            "signature": True,
            "notes": {"es": "Prótesis parcial entregada", "en": "Partial denture delivered"},
        },
        "appointments": [
            {"week": "past", "covers": [0], "status": "completed"},
            {"week": "past", "covers": [1], "status": "completed"},
        ],
        "invoice": {
            "id_idx": 6,
            "status": "paid",
            "payments": [{"method": "direct_debit", "percent": 100}],
            "covers": [0, 1],
            "notes": None,
        },
    },
    # Patient 11 — María Teresa / Patricia (pulpitis; no budget)
    {
        "patient_idx": 11,
        "plan": {
            "id_idx": 11,
            "status": "active",
            "title": {"es": "Tratamiento de pulpitis", "en": "Pulpitis treatment"},
            "diagnosis_notes": {
                "es": "Tratamiento de pulpitis con corona posterior.",
                "en": "Pulpitis treatment with follow-up crown.",
            },
            "items": [
                {"catalog_code": "DX-VISIT", "is_global": True},
                {"catalog_code": "ENDO-UNI", "tooth": 36, "is_global": False},
                {"catalog_code": "REST-COMP", "tooth": 36, "is_global": False},
            ],
        },
        "appointments": [
            {"week": "current", "covers": [0], "status": "confirmed"},
            {"week": "future", "covers": [1], "status": "scheduled"},
            {"week": "future", "covers": [2], "status": "scheduled"},
        ],
    },
    # Patient 12 — José Luis / Richard (anticoagulated; overdue invoice)
    {
        "patient_idx": 12,
        "plan": {
            "id_idx": 12,
            "status": "active",
            "title": {"es": "Endodoncia urgente", "en": "Urgent root canal"},
            "diagnosis_notes": {
                "es": "Endodoncia urgente por absceso. Paciente anticoagulado.",
                "en": "Urgent root canal due to abscess. Anticoagulated patient.",
            },
            "items": [
                {"catalog_code": "DX-VISIT", "is_global": True, "completed": True},
                {"catalog_code": "ENDO-MULTI", "tooth": 46, "is_global": False, "completed": True},
            ],
        },
        "budget": {
            "id_idx": 9,
            "status": "accepted",
            "global_discount": None,
            "signature": True,
            "notes": {
                "es": "Anticoagulado - cuidado post-operatorio",
                "en": "Anticoagulated - post-op care",
            },
        },
        "appointments": [
            {"week": "past", "covers": [0], "status": "completed"},
            {"week": "past", "covers": [1], "status": "completed"},
        ],
        "invoice": {
            "id_idx": 7,
            "status": "issued",
            "overdue": True,
            "payments": [],
            "covers": [0, 1],
            "notes": {"es": "Factura vencida", "en": "Overdue invoice"},
        },
    },
    # Patient 13 — Dolores / Barbara (evaluation; no budget)
    {
        "patient_idx": 13,
        "plan": {
            "id_idx": 13,
            "status": "active",
            "title": {"es": "Evaluación y limpieza", "en": "Evaluation and cleaning"},
            "diagnosis_notes": {"es": "Evaluación periódica.", "en": "Periodic evaluation."},
            "items": [
                {"catalog_code": "DX-VISIT", "is_global": True},
                {"catalog_code": "DX-RXPAN", "is_global": True},
                {"catalog_code": "PREV-CLEAN", "is_global": True},
            ],
        },
        "appointments": [
            {"week": "current", "covers": [0, 1], "status": "confirmed"},
            {"week": "future", "covers": [2], "status": "scheduled"},
        ],
    },
    # Patient 14 — Manuel / Charles (prosthetic maintenance; no budget)
    {
        "patient_idx": 14,
        "plan": {
            "id_idx": 14,
            "status": "active",
            "title": {"es": "Mantenimiento protésico", "en": "Prosthetic maintenance"},
            "diagnosis_notes": {
                "es": "Ajustes periódicos de prótesis completa.",
                "en": "Periodic complete denture adjustments.",
            },
            "items": [
                {"catalog_code": "DX-VISIT", "is_global": True, "completed": True},
                {"catalog_code": "PREV-CLEAN", "is_global": True},
            ],
        },
        "appointments": [
            {"week": "past", "covers": [0], "status": "completed"},
            {"week": "future", "covers": [1], "status": "scheduled"},
        ],
    },
]


def _calculate_line_totals(
    unit_price: Decimal, quantity: int, vat_rate: float | None
) -> tuple[Decimal, Decimal, Decimal]:
    """Return (line_subtotal, line_tax, line_total). Shared by budgets and invoices."""
    subtotal = Decimal(str(unit_price)) * quantity
    tax = subtotal * Decimal(str(vat_rate or 0)) / 100
    return subtotal, tax, subtotal + tax


def _global_discount_amount(subtotal: Decimal, global_discount: dict | None) -> Decimal:
    """Compute total discount from a {"type": percentage|absolute, "value": N} dict."""
    if not global_discount:
        return Decimal("0.00")
    value = Decimal(str(global_discount["value"]))
    if global_discount["type"] == "percentage":
        return subtotal * value / 100
    return value


# =============================================================================
# Treatment Plan Generator
# =============================================================================


def generate_treatment_plans_data(catalog_items_map: dict[str, dict]) -> dict:
    """Build TreatmentPlan + backing Treatment + PlannedTreatmentItem rows per journey.

    Args:
        catalog_items_map: internal_code -> {id, default_price, vat_type_id, vat_rate,
                           odontogram_treatment_type}.

    Returns:
        dict with:
          plans: list of TreatmentPlan dicts (budget_id=None; wired by seed_demo.py)
          plan_treatments: list of backing Treatment dicts
          items: list of PlannedTreatmentItem dicts
          plan_details: {plan_id: {
              "patient_id", "plan_number", "status", "assigned_professional_id",
              "items": [{"idx", "plan_item_id", "treatment_id", "catalog_code",
                         "catalog_item_id", "unit_price", "vat_type_id", "vat_rate",
                         "tooth_number", "is_global", "is_completed"}]}}
    """
    patients_data = get_patients_data()
    plans = []
    planned_items = []
    plan_treatments = []
    plan_details: dict = {}

    plan_item_idx = 0

    for scenario_idx, journey in enumerate(PATIENT_JOURNEYS):
        plan_scenario = journey["plan"]
        patient = patients_data[journey["patient_idx"]]
        plan_id = TREATMENT_PLAN_IDS[plan_scenario["id_idx"]]

        plan_number = f"PLAN-2024-{scenario_idx + 1:04d}"
        plans.append(
            {
                "id": plan_id,
                "clinic_id": CLINIC_ID,
                "patient_id": patient["id"],
                "plan_number": plan_number,
                "title": t(plan_scenario["title"]) if plan_scenario.get("title") else None,
                "status": plan_scenario["status"],
                "budget_id": None,  # wired by seed_demo after budgets are created
                "assigned_professional_id": USER_DENTIST_ID,
                "created_by": USER_DENTIST_ID,
                "diagnosis_notes": t(plan_scenario["diagnosis_notes"])
                if plan_scenario.get("diagnosis_notes")
                else None,
                "internal_notes": None,
                "deleted_at": None,
            }
        )

        details_items = []
        for seq_order, item_scenario in enumerate(plan_scenario.get("items", []), start=1):
            catalog_code = item_scenario["catalog_code"]
            catalog_item = catalog_items_map.get(catalog_code)
            if not catalog_item:
                continue

            planned_item_id = PLANNED_ITEM_IDS[plan_item_idx]
            treatment_id = PLAN_TREATMENT_IDS[plan_item_idx]
            plan_item_idx += 1

            is_completed = item_scenario.get("completed", False)
            plan_treatment_status = "performed" if is_completed else "planned"
            recorded_at = datetime.now() - timedelta(days=30)
            performed_at = datetime.now() - timedelta(days=10) if is_completed else None

            plan_treatments.append(
                {
                    "id": treatment_id,
                    "clinic_id": CLINIC_ID,
                    "patient_id": patient["id"],
                    "clinical_type": catalog_item.get("odontogram_treatment_type")
                    or "filling_composite",
                    "catalog_item_id": catalog_item["id"],
                    "status": plan_treatment_status,
                    "recorded_at": recorded_at,
                    "performed_at": performed_at,
                    "performed_by": USER_DENTIST_ID if is_completed else None,
                    "price_snapshot": catalog_item.get("default_price"),
                    "currency_snapshot": "EUR",
                    "duration_snapshot": None,
                    "vat_rate_snapshot": None,
                    "budget_item_id": None,
                    "notes": None,
                    "source_module": "treatment_plan",
                    "deleted_at": None,
                }
            )

            planned_items.append(
                {
                    "id": planned_item_id,
                    "clinic_id": CLINIC_ID,
                    "treatment_plan_id": plan_id,
                    "treatment_id": treatment_id,
                    "sequence_order": seq_order,
                    "status": "completed" if is_completed else "pending",
                    "completed_without_appointment": is_completed,
                    "completed_at": datetime.now() - timedelta(days=10) if is_completed else None,
                    "completed_by": USER_DENTIST_ID if is_completed else None,
                    "notes": None,
                }
            )

            details_items.append(
                {
                    "idx": len(details_items),
                    "plan_item_id": planned_item_id,
                    "treatment_id": treatment_id,
                    "catalog_code": catalog_code,
                    "catalog_item_id": catalog_item["id"],
                    "unit_price": catalog_item["default_price"],
                    "vat_type_id": catalog_item.get("vat_type_id"),
                    "vat_rate": catalog_item.get("vat_rate", 0.0) or 0.0,
                    "tooth_number": item_scenario.get("tooth"),
                    "is_global": item_scenario.get("is_global", True),
                    "is_completed": is_completed,
                }
            )

        plan_details[plan_id] = {
            "patient_id": patient["id"],
            "plan_number": plan_number,
            "status": plan_scenario["status"],
            "assigned_professional_id": USER_DENTIST_ID,
            "items": details_items,
            "journey_idx": scenario_idx,
        }

    return {
        "plans": plans,
        "plan_treatments": plan_treatments,
        "items": planned_items,
        "plan_details": plan_details,
    }


# =============================================================================
# Budget Generator
# =============================================================================


def generate_budgets_data(catalog_items_map: dict[str, dict], plans_result: dict) -> dict:
    """Build Budget + BudgetItem + BudgetSignature rows derived from plans.

    Each budget is 1-to-1 with the journey's plan: items mirror plan.items (same
    catalog, same tooth_number) and each BudgetItem.treatment_id points to the
    plan's backing Treatment row.

    Returns dict with:
      budgets, items, signatures
      plan_to_budget: {plan_id: budget_id} — consumed by seed_demo.py to wire
                      TreatmentPlan.budget_id after budgets are committed.
      budget_item_details: {budget_id: [{"idx", "budget_item_id", "quantity",
                           "unit_price", "vat_type_id", "vat_rate", "catalog_code",
                           "catalog_item_id", "tooth_number"}]}
                           — consumed by the invoice generator.
    """
    budgets = []
    items = []
    signatures = []
    plan_to_budget: dict = {}
    budget_item_details: dict = {}

    item_idx = 0
    signature_idx = 0

    patients_data = get_patients_data()

    for journey_idx, journey in enumerate(PATIENT_JOURNEYS):
        budget_scenario = journey.get("budget")
        if not budget_scenario:
            continue

        patient = patients_data[journey["patient_idx"]]
        plan_id = TREATMENT_PLAN_IDS[journey["plan"]["id_idx"]]
        plan_detail = plans_result["plan_details"][plan_id]
        budget_id = BUDGET_IDS[budget_scenario["id_idx"]]

        plan_to_budget[plan_id] = budget_id

        budget_number = f"PRES-2024-{journey_idx + 1:04d}"
        valid_from = date.today() - timedelta(days=max(5, 30 - journey_idx * 5))
        valid_until = valid_from + timedelta(days=60)

        budget_items_local = []
        subtotal = Decimal("0.00")

        for plan_item in plan_detail["items"]:
            quantity = 1
            catalog_item = catalog_items_map.get(plan_item["catalog_code"])
            if not catalog_item:
                continue

            item_id = BUDGET_ITEM_IDS[item_idx]
            item_idx += 1

            unit_price = catalog_item["default_price"]
            vat_rate = catalog_item.get("vat_rate", 0.0) or 0.0
            line_subtotal, line_tax, line_total = _calculate_line_totals(
                unit_price, quantity, vat_rate
            )
            subtotal += line_subtotal

            budget_items_local.append(
                {
                    "id": item_id,
                    "clinic_id": CLINIC_ID,
                    "budget_id": budget_id,
                    "catalog_item_id": catalog_item["id"],
                    "unit_price": unit_price,
                    "quantity": quantity,
                    "discount_type": None,
                    "discount_value": None,
                    "vat_type_id": catalog_item.get("vat_type_id"),
                    "vat_rate": vat_rate,
                    "line_subtotal": line_subtotal,
                    "line_discount": Decimal("0.00"),
                    "line_tax": line_tax,
                    "line_total": line_total,
                    "tooth_number": plan_item["tooth_number"],
                    "surfaces": None,
                    "treatment_id": plan_item["treatment_id"],
                    "invoiced_quantity": 0,
                    "display_order": len(budget_items_local) + 1,
                    "notes": None,
                }
            )

        items.extend(budget_items_local)

        global_discount_type = None
        global_discount_value = None
        gd = budget_scenario.get("global_discount")
        if gd:
            global_discount_type = gd["type"]
            global_discount_value = Decimal(str(gd["value"]))
        total_discount = _global_discount_amount(subtotal, gd)
        total_tax = sum((bi["line_tax"] for bi in budget_items_local), Decimal("0.00"))
        total = subtotal - total_discount + total_tax

        budgets.append(
            {
                "id": budget_id,
                "clinic_id": CLINIC_ID,
                "patient_id": patient["id"],
                "budget_number": budget_number,
                "version": 1,
                "parent_budget_id": None,
                "status": budget_scenario["status"],
                "valid_from": valid_from,
                "valid_until": valid_until,
                "created_by": USER_DENTIST_ID,
                "assigned_professional_id": USER_DENTIST_ID,
                "global_discount_type": global_discount_type,
                "global_discount_value": global_discount_value,
                "subtotal": subtotal,
                "total_discount": total_discount,
                "total_tax": total_tax,
                "total": total,
                "currency": t({"es": "EUR", "en": "USD"}),
                "internal_notes": t(budget_scenario["notes"])
                if budget_scenario.get("notes")
                else None,
                "patient_notes": None,
                "insurance_estimate": None,
                "deleted_at": None,
            }
        )

        if budget_scenario.get("signature") and budget_scenario["status"] not in (
            "draft",
            "rejected",
        ):
            signature_id = BUDGET_SIGNATURE_IDS[signature_idx]
            signature_idx += 1
            signatures.append(
                {
                    "id": signature_id,
                    "clinic_id": CLINIC_ID,
                    "budget_id": budget_id,
                    "signature_type": "full_acceptance",
                    "signed_items": [str(bi["id"]) for bi in budget_items_local],
                    "signed_by_name": f"{patient['first_name']} {patient['last_name']}",
                    "signed_by_email": patient.get("email"),
                    "relationship_to_patient": "patient",
                    "signature_method": "click_accept",
                    "signature_data": {
                        "accepted_terms": True,
                        "timestamp": datetime.now().isoformat(),
                    },
                    "ip_address": "192.168.1.100",
                    "user_agent": "Mozilla/5.0 (Demo Browser)",
                    "signed_at": datetime.now() - timedelta(days=15),
                    "external_signature_id": None,
                    "external_provider": None,
                    "document_hash": None,
                }
            )

        budget_item_details[budget_id] = [
            {
                "idx": local_idx,
                "budget_item_id": bi["id"],
                "quantity": bi["quantity"],
                "unit_price": bi["unit_price"],
                "vat_type_id": bi["vat_type_id"],
                "vat_rate": bi["vat_rate"],
                "catalog_code": plan_detail["items"][local_idx]["catalog_code"],
                "catalog_item_id": bi["catalog_item_id"],
                "tooth_number": bi["tooth_number"],
            }
            for local_idx, bi in enumerate(budget_items_local)
        ]

    return {
        "budgets": budgets,
        "items": items,
        "signatures": signatures,
        "plan_to_budget": plan_to_budget,
        "budget_item_details": budget_item_details,
    }


# =============================================================================
# Appointment Generator
# =============================================================================


def generate_appointments_data(plans_result: dict, reference_date: date | None = None) -> dict:
    """Build Appointment + AppointmentTreatment rows anchored to plan items.

    Each journey declares its appointments with a `covers` list of plan-item indexes
    the visit performs. The generator:
      - places each appointment in an available slot (past/current/future week)
      - sets patient/professional from the plan
      - derives duration/color/treatment_type from the first covered item's
        catalog code
      - emits one AppointmentTreatment row per covered item, linking to the
        corresponding PlannedTreatmentItem and catalog_item.

    Returns:
        dict with:
          appointments: list of Appointment dicts
          appointment_treatments: list of AppointmentTreatment dicts
    """
    from uuid import uuid4

    if reference_date is None:
        reference_date = date.today()

    current_monday = reference_date - timedelta(days=reference_date.weekday())
    week_starts = {
        "past": current_monday - timedelta(days=7),
        "current": current_monday,
        "future": current_monday + timedelta(days=7),
    }

    clinic_data = get_clinic_data()
    cabinets = [c["name"] for c in clinic_data["cabinets"]]

    appointments: list[dict] = []
    appointment_treatments: list[dict] = []
    used_slots: set[tuple[str, str, datetime]] = set()

    # Spread visits across days/slots deterministically: counter drives day/slot pick.
    pick_counter = 0

    for journey in PATIENT_JOURNEYS:
        plan_id = TREATMENT_PLAN_IDS[journey["plan"]["id_idx"]]
        plan_detail = plans_result["plan_details"][plan_id]
        patient_id = plan_detail["patient_id"]
        professional_id = plan_detail["assigned_professional_id"]

        for appt_scenario in journey.get("appointments", []):
            covers = appt_scenario.get("covers", [])
            if not covers:
                continue

            covered_items = [plan_detail["items"][idx] for idx in covers]
            first_code = covered_items[0]["catalog_code"]
            look = _appt_look_for(first_code)
            total_duration = sum(
                _appt_look_for(ci["catalog_code"])["duration"] for ci in covered_items
            )
            # round up to the next 30-minute slot
            total_duration = ((total_duration + 29) // 30) * 30

            week_start = week_starts[appt_scenario["week"]]

            # Find a free slot (avoid conflicts on cabinet + professional + datetime).
            start_time = None
            for attempt in range(80):
                day_offset = (pick_counter + attempt) % 5  # Mon-Fri
                slot_pool = MORNING_SLOTS if (pick_counter + attempt) % 3 != 0 else AFTERNOON_SLOTS
                time_str = slot_pool[(pick_counter + attempt) % len(slot_pool)]
                hour, minute = map(int, time_str.split(":"))
                candidate = datetime(
                    week_start.year,
                    week_start.month,
                    week_start.day,
                    hour,
                    minute,
                    0,
                ) + timedelta(days=day_offset)
                cabinet_pick = cabinets[(pick_counter + attempt) % len(cabinets)]
                slot_key = (cabinet_pick, str(professional_id), candidate)
                if slot_key in used_slots:
                    continue
                used_slots.add(slot_key)
                start_time = candidate
                cabinet = cabinet_pick
                break
            if start_time is None:
                continue
            pick_counter += 1

            end_time = start_time + timedelta(minutes=total_duration)
            appointment_id = uuid4()

            appointments.append(
                {
                    "id": appointment_id,
                    "clinic_id": CLINIC_ID,
                    "patient_id": patient_id,
                    "professional_id": professional_id,
                    "cabinet": cabinet,
                    "start_time": start_time,
                    "end_time": end_time,
                    "treatment_type": t(look["name"]),
                    "status": appt_scenario["status"],
                    "notes": None,
                    "color": look["color"],
                }
            )

            for display_order, ci in enumerate(covered_items):
                appointment_treatments.append(
                    {
                        "appointment_id": appointment_id,
                        "planned_treatment_item_id": ci["plan_item_id"],
                        "catalog_item_id": ci["catalog_item_id"],
                        "display_order": display_order,
                    }
                )

    return {
        "appointments": appointments,
        "appointment_treatments": appointment_treatments,
    }


# =============================================================================
# Invoice Generator
# =============================================================================


def generate_invoice_series_data() -> list[dict]:
    """Generate invoice series seed data."""
    current_year = date.today().year
    num_invoices = sum(1 for j in PATIENT_JOURNEYS if j.get("invoice"))
    definitions = [
        {
            "id": INVOICE_SERIES_IDS[0],
            "prefix": "FAC",
            "series_type": "invoice",
            "description": t({"es": "Serie principal de facturas", "en": "Main invoice series"}),
            "current_number": num_invoices + 1,
            "is_default": True,
        },
        {
            "id": INVOICE_SERIES_IDS[1],
            "prefix": "RECT",
            "series_type": "credit_note",
            "description": t({"es": "Notas de crédito", "en": "Credit notes"}),
            "current_number": 1,
            "is_default": True,
        },
    ]
    return [
        {
            "id": s["id"],
            "clinic_id": CLINIC_ID,
            "prefix": s["prefix"],
            "series_type": s["series_type"],
            "description": s["description"],
            "current_number": s["current_number"],
            "reset_yearly": True,
            "last_reset_year": current_year,
            "is_default": s["is_default"],
            "is_active": True,
        }
        for s in definitions
    ]


def generate_invoices_data(catalog_items_map: dict[str, dict], budgets_result: dict) -> dict:
    """Build Invoice + InvoiceItem + Payment rows anchored to budgets.

    Every invoice references its journey's budget, and every InvoiceItem links back
    to the BudgetItem it invoices (budget_item_id). The generator also returns the
    aggregate invoiced quantity per BudgetItem so callers can update
    BudgetItem.invoiced_quantity in the database.

    Returns dict with:
      series, invoices, items, payments
      invoiced_quantity_by_budget_item: {budget_item_id: total_qty}
    """
    patients_data = get_patients_data()
    invoices: list[dict] = []
    items: list[dict] = []
    payments: list[dict] = []
    invoiced_quantity: dict = {}

    invoice_idx = 0
    item_idx = 0
    payment_idx = 0
    sequential_number = 0
    current_year = date.today().year
    series = generate_invoice_series_data()

    for journey_idx, journey in enumerate(PATIENT_JOURNEYS):
        invoice_scenario = journey.get("invoice")
        if not invoice_scenario:
            continue
        budget_scenario = journey.get("budget")
        if not budget_scenario:
            continue  # cannot invoice without a budget

        patient = patients_data[journey["patient_idx"]]
        budget_id = BUDGET_IDS[budget_scenario["id_idx"]]
        budget_items = budgets_result["budget_item_details"][budget_id]

        invoice_id = INVOICE_IDS[invoice_scenario["id_idx"]]
        invoice_idx += 1
        sequential_number += 1
        invoice_number = f"FAC-{current_year}-{sequential_number:04d}"

        is_overdue = invoice_scenario.get("overdue", False)
        if invoice_scenario["status"] == "draft":
            issue_date = None
            due_date = None
        elif is_overdue:
            issue_date = date.today() - timedelta(days=45)
            due_date = date.today() - timedelta(days=15)
        else:
            days_ago = max(5, (7 - journey_idx) * 3 + 5)
            issue_date = date.today() - timedelta(days=days_ago)
            due_date = issue_date + timedelta(days=30)

        invoice_items_local: list[dict] = []
        subtotal = Decimal("0.00")
        total_tax = Decimal("0.00")

        for budget_item in [budget_items[i] for i in invoice_scenario["covers"]]:
            item_id = INVOICE_ITEM_IDS[item_idx]
            item_idx += 1

            unit_price = budget_item["unit_price"]
            quantity = budget_item["quantity"]
            vat_rate = budget_item["vat_rate"]
            line_subtotal, line_tax, line_total = _calculate_line_totals(
                unit_price, quantity, vat_rate
            )
            subtotal += line_subtotal
            total_tax += line_tax

            invoice_items_local.append(
                {
                    "id": item_id,
                    "clinic_id": CLINIC_ID,
                    "invoice_id": invoice_id,
                    "budget_item_id": budget_item["budget_item_id"],
                    "catalog_item_id": budget_item["catalog_item_id"],
                    "description": t(
                        {
                            "es": f"Tratamiento {budget_item['catalog_code']}",
                            "en": f"Treatment {budget_item['catalog_code']}",
                        }
                    ),
                    "internal_code": budget_item["catalog_code"],
                    "unit_price": unit_price,
                    "quantity": quantity,
                    "discount_type": None,
                    "discount_value": None,
                    "vat_type_id": budget_item["vat_type_id"],
                    "vat_rate": vat_rate,
                    "vat_exempt_reason": None,
                    "line_subtotal": line_subtotal,
                    "line_discount": Decimal("0.00"),
                    "line_tax": line_tax,
                    "line_total": line_total,
                    "tooth_number": budget_item["tooth_number"],
                    "surfaces": None,
                    "display_order": len(invoice_items_local) + 1,
                }
            )
            invoiced_quantity[budget_item["budget_item_id"]] = (
                invoiced_quantity.get(budget_item["budget_item_id"], 0) + quantity
            )

        items.extend(invoice_items_local)
        total = subtotal + total_tax

        total_paid = Decimal("0.00")
        for payment_data in invoice_scenario.get("payments", []):
            payment_id = PAYMENT_IDS[payment_idx]
            payment_idx += 1
            amount = (total * Decimal(str(payment_data["percent"]))) / 100
            total_paid += amount
            payments.append(
                {
                    "id": payment_id,
                    "clinic_id": CLINIC_ID,
                    "invoice_id": invoice_id,
                    "amount": amount,
                    "payment_method": payment_data["method"],
                    "payment_date": issue_date + timedelta(days=3) if issue_date else date.today(),
                    "reference": f"REF-{payment_idx:04d}",
                    "notes": None,
                    "recorded_by": USER_RECEPTIONIST_ID,
                    "is_voided": False,
                    "voided_at": None,
                    "voided_by": None,
                    "void_reason": None,
                }
            )

        invoices.append(
            {
                "id": invoice_id,
                "clinic_id": CLINIC_ID,
                "patient_id": patient["id"],
                "invoice_number": invoice_number,
                "series_id": INVOICE_SERIES_IDS[0],
                "sequential_number": sequential_number,
                "budget_id": budget_id,
                "credit_note_for_id": None,
                "status": invoice_scenario["status"],
                "issue_date": issue_date,
                "due_date": due_date,
                "payment_term_days": 30,
                "billing_name": f"{patient['first_name']} {patient['last_name']}",
                "billing_tax_id": None,
                "billing_address": None,
                "billing_email": patient.get("email"),
                "subtotal": subtotal,
                "total_discount": Decimal("0.00"),
                "total_tax": total_tax,
                "total": total,
                "total_paid": total_paid,
                "balance_due": total - total_paid,
                "currency": t({"es": "EUR", "en": "USD"}),
                "internal_notes": t(invoice_scenario["notes"])
                if invoice_scenario.get("notes")
                else None,
                "public_notes": None,
                "compliance_data": None,
                "document_hash": None,
                "created_by": USER_RECEPTIONIST_ID,
                "issued_by": USER_RECEPTIONIST_ID
                if invoice_scenario["status"] != "draft"
                else None,
                "deleted_at": None,
            }
        )

    return {
        "series": series,
        "invoices": invoices,
        "items": items,
        "payments": payments,
        "invoiced_quantity_by_budget_item": invoiced_quantity,
    }
