<!-- /autoplan restore point: /Users/ramonmartinez/.gstack/projects/dentalpin/feature-day1-architecture-autoplan-restore-20260330-155517.md -->
# Plan: DentalPin MVP — Full Implementation

**Branch:** feature/day1-architecture
**Goal:** Implement the complete MVP: Agenda + Pacientes with modular architecture
**Scope:** Full 7-day build as specified in CLAUDE.md, scoped to the reduced MVP from design doc

---

## MVP Scope (from /office-hours design doc)

The MVP is "Agenda + Pacientes" with full modular architecture:
- Backend: Plugin system, JWT auth, Patient CRUD, Appointment CRUD, single clinic
- Frontend: Login, patient list/detail, weekly calendar
- Infrastructure: docker-compose, README, seed data

**Explicitly NOT in MVP:**
- Odontogram (deferred to TODOS.md)
- Budgets/Invoices (deferred)
- Verifactu integration (schema fields only)
- RBAC beyond admin role
- Multi-clinic support
- Calendar drag-and-drop
- Multi-cabinet calendar view

---

## Day 1: Architecture + Backend Foundation

### 1.1 Repository Structure

```
/
├── README.md
├── LICENSE (BSL 1.1)
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── docker-compose.yml
├── .github/
│   └── workflows/ci.yml
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
├── frontend/
│   └── [Day 2]
└── docs/
```

### 1.2 Plugin System

**BaseModule (app/core/plugins/base.py):**
```python
class BaseModule(ABC):
    @property
    @abstractmethod
    def name(self) -> str: pass

    @property
    @abstractmethod
    def version(self) -> str: pass

    @property
    def dependencies(self) -> list[str]: return []

    @abstractmethod
    def get_models(self) -> list[type[DeclarativeBase]]: pass

    @abstractmethod
    def get_router(self) -> APIRouter: pass

    def get_event_handlers(self) -> dict[str, callable]: return {}
    def get_permissions(self) -> list[str]: return []
```

**Module Loader (app/core/plugins/loader.py):**
- Scan `backend/app/modules/` for BaseModule subclasses
- Resolve dependency order (topological sort)
- Register models with SQLAlchemy metadata
- Mount routers at `/api/v1/{module_name}/`
- Subscribe event handlers

**Module Registry (app/core/plugins/registry.py):**
- `get_module(name)` → ModuleInstance
- `list_modules()` → list[ModuleInstance]
- `is_loaded(name)` → bool

### 1.3 Event Bus (Stub for MVP)

```python
class EventBus:
    def __init__(self):
        self._handlers: dict[str, list[callable]] = {}

    def subscribe(self, event_type: str, handler: callable):
        self._handlers.setdefault(event_type, []).append(handler)

    def publish(self, event_type: str, data: dict):
        # MVP: log to console, no actual subscribers
        logger.info(f"Event: {event_type}", extra={"data": data})
        for handler in self._handlers.get(event_type, []):
            handler(data)

event_bus = EventBus()  # Singleton
```

### 1.4 SQLAlchemy Models (MVP subset)

**Core models (app/core/auth/models.py):**
- Clinic (id, name, tax_id, address, phone, email, settings, cabinets)
- User (id, email, password_hash, first_name, last_name, professional_id, is_active)
- ClinicMembership (id, user_id, clinic_id, role)

**Clinical module (app/modules/clinical/models.py):**
- Patient (id, clinic_id, first_name, last_name, phone, email, date_of_birth, notes, status)
  - MVP fields only: skip medical_history, insurance, address, consent for now
- Appointment (id, clinic_id, patient_id, professional_id, cabinet, start_time, end_time, treatment_type, status, notes, color)

**All models:**
- UUID primary keys (uuid4)
- TIMESTAMPTZ for all timestamps
- `created_at`, `updated_at` auto-managed via SQLAlchemy events

### 1.5 Database Configuration

**database.py:**
```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=1800
)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session
```

**Alembic:**
- `alembic.ini` configured for asyncpg
- `env.py` with async support
- Single initial migration for MVP schema

### 1.6 Authentication System

**JWT Configuration:**
- Access token TTL: 15 minutes
- Refresh token TTL: 7 days
- Algorithm: HS256
- Secret from environment variable
- Token revocation: User model includes `token_version` field. On password change or "logout all", increment version. Validate version claim on refresh.

**Rate Limiting (slowapi):**
- `/login`: 5 attempts per minute per IP
- `/register`: 3 per hour per IP
- `/refresh`: 10 per minute per user

**Password Requirements:**
- Minimum 8 characters
- At least one letter and one number

**Auth Router (app/core/auth/router.py):**
```
POST /api/v1/auth/register  → Create user, return tokens
POST /api/v1/auth/login     → Verify credentials, return tokens
POST /api/v1/auth/refresh   → Exchange refresh token for new access token
GET  /api/v1/auth/me        → Return current user info
```

**Auth Service (app/core/auth/service.py):**
- `hash_password(password)` → bcrypt hash
- `verify_password(password, hash)` → bool
- `create_access_token(user_id, clinic_id)` → JWT
- `create_refresh_token(user_id)` → JWT
- `decode_token(token)` → payload or raises

**Auth Dependencies (app/core/auth/dependencies.py):**
```python
async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    # Decode JWT, fetch user from DB

async def get_clinic_context(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ClinicContext:
    # Return user + their active clinic membership
```

### 1.7 Clinical Module CRUD

**Schemas (app/modules/clinical/schemas.py):**
- PatientCreate, PatientUpdate, PatientResponse
- AppointmentCreate, AppointmentUpdate, AppointmentResponse
- Pagination: `{data: [...], total: N, page: N, page_size: N}`

**Router (app/modules/clinical/router.py):**

Patients:
```
GET    /patients/           → List (paginated, searchable by name/phone)
POST   /patients/           → Create patient
GET    /patients/{id}       → Get patient detail
PUT    /patients/{id}       → Update patient
DELETE /patients/{id}       → Soft delete (status=archived)
```

Appointments:
```
GET    /appointments/       → List (filterable by date_range, cabinet, professional, status)
POST   /appointments/       → Create (with conflict check → 409 if slot occupied)
GET    /appointments/{id}   → Get detail
PUT    /appointments/{id}   → Update (reschedule, change status)
DELETE /appointments/{id}   → Cancel (set status=cancelled)
```

Clinics:
```
GET    /clinics/            → List user's clinics
GET    /clinics/{id}        → Get clinic detail (cabinets, settings)
```

**Service (app/modules/clinical/service.py):**
- Business logic separated from router
- Event publishing on create/update/delete
- Appointment conflict detection via database unique index (race-condition safe):
  ```sql
  CREATE UNIQUE INDEX idx_appointment_slot
  ON appointments (clinic_id, cabinet, professional_id, start_time)
  WHERE status NOT IN ('cancelled');
  ```
- On IntegrityError from index: return 409 Conflict
- Validate patient exists AND belongs to same clinic before creating appointment (return 404 if not)

### 1.8 Docker Setup

**docker-compose.yml:**
```yaml
services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: dental_clinic
      POSTGRES_USER: dental
      POSTGRES_PASSWORD: dental_dev
    ports: ["5432:5432"]
    volumes: [pgdata:/var/lib/postgresql/data]

  backend:
    build: ./backend
    environment:
      DATABASE_URL: postgresql+asyncpg://dental:dental_dev@db:5432/dental_clinic
      SECRET_KEY: dev-secret-key-change-in-production
      ENVIRONMENT: development
    ports: ["8000:8000"]
    depends_on: [db]
    volumes: ["./backend:/app"]
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build: ./frontend
    environment:
      API_BASE_URL: http://backend:8000
    ports: ["3000:3000"]
    depends_on: [backend]
    volumes: ["./frontend:/app", "/app/node_modules"]
    command: npx nuxt dev --host 0.0.0.0

volumes:
  pgdata:
```

**backend/Dockerfile:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir .
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 1.9 CORS Configuration

```python
# backend/app/main.py
from fastapi.middleware.cors import CORSMiddleware

# CORS: Explicitly require ALLOWED_ORIGINS in production
if settings.ENVIRONMENT == "production" and not settings.ALLOWED_ORIGINS:
    raise ValueError("ALLOWED_ORIGINS must be set in production")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.ENVIRONMENT == "development" else settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Day 1 Verification:**
- `docker-compose up` starts all services
- Swagger UI at http://localhost:8000/docs
- All CRUD endpoints functional
- JWT auth flow works

---

## Day 2: Frontend Base + Patients

### 2.1 Nuxt 3 Project Setup

```bash
npx nuxi init frontend
cd frontend
npm install @nuxt/ui @nuxtjs/i18n
```

**nuxt.config.ts:**
```typescript
export default defineNuxtConfig({
  modules: ['@nuxt/ui', '@nuxtjs/i18n'],
  i18n: {
    locales: ['es'],
    defaultLocale: 'es',
    vueI18n: './i18n.config.ts'
  },
  runtimeConfig: {
    public: {
      apiBaseUrl: process.env.API_BASE_URL || 'http://localhost:8000'
    }
  }
})
```

### 2.2 Layout (layouts/default.vue)

```
+------------------------------------------+
|  Header: Clinic name | User | Logout     |
+--------+---------------------------------+
| Sidebar|                                 |
| - Inicio                                 |
| - Pacientes                              |
| - Agenda                                 |
|        |     [Router View]               |
|        |                                 |
+--------+---------------------------------+
```

- Sidebar: collapsible, icons + labels
- Built dynamically from moduleRegistry
- Current clinic selector (future: multi-clinic)

### 2.3 Module Registry (utils/moduleRegistry.ts)

```typescript
interface ModuleDefinition {
  name: string
  label: string
  icon: string
  navigation: NavigationItem[]
}

const modules: ModuleDefinition[] = []

export function registerModule(mod: ModuleDefinition) {
  modules.push(mod)
}

export function getModules(): ModuleDefinition[] {
  return modules
}
```

### 2.4 Auth Composable (composables/useAuth.ts)

```typescript
export function useAuth() {
  const user = useState<User | null>('user', () => null)
  const accessToken = useCookie('access_token')
  const refreshToken = useCookie('refresh_token')

  async function login(email: string, password: string) { ... }
  async function logout() { ... }
  async function refresh() { ... }
  function isAuthenticated() { return !!accessToken.value }

  return { user, login, logout, refresh, isAuthenticated }
}
```

### 2.5 API Client (composables/useApi.ts)

```typescript
export function useApi() {
  const config = useRuntimeConfig()
  const auth = useAuth()

  async function $api<T>(path: string, options?: FetchOptions): Promise<T> {
    return $fetch(path, {
      baseURL: config.public.apiBaseUrl,
      headers: {
        Authorization: `Bearer ${auth.accessToken.value}`
      },
      ...options
    })
  }

  return { $api }
}
```

### 2.6 Login Page (pages/login.vue)

- Email + password form
- Submit → POST /api/v1/auth/login
- On success: store tokens, redirect to /
- Error states: invalid credentials, network error

### 2.7 Patient List (pages/patients/index.vue)

```
+------------------------------------------+
| Pacientes                    [+ Nuevo]   |
+------------------------------------------+
| Search: [__________________] [Buscar]    |
+------------------------------------------+
| Nombre       | Teléfono  | Estado | →    |
|--------------|-----------|--------|------|
| García, Juan | 612...    | Activo |  >   |
| López, María | 655...    | Activo |  >   |
+------------------------------------------+
| < Anterior  Página 1 de 5  Siguiente >   |
+------------------------------------------+
```

- Paginated table (default 20 per page)
- Search by name or phone
- Click row → navigate to patient detail
- [+ Nuevo] → opens create modal

### 2.8 Patient Detail (pages/patients/[id].vue)

```
+------------------------------------------+
| ← Pacientes   |   García, Juan           |
+------------------------------------------+
| [Info] [Historial] [Citas]               |
+------------------------------------------+
| Tab: Info                                |
|   Nombre: Juan García                    |
|   Teléfono: 612 345 678                  |
|   Email: juan@example.com                |
|   Fecha nacimiento: 15/03/1985           |
|   Notas: ...                             |
|                           [Editar]       |
+------------------------------------------+
| Tab: Historial                           |
|   "Notas clínicas disponibles en         |
|    futura versión"                       |
+------------------------------------------+
| Tab: Citas                               |
|   [List of patient's appointments]       |
+------------------------------------------+
```

### 2.9 Error Handling

**Frontend error states:**
- 404: "Paciente no encontrado" + back link
- 403: Redirect to list with toast
- 500: Toast with retry button
- Network error: Toast with retry

**API timeout:** 10 seconds, then error state

**Day 2 Verification:**
- Login → see patient list
- Create patient → appears in list
- Search → filters correctly
- Click patient → see detail with tabs

---

## Day 3: Appointment Calendar

### 3.1 Weekly Calendar View (pages/appointments/index.vue)

```
+--------------------------------------------------+
| Agenda              < Semana Actual >   [Hoy]    |
+--------------------------------------------------+
|       | Lun 15 | Mar 16 | Mie 17 | Jue 18 | ...  |
| 08:00 |        |        |        |        |      |
| 08:15 |        | García |        |        |      |
| 08:30 |        | García |        |        |      |
| 08:45 |        |        |        |        |      |
| 09:00 |        |        | López  |        |      |
| ...   |        |        |        |        |      |
+--------------------------------------------------+
```

- **Slot duration:** 15 minutes (hardcoded for MVP)
- **Time range:** 08:00 - 21:00
- **Columns:** Days of current week (Mon-Sun)
- **Navigation:** prev/next week buttons, "Hoy" to jump to current week

### 3.2 Appointment Display

- **Block height:** spans correct number of slots based on duration
- **Content:** Patient name + treatment type
- **Visual states:**
  - `scheduled`: solid color
  - `confirmed`: solid + checkmark icon
  - `in_progress`: pulsing border
  - `completed`: faded
  - `cancelled`: strikethrough
  - `no_show`: red border

### 3.3 Appointment Modal (components/clinical/AppointmentModal.vue)

```
+------------------------------------------+
| Nueva Cita                         [X]   |
+------------------------------------------+
| Paciente: [____________________] (search)|
| Profesional: [Dropdown]                  |
| Gabinete: [Dropdown]                     |
| Fecha: [Date picker]                     |
| Hora inicio: [Time picker]               |
| Duración: [30 min ▼]                     |
| Tipo tratamiento: [Optional text]        |
| Notas: [Textarea]                        |
+------------------------------------------+
|                    [Cancelar] [Guardar]  |
+------------------------------------------+
```

- Patient search: autocomplete by name/phone (PatientSearch component)
- Professional dropdown: populated from clinic members
- Gabinete dropdown: from clinic.cabinets
- Duration: 15, 30, 45, 60 minutes

### 3.4 Click Interactions

- **Click empty slot:** Opens AppointmentModal with pre-filled date/time
- **Click existing appointment:** Opens modal in edit mode
- **Edit modal options:** Update details, Cancel appointment

### 3.5 Conflict Detection

When saving appointment:
1. POST/PUT to backend
2. Backend checks for conflicts (same cabinet + professional + overlapping time)
3. If 409 Conflict: show toast "Este horario ya está ocupado"

### 3.6 Loading UX

- **Initial load:** Skeleton loader for calendar grid
- **API timeout:** 10 seconds, then show error with retry button
- **Saving:** Button shows spinner, disabled during save

**Day 3 Verification:**
- Navigate weeks → calendar updates
- Click empty slot → create appointment modal
- Create appointment → appears in calendar
- Click appointment → edit/cancel
- Conflict → 409 error shown

---

## Day 4: Patient Search + Polish

### 4.1 PatientSearch Component (components/shared/PatientSearch.vue)

```typescript
// Props
interface PatientSearchProps {
  modelValue: Patient | null
  placeholder?: string
}

// Emits
defineEmits<{
  'update:modelValue': [patient: Patient | null]
}>()
```

- Debounced search (300ms)
- Shows name + phone in dropdown
- Keyboard navigation (up/down/enter)
- Clear button

### 4.2 Toast Notifications

Using Nuxt UI's `useToast()`:
```typescript
const toast = useToast()
toast.add({ title: 'Paciente creado', color: 'green' })
toast.add({ title: 'Error al guardar', color: 'red' })
```

### 4.3 Loading States

- **Tables:** Skeleton rows while loading
- **Forms:** Button spinner + disabled during submit
- **Page transitions:** NProgress bar

### 4.4 Empty States

| Location | Empty State Message | Action |
|----------|---------------------|--------|
| Patient list | "No hay pacientes registrados" | "Crear primer paciente" button |
| Patient search (no results) | "No se encontraron pacientes" | — |
| Appointments (day with none) | Day column is empty | Click to create |
| Patient appointments tab | "Este paciente no tiene citas" | "Agendar cita" button |

### 4.5 Form Validation

- **Client-side:** Required fields marked, inline error messages
- **Server-side:** 422 errors mapped to field messages
- Pattern: VeeValidate with Zod schemas matching backend Pydantic

### 4.6 i18n Setup

```typescript
// i18n.config.ts
export default defineI18nConfig(() => ({
  legacy: false,
  locale: 'es',
  messages: {
    es: {
      patients: {
        title: 'Pacientes',
        create: 'Nuevo paciente',
        // ...
      },
      appointments: {
        title: 'Agenda',
        // ...
      }
    }
  }
}))
```

**Day 4 Verification:**
- Patient search works in appointment modal
- Toast notifications appear correctly
- Empty states show appropriate messages
- Form validation provides clear feedback

---

## Day 5: Dashboard + Settings

### 5.1 Dashboard (pages/index.vue)

```
+------------------------------------------+
| Dashboard                                |
+------------------------------------------+
| +----------------+ +-------------------+ |
| | Citas Hoy      | | Pacientes recientes |
| | 5 citas        | | • García, Juan     |
| | Próxima: 10:00 | | • López, María     |
| | García, Juan   | | • Pérez, Carlos    |
| +----------------+ +-------------------+ |
+------------------------------------------+
```

**Widgets:**
1. **Citas Hoy:** Count + next upcoming
2. **Pacientes Recientes:** Last 5 seen

**Future widgets (NOT MVP):**
- Presupuestos pendientes
- Estadísticas mensuales

### 5.2 Settings Page (pages/settings/index.vue)

**MVP scope:**
- View clinic name and cabinets (read-only)
- User profile (name, email) - editable

**NOT MVP (deferred):**
- Clinic CRUD
- User management
- Cabinet management

**Day 5 Verification:**
- Dashboard shows real data
- Settings page loads without error

---

## Day 6: Seed Data + Tests

### 6.1 Seed Data Script (backend/app/modules/clinical/seed.py)

```python
async def seed_demo_data(db: AsyncSession):
    # 1. Create clinic
    clinic = Clinic(
        name="Clínica Dental Demo",
        tax_id="B12345678",
        cabinets=[{"name": "Gabinete 1", "color": "#3B82F6"}],
        settings={"slot_duration_min": 15, "currency": "EUR"}
    )

    # 2. Create admin user
    admin = User(
        email="admin@demo.clinic",
        password_hash=hash_password("demo1234"),
        first_name="Admin",
        last_name="Demo"
    )

    # 3. Create clinic membership
    ClinicMembership(user=admin, clinic=clinic, role="admin")

    # 4. Create 5 patients
    patients = [
        Patient(clinic=clinic, first_name="Juan", last_name="García", phone="612345678"),
        Patient(clinic=clinic, first_name="María", last_name="López", phone="655123456"),
        Patient(clinic=clinic, first_name="Carlos", last_name="Pérez", phone="678901234"),
        Patient(clinic=clinic, first_name="Ana", last_name="Martínez", phone="611222333"),
        Patient(clinic=clinic, first_name="Pedro", last_name="Sánchez", phone="699888777"),
    ]

    # 5. Create 10 appointments spread across current week
    # ...
```

### 6.2 Backend Tests

**tests/conftest.py:**
```python
@pytest.fixture
async def db():
    # Create test database, run migrations, yield session, cleanup

@pytest.fixture
async def client(db):
    # TestClient with test database

@pytest.fixture
async def auth_headers(client):
    # Register user, login, return headers
```

**tests/modules/clinical/test_patients.py:**
- `test_create_patient` - happy path
- `test_create_patient_validation_error` - missing required fields
- `test_list_patients_paginated`
- `test_search_patients_by_name`
- `test_update_patient`
- `test_delete_patient_soft_delete`

**tests/modules/clinical/test_appointments.py:**
- `test_create_appointment` - happy path
- `test_create_appointment_conflict` - 409 when slot occupied
- `test_list_appointments_by_date_range`
- `test_update_appointment_reschedule`
- `test_cancel_appointment`

**tests/core/auth/test_auth.py:**
- `test_register`
- `test_login_success`
- `test_login_invalid_credentials`
- `test_refresh_token`
- `test_protected_endpoint_without_token`

### 6.3 Frontend Tests (vitest)

**frontend/tests/:**
- `login.test.ts` - form submission, error states
- `patients.test.ts` - list rendering, search
- `appointments.test.ts` - calendar navigation, modal

### 6.4 E2E Tests (Playwright)

**frontend/e2e/:**
- `login.spec.ts` - full login flow
- `patients.spec.ts` - create patient, verify in list
- `appointments.spec.ts` - create appointment, verify in calendar

**Day 6 Verification:**
- `docker-compose up` runs seed automatically in dev
- `pytest backend/tests/ -v` - all green
- `npm run test` in frontend - all green

---

## Day 7: CI/CD + Docs + Deploy

### 7.1 GitHub Actions CI (.github/workflows/ci.yml)

```yaml
name: CI
on: [push, pull_request]

jobs:
  backend:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_DB: test_db
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
        ports: ["5432:5432"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -e ./backend[dev]
      - run: ruff check backend/
      - run: pytest backend/tests/ -v
        env:
          DATABASE_URL: postgresql+asyncpg://test:test@localhost:5432/test_db
          SECRET_KEY: test-secret

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: "18" }
      - run: cd frontend && npm ci
      - run: cd frontend && npm run lint
      - run: cd frontend && npm run test

  docker:
    needs: [backend, frontend]
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: docker compose build
```

### 7.2 Documentation

**README.md:**
```markdown
# DentalPin

Open source dental clinic management software.

## Quick Start

docker-compose up

Open http://localhost:3000
Login: admin@demo.clinic / demo1234

## Tech Stack
- Backend: FastAPI + PostgreSQL
- Frontend: Nuxt 3 + Nuxt UI
- See CLAUDE.md for full architecture
```

**docs/getting-started.md:** Step-by-step setup
**docs/architecture.md:** Plugin system, data flow
**docs/creating-modules.md:** How to add a new module

### 7.3 Project Files

- **LICENSE:** BSL 1.1 with use limitation clause
- **CONTRIBUTING.md:** How to contribute
- **CODE_OF_CONDUCT.md:** Contributor Covenant v2.1

**Day 7 Verification:**
- Push to GitHub → CI runs green
- README enables setup in <5 minutes
- Docs are readable and accurate

---

## Technical Decisions

1. **Async all the way:** AsyncSession, async endpoints, asyncpg driver
2. **Pydantic v2:** Request/response schemas with strict validation
3. **SQLAlchemy 2.0:** Modern `mapped_column` syntax, full type hints
4. **JWT with refresh:** 15min access + 7d refresh
5. **Soft deletes:** Patient data archived, never hard deleted (GDPR)
6. **Event bus stub:** Log-only for MVP, real pub/sub when second module needs it
7. **Single cabinet:** MVP calendar is single-column, multi-cabinet deferred

---

## Error Handling

**API Response Format:**
```json
{
  "data": {...},
  "message": "Success",
  "errors": []
}
```

**Error Codes:**
- 400: Bad request (malformed JSON, etc)
- 401: Unauthorized (missing/invalid token)
- 403: Forbidden (no access to resource)
- 404: Not found
- 409: Conflict (appointment slot occupied)
- 422: Validation error (field-level messages)
- 500: Internal server error

**Frontend Error Handling:**
- Network errors: Toast + retry option
- 401: Redirect to /login
- 403: Redirect to list with toast
- 404: "No encontrado" page
- 422: Inline field validation
- 500: Toast with generic message

---

## Interaction State Coverage

| Feature | Loading | Empty | Error | Success |
|---------|---------|-------|-------|---------|
| Patient list | Skeleton table | "No hay pacientes" + CTA | Toast + retry | Table renders |
| Patient search | Spinner in input | "No encontrados" | Toast | Dropdown shows |
| Appointment calendar | Skeleton grid | Empty day columns | Toast + retry | Appointments render |
| Create patient | Button spinner | N/A | Inline validation | Toast + redirect |
| Create appointment | Button spinner | N/A | Conflict toast | Toast + modal closes |
| Login | Button spinner | N/A | "Credenciales inválidas" | Redirect to / |

---

## Design Specifications (from /autoplan review)

### First-Time User Experience
1. Dashboard with empty widgets shows: "Bienvenido a DentalPin. Comienza creando tu primer paciente." with prominent CTA
2. Patient list empty state leads to patient creation form
3. After first patient created, calendar empty state suggests: "Agenda la primera cita de [Patient Name]"

### Calendar "Now" Indicator
Red horizontal line with "Ahora" label traverses the time column at current time. Auto-scrolls into view on page load if viewing today.

### Appointment Status Transitions
Click appointment → modal shows status dropdown. Allowed transitions:
- scheduled → confirmed → in_progress → completed
- any status → cancelled
- past appointments: any → no_show

Past appointments in `scheduled`/`confirmed` show action buttons: "Marcar como atendida" or "No se presentó"

### Unsaved Changes Behavior
Forms trigger browser confirmation dialog on navigation with unsaved changes. Form state NOT persisted to localStorage (acceptable data loss on accident for MVP).

### Delete Confirmation
Delete patient requires confirmation modal: "¿Archivar paciente [Name]? Esta acción ocultará al paciente de las búsquedas. Las citas existentes no se eliminarán." with [Cancelar] [Archivar] buttons.

### Mobile Responsiveness
MVP is desktop-first. Mobile breakpoint (<768px):
- Sidebar collapses to hamburger menu
- Calendar shows single-day view by default
- Patient list is full-width
- Usable but not optimized

### Calendar Slot Sizing
- Each time slot: minimum 44px tall (accessibility)
- 30-min appointment = 88px minus 2px gap = 86px
- Patient name truncates with ellipsis
- Treatment type shown only if height >= 60px (45+ min appointments)

### Sidebar Behavior
- Collapsed: icons only, 64px wide
- Expanded: icons + labels, 240px wide
- Toggle via hamburger icon in header
- State persisted to localStorage
- Transition: 200ms ease-out

### Date/Time Format
- Time: 24-hour (08:00, 14:30)
- Date display: DD/MM/YYYY
- Date API: ISO format
- Spanish locale for day names

### Concurrent Edit Behavior (MVP)
Last write wins with no conflict detection for patient edits. Backend returns updated_at in responses; frontend does NOT check for staleness. Documented as known limitation.

### Offline State
Page shows stale data with top banner: "Sin conexión — datos pueden no estar actualizados". Forms remain editable but submit shows "Sin conexión" error. No offline queue for MVP

---

## NOT in Scope (MVP)

Items deferred with rationale:

| Item | Rationale | Captured In |
|------|-----------|-------------|
| Odontogram SVG | Complex (~500 LOC), not needed for basic agenda | TODOS.md |
| Budgets | Requires treatment catalog, PDF generation | TODOS.md |
| Invoices | Requires budgets, Verifactu integration | TODOS.md |
| Multi-cabinet calendar | Single column is sufficient for MVP | TODOS.md |
| Calendar drag-and-drop | Click-to-edit is sufficient | TODOS.md |
| RBAC beyond admin | All MVP users are admin | TODOS.md |
| Multi-clinic | Single seeded clinic for MVP | TODOS.md |
| Medical history fields | Simplified patient model for MVP | TODOS.md |
| Verifactu integration | Schema fields present, integration later | TODOS.md |

---

## Success Criteria

1. `docker-compose up` works in <5 minutes
2. Create patient → create appointment → see in calendar → works
3. A real small clinic could use this to manage their week
4. Architecture is modular: adding a module doesn't touch existing code
5. CI green on push
6. Tests cover critical paths (patient CRUD, appointment CRUD, auth)

---

## /autoplan Decision Audit Trail

| # | Phase | Decision | Classification | Principle | Rationale |
|---|-------|----------|----------------|-----------|-----------|
| 1 | CEO | Keep plugin architecture | TASTE | P1 completeness | ~100 LOC overhead, enables future modules |
| 2 | CEO | Proceed without user validation | TASTE | P6 action | Dentaltix has market context, contact exists |
| 3 | CEO | Accept all premises | MECHANICAL | P6 action | Premises grounded in design doc research |
| 4 | CEO | GTM outside scope | MECHANICAL | P3 pragmatic | Technical plan, not business plan |
| 5 | Design | Add first-time UX | MECHANICAL | P1 completeness | Critical for adoption |
| 6 | Design | Add unsaved changes dialog | MECHANICAL | P5 explicit | Prevent data loss |
| 7 | Design | Add "Now" indicator | MECHANICAL | P1 completeness | Essential for calendar usability |
| 8 | Design | Add status transitions | MECHANICAL | P5 explicit | Unblock implementer |
| 9 | Design | Desktop-first explicit | MECHANICAL | P5 explicit | Clear mobile strategy |
| 10 | Design | Tab order unchanged | TASTE | P3 pragmatic | User preference, not critical |
| 11 | Eng | Add unique index for conflicts | MECHANICAL | P1 completeness | Race condition prevention |
| 12 | Eng | Add rate limiting | MECHANICAL | P1 completeness | Security requirement |
| 13 | Eng | Add token revocation | MECHANICAL | P1 completeness | Security requirement |
| 14 | Eng | Add connection pool config | MECHANICAL | P3 pragmatic | Performance under load |
| 15 | Eng | CORS production validation | MECHANICAL | P5 explicit | Security hardening |
| 16 | Eng | Password requirements | MECHANICAL | P1 completeness | Basic security |

---

## GSTACK REVIEW REPORT

| Review | Trigger | Why | Runs | Status | Findings |
|--------|---------|-----|------|--------|----------|
| CEO Review | `/plan-ceo-review` | Scope & strategy | 1 | CLEAR | 4 premises accepted, scope confirmed |
| CEO Voices | `/autoplan` | Dual perspective | 1 | FLAGGED | 6 concerns, 2 taste decisions |
| Design Review | `/plan-design-review` | UI/UX gaps | 1 | AMENDED | 21 issues, 8 critical/high fixed |
| Design Voices | `/autoplan` | Dual perspective | 1 | FLAGGED | 7 dimensions scored |
| Eng Review | `/plan-eng-review` | Architecture & tests | 1 | AMENDED | 18 issues, 4 high fixed |
| Eng Voices | `/autoplan` | Dual perspective | 1 | CONFIRMED | 4/6 dimensions confirmed |
| Codex Review | `/codex review` | Independent 2nd opinion | 0 | N/A | Codex not available |

**VERDICT:** REVIEW COMPLETE — 2 taste decisions require user confirmation, plan ready for implementation.
