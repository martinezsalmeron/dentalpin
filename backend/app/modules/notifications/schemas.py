"""Notifications module Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

# ============================================================================
# Email Template Schemas
# ============================================================================


class EmailTemplateBase(BaseModel):
    """Base schema for email templates."""

    template_key: str = Field(..., max_length=100)
    locale: str = Field(default="es", max_length=5)
    subject: str = Field(..., max_length=255)
    body_html: str
    body_text: str | None = None
    variables: dict | None = None
    description: str | None = Field(default=None, max_length=500)
    is_active: bool = True


class EmailTemplateCreate(EmailTemplateBase):
    """Schema for creating an email template."""

    pass


class EmailTemplateUpdate(BaseModel):
    """Schema for updating an email template."""

    subject: str | None = Field(default=None, max_length=255)
    body_html: str | None = None
    body_text: str | None = None
    variables: dict | None = None
    description: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None


class EmailTemplateResponse(EmailTemplateBase):
    """Schema for email template response."""

    id: UUID
    clinic_id: UUID | None
    is_system: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ============================================================================
# Notification Preference Schemas
# ============================================================================


class NotificationPreferenceBase(BaseModel):
    """Base schema for notification preferences."""

    email_enabled: bool = True
    preferences: dict = Field(
        default_factory=lambda: {
            "appointment_confirmation": True,
            "appointment_reminder": True,
            "appointment_cancelled": True,
            "budget_sent": True,
            "budget_accepted": True,
            "welcome": True,
        }
    )
    preferred_locale: str = Field(default="es", max_length=5)


class NotificationPreferenceCreate(NotificationPreferenceBase):
    """Schema for creating notification preferences."""

    patient_id: UUID | None = None
    user_id: UUID | None = None


class NotificationPreferenceUpdate(BaseModel):
    """Schema for updating notification preferences."""

    email_enabled: bool | None = None
    preferences: dict | None = None
    preferred_locale: str | None = Field(default=None, max_length=5)


class NotificationPreferenceResponse(NotificationPreferenceBase):
    """Schema for notification preference response."""

    id: UUID
    clinic_id: UUID
    patient_id: UUID | None
    user_id: UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ============================================================================
# Clinic Notification Settings Schemas
# ============================================================================


class NotificationTypeSettings(BaseModel):
    """Settings for a specific notification type."""

    auto_send: bool = True
    enabled: bool = True
    hours_before: int | None = None  # For reminders


class ClinicNotificationSettingsBase(BaseModel):
    """Base schema for clinic notification settings."""

    settings: dict = Field(
        default_factory=lambda: {
            "appointment_confirmation": {"auto_send": True, "enabled": True},
            "appointment_cancelled": {"auto_send": True, "enabled": True},
            "appointment_reminder": {"auto_send": True, "enabled": True, "hours_before": 24},
            "budget_sent": {"auto_send": False, "enabled": True},
            "budget_accepted": {"auto_send": True, "enabled": True},
            "welcome": {"auto_send": False, "enabled": True},
        }
    )


class ClinicNotificationSettingsUpdate(BaseModel):
    """Schema for updating clinic notification settings."""

    settings: dict


class ClinicNotificationSettingsResponse(ClinicNotificationSettingsBase):
    """Schema for clinic notification settings response."""

    id: UUID
    clinic_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ============================================================================
# Email Log Schemas
# ============================================================================


class EmailLogResponse(BaseModel):
    """Schema for email log response."""

    id: UUID
    clinic_id: UUID
    recipient_email: str
    patient_id: UUID | None
    template_key: str
    subject: str
    status: str
    provider: str
    provider_message_id: str | None
    error_message: str | None
    created_at: datetime
    sent_at: datetime | None
    triggered_by_event: str | None

    model_config = {"from_attributes": True}


# ============================================================================
# Manual Send Schemas
# ============================================================================


class ManualSendRequest(BaseModel):
    """Schema for manual email send request."""

    notification_type: str = Field(..., description="Type of notification to send")
    patient_id: UUID | None = Field(
        default=None, description="Patient to send to (required for most types)"
    )
    appointment_id: UUID | None = Field(
        default=None, description="Appointment ID (for appointment notifications)"
    )
    budget_id: UUID | None = Field(
        default=None, description="Budget ID (for budget notifications)"
    )
    custom_context: dict | None = Field(
        default=None, description="Additional context variables"
    )


class ManualSendResponse(BaseModel):
    """Schema for manual send response."""

    success: bool
    message: str
    log_id: UUID | None = None


# ============================================================================
# Test Email Schema
# ============================================================================


class TestEmailRequest(BaseModel):
    """Schema for testing email configuration."""

    to_email: str = Field(..., description="Email address to send test to")


class TestEmailResponse(BaseModel):
    """Schema for test email response."""

    success: bool
    message: str
    provider: str


# ============================================================================
# SMTP Settings Schemas
# ============================================================================


class SmtpSettingsResponse(BaseModel):
    """Schema for SMTP settings response.

    Note: Never includes the actual password, only has_password boolean.
    """

    provider: str
    host: str | None
    port: int | None
    username: str | None
    has_password: bool
    use_tls: bool
    use_ssl: bool
    from_email: str | None
    from_name: str | None
    is_active: bool
    is_verified: bool
    last_verified_at: datetime | None

    model_config = {"from_attributes": True}


class SmtpSettingsUpdate(BaseModel):
    """Schema for updating SMTP settings."""

    provider: str = Field(default="smtp", pattern="^(smtp|console|disabled)$")
    host: str | None = Field(default=None, max_length=255)
    port: int = Field(default=587, ge=1, le=65535)
    username: str | None = Field(default=None, max_length=255)
    password: str | None = Field(default=None)  # Only for updates, never returned
    use_tls: bool = True
    use_ssl: bool = False
    from_email: str | None = Field(default=None, max_length=255)
    from_name: str | None = Field(default=None, max_length=255)


class SmtpTestRequest(BaseModel):
    """Schema for testing SMTP connection with specific settings."""

    host: str = Field(..., max_length=255)
    port: int = Field(default=587, ge=1, le=65535)
    username: str | None = Field(default=None, max_length=255)
    password: str | None = Field(default=None)
    use_tls: bool = True
    use_ssl: bool = False
    from_email: str = Field(..., max_length=255)
    to_email: str = Field(..., max_length=255)
