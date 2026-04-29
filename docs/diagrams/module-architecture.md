# Module Architecture

How the plugin/module system works.

## Module Structure

```mermaid
classDiagram
    class BaseModule {
        <<abstract>>
        +name: str
        +version: str
        +dependencies: list[str]
        +get_models() list
        +get_router() APIRouter
        +get_permissions() list[str]
        +get_event_handlers() dict
    }

    class ClinicalModule {
        +name = "clinical"
        +get_models()
        +get_router()
        +get_permissions()
    }

    class OdontogramModule {
        +name = "odontogram"
        +dependencies = ["clinical"]
        +get_models()
        +get_router()
    }

    class BillingModule {
        +name = "billing"
        +dependencies = ["clinical"]
        +get_models()
        +get_router()
    }

    BaseModule <|-- ClinicalModule
    BaseModule <|-- OdontogramModule
    BaseModule <|-- BillingModule
```

## Module Loading

```mermaid
sequenceDiagram
    participant App as FastAPI App
    participant Loader as ModuleLoader
    participant Registry as ModuleRegistry
    participant Module as Module Instance

    App->>Loader: discover_modules()
    Loader->>Loader: Scan backend/app/modules/
    loop For each module
        Loader->>Module: Import & instantiate
        Loader->>Registry: register(module)
        Registry->>Registry: Sort by dependencies
    end

    App->>Registry: get_all_modules()
    loop For each module (sorted)
        App->>Module: get_models()
        App->>App: Register with SQLAlchemy
        App->>Module: get_router()
        App->>App: Mount at /api/v1/{name}/
        App->>Module: get_permissions()
        App->>App: Add to permission list
        App->>Module: get_event_handlers()
        App->>App: Subscribe to event bus
    end
```

## Module Directory

```
backend/app/modules/{module_name}/
├── __init__.py      # Module class definition
├── models.py        # SQLAlchemy models
├── router.py        # FastAPI endpoints
├── schemas.py       # Pydantic models
└── service.py       # Business logic
```

## Adding a Module

1. Create directory in `backend/app/modules/`
2. Define class extending `BaseModule`
3. Implement required methods
4. Module auto-discovered on startup

See [Creating Modules](../technical/creating-modules.md) for detailed guide.
