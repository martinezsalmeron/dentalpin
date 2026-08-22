"""Event types this module actually delivers.

Phase 1 ships exactly one working trigger end-to-end (Ramón 2026-08-21,
notes/dentalpin/65-integrations-api.md "Current status"). Almost every
other event issue #65 §3 wants already exists on the bus
(``core/events/types.py``) — adding it here means only "declare a new
transactional handler in handlers.py", no new bus infra. Keeping this
list separate from ``EventType`` (which has ~60 events, most
irrelevant to webhooks) is what lets ``WebhookSubscriptionCreate``
reject a subscription for an event nobody will ever deliver, instead
of silently accepting one that never fires.
"""

from app.core.events import EventType

SUPPORTED_EVENT_TYPES: frozenset[str] = frozenset({EventType.PATIENT_CREATED})
