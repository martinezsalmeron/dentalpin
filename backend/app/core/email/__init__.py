"""Core email infrastructure.

This module provides an abstraction layer for sending emails that can be used
by any other module in the application. It supports multiple email providers
through a plugin architecture.

Usage:
    from app.core.email import email_service

    await email_service.send_templated(
        to_email="patient@example.com",
        to_name="John Doe",
        template_key="appointment_confirmation",
        locale="es",
        context={"patient_name": "John", "appointment_date": "2024-12-15"},
    )
"""

from app.core.email.providers.base import EmailMessage, EmailProvider, EmailResult
from app.core.email.service import email_service

__all__ = ["email_service", "EmailMessage", "EmailProvider", "EmailResult"]
