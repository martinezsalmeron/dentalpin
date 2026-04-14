# CLAUDE.md

Comprehensive documentation for AI coding agents working on DentalPin.

## Project Overview

**DentalPin** - Open source dental clinic management software with modular plugin architecture.

| Component | Technology |
|-----------|------------|
| Backend | FastAPI (Python 3.11+), SQLAlchemy 2.0, Alembic |
| Frontend | Vue 3, Nuxt 3, Nuxt UI, TypeScript |
| Database | PostgreSQL with asyncpg |
| Auth | JWT (access + refresh tokens) |
| Container | Docker Compose |

**License:** BSL 1.1 (commercial SaaS restricted, converts to Apache 2.0 after 4 years)

**Architecture Diagrams:** See [docs/diagrams/](docs/diagrams/) for visual documentation.

---

## Quick Start

```bash
# Start all services
docker-compose up

# Run backend tests (inside container)
docker-compose exec backend python -m pytest -v

# Run linters
cd backend && ruff check . && ruff format --check .
cd frontend && npm run lint

# Demo login
# Email: admin@demo.clinic
# Password: demo1234
```

---

## Directory Structure

```
dentalpin/
├── backend/
│   ├── app/
│   │   ├── core/
│   │   │   ├── auth/           # Authentication & RBAC
│   │   │   │   ├── dependencies.py  # get_clinic_context, require_permission
│   │   │   │   ├── models.py        # User, Clinic, ClinicMembership
│   │   │   │   ├── permissions.py   # ROLE_PERMISSIONS, has_permission()
│   │   │   │   ├── router.py        # /auth/* endpoints
│   │   │   │   ├── schemas.py       # Pydantic models
│   │   │   │   └── service.py       # JWT, password hashing
│   │   │   ├── plugins/        # Module system
│   │   │   │   ├── base.py          # BaseModule abstract class
│   │   │   │   ├── registry.py      # Module registration
│   │   │   │   └── loader.py        # Auto-discovery
│   │   │   └── events/         # Event bus
│   │   ├── modules/
│   │   │   └── clinical/       # First module
│   │   │       ├── __init__.py      # ClinicalModule class
│   │   │       ├── models.py        # Patient, Appointment
│   │   │       ├── router.py        # /clinical/* endpoints
│   │   │       ├── schemas.py
│   │   │       └── service.py
│   │   ├── config.py           # Settings from env
│   │   ├── database.py         # DB connection, Base
│   │   └── main.py             # FastAPI app
│   ├── tests/
│   └── alembic/                # Migrations
├── frontend/
│   ├── app/
│   │   ├── components/
│   │   │   ├── clinical/       # Domain components
│   │   │   └── shared/         # Reusable (ActionButton, PatientSearch)
│   │   ├── composables/        # Vue composables
│   │   │   ├── useAuth.ts           # Authentication state
│   │   │   ├── usePermissions.ts    # Permission checks
│   │   │   ├── useApi.ts            # HTTP client
│   │   │   ├── useClinic.ts         # Clinic state
│   │   │   ├── useModules.ts        # Navigation (filtered by permissions)
│   │   │   └── useUsers.ts          # User management (admin)
│   │   ├── config/
│   │   │   └── permissions.ts  # SINGLE SOURCE OF TRUTH for permissions
│   │   ├── layouts/
│   │   ├── middleware/
│   │   ├── pages/
│   │   ├── types/
│   │   │   └── index.ts        # All TypeScript interfaces
│   │   └── utils/
│   │       └── moduleRegistry.ts    # Navigation registration
│   └── nuxt.config.ts
└── docs/
    └── creating-modules.md
```

---

## RBAC System (Role-Based Access Control)

### Architecture Overview

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ Backend         │     │ API Response     │     │ Frontend        │
│ permissions.py  │────▶│ /me.permissions  │────▶│ usePermissions  │
│ (source)        │     │ (expanded list)  │     │ (checks)        │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

### Backend: Permission Definition

**File:** `backend/app/core/auth/permissions.py`

```python
ROLE_PERMISSIONS: Final[dict[str, list[str]]] = {
    "admin": ["*"],                    # Wildcard = all permissions
    "dentist": ["clinical.*"],         # All clinical permissions
    "hygienist": ["clinical.patients.read", "clinical.appointments.*"],
    "assistant": ["clinical.patients.*", "clinical.appointments.*"],
    "receptionist": ["clinical.patients.*", "clinical.appointments.*"],
}
```

**Wildcards:**
- `*` → matches everything (admin gets all current and future permissions)
- `module.*` → matches all permissions in that module

### Backend: Protecting Endpoints

**File:** `backend/app/modules/clinical/router.py`

```python
from app.core.auth.dependencies import get_clinic_context, require_permission

@router.get("/patients")
async def list_patients(
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("clinical.patients.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # Only users with clinical.patients.read can access
    ...
```

### Backend: Adding Permissions to a Module

**File:** `backend/app/modules/{module}/__init__.py`

```python
class MyModule(BaseModule):
    def get_permissions(self) -> list[str]:
        return [
            "resource.read",   # Will become "mymodule.resource.read"
            "resource.write",
        ]
```

The registry namespaces permissions automatically: `inventory.read` → `inventory.inventory.read`

### Frontend: Permission Config (Single Source of Truth)

**File:** `frontend/app/config/permissions.ts`

```typescript
export const PERMISSIONS = {
  patients: {
    read: 'clinical.patients.read',
    write: 'clinical.patients.write'
  },
  appointments: {
    read: 'clinical.appointments.read',
    write: 'clinical.appointments.write'
  },
  users: {
    read: 'admin.users.read',
    write: 'admin.users.write'
  }
} as const
```

**IMPORTANT:** Always reference `PERMISSIONS.resource.action` instead of hardcoding strings.

### Frontend: Checking Permissions

**Option 1: usePermissions composable**
```typescript
const { can, canAny, isAdmin } = usePermissions()

if (can('clinical.patients.write')) {
  // Show edit button
}
```

**Option 2: ActionButton component (recommended for buttons)**
```vue
<ActionButton
  resource="patients"
  action="write"
  icon="i-lucide-plus"
  @click="createPatient"
>
  New Patient
</ActionButton>
<!-- Button only renders if user has clinical.patients.write -->
```

**Option 3: Navigation filtering (automatic)**
```typescript
// In moduleRegistry.ts - items are auto-filtered by useModules
{
  label: 'nav.patients',
  to: '/patients',
  permission: PERMISSIONS.patients.read  // Only shown if user has this
}
```

### Adding a New Permission

1. **Backend:** Add to role mapping in `permissions.py`
2. **Backend:** Add to module's `get_permissions()` if module-specific
3. **Backend:** Use `require_permission()` on endpoints
4. **Frontend:** Add to `config/permissions.ts`
5. **Frontend:** Use via `ActionButton` or `usePermissions`

---

## Frontend Patterns

### Composables

| Composable | Purpose | Key exports |
|------------|---------|-------------|
| `useAuth` | Auth state, login/logout | `user`, `permissions`, `login()`, `logout()` |
| `usePermissions` | Permission checks | `can()`, `canAny()`, `isAdmin` |
| `useApi` | HTTP client with auth | `get()`, `post()`, `put()`, `del()` |
| `useClinic` | Current clinic state | `currentClinic`, `cabinets` |
| `useModules` | Navigation items | `navigationItems` (filtered by permissions) |
| `useUsers` | User management | `users`, `createUser()`, `fetchUsers()` |
| `useProfessionals` | Professionals (dentists/hygienists) | `professionals`, `fetchProfessionals()`, `getProfessionalColor()` |

### Component Organization

```
components/
├── clinical/           # Domain-specific
│   ├── AppointmentCalendar.vue   # Weekly view with drag & drop
│   ├── AppointmentDailyView.vue  # Daily view with columns per professional
│   └── AppointmentModal.vue      # Create/edit appointment form
└── shared/             # Reusable
    ├── ActionButton.vue    # Permission-aware button
    └── PatientSearch.vue   # Autocomplete search
```

### State Management

Uses Nuxt's `useState` for SSR-compatible state:

```typescript
// In composable
const user = useState<User | null>('auth:user', () => null)

// State is shared across components via the key 'auth:user'
```

### API Calls

```typescript
import type { ApiResponse, PaginatedResponse, Patient } from '~/types'
const api = useApi()

// GET paginated list (data is in response.data array)
const response = await api.get<PaginatedResponse<Patient>>('/api/v1/clinical/patients')
const patients = response.data  // Patient[]

// GET single item (wrapped in ApiResponse)
const response = await api.get<ApiResponse<Patient>>('/api/v1/clinical/patients/123')
const patient = response.data  // Patient

// POST (wrapped in ApiResponse)
const response = await api.post<ApiResponse<Patient>>('/api/v1/clinical/patients', {
  first_name: 'John',
  last_name: 'Doe'
})
const newPatient = response.data  // Patient

// Auto-handles: auth headers, token refresh, error toasts
```

### UI Components

Uses **Nuxt UI** (built on Radix Vue):
- `UButton`, `UInput`, `UCard`, `UModal`, `USelect`
- `UFormField` for form labels
- `UBadge` for status indicators
- `UAvatar` for user avatars
- `USkeleton` for loading states

---

## Backend Patterns

### Endpoint Structure

```python
from app.core.schemas import ApiResponse, PaginatedApiResponse

# For paginated lists
@router.get("/resources", response_model=PaginatedApiResponse[ResourceResponse])
async def list_resources(
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("module.resource.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> PaginatedApiResponse[ResourceResponse]:
    """List resources with pagination."""
    items, total = await ResourceService.list(db, ctx.clinic_id, page, page_size)
    return PaginatedApiResponse(
        data=[ResourceResponse.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
    )

# For single item
@router.get("/resources/{id}", response_model=ApiResponse[ResourceResponse])
async def get_resource(
    id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("module.resource.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[ResourceResponse]:
    """Get a resource by ID."""
    resource = await ResourceService.get(db, ctx.clinic_id, id)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    return ApiResponse(data=ResourceResponse.model_validate(resource))

# For create
@router.post("/resources", response_model=ApiResponse[ResourceResponse], status_code=201)
async def create_resource(
    data: ResourceCreate,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("module.resource.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[ResourceResponse]:
    """Create a resource."""
    resource = await ResourceService.create(db, ctx.clinic_id, data.model_dump())
    return ApiResponse(data=ResourceResponse.model_validate(resource))
```

### Service Layer

```python
# service.py - Business logic, no HTTP concerns
class ResourceService:
    @staticmethod
    async def list(db: AsyncSession, clinic_id: UUID, page: int, page_size: int):
        query = select(Resource).where(Resource.clinic_id == clinic_id)
        # ... pagination logic
        return items, total

    @staticmethod
    async def create(db: AsyncSession, clinic_id: UUID, data: dict):
        resource = Resource(clinic_id=clinic_id, **data)
        db.add(resource)
        await db.commit()
        return resource
```

### Multi-Tenancy

Every query MUST filter by `clinic_id`:

```python
# CORRECT
select(Patient).where(Patient.clinic_id == ctx.clinic_id)

# WRONG - Security vulnerability!
select(Patient).where(Patient.id == patient_id)
```

---

## Database Conventions

### Model Template

```python
class MyModel(Base):
    __tablename__ = "my_models"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    clinic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clinics.id"), nullable=False, index=True
    )
    # ... fields ...
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
```

### Conventions

- **UUIDs** for all primary keys
- **TIMESTAMPTZ** for all timestamps (timezone-aware)
- **JSONB** for flexible data (addresses, settings)
- **Soft deletes** via `status` field (never hard delete patient data)
- **Index** on `clinic_id` for multi-tenant queries

### Migrations

```bash
# Create migration
docker-compose exec backend alembic revision --autogenerate -m "description"

# Apply migrations
docker-compose exec backend alembic upgrade head

# If tables missing but version exists, reset:
docker-compose exec db psql -U dental -d dental_clinic -c "DELETE FROM alembic_version;"
docker-compose exec backend alembic upgrade head
```

---

## Module System

See `docs/creating-modules.md` for full guide.

### Quick Reference

```python
# backend/app/modules/mymodule/__init__.py
class MyModule(BaseModule):
    @property
    def name(self) -> str:
        return "mymodule"  # Router mounted at /api/v1/mymodule/

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def dependencies(self) -> list[str]:
        return ["clinical"]  # Loaded after clinical

    def get_models(self) -> list:
        return [MyModel]

    def get_router(self) -> APIRouter:
        return router

    def get_permissions(self) -> list[str]:
        return ["resource.read", "resource.write"]

    def get_event_handlers(self) -> dict:
        return {"patient.created": self._on_patient_created}
```

### Event Bus

```python
# Publishing
from app.core.events import event_bus
event_bus.publish("patient.created", {"patient_id": str(patient.id)})

# Subscribing (in module class)
def get_event_handlers(self) -> dict:
    return {"patient.created": self._handle}
```

---

## API Conventions

### API Response Schemas

All endpoints (except auth tokens) use standardized wrappers defined in `backend/app/core/schemas.py`:

| Case | Schema | Importar de |
|------|--------|-------------|
| Item individual | `ApiResponse[T]` | `app.core.schemas` |
| Lista paginada | `PaginatedApiResponse[T]` | `app.core.schemas` |
| Error | `ErrorResponse` | `app.core.schemas` |

**IMPORTANT:** Auth token endpoints (`/login`, `/register`, `/refresh`) do NOT use wrappers because they return tokens, not data.

### Response Formats

**Single item (wrapped):**
```json
{
  "data": {
    "id": "uuid",
    "field": "value",
    "created_at": "2024-01-01T00:00:00Z"
  },
  "message": null
}
```

**Paginated list:**
```json
{
  "data": [...],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "message": null
}
```

**Error:**
```json
{
  "data": null,
  "message": "Error description",
  "errors": ["Error description"]
}
```

**Auth tokens (exception - NOT wrapped):**
```json
{
  "access_token": "jwt...",
  "refresh_token": "jwt...",
  "token_type": "bearer"
}
```

### HTTP Status Codes

| Code | Usage |
|------|-------|
| 200 | Success (GET, PUT) |
| 201 | Created (POST) |
| 204 | No Content (DELETE) |
| 400 | Bad Request |
| 401 | Unauthorized (invalid/expired token) |
| 403 | Forbidden (valid token, no permission) |
| 404 | Not Found |
| 409 | Conflict (duplicate) |
| 422 | Validation Error |

---

## Professionals & Appointments System

### Overview

Appointments are associated with professionals (users with role `dentist` or `hygienist`). The system provides:
- Endpoint to list professionals for a clinic
- Validation that appointments can only be assigned to valid professionals
- Professional info included in appointment responses
- Calendar views (weekly/daily) with professional visualization

### Backend: Professionals Endpoint

**Endpoint:** `GET /api/v1/auth/professionals`
**Permission:** `clinical.appointments.read`
**Returns:** List of active dentists and hygienists in the clinic

```python
# Response schema
class ProfessionalResponse(BaseModel):
    id: UUID
    email: str
    first_name: str
    last_name: str
    role: str  # "dentist" or "hygienist"
```

### Backend: Professional Validation in Appointments

When creating or updating appointments, the `professional_id` is validated:

```python
# In AppointmentService
@staticmethod
async def validate_professional_access(
    db: AsyncSession, clinic_id: UUID, professional_id: UUID
) -> bool:
    """Check if professional exists, belongs to clinic, and has valid role."""
    result = await db.execute(
        select(ClinicMembership.id).where(
            ClinicMembership.user_id == professional_id,
            ClinicMembership.clinic_id == clinic_id,
            ClinicMembership.role.in_(["dentist", "hygienist"]),
        )
    )
    return result.scalar_one_or_none() is not None
```

**Error response (400):** `"Invalid professional: must be a dentist or hygienist in this clinic"`

### Backend: Appointment Response with Professional

Appointments include the professional info:

```python
class AppointmentResponse(BaseModel):
    # ... other fields ...
    professional_id: UUID
    professional: ProfessionalBrief | None  # Eager loaded

class ProfessionalBrief(BaseModel):
    id: UUID
    first_name: str
    last_name: str
```

### Frontend: useProfessionals Composable

```typescript
const {
  professionals,           // Ref<Professional[]>
  fetchProfessionals,      // () => Promise<void>
  getProfessionalById,     // (id: string) => Professional | undefined
  getProfessionalColor,    // (id: string) => string (hex color)
  getProfessionalInitials, // (prof: Professional) => string (e.g., "JD")
  getProfessionalFullName  // (prof: Professional) => string
} = useProfessionals()
```

Colors are auto-assigned from a predefined palette based on order.

### Frontend: Appointment Modal

The `AppointmentModal` component accepts:
- `initialProfessionalId?: string` - Pre-select a professional (used in daily view)

Default behavior:
1. If `initialProfessionalId` provided → use it
2. Else if current user is a professional → use their ID
3. Else → use first professional in list

### Frontend: Calendar Views

**Weekly View (`AppointmentCalendar.vue`):**
- Shows professional badge (initials + color) in top-right of appointments
- Hover shows full name tooltip
- Drag & drop to move/resize appointments

**Daily View (`AppointmentDailyView.vue`):**
- Columns per professional
- Click slot → opens modal with professional pre-selected
- Drag appointment horizontally → change professional
- Supports same drag & drop features

**View Toggle:**
```vue
<UButton @click="viewMode = 'week'">{{ t('appointments.weeklyView') }}</UButton>
<UButton @click="viewMode = 'day'">{{ t('appointments.dailyView') }}</UButton>
```

### Frontend: Professional Filter

On appointments page, filter by professional (similar to cabinet filter):

```typescript
const selectedProfessionals = ref<string[]>([])

const filteredAppointments = computed(() => {
  let result = appointments.value
  if (selectedProfessionals.value.length > 0) {
    result = result.filter(apt => selectedProfessionals.value.includes(apt.professional_id))
  }
  return result
})
```

### Testing Professionals Feature

```bash
# Run all professionals tests
docker-compose exec backend python -m pytest tests/test_professionals.py -v
```

Key test cases:
- `test_list_professionals` - Returns only dentists/hygienists
- `test_list_professionals_excludes_inactive` - Inactive users excluded
- `test_create_appointment_with_invalid_professional_role` - Rejects receptionist
- `test_appointment_response_includes_professional` - Professional info in response

---

## Testing

### Running Tests

```bash
# All tests (in Docker)
docker-compose exec backend python -m pytest -v

# Specific file
docker-compose exec backend python -m pytest tests/test_auth.py -v

# With coverage
docker-compose exec backend python -m pytest --cov=app
```

### Test Fixtures

```python
# conftest.py provides:
@pytest.fixture
async def db_session():  # Fresh database per test

@pytest.fixture
async def client():  # HTTP client

@pytest.fixture
async def auth_headers():  # {"Authorization": "Bearer ..."}
```

### Test Pattern

```python
@pytest.mark.asyncio
async def test_create_patient(client: AsyncClient, auth_headers: dict):
    response = await client.post(
        "/api/v1/clinical/patients",
        json={"first_name": "John", "last_name": "Doe"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    assert response.json()["first_name"] == "John"
```

---

## Common Tasks

### Adding a New Endpoint

1. Add route in `router.py` with `require_permission()`
2. Add service method in `service.py`
3. Add schemas in `schemas.py`
4. Add permission to `permissions.py` if new
5. Update `config/permissions.ts` in frontend
6. Write tests

### Adding a New Page (Frontend)

1. Create `pages/mypage/index.vue`
2. Add to navigation in `utils/moduleRegistry.ts`
3. Add permission to navigation item if restricted
4. Create composable in `composables/` if needed

### Adding a New Role

1. Add to `ROLE_PERMISSIONS` in `backend/app/core/auth/permissions.py`
2. Add to `ROLES` list in same file
3. Add to `UserRole` type in `frontend/app/types/index.ts`
4. Add label in UI where roles are displayed

---

## Environment Variables

```bash
# Required
DATABASE_URL=postgresql+asyncpg://dental:dental_dev@db:5432/dental_clinic
SECRET_KEY=your-secret-key-min-32-chars

# Optional
ENVIRONMENT=development  # development | test | production
TESTING=false           # Set true in test runner
```

---

## Troubleshooting

### "relation does not exist" error

This happens when backend tests run (they drop all tables). Use the reset script:

```bash
./scripts/reset-db.sh
```

Or manually:
```bash
docker-compose exec db psql -U dental -d dental_clinic -c "DELETE FROM alembic_version;"
docker-compose exec backend alembic upgrade head
# Then recreate demo data (see script)
```

### Login returns "Invalid email or password"

```bash
# Regenerate password hash
docker-compose exec backend python -c "
from app.core.auth.service import hash_password
print(hash_password('demo1234'))
"
# Then update in database
```

### Frontend changes not showing

```bash
docker-compose up -d --build frontend
```

### Permission denied but should have access

1. Check role in `clinic_memberships` table
2. Verify permission string matches exactly
3. Check `/me` response includes the permission
4. Clear browser cookies and re-login

---

## Code Style

- **Language:** Code in English, UI strings in Spanish (i18n)
- **Python:** Type hints required, ruff for linting/formatting
- **TypeScript:** Strict mode, ESLint
- **Commits:** Conventional commits (`feat:`, `fix:`, `docs:`)
- **No over-engineering:** Only add what's needed now
