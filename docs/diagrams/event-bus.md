# Event Bus

Cross-module communication via events.

## Overview

```mermaid
graph LR
    subgraph "Publisher"
        MOD_A[Module A]
    end

    subgraph "Event Bus"
        BUS[EventBus<br/>singleton]
    end

    subgraph "Subscribers"
        MOD_B[Module B]
        MOD_C[Module C]
    end

    MOD_A -->|publish| BUS
    BUS -->|notify| MOD_B
    BUS -->|notify| MOD_C
```

## Event Flow

```mermaid
sequenceDiagram
    participant SVC as PatientService
    participant BUS as event_bus
    participant NOTIF as NotificationsModule

    Note over SVC: Patient created
    SVC->>BUS: publish("patient.created", {patient_id})
    BUS->>BUS: Log event
    BUS->>NOTIF: handler(data)
    NOTIF->>NOTIF: Send welcome email
    Note over BUS: Errors logged,<br/>don't propagate
```

## Subscription Setup

```mermaid
sequenceDiagram
    participant APP as App Startup
    participant MOD as Module
    participant BUS as EventBus

    APP->>MOD: get_event_handlers()
    MOD-->>APP: {"patient.created": handler}
    APP->>BUS: subscribe("patient.created", handler)
    BUS->>BUS: Store in _handlers dict
```

## EventBus Class

```mermaid
classDiagram
    class EventBus {
        -_handlers: dict[str, list[Handler]]
        +subscribe(event_type, handler)
        +unsubscribe(event_type, handler)
        +publish(event_type, data)
        +clear()
    }

    class Handler {
        <<type>>
        Callable[[dict], None]
    }

    EventBus --> Handler : stores
```

## Usage Example

**Publishing an event:**
```python
from app.core.events import event_bus

# In service layer
event_bus.publish("patient.created", {
    "patient_id": str(patient.id),
    "clinic_id": str(patient.clinic_id),
})
```

**Subscribing to events:**
```python
# In module's __init__.py
class NotificationsModule(BaseModule):
    def get_event_handlers(self) -> dict:
        return {
            "patient.created": self._on_patient_created,
            "appointment.scheduled": self._on_appointment_scheduled,
        }

    def _on_patient_created(self, data: dict) -> None:
        # Queue welcome notification
        pass
```

## Event Types

| Event | Data | Triggered By |
|-------|------|--------------|
| `patient.created` | patient_id, clinic_id | PatientService.create |
| `appointment.scheduled` | appointment_id, patient_id | AppointmentService.create |
| `appointment.cancelled` | appointment_id | AppointmentService.cancel |
| `invoice.paid` | invoice_id, amount | BillingService.record_payment |

## Design Notes

- **Synchronous**: Handlers run in same request (MVP)
- **Fire-and-forget**: Errors logged, don't propagate
- **Singleton**: One global `event_bus` instance
- **Testing**: Call `event_bus.clear()` in fixtures
