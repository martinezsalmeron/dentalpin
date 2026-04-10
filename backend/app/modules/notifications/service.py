"""Notifications module business logic."""

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.email import EmailResult, email_service
from app.core.email.providers.base import EmailStatus

from .models import (
    ClinicNotificationSettings,
    ClinicSmtpSettings,
    EmailLog,
    EmailTemplate,
    NotificationPreference,
)

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for managing notifications and sending emails."""

    # ========================================================================
    # Email Template Management
    # ========================================================================

    @staticmethod
    async def list_templates(
        db: AsyncSession,
        clinic_id: UUID,
        page: int = 1,
        page_size: int = 20,
        locale: str | None = None,
        include_system: bool = True,
    ) -> tuple[list[EmailTemplate], int]:
        """List email templates for a clinic.

        Returns clinic-specific templates and optionally system templates.
        """
        # Build base query
        conditions = []

        if include_system:
            # Include system templates and clinic templates
            conditions.append(
                (EmailTemplate.clinic_id == clinic_id) | (EmailTemplate.clinic_id.is_(None))
            )
        else:
            conditions.append(EmailTemplate.clinic_id == clinic_id)

        if locale:
            conditions.append(EmailTemplate.locale == locale)

        # Count total
        count_query = select(func.count()).select_from(EmailTemplate)
        for condition in conditions:
            count_query = count_query.where(condition)
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # Get items
        query = select(EmailTemplate).order_by(
            EmailTemplate.template_key, EmailTemplate.locale
        )
        for condition in conditions:
            query = query.where(condition)

        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(query)
        items = list(result.scalars().all())

        return items, total

    @staticmethod
    async def get_template(
        db: AsyncSession,
        clinic_id: UUID,
        template_key: str,
        locale: str = "es",
    ) -> EmailTemplate | None:
        """Get a template by key and locale.

        Priority: clinic-specific > system template.
        """
        # First try clinic-specific
        result = await db.execute(
            select(EmailTemplate).where(
                EmailTemplate.clinic_id == clinic_id,
                EmailTemplate.template_key == template_key,
                EmailTemplate.locale == locale,
                EmailTemplate.is_active == True,  # noqa: E712
            )
        )
        template = result.scalar_one_or_none()
        if template:
            return template

        # Fallback to system template
        result = await db.execute(
            select(EmailTemplate).where(
                EmailTemplate.clinic_id.is_(None),
                EmailTemplate.template_key == template_key,
                EmailTemplate.locale == locale,
                EmailTemplate.is_active == True,  # noqa: E712
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_template_by_id(
        db: AsyncSession,
        clinic_id: UUID,
        template_id: UUID,
    ) -> EmailTemplate | None:
        """Get a template by ID."""
        result = await db.execute(
            select(EmailTemplate).where(
                EmailTemplate.id == template_id,
                (EmailTemplate.clinic_id == clinic_id) | (EmailTemplate.clinic_id.is_(None)),
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create_template(
        db: AsyncSession,
        clinic_id: UUID,
        data: dict,
    ) -> EmailTemplate:
        """Create a new email template for a clinic."""
        template = EmailTemplate(
            clinic_id=clinic_id,
            is_system=False,
            **data,
        )
        db.add(template)
        await db.commit()
        await db.refresh(template)
        return template

    @staticmethod
    async def update_template(
        db: AsyncSession,
        template: EmailTemplate,
        data: dict,
    ) -> EmailTemplate:
        """Update an email template."""
        if template.is_system:
            raise ValueError("Cannot modify system templates")

        for key, value in data.items():
            if value is not None:
                setattr(template, key, value)

        await db.commit()
        await db.refresh(template)
        return template

    @staticmethod
    async def delete_template(
        db: AsyncSession,
        template: EmailTemplate,
    ) -> None:
        """Delete an email template."""
        if template.is_system:
            raise ValueError("Cannot delete system templates")

        await db.delete(template)
        await db.commit()

    # ========================================================================
    # Notification Preferences
    # ========================================================================

    @staticmethod
    async def get_patient_preferences(
        db: AsyncSession,
        clinic_id: UUID,
        patient_id: UUID,
    ) -> NotificationPreference | None:
        """Get notification preferences for a patient."""
        result = await db.execute(
            select(NotificationPreference).where(
                NotificationPreference.clinic_id == clinic_id,
                NotificationPreference.patient_id == patient_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_or_create_patient_preferences(
        db: AsyncSession,
        clinic_id: UUID,
        patient_id: UUID,
    ) -> NotificationPreference:
        """Get or create notification preferences for a patient."""
        prefs = await NotificationService.get_patient_preferences(db, clinic_id, patient_id)
        if prefs:
            return prefs

        # Create default preferences
        prefs = NotificationPreference(
            clinic_id=clinic_id,
            patient_id=patient_id,
        )
        db.add(prefs)
        await db.commit()
        await db.refresh(prefs)
        return prefs

    @staticmethod
    async def update_patient_preferences(
        db: AsyncSession,
        clinic_id: UUID,
        patient_id: UUID,
        data: dict,
    ) -> NotificationPreference:
        """Update notification preferences for a patient."""
        prefs = await NotificationService.get_or_create_patient_preferences(
            db, clinic_id, patient_id
        )

        for key, value in data.items():
            if value is not None:
                setattr(prefs, key, value)

        await db.commit()
        await db.refresh(prefs)
        return prefs

    # ========================================================================
    # Clinic Settings
    # ========================================================================

    @staticmethod
    async def get_clinic_settings(
        db: AsyncSession,
        clinic_id: UUID,
    ) -> ClinicNotificationSettings | None:
        """Get notification settings for a clinic."""
        result = await db.execute(
            select(ClinicNotificationSettings).where(
                ClinicNotificationSettings.clinic_id == clinic_id
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_or_create_clinic_settings(
        db: AsyncSession,
        clinic_id: UUID,
    ) -> ClinicNotificationSettings:
        """Get or create notification settings for a clinic."""
        settings = await NotificationService.get_clinic_settings(db, clinic_id)
        if settings:
            return settings

        # Create default settings
        settings = ClinicNotificationSettings(clinic_id=clinic_id)
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
        return settings

    @staticmethod
    async def update_clinic_settings(
        db: AsyncSession,
        clinic_id: UUID,
        data: dict,
    ) -> ClinicNotificationSettings:
        """Update notification settings for a clinic."""
        settings = await NotificationService.get_or_create_clinic_settings(db, clinic_id)

        if "settings" in data:
            # Merge settings instead of replacing
            # Create a copy to ensure SQLAlchemy detects the change
            current_settings = dict(settings.settings) if settings.settings else {}
            for key, value in data["settings"].items():
                if key in current_settings:
                    # Create a new dict with merged values
                    current_settings[key] = {**current_settings[key], **value}
                else:
                    current_settings[key] = value
            settings.settings = current_settings

        await db.commit()
        await db.refresh(settings)
        return settings

    # ========================================================================
    # SMTP Settings
    # ========================================================================

    @staticmethod
    async def get_smtp_settings(
        db: AsyncSession,
        clinic_id: UUID,
    ) -> ClinicSmtpSettings | None:
        """Get SMTP settings for a clinic."""
        result = await db.execute(
            select(ClinicSmtpSettings).where(ClinicSmtpSettings.clinic_id == clinic_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_or_create_smtp_settings(
        db: AsyncSession,
        clinic_id: UUID,
    ) -> ClinicSmtpSettings:
        """Get or create SMTP settings for a clinic."""
        settings = await NotificationService.get_smtp_settings(db, clinic_id)
        if settings:
            return settings

        # Create default settings (disabled by default)
        settings = ClinicSmtpSettings(
            clinic_id=clinic_id,
            provider="disabled",
        )
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
        return settings

    @staticmethod
    async def update_smtp_settings(
        db: AsyncSession,
        clinic_id: UUID,
        data: dict,
    ) -> ClinicSmtpSettings:
        """Update SMTP settings for a clinic.

        Handles password encryption if a new password is provided.
        """
        from app.core.email.encryption import encrypt_password

        settings = await NotificationService.get_or_create_smtp_settings(db, clinic_id)

        # Handle password separately - encrypt if provided
        if "password" in data:
            password = data.pop("password")
            if password:
                settings.password_encrypted = encrypt_password(password)
            # If password is None/empty, don't change existing password

        # Reset verification if connection settings change
        connection_fields = {"host", "port", "username", "use_tls", "use_ssl"}
        if any(field in data for field in connection_fields):
            settings.is_verified = False
            settings.last_verified_at = None

        # Update other fields
        for key, value in data.items():
            if hasattr(settings, key) and value is not None:
                setattr(settings, key, value)

        await db.commit()
        await db.refresh(settings)
        return settings

    @staticmethod
    async def test_smtp_settings(
        db: AsyncSession,
        clinic_id: UUID,
        host: str,
        port: int,
        username: str | None,
        password: str | None,
        use_tls: bool,
        use_ssl: bool,
        from_email: str,
        to_email: str,
    ) -> EmailResult:
        """Test SMTP connection with specific settings.

        Creates a temporary SMTP provider and sends a test email.
        On success, marks the clinic's SMTP settings as verified.
        """
        from app.core.email.encryption import decrypt_password
        from app.core.email.providers.base import EmailMessage
        from app.core.email.providers.smtp import SMTPProvider

        # If no password provided, try to use existing one from DB
        actual_password = password
        if not actual_password:
            settings = await NotificationService.get_smtp_settings(db, clinic_id)
            if settings and settings.password_encrypted:
                actual_password = decrypt_password(settings.password_encrypted)

        # Create a temporary SMTP provider with the test settings
        provider = SMTPProvider(
            host=host,
            port=port,
            username=username,
            password=actual_password,
            use_tls=use_tls,
            use_ssl=use_ssl,
            default_from_email=from_email,
            default_from_name="DentalPin",
        )

        # Send test email
        message = EmailMessage(
            to_email=to_email,
            subject="DentalPin - Test de conexión SMTP",
            body_html="""
            <html>
            <body style="font-family: sans-serif; padding: 20px;">
                <h2>Conexión SMTP exitosa</h2>
                <p>Este es un email de prueba de la configuración SMTP de tu clínica.</p>
                <p>Si has recibido este mensaje, la configuración está funcionando correctamente.</p>
                <hr>
                <p style="color: #666; font-size: 12px;">
                    Enviado desde DentalPin
                </p>
            </body>
            </html>
            """,
            body_text="Conexión SMTP exitosa. La configuración está funcionando correctamente.",
            from_email=from_email,
        )

        result = await provider.send(message)

        # Mark as verified if successful
        if result.is_success:
            settings = await NotificationService.get_or_create_smtp_settings(db, clinic_id)
            settings.is_verified = True
            settings.last_verified_at = datetime.now(UTC)
            await db.commit()

        return result

    # ========================================================================
    # Email Logs
    # ========================================================================

    @staticmethod
    async def list_logs(
        db: AsyncSession,
        clinic_id: UUID,
        page: int = 1,
        page_size: int = 20,
        patient_id: UUID | None = None,
        status: str | None = None,
        template_key: str | None = None,
    ) -> tuple[list[EmailLog], int]:
        """List email logs with optional filters."""
        conditions = [EmailLog.clinic_id == clinic_id]

        if patient_id:
            conditions.append(EmailLog.patient_id == patient_id)
        if status:
            conditions.append(EmailLog.status == status)
        if template_key:
            conditions.append(EmailLog.template_key == template_key)

        # Count total
        count_query = select(func.count()).select_from(EmailLog)
        for condition in conditions:
            count_query = count_query.where(condition)
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # Get items
        query = select(EmailLog).order_by(EmailLog.created_at.desc())
        for condition in conditions:
            query = query.where(condition)

        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(query)
        items = list(result.scalars().all())

        return items, total

    @staticmethod
    async def create_log(
        db: AsyncSession,
        clinic_id: UUID,
        recipient_email: str,
        template_key: str,
        subject: str,
        status: str,
        provider: str,
        patient_id: UUID | None = None,
        provider_message_id: str | None = None,
        error_message: str | None = None,
        triggered_by_event: str | None = None,
        triggered_by_user_id: UUID | None = None,
        context_data: dict | None = None,
    ) -> EmailLog:
        """Create an email log entry."""
        log = EmailLog(
            clinic_id=clinic_id,
            recipient_email=recipient_email,
            patient_id=patient_id,
            template_key=template_key,
            subject=subject,
            status=status,
            provider=provider,
            provider_message_id=provider_message_id,
            error_message=error_message,
            triggered_by_event=triggered_by_event,
            triggered_by_user_id=triggered_by_user_id,
            context_data=context_data,
            sent_at=datetime.now(UTC) if status == "sent" else None,
        )
        db.add(log)
        await db.commit()
        await db.refresh(log)
        return log

    # ========================================================================
    # Send Email
    # ========================================================================

    @staticmethod
    async def should_send_notification(
        db: AsyncSession,
        clinic_id: UUID,
        notification_type: str,
        patient_id: UUID | None = None,
        check_auto_send: bool = True,
    ) -> tuple[bool, str]:
        """Check if a notification should be sent.

        Returns (should_send, reason).
        """
        # Check clinic settings
        clinic_settings = await NotificationService.get_clinic_settings(db, clinic_id)
        if clinic_settings:
            type_settings = clinic_settings.settings.get(notification_type, {})

            # Check if enabled
            if not type_settings.get("enabled", True):
                return False, "disabled_at_clinic_level"

            # Check auto_send if required
            if check_auto_send and not type_settings.get("auto_send", True):
                return False, "manual_send_required"

        # Check patient preferences
        if patient_id:
            prefs = await NotificationService.get_patient_preferences(db, clinic_id, patient_id)
            if prefs:
                # Check global email toggle
                if not prefs.email_enabled:
                    return False, "patient_opted_out"

                # Check specific preference
                if not prefs.preferences.get(notification_type, True):
                    return False, f"patient_opted_out_of_{notification_type}"

        return True, "ok"

    @staticmethod
    async def send_notification(
        db: AsyncSession,
        clinic_id: UUID,
        notification_type: str,
        to_email: str,
        context: dict[str, Any],
        patient_id: UUID | None = None,
        triggered_by_event: str | None = None,
        triggered_by_user_id: UUID | None = None,
        force_send: bool = False,
    ) -> EmailResult:
        """Send a notification email.

        Args:
            db: Database session.
            clinic_id: Clinic ID.
            notification_type: Type of notification (e.g., 'appointment_confirmation').
            to_email: Recipient email address.
            context: Template context variables.
            patient_id: Patient ID (optional).
            triggered_by_event: Event that triggered this email (optional).
            triggered_by_user_id: User who triggered manual send (optional).
            force_send: Skip preference checks (for manual send).

        Returns:
            EmailResult with status.
        """
        # Check if should send (unless forced)
        if not force_send:
            should_send, reason = await NotificationService.should_send_notification(
                db, clinic_id, notification_type, patient_id
            )
            if not should_send:
                logger.info(
                    f"Skipping notification {notification_type}: {reason}",
                    extra={"clinic_id": str(clinic_id), "patient_id": str(patient_id)},
                )
                # Log the skipped email
                await NotificationService.create_log(
                    db=db,
                    clinic_id=clinic_id,
                    recipient_email=to_email,
                    template_key=notification_type,
                    subject=f"[SKIPPED] {notification_type}",
                    status="skipped",
                    provider=email_service.get_provider_name(),
                    patient_id=patient_id,
                    error_message=reason,
                    triggered_by_event=triggered_by_event,
                    triggered_by_user_id=triggered_by_user_id,
                )
                return EmailResult(
                    status=EmailStatus.SKIPPED,
                    provider=email_service.get_provider_name(),
                    error_message=reason,
                )

        # Get patient locale preference
        locale = "es"
        if patient_id:
            prefs = await NotificationService.get_patient_preferences(db, clinic_id, patient_id)
            if prefs:
                locale = prefs.preferred_locale

        # Get template
        template = await NotificationService.get_template(
            db, clinic_id, notification_type, locale
        )

        # Build subject from template or use default
        subject = template.subject if template else f"Notificación: {notification_type}"

        # Get custom template content if available
        template_html = template.body_html if template else None
        template_text = template.body_text if template else None

        # Send email (use clinic-specific SMTP if configured)
        result = await email_service.send_templated(
            to_email=to_email,
            to_name=context.get("patient_name"),
            template_key=notification_type,
            locale=locale,
            context=context,
            subject=subject,
            template_html=template_html,
            template_text=template_text,
            db=db,
            clinic_id=clinic_id,
        )

        # Sanitize context for logging (remove sensitive data)
        safe_context = {k: v for k, v in context.items() if k not in ["password", "token"]}

        # Log the email
        await NotificationService.create_log(
            db=db,
            clinic_id=clinic_id,
            recipient_email=to_email,
            template_key=notification_type,
            subject=subject,
            status="sent" if result.is_success else "failed",
            provider=result.provider,
            patient_id=patient_id,
            provider_message_id=result.message_id,
            error_message=result.error_message,
            triggered_by_event=triggered_by_event,
            triggered_by_user_id=triggered_by_user_id,
            context_data=safe_context,
        )

        return result

    @staticmethod
    async def test_email_connection(to_email: str) -> EmailResult:
        """Send a test email to verify configuration."""
        from app.core.email.providers.base import EmailMessage

        message = EmailMessage(
            to_email=to_email,
            subject="DentalPin - Test de conexión de email",
            body_html="""
            <html>
            <body style="font-family: sans-serif; padding: 20px;">
                <h2>¡Conexión exitosa!</h2>
                <p>Este es un email de prueba de DentalPin.</p>
                <p>Si has recibido este mensaje, la configuración de email está funcionando correctamente.</p>
                <hr>
                <p style="color: #666; font-size: 12px;">
                    Enviado desde DentalPin
                </p>
            </body>
            </html>
            """,
            body_text="¡Conexión exitosa! Este es un email de prueba de DentalPin.",
        )

        return await email_service.send(message)
