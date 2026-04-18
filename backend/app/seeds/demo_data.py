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
# Appointment Templates
# =============================================================================

# Treatment types with typical durations (in minutes)
# catalog_codes: list of internal_code from treatment catalog to associate with appointment
TREATMENT_TYPES_I18N = [
    {
        "names": {"es": "Revisión", "en": "Checkup"},
        "duration": 30,
        "color": "#3B82F6",
        "catalog_codes": ["DX-VISIT"],
    },
    {
        "names": {"es": "Limpieza dental", "en": "Dental cleaning"},
        "duration": 45,
        "color": "#10B981",
        "catalog_codes": ["PREV-LIMP"],
    },
    {
        "names": {"es": "Empaste", "en": "Filling"},
        "duration": 45,
        "color": "#F59E0B",
        "catalog_codes": ["REST-COMP"],
    },
    {
        "names": {"es": "Extracción", "en": "Extraction"},
        "duration": 60,
        "color": "#EF4444",
        "catalog_codes": ["CIR-EXT-S"],
    },
    {
        "names": {"es": "Endodoncia", "en": "Root canal"},
        "duration": 90,
        "color": "#8B5CF6",
        "catalog_codes": ["ENDO-UNI"],
    },
    {
        "names": {"es": "Ortodoncia - Revisión", "en": "Orthodontics - Checkup"},
        "duration": 30,
        "color": "#EC4899",
        "catalog_codes": ["DX-VISIT"],
    },
    {
        "names": {"es": "Blanqueamiento", "en": "Whitening"},
        "duration": 60,
        "color": "#06B6D4",
        "catalog_codes": ["EST-BLANQ-C"],
    },
    {
        "names": {"es": "Implante - Consulta", "en": "Implant - Consultation"},
        "duration": 45,
        "color": "#84CC16",
        "catalog_codes": ["DX-VISIT", "DX-RXPAN"],
    },
    {
        "names": {"es": "Urgencia", "en": "Emergency"},
        "duration": 30,
        "color": "#DC2626",
        "catalog_codes": ["DX-VISIT"],
    },
]


def get_treatment_types() -> list[dict]:
    """Get treatment types in current language."""
    return [
        {
            "name": t(tt["names"]),
            "duration": tt["duration"],
            "color": tt["color"],
            "catalog_codes": tt.get("catalog_codes", []),
        }
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
                    "catalog_codes": treatment.get("catalog_codes", []),
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
# Budget Seed Data
# =============================================================================

# Fixed UUIDs for budgets
BUDGET_IDS = [UUID(f"aa00bc99-9c0b-4ef8-bb6d-6bb9bd380b{i:02x}") for i in range(10)]

# Fixed UUIDs for budget items
BUDGET_ITEM_IDS = [UUID(f"bb00bc99-9c0b-4ef8-bb6d-6bb9bd380c{i:02x}") for i in range(50)]

# Fixed UUIDs for budget signatures
BUDGET_SIGNATURE_IDS = [UUID(f"cc00bc99-9c0b-4ef8-bb6d-6bb9bd380d{i:02x}") for i in range(10)]

# Budget scenarios for different patients
BUDGET_SCENARIOS = [
    # Budget 0: Draft budget for patient 3 (Carmen/Emma - sensitivity)
    {
        "patient_idx": 3,
        "status": "draft",
        "items": [
            {"code": "DX-VISIT", "qty": 1, "tooth": None},
            {"code": "DX-RXPAN", "qty": 1, "tooth": None},
            {"code": "REST-COMP", "qty": 2, "tooth": 16},
        ],
        "global_discount": None,
        "notes": {"es": "Presupuesto pendiente de revisión", "en": "Budget pending review"},
    },
    # Budget 1: Draft budget for patient 4 (David/William)
    {
        "patient_idx": 4,
        "status": "draft",
        "items": [
            {"code": "PREV-LIMP", "qty": 1, "tooth": None},
            {"code": "REST-COMP", "qty": 3, "tooth": 26},
            {"code": "ENDO-UNI", "qty": 1, "tooth": 21},
        ],
        "global_discount": {"type": "percentage", "value": 5},
        "notes": {"es": "Pendiente de aceptación", "en": "Pending acceptance"},
    },
    # Budget 2: Accepted budget for patient 6 (Javier/Daniel - diabetic)
    {
        "patient_idx": 6,
        "status": "accepted",
        "items": [
            {"code": "DX-VISIT", "qty": 1, "tooth": None},
            {"code": "REST-CRO", "qty": 2, "tooth": 36},
            {"code": "ENDO-MULTI", "qty": 1, "tooth": 36},
        ],
        "global_discount": None,
        "notes": {
            "es": "Paciente diabético - control especial",
            "en": "Diabetic patient - special care",
        },
        "signature": True,
    },
    # Budget 3: Accepted budget for patient 8 (Francisco/Alexander - allergic)
    {
        "patient_idx": 8,
        "status": "accepted",
        "items": [
            {"code": "PERIO-RAD", "qty": 4, "tooth": None},
            {"code": "REST-COMP", "qty": 2, "tooth": 17},
            {"code": "REST-COMP", "qty": 1, "tooth": 26},
        ],
        "global_discount": {"type": "absolute", "value": 50},
        "notes": {"es": "Alérgico a penicilina", "en": "Allergic to penicillin"},
        "signature": True,
    },
    # Budget 4: Completed budget for patient 10 (Antonio/Robert)
    {
        "patient_idx": 10,
        "status": "completed",
        "items": [
            {"code": "PROT-PARC", "qty": 1, "tooth": None},
            {"code": "DX-VISIT", "qty": 1, "tooth": None},
        ],
        "global_discount": None,
        "notes": {"es": "Prótesis parcial entregada", "en": "Partial denture delivered"},
        "signature": True,
    },
    # Budget 5: Rejected budget for patient 7 (Isabel/Mia)
    {
        "patient_idx": 7,
        "status": "rejected",
        "items": [
            {"code": "EST-BLANQ-C", "qty": 1, "tooth": None},
            {"code": "REST-VEN", "qty": 4, "tooth": 11},
        ],
        "global_discount": None,
        "notes": {"es": "Rechazado por precio", "en": "Rejected due to price"},
    },
    # Budget 6: Accepted for patient 9 (Rosa/Charlotte - hypertensive)
    {
        "patient_idx": 9,
        "status": "accepted",
        "items": [
            {"code": "DX-VISIT", "qty": 1, "tooth": None},
            {"code": "REST-CRO", "qty": 1, "tooth": 46},
            {"code": "REST-CRO", "qty": 1, "tooth": 36},
            {"code": "ENDO-MULTI", "qty": 1, "tooth": 36},
        ],
        "global_discount": {"type": "percentage", "value": 10},
        "notes": {"es": "Tratamiento en curso", "en": "Treatment in progress"},
        "signature": True,
    },
]


def generate_budgets_data(catalog_items_map: dict[str, dict]) -> dict:
    """Generate budget seed data.

    Args:
        catalog_items_map: Dictionary mapping internal_code to catalog item data
                          (must include id, default_price, vat_type_id, vat_rate)

    Returns:
        Dictionary with:
        - budgets: List of Budget data
        - items: List of BudgetItem data
        - signatures: List of BudgetSignature data
    """
    from decimal import Decimal

    budgets = []
    items = []
    signatures = []
    patients_data = get_patients_data()

    budget_idx = 0
    item_idx = 0
    signature_idx = 0

    for scenario_idx, scenario in enumerate(BUDGET_SCENARIOS):
        patient = patients_data[scenario["patient_idx"]]
        budget_id = BUDGET_IDS[budget_idx]
        budget_idx += 1

        # Calculate budget number
        budget_number = f"PRES-2024-{scenario_idx + 1:04d}"

        # Dates
        valid_from = date.today() - timedelta(days=30 - scenario_idx * 5)
        valid_until = valid_from + timedelta(days=60)

        # Create budget items and calculate totals
        budget_items = []
        subtotal = Decimal("0.00")

        for item_data in scenario["items"]:
            catalog_item = catalog_items_map.get(item_data["code"])
            if not catalog_item:
                continue  # Skip if catalog item not found

            item_id = BUDGET_ITEM_IDS[item_idx]
            item_idx += 1

            unit_price = catalog_item["default_price"]
            quantity = item_data["qty"]
            vat_rate = catalog_item.get("vat_rate", 0.0) or 0.0

            line_subtotal = unit_price * quantity
            line_tax = line_subtotal * Decimal(str(vat_rate)) / 100
            line_total = line_subtotal + line_tax

            subtotal += line_subtotal

            budget_item = {
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
                "tooth_number": item_data.get("tooth"),
                "surfaces": None,
                "treatment_id": None,
                "invoiced_quantity": 0,
                "display_order": len(budget_items) + 1,
                "notes": None,
            }
            budget_items.append(budget_item)
            items.append(budget_item)

        # Calculate totals
        total_discount = Decimal("0.00")
        global_discount_type = None
        global_discount_value = None

        if scenario.get("global_discount"):
            global_discount_type = scenario["global_discount"]["type"]
            global_discount_value = Decimal(str(scenario["global_discount"]["value"]))
            if global_discount_type == "percentage":
                total_discount = subtotal * global_discount_value / 100
            else:
                total_discount = global_discount_value

        # Calculate total tax
        total_tax = sum(Decimal(str(item["line_tax"])) for item in budget_items)
        total = subtotal - total_discount + total_tax

        budget = {
            "id": budget_id,
            "clinic_id": CLINIC_ID,
            "patient_id": patient["id"],
            "budget_number": budget_number,
            "version": 1,
            "parent_budget_id": None,
            "status": scenario["status"],
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
            "internal_notes": t(scenario["notes"]) if scenario.get("notes") else None,
            "patient_notes": None,
            "insurance_estimate": None,
            "deleted_at": None,
        }
        budgets.append(budget)

        # Create signature if needed (for accepted budgets)
        if scenario.get("signature") and scenario["status"] not in ["draft", "rejected"]:
            signature_id = BUDGET_SIGNATURE_IDS[signature_idx]
            signature_idx += 1

            # All items are signed together when budget is accepted
            signed_items = [str(item["id"]) for item in budget_items]

            signature = {
                "id": signature_id,
                "clinic_id": CLINIC_ID,
                "budget_id": budget_id,
                "signature_type": "full_acceptance",
                "signed_items": signed_items,
                "signed_by_name": f"{patient['first_name']} {patient['last_name']}",
                "signed_by_email": patient.get("email"),
                "relationship_to_patient": "patient",
                "signature_method": "click_accept",
                "signature_data": {"accepted_terms": True, "timestamp": datetime.now().isoformat()},
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0 (Demo Browser)",
                "signed_at": datetime.now() - timedelta(days=15),
                "external_signature_id": None,
                "external_provider": None,
                "document_hash": None,
            }
            signatures.append(signature)

    return {
        "budgets": budgets,
        "items": items,
        "signatures": signatures,
    }


# =============================================================================
# Invoice Seed Data
# =============================================================================

# Fixed UUIDs for invoice series
INVOICE_SERIES_IDS = [UUID(f"fa00bc99-9c0b-4ef8-bb6d-6bb9bd380e{i:02x}") for i in range(5)]

# Fixed UUIDs for invoices
INVOICE_IDS = [UUID(f"fb00bc99-9c0b-4ef8-bb6d-6bb9bd380f{i:02x}") for i in range(20)]

# Fixed UUIDs for invoice items
INVOICE_ITEM_IDS = [UUID(f"fc00bc99-9c0b-4ef8-bb6d-6bb9bd380{i:03x}") for i in range(100)]

# Fixed UUIDs for payments
PAYMENT_IDS = [UUID(f"fd00bc99-9c0b-4ef8-bb6d-6bb9bd380{i:03x}") for i in range(30)]

# Invoice scenarios for different patients
INVOICE_SCENARIOS = [
    # Invoice 0: Draft invoice for patient 2 (Miguel/James)
    {
        "patient_idx": 2,
        "status": "draft",
        "items": [
            {"code": "DX-VISIT", "qty": 1, "tooth": None},
            {"code": "PREV-LIMP", "qty": 1, "tooth": None},
        ],
        "payments": [],
        "notes": {"es": "Borrador - pendiente de emitir", "en": "Draft - pending issuance"},
    },
    # Invoice 1: Issued invoice for patient 3 (Carmen/Emma) - no payments yet
    {
        "patient_idx": 3,
        "status": "issued",
        "items": [
            {"code": "DX-VISIT", "qty": 1, "tooth": None},
            {"code": "REST-COMP", "qty": 2, "tooth": 16},
        ],
        "payments": [],
        "notes": {"es": "Emitida - pendiente de pago", "en": "Issued - pending payment"},
    },
    # Invoice 2: Partially paid invoice for patient 5 (Elena/Sophia)
    {
        "patient_idx": 5,
        "status": "partial",
        "items": [
            {"code": "DX-VISIT", "qty": 1, "tooth": None},
            {"code": "DX-RXPAN", "qty": 1, "tooth": None},
            {"code": "REST-COMP", "qty": 3, "tooth": 26},
        ],
        "payments": [
            {"method": "card", "percent": 50},  # 50% of total
        ],
        "notes": {"es": "Pago parcial recibido", "en": "Partial payment received"},
    },
    # Invoice 3: Fully paid invoice for patient 6 (Javier/Daniel)
    {
        "patient_idx": 6,
        "status": "paid",
        "items": [
            {"code": "DX-VISIT", "qty": 1, "tooth": None},
            {"code": "REST-CRO", "qty": 2, "tooth": 36},
        ],
        "payments": [
            {"method": "bank_transfer", "percent": 100},
        ],
        "notes": {"es": "Pagado por transferencia", "en": "Paid by bank transfer"},
    },
    # Invoice 4: Paid invoice for patient 8 (Francisco/Alexander) - multiple payments
    {
        "patient_idx": 8,
        "status": "paid",
        "items": [
            {"code": "PERIO-RAD", "qty": 4, "tooth": None},
            {"code": "REST-COMP", "qty": 2, "tooth": 17},
        ],
        "payments": [
            {"method": "cash", "percent": 40},
            {"method": "card", "percent": 60},
        ],
        "notes": {"es": "Pagado en dos plazos", "en": "Paid in two installments"},
    },
    # Invoice 5: Paid invoice for patient 10 (Antonio/Robert)
    {
        "patient_idx": 10,
        "status": "paid",
        "items": [
            {"code": "PROT-PARC", "qty": 1, "tooth": None},
        ],
        "payments": [
            {"method": "direct_debit", "percent": 100},
        ],
        "notes": None,
    },
    # Invoice 6: Overdue issued invoice for patient 12 (José Luis/Richard)
    {
        "patient_idx": 12,
        "status": "issued",
        "overdue": True,
        "items": [
            {"code": "DX-VISIT", "qty": 1, "tooth": None},
            {"code": "ENDO-MULTI", "qty": 1, "tooth": 46},
        ],
        "payments": [],
        "notes": {"es": "Factura vencida", "en": "Overdue invoice"},
    },
    # Invoice 7: Paid invoice from last month for patient 9 (Rosa/Charlotte)
    {
        "patient_idx": 9,
        "status": "paid",
        "items": [
            {"code": "DX-VISIT", "qty": 1, "tooth": None},
            {"code": "REST-CRO", "qty": 1, "tooth": 46},
        ],
        "payments": [
            {"method": "card", "percent": 100},
        ],
        "notes": None,
    },
]


def generate_invoice_series_data() -> list[dict]:
    """Generate invoice series seed data.

    Returns:
        List of InvoiceSeries data dictionaries.
    """
    current_year = date.today().year

    series_definitions = [
        {
            "id": INVOICE_SERIES_IDS[0],
            "prefix": "FAC",
            "series_type": "invoice",
            "description": t({"es": "Serie principal de facturas", "en": "Main invoice series"}),
            "current_number": len(INVOICE_SCENARIOS) + 1,
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

    series = []
    for s in series_definitions:
        series.append(
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
        )

    return series


def generate_invoices_data(catalog_items_map: dict[str, dict]) -> dict:
    """Generate invoice seed data.

    Args:
        catalog_items_map: Dictionary mapping internal_code to catalog item data
                          (must include id, default_price, vat_type_id, vat_rate)

    Returns:
        Dictionary with:
        - series: List of InvoiceSeries data (for backwards compatibility)
        - invoices: List of Invoice data
        - items: List of InvoiceItem data
        - payments: List of Payment data
    """
    from decimal import Decimal

    invoices = []
    items = []
    payments = []
    patients_data = get_patients_data()

    current_year = date.today().year

    # Series is now created separately via generate_invoice_series_data()
    series = generate_invoice_series_data()

    invoice_idx = 0
    item_idx = 0
    payment_idx = 0

    for scenario_idx, scenario in enumerate(INVOICE_SCENARIOS):
        patient = patients_data[scenario["patient_idx"]]
        invoice_id = INVOICE_IDS[invoice_idx]
        invoice_idx += 1

        # Calculate invoice number
        invoice_number = f"FAC-{current_year}-{scenario_idx + 1:04d}"
        sequential_number = scenario_idx + 1

        # Dates based on status
        is_overdue = scenario.get("overdue", False)
        if scenario["status"] == "draft":
            issue_date = None
            due_date = None
            days_ago = 5
        elif is_overdue:
            issue_date = date.today() - timedelta(days=45)
            due_date = date.today() - timedelta(days=15)  # 15 days overdue
            days_ago = 45
        else:
            days_ago = (7 - scenario_idx) * 3 + 5  # Spread out over time
            issue_date = date.today() - timedelta(days=days_ago)
            due_date = issue_date + timedelta(days=30)

        # Create invoice items and calculate totals
        invoice_items = []
        subtotal = Decimal("0.00")
        total_tax = Decimal("0.00")

        for item_data in scenario["items"]:
            catalog_item = catalog_items_map.get(item_data["code"])
            if not catalog_item:
                continue  # Skip if catalog item not found

            item_id = INVOICE_ITEM_IDS[item_idx]
            item_idx += 1

            unit_price = catalog_item["default_price"]
            quantity = item_data["qty"]
            vat_rate = catalog_item.get("vat_rate", 0.0) or 0.0

            line_subtotal = unit_price * quantity
            line_tax = line_subtotal * Decimal(str(vat_rate)) / 100
            line_total = line_subtotal + line_tax

            subtotal += line_subtotal
            total_tax += line_tax

            invoice_item = {
                "id": item_id,
                "clinic_id": CLINIC_ID,
                "invoice_id": invoice_id,
                "budget_item_id": None,
                "catalog_item_id": catalog_item["id"],
                "description": t(
                    {
                        "es": f"Tratamiento {item_data['code']}",
                        "en": f"Treatment {item_data['code']}",
                    }
                ),
                "internal_code": item_data["code"],
                "unit_price": unit_price,
                "quantity": quantity,
                "discount_type": None,
                "discount_value": None,
                "vat_type_id": catalog_item.get("vat_type_id"),
                "vat_rate": vat_rate,
                "vat_exempt_reason": None,
                "line_subtotal": line_subtotal,
                "line_discount": Decimal("0.00"),
                "line_tax": line_tax,
                "line_total": line_total,
                "tooth_number": item_data.get("tooth"),
                "surfaces": None,
                "display_order": len(invoice_items) + 1,
            }
            invoice_items.append(invoice_item)
            items.append(invoice_item)

        total = subtotal + total_tax

        # Calculate payments and balance
        total_paid = Decimal("0.00")
        invoice_payments = []

        for payment_data in scenario.get("payments", []):
            payment_id = PAYMENT_IDS[payment_idx]
            payment_idx += 1

            payment_amount = (total * payment_data["percent"]) / 100
            total_paid += payment_amount

            payment_date = issue_date + timedelta(days=3) if issue_date else date.today()

            payment = {
                "id": payment_id,
                "clinic_id": CLINIC_ID,
                "invoice_id": invoice_id,
                "amount": payment_amount,
                "payment_method": payment_data["method"],
                "payment_date": payment_date,
                "reference": f"REF-{payment_idx:04d}",
                "notes": None,
                "recorded_by": USER_RECEPTIONIST_ID,
                "is_voided": False,
                "voided_at": None,
                "voided_by": None,
                "void_reason": None,
            }
            invoice_payments.append(payment)
            payments.append(payment)

        balance_due = total - total_paid

        invoice = {
            "id": invoice_id,
            "clinic_id": CLINIC_ID,
            "patient_id": patient["id"],
            "invoice_number": invoice_number,
            "series_id": INVOICE_SERIES_IDS[0],
            "sequential_number": sequential_number,
            "budget_id": None,
            "credit_note_for_id": None,
            "status": scenario["status"],
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
            "balance_due": balance_due,
            "currency": t({"es": "EUR", "en": "USD"}),
            "internal_notes": t(scenario["notes"]) if scenario.get("notes") else None,
            "public_notes": None,
            "compliance_data": None,
            "document_hash": None,
            "created_by": USER_RECEPTIONIST_ID,
            "issued_by": USER_RECEPTIONIST_ID if scenario["status"] != "draft" else None,
            "deleted_at": None,
        }
        invoices.append(invoice)

    return {
        "series": series,
        "invoices": invoices,
        "items": items,
        "payments": payments,
    }


# =============================================================================
# Treatment Plan Seed Data
# =============================================================================

# Fixed UUIDs for treatment plans (expanded for more coverage)
TREATMENT_PLAN_IDS = [UUID(f"fe00bc99-9c0b-4ef8-bb6d-6bb9bd380{i:03x}") for i in range(20)]

# Reserved treatment IDs for plan items (separate from odontogram TREATMENT_IDS).
PLAN_TREATMENT_IDS = [UUID(f"fa00bc99-9c0b-4ef8-bb6d-6bb9bd381{i:03x}") for i in range(200)]

# Fixed UUIDs for planned treatment items (expanded for appointments)
PLANNED_ITEM_IDS = [UUID(f"ff00bc99-9c0b-4ef8-bb6d-6bb9bd380{i:03x}") for i in range(200)]

# Treatment plan scenarios
# Links to existing budgets where applicable
TREATMENT_PLAN_SCENARIOS = [
    # Plan 0: Draft plan for patient 3 (Carmen/Emma) - links to budget 0
    {
        "patient_idx": 3,
        "status": "draft",
        "budget_idx": 0,  # Links to BUDGET_IDS[0]
        "title": {"es": "Plan de tratamiento inicial", "en": "Initial treatment plan"},
        "items": [
            {"catalog_code": "DX-VISIT", "is_global": True},
            {"catalog_code": "DX-RXPAN", "is_global": True},
            {"catalog_code": "REST-COMP", "tooth": 16, "is_global": False},
        ],
        "diagnosis_notes": {
            "es": "Paciente con sensibilidad dental. Requiere empastes en molares.",
            "en": "Patient with dental sensitivity. Requires fillings on molars.",
        },
    },
    # Plan 1: Active plan for patient 6 (Javier/Daniel - diabetic) - links to budget 2
    {
        "patient_idx": 6,
        "status": "active",
        "budget_idx": 2,  # Links to BUDGET_IDS[2] (accepted)
        "title": {"es": "Coronas y endodoncia", "en": "Crowns and root canal"},
        "items": [
            {"catalog_code": "DX-VISIT", "is_global": True, "completed": True},
            {"catalog_code": "REST-CRO", "tooth": 36, "is_global": False},
            {"catalog_code": "ENDO-MULTI", "tooth": 36, "is_global": False},
        ],
        "diagnosis_notes": {
            "es": "Paciente diabético. Control especial de cicatrización.",
            "en": "Diabetic patient. Special healing monitoring.",
        },
    },
    # Plan 2: Active plan for patient 8 (Francisco/Alexander - allergic) - links to budget 3
    {
        "patient_idx": 8,
        "status": "active",
        "budget_idx": 3,  # Links to BUDGET_IDS[3] (accepted)
        "title": {"es": "Tratamiento periodontal", "en": "Periodontal treatment"},
        "items": [
            {"catalog_code": "PERIO-RAD", "is_global": True, "completed": True},
            {"catalog_code": "REST-COMP", "tooth": 17, "is_global": False},
            {"catalog_code": "REST-COMP", "tooth": 26, "is_global": False},
        ],
        "diagnosis_notes": {
            "es": "ALÉRGICO A PENICILINA. Usar alternativas.",
            "en": "ALLERGIC TO PENICILLIN. Use alternatives.",
        },
    },
    # Plan 3: Completed plan for patient 10 (Antonio/Robert) - links to budget 4
    {
        "patient_idx": 10,
        "status": "completed",
        "budget_idx": 4,  # Links to BUDGET_IDS[4] (completed)
        "title": {"es": "Prótesis parcial", "en": "Partial denture"},
        "items": [
            {"catalog_code": "PROT-PARC", "is_global": True, "completed": True},
            {"catalog_code": "DX-VISIT", "is_global": True, "completed": True},
        ],
        "diagnosis_notes": {
            "es": "Prótesis parcial superior entregada y ajustada.",
            "en": "Upper partial denture delivered and adjusted.",
        },
    },
    # Plan 4: Active plan for patient 9 (Rosa/Charlotte - hypertensive) - links to budget 6
    {
        "patient_idx": 9,
        "status": "active",
        "budget_idx": 6,  # Links to BUDGET_IDS[6] (accepted)
        "title": {"es": "Rehabilitación oral", "en": "Oral rehabilitation"},
        "items": [
            {"catalog_code": "DX-VISIT", "is_global": True, "completed": True},
            {"catalog_code": "REST-CRO", "tooth": 46, "is_global": False, "completed": True},
            {"catalog_code": "REST-CRO", "tooth": 36, "is_global": False},
            {"catalog_code": "ENDO-MULTI", "tooth": 36, "is_global": False},
        ],
        "diagnosis_notes": {
            "es": "Hipertensa - verificar presión antes de procedimientos.",
            "en": "Hypertensive - check blood pressure before procedures.",
        },
    },
    # Plan 5: Draft plan for patient 2 (Miguel/James) - no budget linked
    {
        "patient_idx": 2,
        "status": "draft",
        "budget_idx": None,
        "title": {"es": "Revisión y limpieza", "en": "Checkup and cleaning"},
        "items": [
            {"catalog_code": "DX-VISIT", "is_global": True},
            {"catalog_code": "PREV-LIMP", "is_global": True},
        ],
        "diagnosis_notes": {
            "es": "Paciente joven, buen estado general.",
            "en": "Young patient, good general condition.",
        },
    },
    # Plan 6: Active plan for patient 0 (María/John)
    {
        "patient_idx": 0,
        "status": "active",
        "budget_idx": None,
        "title": {"es": "Plan preventivo", "en": "Preventive plan"},
        "items": [
            {"catalog_code": "DX-VISIT", "is_global": True},
            {"catalog_code": "PREV-LIMP", "is_global": True},
            {"catalog_code": "DX-RXPAN", "is_global": True},
            {"catalog_code": "REST-COMP", "tooth": 26, "is_global": False},
        ],
        "diagnosis_notes": {
            "es": "Control preventivo anual.",
            "en": "Annual preventive checkup.",
        },
    },
    # Plan 7: Active plan for patient 1 (Carlos/Sarah)
    {
        "patient_idx": 1,
        "status": "active",
        "budget_idx": None,
        "title": {"es": "Tratamiento conservador", "en": "Conservative treatment"},
        "items": [
            {"catalog_code": "DX-VISIT", "is_global": True},
            {"catalog_code": "REST-COMP", "tooth": 36, "is_global": False},
            {"catalog_code": "REST-COMP", "tooth": 46, "is_global": False},
            {"catalog_code": "ENDO-UNI", "tooth": 46, "is_global": False},
        ],
        "diagnosis_notes": {
            "es": "Caries en molares inferiores.",
            "en": "Caries on lower molars.",
        },
    },
    # Plan 8: Active plan for patient 4 (Ana/Michael)
    {
        "patient_idx": 4,
        "status": "active",
        "budget_idx": None,
        "title": {"es": "Plan estético", "en": "Aesthetic plan"},
        "items": [
            {"catalog_code": "DX-VISIT", "is_global": True},
            {"catalog_code": "EST-BLANQ-C", "is_global": True},
            {"catalog_code": "PREV-LIMP", "is_global": True},
        ],
        "diagnosis_notes": {
            "es": "Paciente interesada en blanqueamiento.",
            "en": "Patient interested in whitening.",
        },
    },
    # Plan 9: Active plan for patient 5 (Luis/Jennifer)
    {
        "patient_idx": 5,
        "status": "active",
        "budget_idx": None,
        "title": {"es": "Extracciones y prótesis", "en": "Extractions and prosthetics"},
        "items": [
            {"catalog_code": "DX-VISIT", "is_global": True},
            {"catalog_code": "CIR-EXT-S", "tooth": 48, "is_global": False},
            {"catalog_code": "CIR-EXT-S", "tooth": 38, "is_global": False},
            {"catalog_code": "DX-RXPAN", "is_global": True},
        ],
        "diagnosis_notes": {
            "es": "Cordales impactados.",
            "en": "Impacted wisdom teeth.",
        },
    },
    # Plan 10: Active plan for patient 7 (Laura/Sophie)
    {
        "patient_idx": 7,
        "status": "active",
        "budget_idx": None,
        "title": {"es": "Revisión periódica", "en": "Periodic checkup"},
        "items": [
            {"catalog_code": "DX-VISIT", "is_global": True},
            {"catalog_code": "PREV-LIMP", "is_global": True},
            {"catalog_code": "REST-COMP", "tooth": 17, "is_global": False},
        ],
        "diagnosis_notes": {
            "es": "Control semestral.",
            "en": "Bi-annual checkup.",
        },
    },
    # Plan 11: Active plan for patient 11 (Isabel/William)
    {
        "patient_idx": 11,
        "status": "active",
        "budget_idx": None,
        "title": {"es": "Tratamiento integral", "en": "Comprehensive treatment"},
        "items": [
            {"catalog_code": "DX-VISIT", "is_global": True},
            {"catalog_code": "ENDO-UNI", "tooth": 36, "is_global": False},
            {"catalog_code": "REST-COMP", "tooth": 36, "is_global": False},
            {"catalog_code": "PREV-LIMP", "is_global": True},
        ],
        "diagnosis_notes": {
            "es": "Tratamiento de pulpitis.",
            "en": "Pulpitis treatment.",
        },
    },
    # Plan 12: Active plan for patient 12 (Pedro/Olivia)
    {
        "patient_idx": 12,
        "status": "active",
        "budget_idx": None,
        "title": {"es": "Urgencia dental", "en": "Dental emergency"},
        "items": [
            {"catalog_code": "DX-VISIT", "is_global": True},
            {"catalog_code": "CIR-EXT-S", "tooth": 46, "is_global": False},
        ],
        "diagnosis_notes": {
            "es": "Extracción urgente por absceso.",
            "en": "Urgent extraction due to abscess.",
        },
    },
    # Plan 13: Active plan for patient 13 (Teresa/Liam)
    {
        "patient_idx": 13,
        "status": "active",
        "budget_idx": None,
        "title": {"es": "Implantes", "en": "Implants"},
        "items": [
            {"catalog_code": "DX-VISIT", "is_global": True},
            {"catalog_code": "DX-RXPAN", "is_global": True},
            {"catalog_code": "PREV-LIMP", "is_global": True},
        ],
        "diagnosis_notes": {
            "es": "Evaluación para implantes.",
            "en": "Implant evaluation.",
        },
    },
    # Plan 14: Active plan for patient 14 (Ramón/Ava)
    {
        "patient_idx": 14,
        "status": "active",
        "budget_idx": None,
        "title": {"es": "Mantenimiento", "en": "Maintenance"},
        "items": [
            {"catalog_code": "DX-VISIT", "is_global": True},
            {"catalog_code": "PREV-LIMP", "is_global": True},
            {"catalog_code": "EST-BLANQ-C", "is_global": True},
        ],
        "diagnosis_notes": {
            "es": "Control y mantenimiento.",
            "en": "Control and maintenance.",
        },
    },
]


def generate_treatment_plans_data(catalog_items_map: dict[str, dict]) -> dict:
    """Generate treatment plan seed data.

    Args:
        catalog_items_map: Dictionary mapping internal_code to catalog item data
                          (must include id, default_price)

    Returns:
        Dictionary with:
        - plans: List of TreatmentPlan data
        - items: List of PlannedTreatmentItem data
    """
    plans = []
    items = []
    plan_treatments: list[dict] = []
    patients_data = get_patients_data()

    plan_idx = 0
    item_idx = 0

    for scenario_idx, scenario in enumerate(TREATMENT_PLAN_SCENARIOS):
        patient = patients_data[scenario["patient_idx"]]
        plan_id = TREATMENT_PLAN_IDS[plan_idx]
        plan_idx += 1

        # Calculate plan number
        plan_number = f"PLAN-2024-{scenario_idx + 1:04d}"

        # Get budget_id if linked
        budget_id = None
        if scenario.get("budget_idx") is not None:
            budget_id = BUDGET_IDS[scenario["budget_idx"]]

        plan = {
            "id": plan_id,
            "clinic_id": CLINIC_ID,
            "patient_id": patient["id"],
            "plan_number": plan_number,
            "title": t(scenario["title"]) if scenario.get("title") else None,
            "status": scenario["status"],
            "budget_id": budget_id,
            "assigned_professional_id": USER_DENTIST_ID,
            "created_by": USER_DENTIST_ID,
            "diagnosis_notes": t(scenario["diagnosis_notes"])
            if scenario.get("diagnosis_notes")
            else None,
            "internal_notes": None,
            "deleted_at": None,
        }
        plans.append(plan)

        # Create planned items: each item creates a Treatment (global, no teeth) backed by
        # the catalog item, then links a PlannedTreatmentItem via treatment_id.
        for seq_order, item_data in enumerate(scenario.get("items", []), start=1):
            catalog_item = catalog_items_map.get(item_data["catalog_code"])
            if not catalog_item:
                continue

            item_id = PLANNED_ITEM_IDS[item_idx]
            treatment_id = PLAN_TREATMENT_IDS[item_idx]
            item_idx += 1

            is_completed = item_data.get("completed", False)
            status = "performed" if is_completed else "planned"
            recorded_at = datetime.now() - timedelta(days=30)
            performed_at = datetime.now() - timedelta(days=10) if is_completed else None

            plan_treatments.append(
                {
                    "id": treatment_id,
                    "clinic_id": CLINIC_ID,
                    "patient_id": patient["id"],
                    "clinical_type": catalog_item.get(
                        "odontogram_treatment_type", "filling_composite"
                    ),
                    "catalog_item_id": catalog_item["id"],
                    "status": status,
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

            planned_item = {
                "id": item_id,
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
            items.append(planned_item)

    return {
        "plans": plans,
        "items": items,
        "plan_treatments": plan_treatments,
    }
