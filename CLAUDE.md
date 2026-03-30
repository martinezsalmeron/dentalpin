# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Open source dental clinic management software with modular plugin architecture.

**Stack:** FastAPI (Python 3.11+) backend, Vue 3/Nuxt 3 frontend, PostgreSQL, Docker
**License:** BSL 1.1 (commercial SaaS use restricted, converts to Apache 2.0 after 4 years)

## Development Commands

### Docker (recommended)
```bash
docker-compose up                    # Start all services (db, backend, frontend)
docker-compose up -d db backend      # Start only backend services
docker-compose down -v               # Stop and remove volumes
```

### Backend
```bash
cd backend
pip install -e ".[dev]"              # Install with dev dependencies
uvicorn app.main:app --reload        # Run locally (needs PostgreSQL)

# Linting
ruff check .                         # Check linting errors
ruff check --fix .                   # Auto-fix linting errors
ruff format .                        # Format code

# Testing
pytest                               # Run all tests
pytest tests/test_auth.py -v         # Run specific test file
pytest -k "test_login" -v            # Run tests matching pattern
pytest --tb=short                    # Shorter tracebacks

# Database migrations
alembic revision --autogenerate -m "description"  # Create migration
alembic upgrade head                              # Apply migrations
```

### Frontend (not yet implemented)
```bash
cd frontend
npm install
npm run dev                          # Start dev server
npm run lint                         # Run ESLint
npm run test                         # Run vitest tests
```

## Architecture

### Plugin/Module System

The backend uses a modular architecture where each feature is a self-contained module:

```
backend/app/
├── core/
│   ├── auth/           # JWT auth, RBAC (always loaded)
│   ├── plugins/        # Module system infrastructure
│   │   ├── base.py     # BaseModule abstract class
│   │   ├── registry.py # Module registration
│   │   └── loader.py   # Auto-discovery and mounting
│   └── events/         # Event bus for cross-module communication
└── modules/
    └── clinical/       # First module: patient/appointment management
        ├── __init__.py # Module manifest (ClinicalModule class)
        ├── models.py   # SQLAlchemy models
        ├── schemas.py  # Pydantic request/response schemas
        ├── router.py   # FastAPI endpoints
        └── service.py  # Business logic
```

**Creating a new module:**
1. Create package under `backend/app/modules/{name}/`
2. Implement a class inheriting from `BaseModule` in `__init__.py`
3. Define required properties and methods:
   - `name` - unique identifier (e.g., `"inventory"`)
   - `version` - semver string (e.g., `"0.1.0"`)
   - `get_models()` - return list of SQLAlchemy models
   - `get_router()` - return FastAPI router
4. Define optional properties:
   - `dependencies` - list of required module names (e.g., `["clinical"]`)
   - `get_event_handlers()` - dict of event subscriptions
   - `get_permissions()` - list of RBAC permissions (e.g., `["inventory.read"]`)
5. Module auto-discovered on startup, router mounted at `/api/v1/{name}/`

See `docs/creating-modules.md` for detailed guide with examples.

### Database

- All models use UUID primary keys
- All timestamps are timezone-aware (TIMESTAMPTZ)
- All models include auto-managed `created_at` and `updated_at`
- JSONB columns for flexible data (addresses, settings, teeth data)
- Soft deletes via status fields (never hard delete patient data)

### Event Bus

Modules communicate via `app.core.events.bus.event_bus`:
```python
from app.core.events.bus import event_bus
event_bus.publish("patient.created", {"patient_id": str(patient.id)})
```

## Key Conventions

- **Code in English** - All code, variables, comments in English. UI strings in Spanish via i18n.
- **Type everything** - Python type hints required, TypeScript strict mode
- **API responses** - Consistent format: `{data: ..., message: "...", errors: [...]}`
- **Pagination** - List endpoints return: `{data: [...], total: N, page: N, page_size: N}`
- **FDI notation** - Teeth identified by FDI numbers (11-48 adult, 51-85 deciduous)

## Environment Variables

```bash
DATABASE_URL=postgresql+asyncpg://dental:dental_dev@localhost:5432/dental_clinic
SECRET_KEY=your-secret-key
ENVIRONMENT=development  # development | test | production
```

## Demo Credentials

`admin@demo.clinic` / `demo1234`
