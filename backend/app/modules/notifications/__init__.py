"""Notifications module - email notifications and preferences management."""

from fastapi import APIRouter

from app.core.plugins import BaseModule

from .models import (
    ClinicNotificationSettings,
    ClinicSmtpSettings,
    EmailLog,
    EmailTemplate,
    NotificationPreference,
)
from .router import router


class NotificationsModule(BaseModule):
    """Notifications module providing email notifications management.

    Features:
    - Customizable email templates per clinic
    - Patient notification preferences
    - Clinic-level settings for auto/manual sending
    - Email logs and auditing
    - Event-driven notifications
    """

    manifest = {
        "name": "notifications",
        "version": "0.1.0",
        "summary": "Email templates, preferences, SMTP, event-driven sending.",
        "author": "DentalPin Core Team",
        "license": "BSL-1.1",
        "category": "official",
        "depends": ["patients", "agenda", "budget", "billing"],
        "installable": True,
        "auto_install": True,
        "removable": False,
        "role_permissions": {
            "admin": ["*"],
            "dentist": ["preferences.read", "preferences.write", "send"],
            "hygienist": [],
            "assistant": ["preferences.read", "preferences.write", "send"],
            "receptionist": ["preferences.read", "preferences.write", "send"],
        },
    }

    def get_models(self) -> list:
        return [
            EmailTemplate,
            NotificationPreference,
            ClinicNotificationSettings,
            ClinicSmtpSettings,
            EmailLog,
        ]

    def get_router(self) -> APIRouter:
        return router

    def get_permissions(self) -> list[str]:
        return [
            "templates.read",  # View email templates
            "templates.write",  # Edit email templates
            "preferences.read",  # View notification preferences
            "preferences.write",  # Edit notification preferences
            "logs.read",  # View email logs
            "send",  # Send emails manually
            "settings.read",  # View clinic notification settings
            "settings.write",  # Edit clinic notification settings
        ]

    def get_event_handlers(self) -> dict:
        from .handlers import NotificationHandlers

        return {
            "appointment.scheduled": NotificationHandlers.on_appointment_scheduled,
            "appointment.cancelled": NotificationHandlers.on_appointment_cancelled,
            "patient.created": NotificationHandlers.on_patient_created,
            "budget.sent": NotificationHandlers.on_budget_sent,
            "budget.accepted": NotificationHandlers.on_budget_accepted,
            "invoice.sent": NotificationHandlers.on_invoice_sent,
        }
