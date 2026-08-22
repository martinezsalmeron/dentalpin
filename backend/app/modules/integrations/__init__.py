"""Integrations module - webhook subscriptions for third-party automations.

Phase 1 (issue #65, narrow first slice approved by Ramón 2026-08-21):
outbox infra + one working trigger (patient.created) + Stripe-style HMAC
signing + subscription CRUD. Public data-read API, API tokens, the
full trigger catalog, Zapier/Make apps, and admin UI are follow-up PRs
— see notes/dentalpin/65-integrations-api.md.
"""

from fastapi import APIRouter

from app.core.events.types import EventType
from app.core.plugins import BaseModule
from app.core.scheduling import ScheduledJob

from .models import WebhookDelivery, WebhookSubscription
from .router import router


class IntegrationsModule(BaseModule):
    """Integrations module providing webhook subscriptions (REST Hooks).

    Features (Phase 1):
    - Webhook subscription CRUD, per clinic
    - Outbox-backed delivery with retry/backoff, auto-disable on repeated
      failure
    - Stripe-style HMAC-SHA256 delivery signing
    - One working trigger: patient.created
    """

    manifest = {
        "name": "integrations",
        "version": "0.1.0",
        "summary": "Webhook subscriptions (REST Hooks) for third-party automations.",
        "author": "DentalPin Core Team",
        "license": "BSL-1.1",
        "category": "official",
        "depends": ["patients"],
        "installable": True,
        "auto_install": False,
        "removable": True,
        "role_permissions": {
            "admin": ["*"],
            "dentist": [],
            "hygienist": [],
            "assistant": [],
            "receptionist": [],
        },
    }

    def get_models(self) -> list:
        return [WebhookSubscription, WebhookDelivery]

    def get_router(self) -> APIRouter:
        return router

    def get_scheduled_jobs(self) -> list[ScheduledJob]:
        from .tasks import dispatch_outbox

        return [
            ScheduledJob(
                id="integrations_dispatch_outbox",
                func=dispatch_outbox,
                trigger="interval",
                trigger_args={"seconds": 45},
                name="Dispatch the webhook outbox (every 45s)",
            ),
        ]

    def get_permissions(self) -> list[str]:
        return [
            "subscriptions.read",
            "subscriptions.write",
        ]

    def get_event_handlers(self) -> dict:
        from .handlers import IntegrationsHandlers

        return {
            EventType.PATIENT_CREATED: IntegrationsHandlers.on_patient_created,
        }
