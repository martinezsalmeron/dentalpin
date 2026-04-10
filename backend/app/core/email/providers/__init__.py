"""Email providers for the core email service."""

from app.core.email.providers.base import EmailMessage, EmailProvider, EmailResult
from app.core.email.providers.console import ConsoleProvider
from app.core.email.providers.smtp import SMTPProvider

__all__ = [
    "EmailMessage",
    "EmailProvider",
    "EmailResult",
    "SMTPProvider",
    "ConsoleProvider",
]
