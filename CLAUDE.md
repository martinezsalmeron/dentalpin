# CLAUDE.md — Dental Clinic Management Open Source Project

## Project Overview

Open source dental clinic management software. Modular architecture with plugin system.
Built to become the industry standard for dental practice management.

**Name:** [To be decided — candidates: ClinicCore, DentHub, OpenClinic, Odontux]
**License:** BSL 1.1 (Use Limitation: offering as commercial SaaS for dental clinic management. Change Date: 4 years. Change License: Apache 2.0)
**Backed by:** Dentaltix (dental supplies distributor)

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | **Vue 3 + Nuxt 3** with TypeScript |
| UI Components | **Nuxt UI** + **Tailwind CSS** |
| Backend | **FastAPI** (Python 3.11+) |
| ORM | **SQLAlchemy 2.0** with Pydantic v2 |
| Database | **PostgreSQL 15+** |
| Migrations | **Alembic** (auto-detect from SQLAlchemy models) |
| Auth | **JWT** with refresh tokens, RBAC |
| Containers | **Docker + Docker Compose** |
| CI/CD | **GitHub Actions** (ruff + eslint + pytest + vitest) |
| Docs | **MkDocs** with Material theme |

---

## Project Structure

```
/
├── README.md
├── LICENSE                          # BSL 1.1
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md               # Contributor Covenant v2.1
├── docker-compose.yml               # 3 services: frontend, backend, db
├── .github/
│   ├── workflows/
│   │   └── ci.yml                   # lint + test + build
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md
│   │   ├── feature_request.md
│   │   └── module_idea.md
│   └── PULL_REQUEST_TEMPLATE.md
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml               # ruff config, dependencies
│   ├── alembic/
│   │   └── alembic.ini
│   ├── app/
│   │   ├── main.py                  # FastAPI app, module loader
│   │   ├── config.py                # Settings via pydantic-settings
│   │   ├── database.py              # SQLAlchemy engine, session
│   │   ├── core/
│   │   │   ├── auth/
│   │   │   │   ├── router.py        # /api/v1/auth/login, register, refresh
│   │   │   │   ├── service.py       # JWT creation, password hashing
│   │   │   │   ├── dependencies.py  # get_current_user, require_role
│   │   │   │   └── models.py        # User, ClinicMembership
│   │   │   ├── plugins/
│   │   │   │   ├── registry.py      # Module discovery and registration
│   │   │   │   ├── base.py          # BaseModule abstract class
│   │   │   │   └── loader.py        # Auto-load modules on startup
│   │   │   └── events/
│   │   │       ├── bus.py           # Event bus (publish/subscribe)
│   │   │       └── types.py         # Event type definitions
│   │   └── modules/
│   │       └── clinical/
│   │           ├── __init__.py      # Module manifest
│   │           ├── models.py        # All SQLAlchemy models
│   │           ├── schemas.py       # Pydantic request/response schemas
│   │           ├── router.py        # FastAPI router with all endpoints
│   │           ├── service.py       # Business logic
│   │           └── seed.py          # Demo data seeder
│   └── tests/
│       ├── conftest.py              # Test DB, fixtures
│       └── modules/
│           └── clinical/
│               ├── test_patients.py
│               ├── test_appointments.py
│               └── test_budgets.py
├── frontend/
│   ├── Dockerfile
│   ├── nuxt.config.ts
│   ├── app.vue
│   ├── layouts/
│   │   └── default.vue              # Sidebar + header + content area
│   ├── pages/
│   │   ├── index.vue                # Dashboard
│   │   ├── login.vue
│   │   ├── patients/
│   │   │   ├── index.vue            # Patient list with search
│   │   │   └── [id].vue             # Patient detail with tabs
│   │   ├── appointments/
│   │   │   └── index.vue            # Weekly calendar view
│   │   ├── budgets/
│   │   │   ├── index.vue            # Budget list
│   │   │   └── [id].vue             # Budget detail / builder
│   │   ├── invoices/
│   │   │   └── index.vue            # Invoice list
│   │   ├── treatments/
│   │   │   └── index.vue            # Treatment catalog CRUD
│   │   └── settings/
│   │       └── index.vue            # Clinic settings, cabinets, users
│   ├── components/
│   │   ├── clinical/
│   │   │   ├── Odontogram.vue       # Interactive SVG dental chart
│   │   │   ├── OdontogramTooth.vue  # Single tooth component
│   │   │   ├── ToothPanel.vue       # Side panel for tooth details
│   │   │   ├── AppointmentCalendar.vue
│   │   │   ├── AppointmentModal.vue
│   │   │   ├── BudgetBuilder.vue
│   │   │   └── ClinicalNoteForm.vue
│   │   └── shared/
│   │       ├── PatientSearch.vue     # Reusable patient search autocomplete
│   │       └── PdfViewer.vue
│   ├── composables/
│   │   ├── useAuth.ts               # Auth state, login/logout
│   │   ├── useApi.ts                # Typed API client with JWT
│   │   ├── useModules.ts            # Module registry access
│   │   └── useClinic.ts             # Current clinic context
│   ├── utils/
│   │   └── moduleRegistry.ts        # Module registration system
│   └── plugins/
│       └── auth.ts                  # Auto-redirect if not authenticated
└── docs/
    ├── mkdocs.yml
    └── docs/
        ├── index.md                 # Project overview
        ├── getting-started.md       # Installation guide
        ├── architecture.md          # Architecture overview
        └── creating-modules.md      # How to create a module
```

---

## Plugin / Module Architecture

### Backend Module Contract

Every module is a Python package under `backend/app/modules/` that exposes a module class inheriting from `BaseModule`:

```python
# backend/app/core/plugins/base.py
from abc import ABC, abstractmethod
from fastapi import APIRouter
from sqlalchemy.orm import DeclarativeBase

class BaseModule(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique module identifier, e.g. 'clinical', 'supplies'"""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Semver string"""
        pass

    @property
    def dependencies(self) -> list[str]:
        """List of required module names"""
        return []

    @abstractmethod
    def get_models(self) -> list[type[DeclarativeBase]]:
        """SQLAlchemy models to register"""
        pass

    @abstractmethod
    def get_router(self) -> APIRouter:
        """FastAPI router, will be mounted at /api/v1/{self.name}/"""
        pass

    def get_event_handlers(self) -> dict[str, callable]:
        """Map of event_name -> handler function"""
        return {}

    def get_permissions(self) -> list[str]:
        """Custom permissions this module adds to RBAC"""
        return []
```

Example module manifest:

```python
# backend/app/modules/clinical/__init__.py
from app.core.plugins.base import BaseModule
from .models import Patient, Appointment, Treatment, Budget, Invoice, ...
from .router import router

class ClinicalModule(BaseModule):
    name = "clinical"
    version = "0.1.0"

    def get_models(self):
        return [Patient, Appointment, Treatment, TreatmentCatalog,
                Budget, ClinicalNote, Invoice, Odontogram]

    def get_router(self):
        return router

    def get_permissions(self):
        return ["patients.read", "patients.write", "appointments.manage",
                "budgets.create", "invoices.issue"]
```

### Module Loader (startup)

```python
# backend/app/core/plugins/loader.py
# On app startup:
# 1. Scan backend/app/modules/ for packages with BaseModule subclass
# 2. Resolve dependency order
# 3. Register all models with SQLAlchemy metadata
# 4. Mount all routers under /api/v1/{module_name}/
# 5. Subscribe event handlers to event bus
```

### Frontend Module Contract

Each module registers itself via `moduleRegistry.ts`:

```typescript
// frontend/utils/moduleRegistry.ts
interface ModuleDefinition {
  name: string
  label: string
  icon: string                    // Lucide icon name
  navigation: NavigationItem[]    // Sidebar entries
  dashboardWidgets?: Component[]  // Dashboard cards
  patientTabs?: PatientTab[]      // Tabs in patient detail view
}

const modules: ModuleDefinition[] = []

export function registerModule(mod: ModuleDefinition) {
  modules.push(mod)
}

export function getModules(): ModuleDefinition[] {
  return modules
}
```

The layout reads this registry to build the sidebar dynamically. Nuxt's file-based routing handles page registration automatically via the `/pages/` directory.

### Event Bus

```python
# backend/app/core/events/bus.py
class EventBus:
    """Simple sync event bus. Modules subscribe to events."""

    def __init__(self):
        self._handlers: dict[str, list[callable]] = {}

    def subscribe(self, event_type: str, handler: callable):
        self._handlers.setdefault(event_type, []).append(handler)

    def publish(self, event_type: str, data: dict):
        for handler in self._handlers.get(event_type, []):
            handler(data)

# Singleton
event_bus = EventBus()
```

Core events emitted by the clinical module:

| Event | Data | When |
|-------|------|------|
| `patient.created` | `{patient_id, clinic_id}` | New patient registered |
| `patient.updated` | `{patient_id, changes}` | Patient data modified |
| `appointment.scheduled` | `{appointment_id, patient_id, professional_id, start_time}` | New appointment created |
| `appointment.completed` | `{appointment_id, patient_id, treatments}` | Appointment marked complete |
| `appointment.cancelled` | `{appointment_id, reason}` | Appointment cancelled |
| `treatment.completed` | `{treatment_id, patient_id, treatment_code, tooth_numbers}` | Treatment finished |
| `budget.created` | `{budget_id, patient_id, total}` | New budget generated |
| `budget.accepted` | `{budget_id, patient_id}` | Patient accepted budget |
| `invoice.created` | `{invoice_id, patient_id, total, items}` | Invoice issued |
| `invoice.paid` | `{invoice_id, payment_method, amount}` | Invoice paid |

---

## Database Models

All models use UUID primary keys. All timestamps are TIMESTAMPTZ. All models include `created_at` and `updated_at` auto-managed fields.

### Clinic

```python
class Clinic(Base):
    __tablename__ = "clinics"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(200))
    tax_id: Mapped[str] = mapped_column(String(20))          # CIF/NIF
    address: Mapped[dict] = mapped_column(JSONB)              # {street, city, postal_code, country}
    phone: Mapped[str | None] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(255))
    settings: Mapped[dict] = mapped_column(JSONB, default={}) # {slot_duration_min: 15, currency: "EUR", timezone: "Europe/Madrid"}
    cabinets: Mapped[list] = mapped_column(JSONB, default=[]) # [{name: "Gabinete 1", color: "#3B82F6"}]
```

### User

```python
class User(Base):
    __tablename__ = "users"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    professional_id: Mapped[str | None] = mapped_column(String(50))  # Colegiado number
    is_active: Mapped[bool] = mapped_column(default=True)

class ClinicMembership(Base):
    __tablename__ = "clinic_memberships"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id"))
    role: Mapped[str] = mapped_column(String(20))  # admin, dentist, hygienist, assistant, receptionist
```

### Patient

```python
class Patient(Base):
    __tablename__ = "patients"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id"), index=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    national_id: Mapped[str | None] = mapped_column(String(20))   # DNI/NIE
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    gender: Mapped[str | None] = mapped_column(String(10))         # male, female, other
    phone: Mapped[str | None] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(255))
    address: Mapped[dict | None] = mapped_column(JSONB)
    medical_history: Mapped[dict] = mapped_column(JSONB, default={})  # {allergies:[], medications:[], conditions:[], notes:""}
    insurance: Mapped[dict | None] = mapped_column(JSONB)             # {provider, policy_number, coverage_type}
    notes: Mapped[str | None] = mapped_column(Text)
    consent_signed: Mapped[bool] = mapped_column(default=False)
    consent_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), default="active")  # active, inactive, archived
```

### Odontogram

One per patient. The `teeth` field is the complete dental state map.

```python
class Odontogram(Base):
    __tablename__ = "odontograms"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    patient_id: Mapped[UUID] = mapped_column(ForeignKey("patients.id"), unique=True)
    teeth: Mapped[dict] = mapped_column(JSONB, default={})
    # teeth structure:
    # {
    #   "18": {
    #     "status": "present",           # present | missing | implant | to_extract | unerupted
    #     "surfaces": {
    #       "mesial": "healthy",         # healthy | caries | filling | crown
    #       "distal": "caries",
    #       "occlusal": "filling",
    #       "vestibular": "healthy",
    #       "lingual": "healthy"
    #     },
    #     "conditions": ["root_canal"],  # root_canal | crown | bridge_anchor | veneer | fracture
    #     "notes": ""
    #   }
    # }
    # Keys use FDI notation: 11-18, 21-28, 31-38, 41-48 (adult), 51-85 (deciduous)

class OdontogramHistory(Base):
    """Tracks every change to the odontogram for audit trail."""
    __tablename__ = "odontogram_history"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    odontogram_id: Mapped[UUID] = mapped_column(ForeignKey("odontograms.id"))
    professional_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    changes: Mapped[dict] = mapped_column(JSONB)  # {tooth: "18", field: "surfaces.mesial", old: "healthy", new: "caries"}
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

### Appointment

```python
class Appointment(Base):
    __tablename__ = "appointments"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id"), index=True)
    patient_id: Mapped[UUID | None] = mapped_column(ForeignKey("patients.id"))  # nullable for blocks
    professional_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    cabinet: Mapped[str] = mapped_column(String(50))
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    treatment_type: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(20), default="scheduled")
    # Status values: scheduled, confirmed, in_progress, completed, cancelled, no_show
    notes: Mapped[str | None] = mapped_column(Text)
    color: Mapped[str | None] = mapped_column(String(7))  # hex color
```

### Treatment & TreatmentCatalog

```python
class TreatmentCatalog(Base):
    """Master table of available treatments with default prices and durations."""
    __tablename__ = "treatment_catalog"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id"), index=True)
    code: Mapped[str] = mapped_column(String(20))        # e.g. END001, COM003
    name: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(100))    # Endodoncia, Restauración, Cirugía...
    default_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    duration_minutes: Mapped[int] = mapped_column(Integer, default=30)
    requires_teeth: Mapped[bool] = mapped_column(default=True)
    is_active: Mapped[bool] = mapped_column(default=True)

class Treatment(Base):
    """Record of each treatment performed or planned."""
    __tablename__ = "treatments"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id"), index=True)
    patient_id: Mapped[UUID] = mapped_column(ForeignKey("patients.id"))
    appointment_id: Mapped[UUID | None] = mapped_column(ForeignKey("appointments.id"))
    professional_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    treatment_code: Mapped[str] = mapped_column(String(20))
    description: Mapped[str] = mapped_column(String(500))
    tooth_numbers: Mapped[list] = mapped_column(ARRAY(Integer), default=[])  # FDI numbers
    surfaces: Mapped[list | None] = mapped_column(ARRAY(String), default=[])
    status: Mapped[str] = mapped_column(String(20), default="planned")
    # Status: planned, in_progress, completed, cancelled
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    clinical_notes: Mapped[str | None] = mapped_column(Text)
```

### Budget

```python
class Budget(Base):
    __tablename__ = "budgets"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id"), index=True)
    patient_id: Mapped[UUID] = mapped_column(ForeignKey("patients.id"))
    budget_number: Mapped[str] = mapped_column(String(20))  # P-2026-001
    items: Mapped[list] = mapped_column(JSONB, default=[])
    # Each item: {treatment_code, description, tooth_numbers:[], quantity, unit_price, discount_percent, subtotal}
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    status: Mapped[str] = mapped_column(String(20), default="draft")
    # Status: draft, presented, accepted, rejected, expired
    valid_until: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)
```

### ClinicalNote

```python
class ClinicalNote(Base):
    """Per-visit clinical record in SOAP format."""
    __tablename__ = "clinical_notes"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id"), index=True)
    patient_id: Mapped[UUID] = mapped_column(ForeignKey("patients.id"))
    appointment_id: Mapped[UUID | None] = mapped_column(ForeignKey("appointments.id"))
    professional_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    subjective: Mapped[str | None] = mapped_column(Text)   # What the patient reports
    objective: Mapped[str | None] = mapped_column(Text)     # Clinical findings
    assessment: Mapped[str | None] = mapped_column(Text)    # Diagnosis
    plan: Mapped[str | None] = mapped_column(Text)          # Treatment plan
    attachments: Mapped[list | None] = mapped_column(JSONB, default=[])  # [{filename, path, type}]
```

### Invoice (Verifactu-ready)

```python
class Invoice(Base):
    __tablename__ = "invoices"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id"), index=True)
    patient_id: Mapped[UUID] = mapped_column(ForeignKey("patients.id"))
    budget_id: Mapped[UUID | None] = mapped_column(ForeignKey("budgets.id"))
    invoice_number: Mapped[str] = mapped_column(String(20), unique=True)  # F-2026-001
    items: Mapped[list] = mapped_column(JSONB, default=[])
    # Each item: {description, quantity, unit_price, tax_rate, subtotal}
    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    status: Mapped[str] = mapped_column(String(20), default="draft")
    # Status: draft, issued, paid, overdue, cancelled
    payment_method: Mapped[str | None] = mapped_column(String(20))
    # Values: cash, card, transfer, insurance
    issued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # --- Verifactu-ready fields (populated by future Verifactu module) ---
    invoice_hash: Mapped[str | None] = mapped_column(String(64))          # SHA-256 hash
    previous_invoice_hash: Mapped[str | None] = mapped_column(String(64)) # Chain link
    verifactu_status: Mapped[str | None] = mapped_column(String(20))      # none|pending|sent|accepted|rejected
    verifactu_metadata: Mapped[dict | None] = mapped_column(JSONB)        # {signature, qr_url, xml_record, aeat_response, sent_at}
```

---

## UI Specifications

### Layout (layouts/default.vue)

- **Sidebar** (left, fixed, collapsible): Built dynamically from `moduleRegistry`. Each module declares nav items with icon + label. Collapse to icons-only on small screens.
- **Header** (top): Clinic name + selector (for multi-clinic), current user name + role, logout button.
- **Content area**: Router view with the current page.
- **Color scheme**: Clean, professional. Light theme default. Use Nuxt UI's built-in theming.

### Odontogram (components/clinical/Odontogram.vue)

**This is the most important and complex UI component.**

- **SVG-based** interactive dental chart
- **32 adult teeth** in FDI notation: upper arch (18-11, 21-28), lower arch (48-41, 31-38)
- **20 deciduous teeth** (51-55, 61-65, 71-75, 81-85) — toggle with button
- **Each tooth** is an SVG group with clickable surfaces:
  - Posterior teeth (premolars, molars): 5 surfaces rendered as a cross pattern (occlusal center, mesial left, distal right, vestibular top/bottom, lingual bottom/top)
  - Anterior teeth (incisors, canines): 4 surfaces (incisal edge, mesial, distal, vestibular, lingual)
- **Click on tooth** → opens side panel (ToothPanel.vue) with:
  - Tooth status selector (present/missing/implant/to_extract/unerupted)
  - Conditions checklist (root_canal, crown, bridge_anchor, veneer, fracture)
  - Notes text field
- **Click on surface** → cycles through states: healthy (white) → caries (red) → filling (blue) → crown (yellow)
- **Color coding**:
  - White/default = healthy
  - Red (#EF4444) = caries/pathology
  - Blue (#3B82F6) = completed treatment
  - Green (#22C55E) = planned treatment
  - Gray (#9CA3AF) = missing
  - Yellow (#EAB308) = prosthesis
- **Save on every change** via API call, with optimistic UI update
- **History**: each change stored in OdontogramHistory with timestamp and professional

### Appointment Calendar (pages/appointments/index.vue)

- **Default view**: Weekly, columns = cabinets (from clinic.cabinets), rows = time slots
- **Slot duration**: configurable per clinic (15/20/30 min), from `clinic.settings.slot_duration_min`
- **Time range**: 8:00 - 21:00 (configurable)
- **Each appointment** = colored block spanning the correct number of slots
  - Shows: patient name + treatment type
  - Color by treatment category or custom color
  - Visual states: solid (confirmed), striped (pending), pulsing border (in progress), faded (completed), strikethrough (cancelled)
- **Click empty slot** → opens AppointmentModal.vue:
  - Patient search (autocomplete by name or phone)
  - Professional selector
  - Treatment type (from TreatmentCatalog, auto-sets duration)
  - Notes
- **Drag & drop**: move appointments between slots and cabinets
- **Day view toggle**: alternative single-column detailed view
- **Navigation**: prev/next week buttons, date picker to jump
- **Blocks**: ability to block slots (meeting, break, maintenance) without a patient

### Budget Builder (components/clinical/BudgetBuilder.vue)

- **Add lines** from TreatmentCatalog (search/select)
- Each line: treatment name, tooth numbers (clickable mini-odontogram or manual input), quantity, unit price (from catalog default, editable), discount %, subtotal
- **Auto-calculate total** on every change
- **Generate PDF** button: professional PDF with clinic logo, patient data, treatment breakdown, total, validity date
- **Status flow**: Draft → Presented → Accepted/Rejected (with buttons)
- **Create invoice** button: available when status = accepted, pre-fills invoice from budget items

### Dashboard (pages/index.vue)

Widget cards:
1. **Today's appointments**: count + next upcoming with patient name and time
2. **Recent patients**: last 5 patients seen
3. **Pending budgets**: count of budgets in "presented" status
4. **Monthly stats**: patients seen, treatments completed, revenue (from paid invoices)

---

## API Endpoints

All under `/api/v1/`. Authentication required except auth endpoints.

### Auth (`/api/v1/auth/`)
- `POST /register` — Create user account
- `POST /login` — Get JWT + refresh token
- `POST /refresh` — Refresh JWT
- `GET /me` — Current user info

### Clinics (`/api/v1/clinical/clinics/`)
- `GET /` — List user's clinics
- `POST /` — Create clinic (admin only)
- `GET /{id}` — Get clinic details
- `PUT /{id}` — Update clinic (admin only)

### Patients (`/api/v1/clinical/patients/`)
- `GET /` — List patients (paginated, searchable by name/phone/national_id)
- `POST /` — Create patient
- `GET /{id}` — Get patient with odontogram, recent appointments, budgets
- `PUT /{id}` — Update patient
- `DELETE /{id}` — Soft delete (set status=archived)
- `GET /{id}/export` — Export all patient data as JSON (GDPR)

### Odontogram (`/api/v1/clinical/odontograms/`)
- `GET /patient/{patient_id}` — Get odontogram
- `PUT /patient/{patient_id}` — Update odontogram (full replace)
- `PATCH /patient/{patient_id}/tooth/{tooth_number}` — Update single tooth
- `GET /patient/{patient_id}/history` — Odontogram change history

### Appointments (`/api/v1/clinical/appointments/`)
- `GET /` — List appointments (filterable by date range, cabinet, professional, status)
- `POST /` — Create appointment
- `GET /{id}` — Get appointment details
- `PUT /{id}` — Update appointment (reschedule, change status)
- `DELETE /{id}` — Cancel appointment

### Treatment Catalog (`/api/v1/clinical/treatment-catalog/`)
- `GET /` — List treatments (filterable by category)
- `POST /` — Create treatment type
- `PUT /{id}` — Update treatment type
- `DELETE /{id}` — Deactivate treatment type

### Treatments (`/api/v1/clinical/treatments/`)
- `GET /` — List treatments (filterable by patient, status)
- `POST /` — Record treatment
- `PUT /{id}` — Update treatment

### Budgets (`/api/v1/clinical/budgets/`)
- `GET /` — List budgets (filterable by patient, status)
- `POST /` — Create budget
- `GET /{id}` — Get budget details
- `PUT /{id}` — Update budget
- `PATCH /{id}/status` — Change status (present, accept, reject)
- `GET /{id}/pdf` — Generate PDF

### Clinical Notes (`/api/v1/clinical/notes/`)
- `GET /patient/{patient_id}` — List notes for patient
- `POST /` — Create clinical note
- `PUT /{id}` — Update note

### Invoices (`/api/v1/clinical/invoices/`)
- `GET /` — List invoices (filterable by patient, status, date range)
- `POST /` — Create invoice (optionally from budget_id)
- `GET /{id}` — Get invoice details
- `PATCH /{id}/status` — Mark as paid, cancelled
- `GET /{id}/pdf` — Generate PDF

---

## Seed Data

On `docker-compose up` in development mode, automatically seed:

- 1 clinic: "Clínica Dental Demo" with 3 cabinets
- 5 users: 1 admin, 2 dentists, 1 hygienist, 1 receptionist
- 30 patients with varied medical histories
- Treatment catalog with ~40 common dental treatments across categories (Endodoncia, Restauración, Cirugía, Periodoncia, Ortodoncia, Prótesis, Prevención, Estética)
- 20 appointments spread across the current week
- 5 budgets in various states
- 10 invoices
- 3 patients with populated odontograms

Default admin credentials: `admin@demo.clinic` / `demo1234`

---

## i18n

- Default language: **Spanish (es)**
- Use `@nuxtjs/i18n` module
- All UI strings in translation files, never hardcoded
- Prepare structure for: es, pt, fr, en (only es needs to be filled for MVP)

---

## Docker Compose

```yaml
services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: dental_clinic
      POSTGRES_USER: dental
      POSTGRES_PASSWORD: dental_dev
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  backend:
    build: ./backend
    environment:
      DATABASE_URL: postgresql+asyncpg://dental:dental_dev@db:5432/dental_clinic
      SECRET_KEY: dev-secret-key-change-in-production
      ENVIRONMENT: development
    ports:
      - "8000:8000"
    depends_on:
      - db
    volumes:
      - ./backend:/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build: ./frontend
    environment:
      API_BASE_URL: http://backend:8000
    ports:
      - "3000:3000"
    depends_on:
      - backend
    volumes:
      - ./frontend:/app
      - /app/node_modules
    command: npx nuxt dev --host 0.0.0.0

volumes:
  pgdata:
```

---

## Development Rules

1. **All code in English** (variable names, comments, function names). UI strings in Spanish via i18n.
2. **Type everything** — TypeScript strict mode in frontend, Python type hints everywhere in backend.
3. **Test critical paths** — At minimum: patient CRUD, appointment CRUD, budget creation, invoice generation.
4. **Format on save** — ruff for Python, eslint+prettier for TypeScript/Vue.
5. **Every endpoint returns consistent JSON** — `{data: ..., message: "...", errors: [...]}`.
6. **Pagination** — All list endpoints return `{data: [...], total: N, page: N, page_size: N}`.
7. **Soft deletes** — Never hard delete patient data. Use status fields.
8. **Audit log** — Log who accessed/modified patient data (GDPR requirement for health data).

---

## Day-by-Day Build Plan

### Day 1: Architecture + Backend
- Generate full repo structure with all root files
- Implement plugin system (BaseModule, loader, registry, event bus)
- Implement all SQLAlchemy models
- Configure Alembic
- Implement JWT auth (register, login, refresh, RBAC middleware)
- Implement full CRUD endpoints for all entities
- Set up docker-compose.yml
- **Verify:** `docker-compose up` → Swagger UI at :8000/docs with all endpoints working

### Day 2: Frontend Base + Patients
- Init Nuxt 3 project with TypeScript, Tailwind, Nuxt UI
- Build default.vue layout with dynamic sidebar
- Implement moduleRegistry.ts and useModules composable
- Build patient pages: list (search + filters), detail (tabs), create/edit form
- Implement auth in frontend: login page, JWT storage, route guards
- **Verify:** Login → create patient → search → view detail with tabs

### Day 3: Odontogram
- Build Odontogram.vue SVG component with 32 adult teeth
- Implement surface clicking with color state changes
- Build ToothPanel.vue side panel
- Add deciduous teeth toggle
- Connect to API for persistence
- **Verify:** Open patient → click teeth/surfaces → colors update → survives reload

### Day 4: Appointment Calendar
- Build weekly calendar with cabinet columns and time slots
- Create AppointmentModal.vue with patient search
- Implement color coding and visual states
- Implement drag & drop for rescheduling
- Add day view toggle
- **Verify:** Navigate weeks → create appointments → drag between slots/cabinets

### Day 5: Budgets + Invoices + Clinical Notes
- Build BudgetBuilder.vue with treatment catalog integration
- Implement PDF generation for budgets and invoices
- Implement budget status flow
- Implement invoice creation from accepted budget
- Build ClinicalNoteForm.vue with SOAP format
- **Verify:** Create budget → generate PDF → accept → create invoice → record clinical note

### Day 6: Dashboard + Catalog + Polish
- Build dashboard with widget cards
- Implement TreatmentCatalog CRUD page
- Polish all UX flows (loading states, empty states, error messages, toast notifications)
- Set up i18n with Spanish translations
- Create seed data script
- **Verify:** Dashboard shows real data, catalog is editable, all flows work without visible errors

### Day 7: Tests + CI + Docs + Deploy
- Write pytest tests for critical API endpoints
- Write basic vitest tests for main components
- Configure GitHub Actions CI
- Complete README.md with screenshots
- Write architecture docs and module creation guide
- Deploy demo instance
- Publish repository
- **Verify:** CI green, demo online, docs enable setup in <10 min
