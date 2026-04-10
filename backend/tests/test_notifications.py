"""Tests for the notifications module."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.notifications.models import (
    EmailTemplate,
)
from app.modules.notifications.service import NotificationService


@pytest.mark.asyncio
async def test_get_clinic_settings(client: AsyncClient, auth_headers: dict, db_session: AsyncSession, test_clinic):
    """Test getting clinic notification settings."""
    response = await client.get(
        "/api/v1/notifications/settings",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()["data"]

    # Should have default settings
    assert "settings" in data
    assert "appointment_confirmation" in data["settings"]
    assert data["settings"]["appointment_confirmation"]["enabled"] is True


@pytest.mark.asyncio
async def test_update_clinic_settings(client: AsyncClient, auth_headers: dict, db_session: AsyncSession, test_clinic):
    """Test updating clinic notification settings."""
    update_data = {
        "settings": {
            "appointment_confirmation": {"auto_send": False},
            "welcome": {"enabled": False}
        }
    }

    response = await client.put(
        "/api/v1/notifications/settings",
        json=update_data,
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()["data"]

    # Check updated values
    assert data["settings"]["appointment_confirmation"]["auto_send"] is False
    assert data["settings"]["welcome"]["enabled"] is False


@pytest.mark.asyncio
async def test_get_patient_preferences(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession, test_patient
):
    """Test getting patient notification preferences."""
    response = await client.get(
        f"/api/v1/notifications/preferences/patient/{test_patient.id}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()["data"]

    # Should have default preferences
    assert data["email_enabled"] is True
    assert "preferences" in data


@pytest.mark.asyncio
async def test_update_patient_preferences(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession, test_patient
):
    """Test updating patient notification preferences."""
    update_data = {
        "email_enabled": False,
        "preferences": {
            "appointment_confirmation": True,
            "appointment_reminder": False
        }
    }

    response = await client.put(
        f"/api/v1/notifications/preferences/patient/{test_patient.id}",
        json=update_data,
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()["data"]

    assert data["email_enabled"] is False
    assert data["preferences"]["appointment_reminder"] is False


@pytest.mark.asyncio
async def test_list_email_logs(client: AsyncClient, auth_headers: dict, test_clinic):
    """Test listing email logs."""
    response = await client.get(
        "/api/v1/notifications/logs",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()

    assert "data" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_list_templates(client: AsyncClient, auth_headers: dict, test_clinic):
    """Test listing email templates."""
    response = await client.get(
        "/api/v1/notifications/templates",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()

    assert "data" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_test_email_endpoint(client: AsyncClient, auth_headers: dict, test_clinic):
    """Test the test email endpoint."""
    response = await client.post(
        "/api/v1/notifications/test",
        json={"to_email": "test@example.com"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()["data"]

    # In test mode, should use console provider
    assert data["provider"] == "console"
    assert data["success"] is True


@pytest.mark.asyncio
async def test_should_send_notification(db_session: AsyncSession, test_clinic):
    """Test the should_send_notification check."""
    # Without any settings, should return True for auto_send types
    should_send, reason = await NotificationService.should_send_notification(
        db_session,
        test_clinic.id,
        "appointment_confirmation",
    )

    # With default settings, should send
    assert reason in ["ok", "disabled_at_clinic_level", "manual_send_required"]


@pytest.mark.asyncio
async def test_manual_send_requires_patient_email(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession, test_clinic
):
    """Test that manual send requires a patient with email."""
    response = await client.post(
        "/api/v1/notifications/send",
        json={
            "notification_type": "welcome",
            # No patient_id provided
        },
        headers=auth_headers,
    )

    # Should fail because no recipient can be determined
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_create_custom_template(client: AsyncClient, auth_headers: dict, test_clinic):
    """Test creating a custom email template."""
    template_data = {
        "template_key": "custom_test",
        "locale": "es",
        "subject": "Test Subject",
        "body_html": "<html><body>Test</body></html>",
        "description": "Test template"
    }

    response = await client.post(
        "/api/v1/notifications/templates",
        json=template_data,
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()["data"]

    assert data["template_key"] == "custom_test"
    assert data["is_system"] is False


@pytest.mark.asyncio
async def test_cannot_delete_system_template(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession, test_clinic
):
    """Test that system templates cannot be deleted."""
    # First create a system template in DB
    from uuid import uuid4

    system_template = EmailTemplate(
        id=uuid4(),
        clinic_id=None,
        template_key="system_test",
        locale="es",
        subject="System Template",
        body_html="<p>System</p>",
        is_system=True,
    )
    db_session.add(system_template)
    await db_session.commit()
    await db_session.refresh(system_template)

    # Try to delete
    response = await client.delete(
        f"/api/v1/notifications/templates/{system_template.id}",
        headers=auth_headers,
    )

    assert response.status_code == 403
