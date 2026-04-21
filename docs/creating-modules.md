# Creating DentalPin modules

A complete guide to shipping a DentalPin module — backend, frontend,
migrations, seeds, tests, distribution — from scratch. Written for
contributors who have never read the core codebase.

Everything below applies to both **official** modules (live inside the
monorepo, maintained by the core team) and **community** modules
(separate repos, shipped as Python packages on PyPI). The contract is
identical — the only difference is where the code lives and who owns
bug fixes.

> **Status:** Fase B complete. The monolithic `clinical` module has
> been split into `patients`, `patients_clinical`, `agenda` and
> `patient_timeline`; every official module now ships its frontend as
> a Nuxt layer. Report gaps at
> https://github.com/dentalpin/dentalpin/issues.

---

## 1. Concepts

### What is a module?

A module is a Python package that groups together:

- SQLAlchemy models (optional — reports has none)
- Alembic migrations (required if the module owns tables)
- FastAPI routes (optional)
- Pydantic schemas (optional)
- Service-layer business logic (optional)
- Event handlers (optional)
- RBAC permissions (strongly encouraged)
- Lifecycle hooks (`install`, `uninstall`, `post_upgrade`)
- Seed data files (optional, YAML)
- A Nuxt Layer for the frontend (optional)

Each module declares its metadata through a **manifest** — a
declarative dict embedded on the module class.

### Official vs community

The manifest field `category` determines the badge shown in the admin
UI (`official` → green, `community` → amber). Trust semantics are
intentionally minimal in v1; richer verification (signatures,
marketplace) is post-v1.

- **Official** modules ship inside `backend/app/modules/<name>/` and
  are installed-by-default on every DentalPin instance.
- **Community** modules live in their own git repo, publish to PyPI,
  and are installed via `pip install` + `dentalpin modules install`.

### Manifest

See `docs/core-api.md` for the full schema. Key fields:

| Field | Required | Purpose |
|-------|----------|---------|
| `name` | yes | Unique id (snake_case). Becomes the API prefix `/api/v1/<name>/` and the permission namespace. |
| `version` | yes | Semver `X.Y.Z`. Bumped per the rules in §8. |
| `summary` / `author` / `license` | recommended | Shown in `dentalpin modules info`. |
| `category` | yes | `official` or `community`. |
| `min_core_version` | recommended | Reject install if core is older. |
| `depends` | yes (list) | Module names that must install first. |
| `installable` / `auto_install` / `removable` | yes | Policy flags. |
| `data_files` | optional | Seed YAML paths (relative). |
| `role_permissions` | recommended | Declarative RBAC (see §7). |
| `frontend.layer_path` | optional | Nuxt Layer folder (community UI). |
| `frontend.navigation` | optional | Sidebar entries (see §4). |

### Event bus

Modules publish events and subscribe to each other's events instead of
importing each other directly. Events are defined in
`app/core/events/types.py` (core ones) and follow the naming
convention `entity.action` (e.g. `appointment.completed`).

### Slots

Slots are named UI extension points (e.g. `patient.detail.sidebar`).
Any module can register a component for a slot without touching the
host page. See §4.

---

## 2. Quick start

### A. Official module (inside the monorepo)

```bash
cd backend
mkdir -p app/modules/inventory/{migrations/versions}
touch app/modules/inventory/{__init__.py,models.py,schemas.py,router.py,service.py}
```

Add the entry point in `backend/pyproject.toml`:

```toml
[project.entry-points."dentalpin.modules"]
inventory = "app.modules.inventory:InventoryModule"
```

Restart the backend, run `dentalpin modules list` — your module now
appears as `uninstalled`.

### B. Community module (standalone repo)

```bash
# Start from the template
git clone https://github.com/dentalpin/dentalpin-module-template my-module
cd my-module
```

The template carries a working `hello` module: backend route, frontend
layer with one page, slot registration. Rename, adjust, publish:

```bash
pip install -e .
```

Inside the DentalPin instance:

```bash
./bin/dentalpin modules install my_module
./bin/dentalpin modules restart
docker compose build frontend && docker compose up -d frontend
```

Open `/my-module` in the app — the module is live.

---

## 3. Anatomy of a module

Walk through every file of a minimal module. File tree:

```
dentalpin_inventory/                        # Python package
├── pyproject.toml
├── dentalpin_inventory/
│   ├── __init__.py
│   ├── manifest.py
│   ├── models.py
│   ├── schemas.py
│   ├── router.py
│   ├── service.py
│   ├── events.py
│   ├── lifecycle.py
│   ├── migrations/
│   │   └── versions/
│   │       └── inv_0001_initial.py
│   ├── data/
│   │   └── default_categories.yaml
│   └── frontend/                           # Nuxt Layer
│       ├── nuxt.config.ts
│       ├── pages/
│       ├── components/
│       ├── composables/
│       ├── i18n/
│       └── slots.ts
├── tests/
└── README.md
```

### `pyproject.toml`

```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "dentalpin-inventory"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["dentalpin-core>=1.0"]

[project.entry-points."dentalpin.modules"]
inventory = "dentalpin_inventory:InventoryModule"
```

### `__init__.py`

Exposes the `BaseModule` subclass referenced by the entry point:

```python
from fastapi import APIRouter
from app.core.plugins import BaseModule, ModuleContext
from . import lifecycle
from .events import on_appointment_completed
from .models import InventoryItem, StockMovement
from .router import router


class InventoryModule(BaseModule):
    manifest = {
        "name": "inventory",
        "version": "0.1.0",
        "summary": "Clinic supplies + stock tracking.",
        "author": "Your Name",
        "license": "MIT",
        "category": "community",
        "min_core_version": "1.0.0",
        "depends": ["patients", "agenda"],
        "installable": True,
        "auto_install": False,
        "removable": True,
        "data_files": ["data/default_categories.yaml"],
        "role_permissions": {
            "admin": ["*"],
            "dentist": ["items.read"],
            "assistant": ["items.read", "items.write"],
        },
        "frontend": {
            "layer_path": "frontend",
            "navigation": [
                {
                    "label": "nav.inventory",
                    "to": "/inventory",
                    "icon": "i-lucide-box",
                    "permission": "inventory.items.read",
                    "order": 70,
                }
            ],
        },
    }

    def get_models(self) -> list:
        return [InventoryItem, StockMovement]

    def get_router(self) -> APIRouter:
        return router

    def get_permissions(self) -> list[str]:
        return ["items.read", "items.write", "movements.read"]

    def get_event_handlers(self) -> dict:
        return {"appointment.completed": on_appointment_completed}

    async def install(self, ctx: ModuleContext) -> None:
        await lifecycle.install(ctx)

    async def uninstall(self, ctx: ModuleContext) -> None:
        await lifecycle.uninstall(ctx)

    async def post_upgrade(self, ctx: ModuleContext, from_version: str) -> None:
        await lifecycle.post_upgrade(ctx, from_version)
```

### `models.py`

Follow these conventions:

- Every table has `id UUID PRIMARY KEY DEFAULT gen_random_uuid()`.
- Multi-tenant tables have `clinic_id UUID NOT NULL INDEX`.
- Timestamps: `DateTime(timezone=True)` with `server_default=func.now()`.
- Soft delete via `status` column, never hard-delete patient data.
- JSONB for flexible/semi-structured fields.

```python
import uuid
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    clinic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("clinics.id"),
        nullable=False,
        index=True,
    )
    code: Mapped[str] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(200))
    metadata_: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
```

### `schemas.py`

Pydantic V2. Use the shared `ApiResponse[T]` / `PaginatedApiResponse[T]`
wrappers from `app.core.schemas`.

```python
from pydantic import BaseModel, ConfigDict
from uuid import UUID


class InventoryItemCreate(BaseModel):
    code: str
    name: str


class InventoryItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    code: str
    name: str
```

### `router.py`

Every route must take `ctx: Annotated[ClinicContext, Depends(get_clinic_context)]`
and `require_permission(...)`. Multi-tenancy is **mandatory**: every
query filters by `ctx.clinic_id`.

```python
from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.auth.dependencies import ClinicContext, get_clinic_context, require_permission
from app.core.schemas import ApiResponse, PaginatedApiResponse
from app.database import get_db
from . import service
from .schemas import InventoryItemCreate, InventoryItemResponse

router = APIRouter()


@router.get("/items", response_model=PaginatedApiResponse[InventoryItemResponse])
async def list_items(
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("inventory.items.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = 1,
    page_size: int = 20,
) -> PaginatedApiResponse[InventoryItemResponse]:
    items, total = await service.list_items(db, ctx.clinic.id, page, page_size)
    return PaginatedApiResponse(
        data=[InventoryItemResponse.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
    )
```

### `service.py`

Business logic lives here. No FastAPI imports, no HTTP concerns.

```python
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from .models import InventoryItem


async def list_items(
    db: AsyncSession, clinic_id: UUID, page: int, page_size: int
) -> tuple[list[InventoryItem], int]:
    query = select(InventoryItem).where(InventoryItem.clinic_id == clinic_id)
    total = (await db.execute(
        select(func.count()).select_from(query.subquery())
    )).scalar_one()
    items = (await db.execute(
        query.offset((page - 1) * page_size).limit(page_size)
    )).scalars().all()
    return list(items), total
```

### `events.py`

```python
from sqlalchemy.ext.asyncio import AsyncSession


async def on_appointment_completed(db: AsyncSession, data: dict) -> None:
    """Consume stock based on the appointment's treatments."""
    # Reach into your service layer here.
```

### `lifecycle.py`

Explicit `install` / `uninstall` / `post_upgrade`. Keep hooks idempotent:
running them twice should be a no-op.

```python
from app.core.plugins import ModuleContext


async def install(ctx: ModuleContext) -> None:
    ctx.logger.info("Inventory module installed")
    # Optional: custom provisioning beyond YAML seeds.


async def uninstall(ctx: ModuleContext) -> None:
    ctx.logger.info("Inventory module uninstalling")
    # Stop background jobs, close external connections, etc.


async def post_upgrade(ctx: ModuleContext, from_version: str) -> None:
    ctx.logger.info(f"Upgrading inventory from {from_version}")
```

### `migrations/`

Brand-new modules get their own Alembic branch:

```python
# migrations/versions/inv_0001_initial.py
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "inv_0001"
down_revision = None
branch_labels = ("inventory",)
depends_on = None


def upgrade() -> None:
    op.create_table(
        "inventory_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("clinic_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(50)),
        sa.Column("name", sa.String(200)),
        sa.Column("metadata_", postgresql.JSONB(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_inventory_items_clinic", "inventory_items", ["clinic_id"])


def downgrade() -> None:
    op.drop_index("ix_inventory_items_clinic", table_name="inventory_items")
    op.drop_table("inventory_items")
```

Generate with:

```bash
alembic revision --autogenerate \
  -m "initial inventory schema" \
  --version-path dentalpin_inventory/migrations/versions \
  --branch-label inventory \
  --head base
```

For **official modules** (`backend/app/modules/<name>/`): each module
owns its initial migration under
`backend/app/modules/<name>/migrations/versions/<mod>_0001_initial.py`.
All module initials chain off the core `0001_core_initial.py`
(main-linear at `backend/alembic/versions/`) via `down_revision`.
Subsequent module migrations chain off the module's own previous
revision. No `branch_labels` needed — the chain is linear across all
modules so Alembic CLI works the same as before.

`backend/alembic.ini`'s `version_locations` lists every module's
`migrations/versions` directory so `alembic history | heads | upgrade`
find them before `env.py` runs.

### `data/*.yaml`

Declarative seed format:

```yaml
- xml_id: inventory.category_consumables
  table: inventory_categories
  noupdate: false
  values:
    name: "Consumables"
    description: "Single-use items"
- xml_id: inventory.item_mask
  table: inventory_items
  values:
    category_id: "$xmlref:inventory.category_consumables"
    code: "MASK-001"
    name: "Face Mask"
```

`$xmlref:` resolves at load time. Records are tracked in
`core_external_id`; running the same file twice is a no-op (upserts
respect `noupdate`).

---

## 4. Frontend layer

Nuxt Layer lives under `<package>/frontend/` and is auto-discovered
when the manifest declares `frontend.layer_path`. Every official
module already ships one (Fase B.6). Structure:

```
frontend/
├── nuxt.config.ts      # see template below — must register components/
├── pages/              # file-based routing, merged with host
├── components/         # auto-imported when declared in nuxt.config.ts
├── composables/        # auto-imported
├── i18n/               # merged with @nuxtjs/i18n
└── slots.ts            # registerSlot(...) calls run at setup
```

The host sets `components: [{path: '~/components', pathPrefix: false}]`,
which **overrides** Nuxt's default auto-scan. Each layer must declare
its own components path so cross-layer auto-import works. The same
applies to `@nuxtjs/i18n` v9: layer locale files are **not**
auto-discovered — each layer that ships translations must declare its
own `i18n` block. When two layers (host + module) register the same
locale `code`, their JSON files are merged into a single locale object
at build time, so each module contributes its own `<module>.*`
namespaced keys:

```ts
// <module>/frontend/nuxt.config.ts
export default defineNuxtConfig({
  components: [
    { path: './components', pathPrefix: false }
  ],
  // Drop this block only if the module ships no UI strings.
  i18n: {
    locales: [
      { code: 'en', file: 'en.json' },
      { code: 'es', file: 'es.json' }
    ],
    langDir: 'locales'
  }
})
```

Place the JSON files at `<module>/frontend/i18n/locales/<code>.json`
and namespace every top-level key under your module name
(e.g. `"inventory": { "nav": { "items": "Items" } }`) to avoid
collisions with the host and with other modules.

TypeScript aliases inside layer files: `~` resolves per-layer, so use
`~~` (rootDir, = host frontend root) to reach shared types:

```ts
import type { Patient } from '~~/app/types'
import { PERMISSIONS } from '~~/app/config/permissions'
```

### Backend-driven navigation

Do **not** register nav items in a TypeScript file. Declare them in
the manifest:

```python
"frontend": {
    "navigation": [
        {
            "label": "nav.inventory",       # i18n key
            "to": "/inventory",
            "icon": "i-lucide-box",
            "permission": "inventory.items.read",
            "order": 70,
        }
    ],
}
```

The frontend fetches `/api/v1/modules/-/active` at login and renders
the merged list. Permission filtering runs server-side; i18n resolves
client-side.

### Canonical slots (v1)

| Name | Context (`ctx`) |
|------|-----------------|
| `patient.detail.tabs` | `{ patient }` |
| `patient.detail.sidebar` | `{ patient }` |
| `appointment.detail.actions` | `{ appointment }` |
| `dashboard.widgets` | `{}` |
| `settings.sections` | `{}` |

Consume:

```vue
<ModuleSlot name="patient.detail.sidebar" :ctx="{ patient }" />
```

Register (typically in `frontend/slots.ts` of your layer):

```ts
import { defineAsyncComponent } from 'vue'
import { registerSlot } from '~/composables/useModuleSlots'

registerSlot('patient.detail.sidebar', {
  id: 'inventory.patient.sidebar',   // stable, unique
  component: defineAsyncComponent(() => import('./components/InventoryWidget.vue')),
  order: 30,
  permission: 'inventory.items.read',
  condition: (ctx) => ctx.patient.status === 'active',
})
```

---

## 5. Lifecycle

State machine tracked in `core_module`:

```
uninstalled ──install──▶ to_install ──restart──▶ installed
installed   ──upgrade──▶ to_upgrade ──restart──▶ installed
installed   ──uninstall─▶ to_remove ──restart──▶ uninstalled
installed   ◀──toggle──▶ disabled    (no restart, no DB write)
```

On each restart, the **pending processor** runs every module in
`to_*` state, in topological order, through these steps:

- **install**: `migrate → seed → module.install(ctx) → finalize`
- **upgrade**: `migrate → seed → module.post_upgrade(ctx, from) → finalize`
- **uninstall**: `backup → module.uninstall(ctx) → delete_data → migrate_down → finalize`

Every step is logged to `core_module_operation_log` with
`started/completed/failed`. Crashes leave a trail; the next restart
can detect and retry.

### External IDs

`core_external_id` tracks every seed record. On `uninstall` every row
owned by the module is deleted (preceded by a `pg_dump` of the
module's tables to `storage/backups/`).

### Explicit restart

Modules never hot-load. CLI responses and REST endpoints always return
"restart required" after a state change. Restart via:

- REST: `POST /api/v1/modules/-/restart`
- CLI hint: `./bin/dentalpin modules rebuild-frontend`
- Host: `docker compose restart backend`

---

## 6. Dependencies and events

### `depends`

Hard dependency. If `billing.depends = ["patients", "catalog", "budget"]`,
all three must be `installed` before billing can be `installed`. The
install flow resolves transitively: installing billing while its
dependencies are uninstalled schedules the full chain.

Circular dependencies are rejected at discovery time (topological
sort fails loud).

### Events

The core publishes a fixed catalog of events. See `docs/core-api.md`
for the full list + payload schemas. Common ones:

- `patient.created`, `patient.updated`, `patient.medical_updated`
- `appointment.scheduled`, `appointment.completed`, `appointment.cancelled`
- `budget.sent`, `budget.accepted`
- `invoice.issued`, `invoice.paid`

Publish your own:

```python
event_bus.publish("inventory.restocked", {
    "clinic_id": str(clinic_id),
    "item_id": str(item.id),
    "qty": qty,
})
```

Naming convention: `<module>.<action>` (lower-snake).

### FK cross-module

Allowed **only** when the target module is in `depends`. A CI
validator rejects migrations that reference tables of undeclared
modules.

---

## 7. Permissions

### Declaring permissions

Your module returns module-local names from `get_permissions()`:

```python
def get_permissions(self) -> list[str]:
    return ["items.read", "items.write", "movements.read"]
```

The registry namespaces them automatically: `inventory.items.read`,
etc. That's the string roles reference.

### `role_permissions` in manifest

Declare which permissions each existing role should obtain on install:

```python
"role_permissions": {
    "admin": ["*"],
    "dentist": ["items.read"],
    "assistant": ["items.read", "items.write"],
}
```

`*` = every permission in this module. Sub-wildcards like `movements.*`
are allowed. Today this metadata is informational; when the RBAC
table moves to the database (post-v2), the registry will apply it at
install time.

### Using permissions in code

Backend:

```python
_: Annotated[None, Depends(require_permission("inventory.items.read"))],
```

Frontend:

```vue
<ActionButton resource="inventory.items" action="write" ...>
```

Or programmatically:

```ts
const { can } = usePermissions()
if (can('inventory.items.read')) { /* ... */ }
```

---

## 8. Versioning

Rules (enforced by CI):

- Any new Alembic revision → bump **minor**.
- Breaking change to public API, permissions or slot contract → bump
  **major**.
- Bugfix with no interface change → bump **patch**.

The manifest validator (`app.core.plugins.manifest_validator`) runs as
part of the test suite and rejects version strings that aren't
semver-ish (`\d+\.\d+\.\d+`).

When you bump, write an entry in your module's `CHANGELOG.md`:

```
## 0.2.0 - 2026-06-01
### Added
- Low-stock alerts.
### Changed
- InventoryItem.code is now unique per clinic (breaking for clinics
  that had duplicates — cleanup script provided).
```

---

## 9. Testing

### Fixtures

The core's `tests/conftest.py` exposes:

- `db_session` — fresh DB + session per test
- `client` — HTTPX async client with lifespan
- `auth_headers` — Bearer token for a registered user

Community modules can import these via pytest discovery once
`dentalpin-core[tests]` is a dev dependency.

### What to cover

- Happy-path CRUD + auth filtering
- Multi-tenancy: patient from clinic A invisible to user in clinic B
- Event bus: your handlers fire on published events; unrelated events
  don't crash
- Seed idempotency: run `install` twice, no duplicates, no errors
- Round-trip schema (modules with Alembic branch): `install` then
  `uninstall` leaves the DB schema identical to pre-install (diff
  via `pg_dump --schema-only`)

### Example

```python
@pytest.mark.asyncio
async def test_create_item(client, auth_headers):
    response = await client.post(
        "/api/v1/inventory/items",
        json={"code": "X", "name": "Widget"},
        headers=auth_headers,
    )
    assert response.status_code == 201
```

---

## 10. Distribution

### Official module

1. Add `backend/app/modules/<name>/` with the files above.
2. Register the entry point in `backend/pyproject.toml`.
3. Open a PR to the main repo.
4. Ship as part of the next DentalPin release.

### Community module

1. Push to GitHub under your own account.
2. `pip install build && python -m build`.
3. Upload to PyPI: `twine upload dist/*`.
4. Document the install steps in your README:

```bash
pip install dentalpin-my-module
./bin/dentalpin modules install my_module
./bin/dentalpin modules restart
docker compose build frontend && docker compose up -d frontend
```

The core team does **not** accept PRs for community modules on the
main repo — you own the code, the releases and the support.

---

## 11. Debugging

### CLI

```bash
./bin/dentalpin modules list              # everything + state
./bin/dentalpin modules info inventory    # full metadata
./bin/dentalpin modules status            # pending + errored summary
./bin/dentalpin modules doctor            # orphans, missing deps, manifest errors
./bin/dentalpin modules sync-frontend     # regenerate modules.json
```

### Useful SQL

```sql
-- Active state + last error
SELECT name, state, error_message, error_at
FROM core_module
ORDER BY name;

-- Recent operations
SELECT module_name, operation, step, status, created_at
FROM core_module_operation_log
ORDER BY id DESC
LIMIT 20;

-- Seed records tracked for a module
SELECT xml_id, table_name, record_id
FROM core_external_id
WHERE module_name = 'inventory';
```

### Logs

Everything goes through `logging`. Look for the logger name
`app.core.plugins.*` (core) or `app.modules.<name>` (your module).

---

## 12. Common recipes

### Add a tab to the patient detail view

```ts
// frontend/slots.ts
registerSlot('patient.detail.tabs', {
  id: 'my_module.patient.tab',
  component: defineAsyncComponent(() => import('./components/MyTab.vue')),
  order: 50,
  permission: 'my_module.read',
})
```

### React to an appointment completion

```python
def get_event_handlers(self) -> dict:
    return {EventType.APPOINTMENT_COMPLETED: on_completed}

async def on_completed(db: AsyncSession, data: dict) -> None:
    appointment_id = UUID(data["appointment_id"])
    # Do work
```

### Seed data that depends on a record from another module

```yaml
- xml_id: my_module.item
  table: my_table
  values:
    category_id: "$xmlref:catalog.category_default"  # cross-module ref
```

Declare `catalog` in `depends` to guarantee the referenced record
exists at install time.

### Migration referencing another module's table

```python
revision = "mymod_0002"
down_revision = "mymod_0001"
branch_labels = None
depends_on = ("catalog@head",)   # ensure catalog ran first

def upgrade() -> None:
    op.add_column(
        "my_table",
        sa.Column("catalog_item_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("treatment_catalog_items.id")),
    )
```

---

## 12. AI agent integration

Every module in DentalPin participates in the AI agent contract. The
contract is intentionally thin so modules can start as "agent-aware"
without committing to LLMs or long-running autonomy up front.

### What the contract requires of every module

```python
class MyModule(BaseModule):
    # ... models, router, permissions, events ...

    def get_tools(self) -> list[Tool]:
        """Callable actions this module exposes to AI agents."""
        return []
```

`get_tools()` is **mandatory** on every `BaseModule` subclass. Return
`[]` until your module has at least one action worth exposing — but
you MUST implement the method. The loader refuses to start if any
module omits it.

Why mandatory and not opt-in: the contract must be the default so a
future agent can trust that *any* discovered module either exposes a
valid (possibly empty) tool list or fails fast at boot.

### When to expose a tool

A module SHOULD expose a tool for every:

- public service method that **mutates state** a human would mutate
  through the UI (create, update, archive, cancel, send, issue, …);
- public service method that **reads domain data** an agent needs to
  plan an action (search, list, get-by-id, get-related, …).

A module SHOULD NOT expose a tool for:

- internal helpers (anything prefixed with `_`);
- event handlers (agents react to events via tools, not by subscribing);
- queries an agent cannot meaningfully combine (low-level DB joins,
  internal caches).

### Declaring a tool

```python
from pydantic import BaseModel
from app.core.agents import Tool, ToolCategory


class SearchPatientsArgs(BaseModel):
    """Arguments an LLM fills in when calling the tool."""
    query: str
    limit: int = 20


async def _search_patients(ctx, params: SearchPatientsArgs):
    return await PatientService.list_patients(
        ctx.db, ctx.clinic_id,
        search=params.query, page=1, page_size=params.limit,
    )


class PatientsModule(BaseModule):
    def get_tools(self) -> list[Tool]:
        return [
            Tool(
                name="search_patients",
                description=(
                    "Search patients by name, phone or email. Returns "
                    "up to `limit` matches in this clinic."
                ),
                parameters=SearchPatientsArgs,
                handler=_search_patients,
                permissions=["patients.read"],
                category=ToolCategory.READ,
            ),
        ]
```

Rules:

- **Namespacing is automatic.** The registry registers this tool as
  `patients.search_patients` — do NOT prefix the `name` field yourself.
- **Permissions reuse the existing RBAC strings.** Do not invent a
  per-tool permission grammar; declare the same string a router handler
  already uses via `require_permission(...)`.
- **Descriptions are LLM-facing prose, not code comments.** Write the
  `description` so an LLM that has never seen your module can pick the
  right tool. Be explicit about what the tool does and does NOT do.
- **Parameters must be a Pydantic V2 model.** The registry serializes
  it to JSON Schema for Anthropic / OpenAI function-calling APIs.
- **Handlers receive `ctx: AgentContext`.** Filter every query by
  `ctx.clinic_id` exactly as routers do — the multi-tenancy rule
  applies identically inside agent tools.

### Categorize every tool

```python
ToolCategory.READ         # never mutates state
ToolCategory.WRITE        # mutates but is recoverable
ToolCategory.DESTRUCTIVE  # deletes, sends external messages, issues money
```

`DESTRUCTIVE` tools automatically require human approval even in
autonomous mode. `WRITE` tools require approval when the agent runs
in supervised mode. Pick the most conservative category that is still
truthful — calling `send_invoice` a `WRITE` just because it's not a
DELETE is a bug. External side-effects (emails, SMS, webhook calls,
money movement) are `DESTRUCTIVE`.

### Building an agent

Modules that *ship* an agent (not just tools) expose it via
`get_agents()`:

```python
from app.core.agents import BaseAgent, AgentMode


class ReminderAgent(BaseAgent):
    name = "appointment_reminder"
    mode = AgentMode.AUTONOMOUS
    allowed_tools = [
        "agenda.list_upcoming_appointments",
        "notifications.send_sms",
    ]

    async def process(self, ctx):
        # Pick your LLM SDK (anthropic, openai, …). Core does not
        # abstract the provider.
        import anthropic
        client = anthropic.AsyncAnthropic()

        schemas = ctx.tools.schemas_for(self.allowed_tools, dialect="anthropic")
        messages = [{"role": "user", "content": "Send reminders for tomorrow."}]
        while True:
            resp = await client.messages.create(
                model="claude-sonnet-4-6", tools=schemas, messages=messages,
                max_tokens=2048,
            )
            if resp.stop_reason != "tool_use":
                break
            for block in resp.content:
                if block.type == "tool_use":
                    # Every tool call MUST go through the registry.
                    result = await ctx.tools.call(ctx, block.name, block.input)
                    messages.append({"role": "assistant", "content": resp.content})
                    messages.append({
                        "role": "user",
                        "content": [{
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": str(result.data or result.error),
                        }],
                    })
        return AgentResult(ok=True, summary="reminders sent")


class AgendaModule(BaseModule):
    def get_agents(self) -> list[type[BaseAgent]]:
        return [ReminderAgent]
```

Rules:

- **Never call service functions directly from inside an agent.** Go
  through `ctx.tools.call(ctx, qualified_name, arguments)`. That is
  the only path where permissions, guardrails, and audit logging run.
- **Subset tools explicitly.** `allowed_tools` is a hard list — the
  agent cannot invoke anything outside it, even if the registry has
  other tools.
- **Pick a mode honestly.** Default to `SUPERVISED` for any agent that
  writes. Only mark `AUTONOMOUS` once you are convinced the guardrails
  + audit story is sufficient for the risk.
- **No LLM abstraction in core.** Each agent imports its own SDK. Core
  guarantees the contract (tools + registry + audit), nothing else.

### Contract checklist for agent-ready modules

- [ ] `get_tools()` is implemented (even if empty)
- [ ] Every write operation the UI exposes is also exposed as a Tool
- [ ] Every tool declares at least one permission string that matches
      an existing RBAC entry
- [ ] Destructive tools are classified `ToolCategory.DESTRUCTIVE`
- [ ] Tool descriptions read well to someone who has never seen the
      module
- [ ] Handlers filter every query by `ctx.clinic_id`
- [ ] State-changing operations publish events via `event_bus` so
      other agents can react
- [ ] If the module ships an agent, `get_agents()` lists its classes

### Where to go deeper

- `backend/app/core/agents/` — the contract itself. Start with
  `tools/registry.py` to see the call chokepoint.
- `docs/design/module-system-architecture.md` — why tools and events
  are two separate extension points.

---

## 13. Pre-publish checklist

Before tagging a community module release:

- [ ] `pytest` passes locally
- [ ] `ruff check .` and `ruff format --check .` are clean
- [ ] `dentalpin modules doctor` reports no issues after install
- [ ] `CHANGELOG.md` has an entry for the new version
- [ ] `README.md` has install + config instructions
- [ ] `version` bumped per §8 rules
- [ ] Smoke test: install on a fresh instance, exercise the module,
      uninstall — DB returns to pre-install schema

---

## 14. Governance

- **Community modules stay in their own repos** and are not merged
  into the DentalPin monorepo.
- **Official modules** are maintained by the core team; PRs welcome
  through the usual review process.
- A **registry of known community modules** will appear at
  `docs/community-modules.md` once the first third-party modules
  exist. Inclusion is informational; it is not an endorsement.
- **Security reports**: email security@dentalpin.example (placeholder
  until the first release). Critical issues trigger a coordinated
  disclosure.
- **Breaking changes to the core API** follow the deprecation policy
  described in `docs/core-api.md`.

---

## Where to go next

- `docs/core-api.md` — full public API reference.
- `docs/operations.md` — admin/self-hoster guide.
- `docs/design/module-system-architecture.md` — why things are the
  way they are.
- `tests/fixtures/sample_module/` — minimal working module you can
  copy.
