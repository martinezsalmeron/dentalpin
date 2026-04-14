# RBAC Flow

How permissions are checked end-to-end.

## Overview

```mermaid
graph LR
    subgraph "Backend (Source of Truth)"
        ROLES[ROLE_PERMISSIONS<br/>permissions.py]
        EXPAND[expand_permissions()]
    end

    subgraph "API Response"
        ME[/me endpoint]
    end

    subgraph "Frontend"
        PERMS[usePermissions()]
        CAN[can() / canAny()]
        BTN[ActionButton]
        NAV[Navigation]
    end

    ROLES --> EXPAND
    EXPAND --> ME
    ME --> PERMS
    PERMS --> CAN
    CAN --> BTN
    CAN --> NAV
```

## Permission Check Flow

```mermaid
sequenceDiagram
    participant EP as Endpoint
    participant DEP as require_permission()
    participant CTX as ClinicContext
    participant PERM as permissions.py

    EP->>DEP: require_permission("clinical.patients.read")
    DEP->>CTX: Get user role
    CTX-->>DEP: role = "dentist"
    DEP->>PERM: has_permission("dentist", "clinical.patients.read")
    PERM->>PERM: Get role permissions
    Note over PERM: dentist has "clinical.*"
    PERM->>PERM: permission_matches("clinical.patients.read", "clinical.*")
    Note over PERM: "clinical.*" matches "clinical.patients.read" ✓
    PERM-->>DEP: True
    DEP-->>EP: Allowed
```

## Wildcard Resolution

```mermaid
graph TD
    subgraph "Wildcards"
        STAR["*"]
        MOD["module.*"]
        RES["module.resource.*"]
        EXACT["module.resource.action"]
    end

    subgraph "Matches"
        STAR --> |matches| ALL[Everything]
        MOD --> |matches| M1["module.x"]
        MOD --> |matches| M2["module.x.y"]
        MOD --> |matches| M3["module.x.y.z"]
        RES --> |matches| R1["module.resource.read"]
        RES --> |matches| R2["module.resource.write"]
        EXACT --> |matches| E1["module.resource.action only"]
    end
```

## Role Hierarchy

```mermaid
graph TB
    ADMIN[admin<br/>"*"]
    DENTIST[dentist<br/>"clinical.*", "odontogram.*", ...]
    HYGIENIST[hygienist<br/>"clinical.patients.read", ...]
    ASSISTANT[assistant<br/>"clinical.patients.*", ...]
    RECEPTION[receptionist<br/>"clinical.patients.*", ...]

    ADMIN --> |inherits all| DENTIST
    DENTIST --> |more than| HYGIENIST
    DENTIST --> |more than| ASSISTANT
    ASSISTANT --> |similar to| RECEPTION
```

## Frontend Permission Check

```mermaid
sequenceDiagram
    participant COMP as Component
    participant USE as usePermissions()
    participant STATE as Auth State

    COMP->>USE: can("clinical.patients.write")
    USE->>STATE: Get permissions[]
    STATE-->>USE: ["clinical.patients.read", "clinical.patients.write", ...]
    USE->>USE: permissions.includes("clinical.patients.write")
    USE-->>COMP: true
    COMP->>COMP: Render edit button
```

## ActionButton Component

```vue
<!-- Only renders if user has permission -->
<ActionButton
  resource="patients"
  action="write"
  @click="edit"
>
  Edit
</ActionButton>
```

```mermaid
graph LR
    PROPS[resource="patients"<br/>action="write"] --> LOOKUP
    LOOKUP[PERMISSIONS.patients.write] --> CHECK
    CHECK["can('clinical.patients.write')"] --> RENDER
    RENDER{has permission?}
    RENDER --> |yes| SHOW[Render button]
    RENDER --> |no| HIDE[Don't render]
```
