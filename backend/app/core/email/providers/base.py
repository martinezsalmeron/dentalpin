"""Base email provider interface and data classes."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


class EmailStatus(StrEnum):
    """Status of an email send operation."""

    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class EmailMessage:
    """Represents an email message to be sent.

    Attributes:
        to_email: Recipient email address.
        to_name: Recipient name (optional).
        subject: Email subject line.
        body_html: HTML body content.
        body_text: Plain text body content (optional, auto-generated if not provided).
        from_email: Sender email address (optional, uses default if not provided).
        from_name: Sender name (optional, uses default if not provided).
        reply_to: Reply-to email address (optional).
        cc: List of CC recipients.
        bcc: List of BCC recipients.
        headers: Additional email headers.
        attachments: List of attachment dictionaries with 'filename', 'content', 'mime_type'.
    """

    to_email: str
    subject: str
    body_html: str
    to_name: str | None = None
    body_text: str | None = None
    from_email: str | None = None
    from_name: str | None = None
    reply_to: str | None = None
    cc: list[str] = field(default_factory=list)
    bcc: list[str] = field(default_factory=list)
    headers: dict[str, str] = field(default_factory=dict)
    attachments: list[dict] = field(default_factory=list)


@dataclass
class EmailResult:
    """Result of an email send operation.

    Attributes:
        status: The status of the operation (success, failed, skipped).
        message_id: Provider-assigned message ID (if successful).
        error_message: Error description (if failed).
        provider: Name of the provider that handled the email.
        sent_at: Timestamp when the email was sent.
    """

    status: EmailStatus
    provider: str
    message_id: str | None = None
    error_message: str | None = None
    sent_at: datetime | None = None

    @property
    def is_success(self) -> bool:
        """Check if the email was sent successfully."""
        return self.status == EmailStatus.SUCCESS


class EmailProvider(ABC):
    """Abstract base class for email providers.

    All email providers must implement this interface to be compatible
    with the email service.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of this provider."""
        pass

    @abstractmethod
    async def send(self, message: EmailMessage) -> EmailResult:
        """Send an email message.

        Args:
            message: The email message to send.

        Returns:
            EmailResult with the status of the operation.
        """
        pass

    async def health_check(self) -> bool:
        """Check if the provider is healthy and can send emails.

        Returns:
            True if the provider is operational, False otherwise.
        """
        return True

    async def close(self) -> None:
        """Clean up any resources used by the provider."""
        pass
