"""WebhookGateway: enqueue matching + dispatch (send, retry, auto-disable)."""

from datetime import UTC, datetime, timedelta

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.email.encryption import encrypt_password
from app.modules.integrations import client as webhook_client
from app.modules.integrations.gateway import MAX_CONSECUTIVE_FAILURES, WebhookGateway
from app.modules.integrations.models import WebhookDelivery, WebhookSubscription
from app.modules.integrations.signing import verify

EVENT = "patient.created"


async def _subscription(db, clinic_id, *, event_types=(EVENT,), secret="whsec", **kwargs):
    sub = WebhookSubscription(
        clinic_id=clinic_id,
        target_url="https://example.com/hook",
        event_types=list(event_types),
        secret_encrypted=encrypt_password(secret),
        **kwargs,
    )
    db.add(sub)
    await db.commit()
    await db.refresh(sub)
    return sub


@pytest.mark.asyncio
async def test_enqueue_only_matching_active_subscriptions(db_session: AsyncSession, test_clinic):
    matching = await _subscription(db_session, test_clinic.id, event_types=(EVENT,))
    await _subscription(db_session, test_clinic.id, event_types=("budget.sent",))  # wrong event
    await _subscription(
        db_session, test_clinic.id, event_types=(EVENT,), is_active=False
    )  # inactive

    deliveries = await WebhookGateway.enqueue_for_event(
        db_session, test_clinic.id, EVENT, {"patient_id": "p1"}
    )
    await db_session.commit()

    assert len(deliveries) == 1
    assert deliveries[0].subscription_id == matching.id
    assert deliveries[0].status == "queued"


@pytest.mark.asyncio
async def test_enqueue_no_match_creates_nothing(db_session: AsyncSession, test_clinic):
    await _subscription(db_session, test_clinic.id, event_types=("budget.sent",))
    deliveries = await WebhookGateway.enqueue_for_event(
        db_session, test_clinic.id, EVENT, {"patient_id": "p1"}
    )
    assert deliveries == []


@pytest.mark.asyncio
async def test_dispatch_success_signs_and_marks_sent(
    db_session: AsyncSession, test_clinic, monkeypatch
):
    sub = await _subscription(db_session, test_clinic.id, secret="s3cret")
    deliveries = await WebhookGateway.enqueue_for_event(
        db_session, test_clinic.id, EVENT, {"patient_id": "p1"}
    )
    await db_session.commit()

    captured = {}

    async def fake_post(url, body, headers):
        captured["url"] = url
        captured["body"] = body
        captured["headers"] = headers
        return httpx.Response(200, request=httpx.Request("POST", url))

    monkeypatch.setattr(webhook_client, "post_webhook", fake_post)

    attempted = await WebhookGateway.dispatch_outbox(db_session)
    assert attempted == 1

    await db_session.refresh(deliveries[0])
    assert deliveries[0].status == "sent"
    assert deliveries[0].response_status_code == 200
    assert deliveries[0].sent_at is not None

    assert captured["url"] == sub.target_url
    assert verify("s3cret", captured["body"], captured["headers"]["X-Integrations-Signature"])


@pytest.mark.asyncio
async def test_dispatch_failure_schedules_retry_and_increments_failures(
    db_session: AsyncSession, test_clinic, monkeypatch
):
    sub = await _subscription(db_session, test_clinic.id)
    deliveries = await WebhookGateway.enqueue_for_event(
        db_session, test_clinic.id, EVENT, {"patient_id": "p1"}
    )
    await db_session.commit()

    async def fake_post(url, body, headers):
        return httpx.Response(500, request=httpx.Request("POST", url))

    monkeypatch.setattr(webhook_client, "post_webhook", fake_post)

    await WebhookGateway.dispatch_outbox(db_session)

    await db_session.refresh(deliveries[0])
    assert deliveries[0].status == "failed"
    assert deliveries[0].attempts == 1
    assert deliveries[0].next_attempt_at is not None
    # first backoff: 60 * 2**(1-1) = 60s
    assert deliveries[0].next_attempt_at <= datetime.now(UTC) + timedelta(seconds=61)

    await db_session.refresh(sub)
    assert sub.consecutive_failures == 1
    assert sub.is_active is True


@pytest.mark.asyncio
async def test_auto_disable_after_max_consecutive_failures(
    db_session: AsyncSession, test_clinic, monkeypatch
):
    sub = await _subscription(db_session, test_clinic.id)

    async def fake_post(url, body, headers):
        return httpx.Response(500, request=httpx.Request("POST", url))

    monkeypatch.setattr(webhook_client, "post_webhook", fake_post)

    for _ in range(MAX_CONSECUTIVE_FAILURES):
        deliveries = await WebhookGateway.enqueue_for_event(
            db_session, test_clinic.id, EVENT, {"patient_id": "p1"}
        )
        await db_session.commit()
        if not deliveries:
            # subscription got auto-disabled mid-loop: enqueue stops matching it
            break
        await WebhookGateway.dispatch_outbox(db_session)

    await db_session.refresh(sub)
    assert sub.consecutive_failures >= MAX_CONSECUTIVE_FAILURES
    assert sub.is_active is False
    assert sub.disabled_at is not None
    assert sub.disabled_reason is not None


@pytest.mark.asyncio
async def test_success_resets_consecutive_failures(
    db_session: AsyncSession, test_clinic, monkeypatch
):
    sub = await _subscription(db_session, test_clinic.id)
    sub.consecutive_failures = 3
    await db_session.commit()

    async def fake_post(url, body, headers):
        return httpx.Response(200, request=httpx.Request("POST", url))

    monkeypatch.setattr(webhook_client, "post_webhook", fake_post)

    await WebhookGateway.enqueue_for_event(db_session, test_clinic.id, EVENT, {"patient_id": "p1"})
    await db_session.commit()
    await WebhookGateway.dispatch_outbox(db_session)

    await db_session.refresh(sub)
    assert sub.consecutive_failures == 0


@pytest.mark.asyncio
async def test_dispatch_transport_error_marks_failed(
    db_session: AsyncSession, test_clinic, monkeypatch
):
    await _subscription(db_session, test_clinic.id)
    deliveries = await WebhookGateway.enqueue_for_event(
        db_session, test_clinic.id, EVENT, {"patient_id": "p1"}
    )
    await db_session.commit()

    from app.modules.integrations.client import WebhookDeliveryError

    async def fake_post(url, body, headers):
        raise WebhookDeliveryError("connection refused")

    monkeypatch.setattr(webhook_client, "post_webhook", fake_post)

    await WebhookGateway.dispatch_outbox(db_session)

    await db_session.refresh(deliveries[0])
    assert deliveries[0].status == "failed"
    assert "connection refused" in deliveries[0].error_message


@pytest.mark.asyncio
async def test_dispatch_skips_not_yet_due_deliveries(
    db_session: AsyncSession, test_clinic, monkeypatch
):
    sub = await _subscription(db_session, test_clinic.id)
    delivery = WebhookDelivery(
        subscription_id=sub.id,
        clinic_id=test_clinic.id,
        event_type=EVENT,
        payload={},
        status="failed",
        attempts=1,
        next_attempt_at=datetime.now(UTC) + timedelta(hours=1),  # not due yet
    )
    db_session.add(delivery)
    await db_session.commit()

    called = False

    async def fake_post(url, body, headers):
        nonlocal called
        called = True
        return httpx.Response(200, request=httpx.Request("POST", url))

    monkeypatch.setattr(webhook_client, "post_webhook", fake_post)

    attempted = await WebhookGateway.dispatch_outbox(db_session)
    assert attempted == 0
    assert called is False


@pytest.mark.asyncio
async def test_dispatch_terminal_after_max_attempts_not_retried(
    db_session: AsyncSession, test_clinic
):
    sub = await _subscription(db_session, test_clinic.id)
    delivery = WebhookDelivery(
        subscription_id=sub.id,
        clinic_id=test_clinic.id,
        event_type=EVENT,
        payload={},
        status="failed",
        attempts=5,
        max_attempts=5,
        next_attempt_at=datetime.now(UTC) - timedelta(minutes=1),
    )
    db_session.add(delivery)
    await db_session.commit()

    attempted = await WebhookGateway.dispatch_outbox(db_session)
    assert attempted == 0


@pytest.mark.asyncio
async def test_dispatch_inactive_subscription_marks_failed_without_network(
    db_session: AsyncSession, test_clinic, monkeypatch
):
    sub = await _subscription(db_session, test_clinic.id, is_active=False)
    delivery = WebhookDelivery(
        subscription_id=sub.id,
        clinic_id=test_clinic.id,
        event_type=EVENT,
        payload={},
        status="queued",
        next_attempt_at=datetime.now(UTC),
    )
    db_session.add(delivery)
    await db_session.commit()

    called = False

    async def fake_post(url, body, headers):
        nonlocal called
        called = True
        return httpx.Response(200, request=httpx.Request("POST", url))

    monkeypatch.setattr(webhook_client, "post_webhook", fake_post)

    await WebhookGateway.dispatch_outbox(db_session)
    assert called is False

    await db_session.refresh(delivery)
    assert delivery.status == "failed"
    assert "inactive" in delivery.error_message
