# System Overview

High-level architecture of DentalPin.

## Architecture

```mermaid
graph TB
    subgraph "Frontend"
        FE[Nuxt 3 + Vue 3<br/>TypeScript]
    end

    subgraph "Backend"
        API[FastAPI<br/>Python 3.11+]

        subgraph "Core"
            AUTH[Auth]
            PLUGINS[Plugin System]
            EVENTS[Event Bus]
        end

        subgraph "Modules"
            CLINICAL[Clinical]
            ODONTO[Odontogram]
            BILLING[Billing]
            BUDGET[Budget]
            CATALOG[Catalog]
            NOTIF[Notifications]
            REPORTS[Reports]
        end
    end

    subgraph "Database"
        DB[(PostgreSQL)]
    end

    FE -->|REST API| API
    API --> AUTH
    API --> PLUGINS
    PLUGINS --> CLINICAL
    PLUGINS --> ODONTO
    PLUGINS --> BILLING
    PLUGINS --> BUDGET
    PLUGINS --> CATALOG
    PLUGINS --> NOTIF
    PLUGINS --> REPORTS
    EVENTS -.->|pub/sub| CLINICAL
    EVENTS -.->|pub/sub| NOTIF
    CLINICAL --> DB
    ODONTO --> DB
    BILLING --> DB
    BUDGET --> DB
    CATALOG --> DB
    NOTIF --> DB
    REPORTS --> DB
```

## Components

| Layer | Technology | Purpose |
|-------|------------|---------|
| Frontend | Nuxt 3, Vue 3, Nuxt UI | SPA with SSR support |
| API | FastAPI | REST endpoints, JWT auth |
| ORM | SQLAlchemy 2.0 | Async database access |
| Database | PostgreSQL + asyncpg | Multi-tenant data storage |
| Migrations | Alembic | Schema versioning |

## Key Patterns

- **Multi-tenancy**: All data scoped by `clinic_id`
- **Modular**: Features as independent modules
- **Event-driven**: Modules communicate via event bus
- **RBAC**: Role-based permissions with wildcards
