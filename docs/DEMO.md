# Demo Data Documentation

This document describes the demo data created by the seed script for testing and evaluation of DentalPin.

## Quick Setup

```bash
# Start services
docker-compose up -d

# Seed demo data
./scripts/seed-demo.sh

# Open browser
open http://localhost:3000
```

## Demo Credentials

All users have password: **`demo1234`**

| Email | Role | Name | Permissions |
|-------|------|------|-------------|
| admin@demo.clinic | admin | Admin Demo | Full access to all features |
| dentist@demo.clinic | dentist | Dra. María García López | Clinical module, own appointments |
| hygienist@demo.clinic | hygienist | Carlos López Martínez | Patients (read), appointments |
| assistant@demo.clinic | assistant | Ana Martínez Ruiz | Patients, appointments |
| receptionist@demo.clinic | receptionist | Laura Sánchez Pérez | Patients, appointments |

### Testing Each Role

1. **Admin** - Can access Settings, manage users, see all data
2. **Dentist** - Can manage patients, view/edit appointments, sees professional calendar
3. **Hygienist** - Can view patients, manage own appointments
4. **Assistant** - Can manage patients and appointments (no settings access)
5. **Receptionist** - Same as assistant (front desk workflow)

## Demo Data Contents

### Clinic

- **Name:** Clínica Dental Demo
- **Tax ID:** B12345678
- **Location:** Calle Gran Vía 123, Madrid 28013
- **Cabinets:** Gabinete 1 (blue), Gabinete 2 (green)
- **Hours:** Mon-Fri 9:00-14:00, 16:00-20:00
- **Timezone:** Europe/Madrid

### Patients (15)

The seed includes 15 patients with varied demographics:

| Patient | Age Group | Notes |
|---------|-----------|-------|
| Pablo Fernández | Child (8) | Pediatric patient |
| Lucía Rodríguez | Teen (14) | Orthodontic treatment |
| Miguel González | Young adult (26) | - |
| Carmen Díaz | Young adult (29) | Dental sensitivity |
| David Martín | Adult (32) | - |
| Elena Ruiz | Adult (39) | Pregnant, no x-rays |
| Javier Sánchez | Adult (44) | Diabetic |
| Isabel López | Adult (46) | - |
| Francisco García | Adult (49) | Penicillin allergy |
| Rosa Martínez | Adult (54) | Hypertensive |
| Antonio Hernández | Senior (64) | Partial denture |
| María Teresa Romero | Senior (69) | Implants |
| José Luis Muñoz | Senior (74) | On anticoagulants |
| Dolores Vega | Senior (76) | - |
| Manuel Castro | Senior (79) | Full denture |

### Appointments (35-40)

Appointments are generated dynamically relative to "today":

- **Last week:** 10-12 appointments (completed, no_show)
- **Current week:** 15-18 appointments (scheduled, confirmed, in_progress)
- **Next week:** 10-12 appointments (scheduled)

**Treatment types:**
- Revisión (30 min)
- Limpieza dental (45 min)
- Empaste (45 min)
- Extracción (60 min)
- Endodoncia (90 min)
- Ortodoncia - Revisión (30 min)
- Blanqueamiento (60 min)
- Implante - Consulta (45 min)
- Urgencia (30 min)

Appointments are distributed between:
- Both professionals (dentist and hygienist)
- Both cabinets
- Morning (9:00-14:00) and afternoon (16:00-20:00) slots

## Scripts Reference

### `./scripts/seed-demo.sh`

Seeds the database with demo data. Safe to run multiple times (checks for existing data).

```bash
./scripts/seed-demo.sh
```

### `./scripts/reset-db.sh`

Resets the database by clearing alembic version and running migrations. Does NOT seed data.

```bash
./scripts/reset-db.sh
```

### `./scripts/setup-demo.sh`

Full reset: clears database AND seeds demo data in one command.

```bash
./scripts/setup-demo.sh
```

## Resetting Demo Data

To start fresh:

```bash
# Option 1: Full reset
./scripts/setup-demo.sh

# Option 2: Manual steps
./scripts/reset-db.sh
./scripts/seed-demo.sh
```

## Customizing Demo Data

Demo data is defined in `backend/app/seeds/demo_data.py`.

### Adding Patients

```python
# In PATIENTS_DATA list
{
    "id": UUID("..."),  # Generate new UUID
    "first_name": "Name",
    "last_name": "Surname",
    "phone": "+34 612 345 XXX",
    "email": "email@example.com",  # Optional
    "date_of_birth": date(1990, 1, 1),
    "notes": "Clinical notes",  # Optional
},
```

### Adding Users

```python
# In USERS_DATA list
{
    "id": UUID("..."),
    "email": "newuser@demo.clinic",
    "first_name": "First",
    "last_name": "Last",
    "role": "dentist",  # admin, dentist, hygienist, assistant, receptionist
    "membership_id": UUID("..."),
},
```

### Modifying Appointment Generation

Edit the `generate_appointments()` function in `demo_data.py` to change:
- Number of appointments per week
- Treatment types
- Time slot distribution
- Status distribution

## Troubleshooting

### "Demo data already exists"

The seed script detects existing data. To reset:

```bash
./scripts/setup-demo.sh
```

### Login fails with valid credentials

Password hash may be corrupted. Reset and reseed:

```bash
./scripts/setup-demo.sh
```

### Appointments not showing in calendar

1. Check you're viewing the correct week (appointments are relative to today)
2. Verify the professional filter isn't excluding appointments
3. Check the cabinet filter

### Database connection errors

Ensure services are running:

```bash
docker-compose up -d
docker-compose ps  # Check status
```
