# Creating Modules

This guide explains how to create new modules for DentalPin's plugin architecture.

> **Visual guide:** See [Module Architecture Diagram](diagrams/module-architecture.md) for how the plugin system works.

## Overview

Modules are self-contained features that provide:
- SQLAlchemy models (database tables)
- FastAPI router (API endpoints)
- Event handlers (react to other modules' events)
- RBAC permissions (access control)

Modules are auto-discovered at startup and loaded in dependency order.

## Directory Structure

```
backend/app/modules/{module_name}/
├── __init__.py      # Module class (required)
├── models.py        # SQLAlchemy models
├── schemas.py       # Pydantic request/response schemas
├── router.py        # FastAPI endpoints
└── service.py       # Business logic
```

## Step 1: Create the Module Class

In `__init__.py`, create a class inheriting from `BaseModule`:

```python
"""Inventory module - supplies and stock management."""

from fastapi import APIRouter

from app.core.plugins import BaseModule

from .models import InventoryItem, StockMovement
from .router import router


class InventoryModule(BaseModule):
    """Inventory module for managing clinic supplies."""

    @property
    def name(self) -> str:
        """Unique module identifier."""
        return "inventory"

    @property
    def version(self) -> str:
        """Module version (semver format)."""
        return "0.1.0"

    @property
    def dependencies(self) -> list[str]:
        """Modules that must be loaded before this one.

        The loader validates these exist and loads them first.
        Circular dependencies will raise an error.
        """
        return ["clinical"]  # Requires clinical module

    def get_models(self) -> list:
        """SQLAlchemy models to register with the database."""
        return [InventoryItem, StockMovement]

    def get_router(self) -> APIRouter:
        """FastAPI router mounted at /api/v1/{name}/."""
        return router

    def get_event_handlers(self) -> dict:
        """Subscribe to events from other modules.

        Returns a dict of event_name -> handler function.
        """
        return {
            "appointment.completed": self._on_appointment_completed,
        }

    def get_permissions(self) -> list[str]:
        """RBAC permissions this module adds.

        Format: 'resource.action'
        """
        return [
            "inventory.read",
            "inventory.write",
            "inventory.manage",
        ]

    def _on_appointment_completed(self, data: dict) -> None:
        """Handle appointment.completed event."""
        # Deduct supplies used in the appointment
        pass
```

## Step 2: Define Models

In `models.py`, define SQLAlchemy models:

```python
"""Inventory models."""

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, Integer, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class InventoryItem(Base):
    """A supply item in the clinic inventory."""

    __tablename__ = "inventory_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    clinic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clinics.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    sku: Mapped[str | None] = mapped_column(String(50))
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    min_quantity: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )
```

## Step 3: Define Schemas

In `schemas.py`, define Pydantic schemas:

```python
"""Inventory schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class InventoryItemBase(BaseModel):
    name: str
    sku: str | None = None
    quantity: int = 0
    min_quantity: int = 0
    notes: str | None = None


class InventoryItemCreate(InventoryItemBase):
    pass


class InventoryItemUpdate(BaseModel):
    name: str | None = None
    sku: str | None = None
    quantity: int | None = None
    min_quantity: int | None = None
    notes: str | None = None


class InventoryItemResponse(InventoryItemBase):
    id: UUID
    clinic_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
```

## Step 4: Define Router

In `router.py`, define API endpoints:

```python
"""Inventory router."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.auth import get_current_user, get_clinic_context

from .schemas import (
    InventoryItemCreate,
    InventoryItemUpdate,
    InventoryItemResponse,
)
from . import service

router = APIRouter()


@router.get("/items", response_model=list[InventoryItemResponse])
async def list_items(
    db: AsyncSession = Depends(get_db),
    clinic = Depends(get_clinic_context),
):
    """List all inventory items for the clinic."""
    return await service.list_items(db, clinic.id)


@router.post("/items", response_model=InventoryItemResponse, status_code=201)
async def create_item(
    data: InventoryItemCreate,
    db: AsyncSession = Depends(get_db),
    clinic = Depends(get_clinic_context),
):
    """Create a new inventory item."""
    return await service.create_item(db, clinic.id, data)


@router.put("/items/{item_id}", response_model=InventoryItemResponse)
async def update_item(
    item_id: UUID,
    data: InventoryItemUpdate,
    db: AsyncSession = Depends(get_db),
    clinic = Depends(get_clinic_context),
):
    """Update an inventory item."""
    item = await service.update_item(db, clinic.id, item_id, data)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item
```

## Step 5: Create Database Migration

After adding models, create an Alembic migration.

> **Note:** This guide is being rewritten in full as part of the module-system
> v1 refactor. The sections below cover the **new** branch-per-module
> convention. The complete guide (with Nuxt layers, slots, lifecycle
> hooks, role_permissions, external IDs, and packaging) lands in Etapa 7.

### Where migrations live

**Brand-new modules (recommended)** keep their migrations in their own
Alembic branch:

```
backend/app/modules/<module_name>/
├── __init__.py
├── manifest.py
├── models.py
├── migrations/
│   └── versions/
│       └── <module>_0001_initial.py   # branch_labels=('<module>',)
└── ...
```

The first revision declares its branch label and no down_revision:

```python
revision = "inv_0001"
down_revision = None
branch_labels = ("inventory",)
depends_on = None
```

`alembic/env.py` auto-discovers `backend/app/modules/*/migrations/versions/`
at load time — there's no configuration step. Create the directory,
write the revision file, and `alembic upgrade head` picks it up.

**Existing modules (Fase A legacy)** — `clinical`, `catalog`, `budget`,
`billing`, `odontogram`, `treatment_plan`, `media`, `notifications`,
`reports` — currently keep their migrations in the main linear chain
at `backend/alembic/versions/`. New migrations for these modules still
go to main linear. The branch extraction is Fase B work.

### Generating a revision

For a **branch module**:

```bash
cd backend
alembic revision \
  --autogenerate \
  -m "add inventory module" \
  --version-path app/modules/inventory/migrations/versions \
  --branch-label inventory \
  --head base
alembic upgrade head
```

For a **legacy module** (main linear):

```bash
cd backend
alembic revision --autogenerate -m "add inventory column"
alembic upgrade head
```

### Frontend layer (optional)

A community module can ship its own UI by bundling a Nuxt Layer inside
its Python package:

```
dentalpin_billing/
├── __init__.py
├── manifest.py
├── ...backend files...
└── frontend/                 # the layer
    ├── nuxt.config.ts
    ├── pages/
    ├── components/
    ├── composables/
    ├── i18n/
    └── slots.ts              # optional: registerSlot(...) calls
```

Declare the layer in the manifest:

```python
MANIFEST = {
    "name": "my_module",
    "version": "0.1.0",
    # ...
    "frontend": {
        "layer_path": "frontend",   # relative to the package root
        "navigation": [
            {
                "label": "nav.myModule",
                "to": "/my-module",
                "icon": "i-lucide-box",
                "permission": "my_module.read",
                "order": 80,
            }
        ],
    },
}
```

At install time, the registry:

1. resolves `<pkg>/frontend` to an absolute path,
2. rewrites `frontend/modules.json` atomically,
3. expects the host to rebuild the frontend container:
   `docker compose build frontend && docker compose up -d frontend`.

`frontend/nuxt.config.ts` reads `modules.json` at boot and passes the
layer array to `extends`, so Nuxt auto-discovers the layer's pages,
components, composables and i18n files.

**Fase A policy**: the 9 official modules keep their UI on the host
frontend and do **not** declare `layer_path` — per the pre-bundled
decision. Install/uninstall of officials never triggers a frontend
rebuild. Community modules are the primary consumer of the layer
mechanism.

CLI helpers inside the backend container:

```bash
./bin/dentalpin modules sync-frontend     # regenerate modules.json
./bin/dentalpin modules rebuild-frontend  # prints the docker command
```

### Cross-module FKs

A migration that references tables owned by another module must declare
the dependency explicitly so Alembic orders the upgrade correctly:

```python
depends_on = ("billing@head",)
```

The other module must also be listed in `manifest["depends"]`. A CI
validator (Etapa 7) rejects PRs that violate this rule.

## Module Dependencies

Dependencies are validated at startup:

```python
@property
def dependencies(self) -> list[str]:
    return ["clinical", "billing"]  # Both must exist
```

If a dependency is missing, the app will fail to start with an error:
```
ValueError: Missing dependency: 'billing' required by 'inventory'
```

Circular dependencies are also detected:
```
ValueError: Circular dependency detected: inventory -> billing -> inventory
```

## Event Bus

Modules can communicate via events:

**Publishing events (in service.py):**
```python
from app.core.events import event_bus

async def complete_appointment(db, appointment_id):
    # ... business logic ...
    event_bus.publish("appointment.completed", {
        "appointment_id": str(appointment_id),
        "patient_id": str(appointment.patient_id),
    })
```

**Subscribing to events (in module class):**
```python
def get_event_handlers(self) -> dict:
    return {
        "appointment.completed": self._handle_completed,
        "patient.created": self._handle_new_patient,
    }

def _handle_completed(self, data: dict) -> None:
    appointment_id = data["appointment_id"]
    # React to the event
```

## RBAC Permissions

Permissions follow the format `resource.action`:

```python
def get_permissions(self) -> list[str]:
    return [
        "inventory.read",    # View inventory
        "inventory.write",   # Create/update items
        "inventory.manage",  # Full control including delete
    ]
```

These permissions are aggregated by the registry and can be assigned to roles.

## Testing Your Module

Create tests in `backend/tests/modules/{module_name}/`:

```python
"""Tests for inventory module."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_inventory_item(client: AsyncClient, auth_headers: dict):
    response = await client.post(
        "/api/v1/inventory/items",
        json={"name": "Dental Floss", "quantity": 100},
        headers=auth_headers,
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Dental Floss"
```

## Checklist

Before submitting a new module:

- [ ] Module class inherits from `BaseModule`
- [ ] `name` and `version` properties defined
- [ ] `get_models()` returns all models
- [ ] `get_router()` returns router with endpoints
- [ ] `dependencies` lists required modules (if any)
- [ ] Database migration created and tested
- [ ] Schemas validate input/output correctly
- [ ] Service layer handles business logic
- [ ] Tests cover critical paths
- [ ] Permissions defined for RBAC
