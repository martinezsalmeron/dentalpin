# Plan: Day 1 — Architecture + Backend Foundation

**Branch:** feature/day1-architecture
**Goal:** Implement the complete backend architecture as specified in CLAUDE.md Day 1.

---

## Scope

This plan covers Day 1 from CLAUDE.md:
- Generate full repo structure with all root files
- Implement plugin system (BaseModule, loader, registry, event bus)
- Implement all SQLAlchemy models
- Configure Alembic
- Implement JWT auth (register, login, refresh, RBAC middleware)
- Implement full CRUD endpoints for all entities
- Set up docker-compose.yml

**Verification:** `docker-compose up` → Swagger UI at :8000/docs with all endpoints working

---

## Tasks

### 1. Repository Structure

Create the full directory structure as specified:
```
/
├── README.md
├── LICENSE (BSL 1.1)
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md (Contributor Covenant v2.1)
├── docker-compose.yml
├── .github/workflows/ci.yml
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── alembic/
│   └── app/
│       ├── main.py
│       ├── config.py
│       ├── database.py
│       └── core/
│           ├── auth/
│           ├── plugins/
│           └── events/
└── docs/
```

### 2. Plugin System Implementation

Implement the modular plugin architecture:

**BaseModule (app/core/plugins/base.py):**
- Abstract base class with name, version, dependencies
- get_models() → list of SQLAlchemy models
- get_router() → FastAPI router
- get_event_handlers() → dict of event handlers
- get_permissions() → list of RBAC permissions

**Module Loader (app/core/plugins/loader.py):**
- Scan backend/app/modules/ for packages with BaseModule subclass
- Resolve dependency order
- Register all models with SQLAlchemy metadata
- Mount all routers under /api/v1/{module_name}/
- Subscribe event handlers to event bus

**Module Registry (app/core/plugins/registry.py):**
- Track loaded modules
- Dependency resolution
- Module discovery

### 3. Event Bus

**EventBus (app/core/events/bus.py):**
- Simple sync publish/subscribe
- handlers dict: event_type → list of callables
- subscribe(event_type, handler)
- publish(event_type, data)

**Event Types (app/core/events/types.py):**
- patient.created, patient.updated
- appointment.scheduled, appointment.completed, appointment.cancelled
- treatment.completed
- budget.created, budget.accepted
- invoice.created, invoice.paid

### 4. SQLAlchemy Models

Implement all models from CLAUDE.md:

**Core:**
- Clinic (id, name, tax_id, address, phone, email, settings, cabinets)
- User (id, email, password_hash, first_name, last_name, professional_id, is_active)
- ClinicMembership (id, user_id, clinic_id, role)

**Clinical Module:**
- Patient (id, clinic_id, first_name, last_name, national_id, dob, gender, phone, email, address, medical_history, insurance, notes, consent, status)
- Odontogram (id, patient_id, teeth JSONB)
- OdontogramHistory (id, odontogram_id, professional_id, changes, timestamp)
- Appointment (id, clinic_id, patient_id, professional_id, cabinet, start_time, end_time, treatment_type, status, notes, color)
- TreatmentCatalog (id, clinic_id, code, name, category, default_price, duration_minutes, requires_teeth, is_active)
- Treatment (id, clinic_id, patient_id, appointment_id, professional_id, treatment_code, description, tooth_numbers, surfaces, status, price, clinical_notes)
- Budget (id, clinic_id, patient_id, budget_number, items, total, status, valid_until, notes)
- ClinicalNote (id, clinic_id, patient_id, appointment_id, professional_id, date, subjective, objective, assessment, plan, attachments)
- Invoice (id, clinic_id, patient_id, budget_id, invoice_number, items, subtotal, tax_amount, total, status, payment_method, issued_at, paid_at, verifactu fields)

All models use:
- UUID primary keys
- TIMESTAMPTZ for all timestamps
- created_at, updated_at auto-managed fields

### 5. Database Configuration

**database.py:**
- AsyncEngine with PostgreSQL
- AsyncSession with sessionmaker
- get_db dependency
- Base declarative class

**Alembic Setup:**
- alembic.ini configuration
- env.py with async support
- Auto-detect from SQLAlchemy models

### 6. Authentication System

**Auth Router (app/core/auth/router.py):**
- POST /register — Create user account
- POST /login — Return JWT + refresh token
- POST /refresh — Refresh JWT
- GET /me — Current user info

**Auth Service (app/core/auth/service.py):**
- JWT creation with PyJWT
- Password hashing with bcrypt
- Token verification

**Auth Dependencies (app/core/auth/dependencies.py):**
- get_current_user — Extract user from JWT
- require_role(role) — RBAC middleware

### 7. Clinical Module CRUD

**Router (app/modules/clinical/router.py):**
All endpoints under /api/v1/clinical/:

Patients:
- GET /patients/ — List (paginated, searchable)
- POST /patients/ — Create
- GET /patients/{id} — Get with odontogram, appointments, budgets
- PUT /patients/{id} — Update
- DELETE /patients/{id} — Soft delete
- GET /patients/{id}/export — GDPR export

Odontogram:
- GET /odontograms/patient/{patient_id}
- PUT /odontograms/patient/{patient_id}
- PATCH /odontograms/patient/{patient_id}/tooth/{tooth_number}
- GET /odontograms/patient/{patient_id}/history

Appointments:
- GET /appointments/ — List (filterable)
- POST /appointments/
- GET /appointments/{id}
- PUT /appointments/{id}
- DELETE /appointments/{id}

Treatment Catalog:
- GET /treatment-catalog/
- POST /treatment-catalog/
- PUT /treatment-catalog/{id}
- DELETE /treatment-catalog/{id}

Treatments:
- GET /treatments/
- POST /treatments/
- PUT /treatments/{id}

Budgets:
- GET /budgets/
- POST /budgets/
- GET /budgets/{id}
- PUT /budgets/{id}
- PATCH /budgets/{id}/status
- GET /budgets/{id}/pdf

Clinical Notes:
- GET /notes/patient/{patient_id}
- POST /notes/
- PUT /notes/{id}

Invoices:
- GET /invoices/
- POST /invoices/
- GET /invoices/{id}
- PATCH /invoices/{id}/status
- GET /invoices/{id}/pdf

Clinics:
- GET /clinics/
- POST /clinics/
- GET /clinics/{id}
- PUT /clinics/{id}

### 8. Docker Setup

**docker-compose.yml:**
- db: postgres:15-alpine
- backend: FastAPI app
- frontend: placeholder for Day 2

**backend/Dockerfile:**
- Python 3.11
- Poetry or pip with pyproject.toml
- uvicorn entrypoint

### 9. Project Files

**README.md:** Project overview, setup instructions, tech stack
**LICENSE:** BSL 1.1 with use limitation clause
**CONTRIBUTING.md:** Contribution guidelines
**CODE_OF_CONDUCT.md:** Contributor Covenant v2.1

---

## Technical Decisions

1. **Async all the way:** Use AsyncSession, async endpoints, asyncpg driver
2. **Pydantic v2:** Request/response schemas with strict validation
3. **SQLAlchemy 2.0:** Modern mapped_column syntax, type hints
4. **JWT with refresh:** Access token (15min) + refresh token (7 days)
5. **Soft deletes:** Patient data archived, never hard deleted
6. **Event bus sync:** Simple sync bus for MVP, async later if needed

---

## Not In Scope (Day 1)

- Frontend (Day 2)
- Odontogram SVG component (Day 3)
- Calendar UI (Day 4)
- Budget PDF generation (Day 5)
- Seed data script (Day 6)
- CI/CD pipeline (Day 7)

---

## Success Criteria

1. `docker-compose up` starts all services
2. Swagger UI accessible at http://localhost:8000/docs
3. All CRUD endpoints functional
4. JWT auth flow works (register → login → protected endpoints)
5. Module system loads clinical module correctly
6. Event bus publishes events on entity changes
7. Alembic migrations run successfully
