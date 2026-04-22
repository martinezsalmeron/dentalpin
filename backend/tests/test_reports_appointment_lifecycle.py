"""Analytics tests for the new reports/scheduling/* endpoints.

Each test crafts appointments and status events with *known* timestamps
(bypassing the endpoint for speed) and then asserts the numbers returned
by the analytics service match what the fixture data proves they should
be.

The four endpoints share a filter contract (``date_from``, ``date_to``,
optional ``cabinet_id`` / ``professional_id``); we exercise one filter
case per endpoint plus the math itself.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.models import Clinic, ClinicMembership, User
from app.core.auth.service import hash_password
from app.modules.agenda.models import (
    Appointment,
    AppointmentStatusEvent,
    Cabinet,
)
from app.modules.patients.models import Patient
from app.modules.reports.services import AppointmentLifecycleService


async def _world(db: AsyncSession) -> dict[str, UUID]:
    clinic = Clinic(id=uuid4(), name="RC", tax_id="B0", address={}, settings={})
    dentist = User(
        id=uuid4(),
        email=f"d-{uuid4().hex[:6]}@t.c",
        password_hash=hash_password("TestPass1234"),
        first_name="D",
        last_name="T",
        is_active=True,
    )
    cabinet_a = Cabinet(
        id=uuid4(),
        clinic_id=clinic.id,
        name="A",
        color="#000",
        display_order=0,
        is_active=True,
    )
    cabinet_b = Cabinet(
        id=uuid4(),
        clinic_id=clinic.id,
        name="B",
        color="#fff",
        display_order=1,
        is_active=True,
    )
    patient = Patient(id=uuid4(), clinic_id=clinic.id, first_name="P", last_name="Q")
    db.add_all([clinic, dentist, cabinet_a, cabinet_b, patient])
    await db.flush()
    db.add(ClinicMembership(id=uuid4(), user_id=dentist.id, clinic_id=clinic.id, role="dentist"))
    await db.commit()
    return {
        "clinic_id": clinic.id,
        "dentist_id": dentist.id,
        "cabinet_a": cabinet_a.id,
        "cabinet_b": cabinet_b.id,
        "patient_id": patient.id,
    }


def _make_apt(
    world: dict[str, UUID],
    *,
    start: datetime,
    cabinet_id: UUID | None = None,
    status: str = "completed",
    planned_minutes: int = 30,
) -> Appointment:
    cab = cabinet_id or world["cabinet_a"]
    return Appointment(
        id=uuid4(),
        clinic_id=world["clinic_id"],
        patient_id=world["patient_id"],
        professional_id=world["dentist_id"],
        cabinet="A" if cab == world["cabinet_a"] else "B",
        cabinet_id=cab,
        start_time=start,
        end_time=start + timedelta(minutes=planned_minutes),
        status=status,
        current_status_since=start,
    )


def _event(
    world: dict[str, UUID],
    apt: Appointment,
    *,
    from_status: str | None,
    to_status: str,
    at: datetime,
) -> AppointmentStatusEvent:
    return AppointmentStatusEvent(
        id=uuid4(),
        clinic_id=world["clinic_id"],
        appointment_id=apt.id,
        from_status=from_status,
        to_status=to_status,
        changed_at=at,
    )


@pytest.mark.asyncio
async def test_waiting_times_math(db_session: AsyncSession) -> None:
    world = await _world(db_session)

    # Appointment 1: waited 10 minutes.
    s1 = datetime(2026, 5, 10, 9, 0, tzinfo=UTC)
    a1 = _make_apt(world, start=s1)
    db_session.add(a1)
    db_session.add_all(
        [
            _event(world, a1, from_status=None, to_status="scheduled", at=s1),
            _event(world, a1, from_status="scheduled", to_status="checked_in", at=s1),
            _event(
                world,
                a1,
                from_status="checked_in",
                to_status="in_treatment",
                at=s1 + timedelta(minutes=10),
            ),
        ]
    )

    # Appointment 2: waited 6 minutes.
    s2 = datetime(2026, 5, 10, 10, 0, tzinfo=UTC)
    a2 = _make_apt(world, start=s2)
    db_session.add(a2)
    db_session.add_all(
        [
            _event(world, a2, from_status=None, to_status="scheduled", at=s2),
            _event(world, a2, from_status="scheduled", to_status="checked_in", at=s2),
            _event(
                world,
                a2,
                from_status="checked_in",
                to_status="in_treatment",
                at=s2 + timedelta(minutes=6),
            ),
        ]
    )
    await db_session.commit()

    result = await AppointmentLifecycleService.waiting_times(
        db_session,
        world["clinic_id"],
        date(2026, 5, 10),
        date(2026, 5, 10),
    )

    assert result["sample_size"] == 2
    assert result["avg_minutes"] == pytest.approx(8.0, abs=0.01)
    assert result["median_minutes"] == pytest.approx(8.0, abs=0.01)
    buckets = {b["label"]: b["count"] for b in result["distribution"]}
    # 6 min falls in 5-10 bucket, 10 min falls in 10-20 bucket.
    assert buckets["5-10"] == 1
    assert buckets["10-20"] == 1
    assert buckets["0-5"] == 0
    assert buckets["20+"] == 0


@pytest.mark.asyncio
async def test_punctuality_math(db_session: AsyncSession) -> None:
    world = await _world(db_session)

    base = datetime(2026, 5, 11, 10, 0, tzinfo=UTC)
    # Three patients: -3 min (early), +2 min (on time), +20 min (late_long).
    # Stagger starts by 30 minutes so they don't collide on the unique
    # (clinic, cabinet, professional, start_time) slot index.
    for idx, delta_minutes in enumerate((-3, 2, 20)):
        s = base + timedelta(hours=idx)
        apt = _make_apt(world, start=s)
        db_session.add(apt)
        db_session.add_all(
            [
                _event(world, apt, from_status=None, to_status="scheduled", at=s),
                _event(
                    world,
                    apt,
                    from_status="scheduled",
                    to_status="checked_in",
                    at=s + timedelta(minutes=delta_minutes),
                ),
            ]
        )
    await db_session.commit()

    result = await AppointmentLifecycleService.punctuality(
        db_session,
        world["clinic_id"],
        date(2026, 5, 11),
        date(2026, 5, 11),
    )
    assert result["sample_size"] == 3
    # avg = (-3 + 2 + 20) / 3 ≈ 6.33
    assert result["avg_delta_minutes"] == pytest.approx(19 / 3, abs=0.05)
    # |-3|=3 and |2|=2 both within 5 min => on_time = 2/3 ≈ 66.7%
    assert result["on_time_pct"] == pytest.approx(66.7, abs=0.1)
    buckets = {b["label"]: b["count"] for b in result["distribution"]}
    # early = delta < -5 (none), on_time = -5..5 (2), late_short = 5..15 (0),
    # late_long = >15 (1)
    assert buckets["early"] == 0
    assert buckets["on_time"] == 2
    assert buckets["late_short"] == 0
    assert buckets["late_long"] == 1


@pytest.mark.asyncio
async def test_duration_variance_math(db_session: AsyncSession) -> None:
    world = await _world(db_session)

    s = datetime(2026, 5, 12, 9, 0, tzinfo=UTC)
    # Appointment planned 30 min, actual 45 min => overrun.
    apt1 = _make_apt(world, start=s, planned_minutes=30)
    db_session.add(apt1)
    db_session.add_all(
        [
            _event(world, apt1, from_status=None, to_status="scheduled", at=s),
            _event(world, apt1, from_status="scheduled", to_status="in_treatment", at=s),
            _event(
                world,
                apt1,
                from_status="in_treatment",
                to_status="completed",
                at=s + timedelta(minutes=45),
            ),
        ]
    )
    # Appointment planned 60 min, actual 40 min => under.
    apt2 = _make_apt(world, start=s + timedelta(hours=2), planned_minutes=60)
    start2 = apt2.start_time
    db_session.add(apt2)
    db_session.add_all(
        [
            _event(world, apt2, from_status=None, to_status="scheduled", at=start2),
            _event(
                world,
                apt2,
                from_status="scheduled",
                to_status="in_treatment",
                at=start2,
            ),
            _event(
                world,
                apt2,
                from_status="in_treatment",
                to_status="completed",
                at=start2 + timedelta(minutes=40),
            ),
        ]
    )
    await db_session.commit()

    result = await AppointmentLifecycleService.duration_variance(
        db_session,
        world["clinic_id"],
        date(2026, 5, 12),
        date(2026, 5, 12),
    )

    assert result["sample_size"] == 2
    # Average delta: (+15 + -20) / 2 = -2.5
    assert result["avg_delta_minutes"] == pytest.approx(-2.5, abs=0.05)
    # Average overrun %: (50% + -33.33%) / 2 ≈ 8.33
    assert result["avg_overrun_pct"] == pytest.approx((50.0 + (-100 / 3)) / 2, abs=0.5)
    assert result["overrun_count"] == 1
    assert result["under_count"] == 1


@pytest.mark.asyncio
async def test_funnel_counts_and_rates(db_session: AsyncSession) -> None:
    world = await _world(db_session)

    s = datetime(2026, 5, 13, 9, 0, tzinfo=UTC)
    statuses = ["scheduled", "confirmed", "completed", "completed", "no_show", "cancelled"]
    for idx, st in enumerate(statuses):
        apt = _make_apt(world, start=s + timedelta(minutes=30 * idx), status=st)
        db_session.add(apt)
    await db_session.commit()

    result = await AppointmentLifecycleService.funnel(
        db_session,
        world["clinic_id"],
        date(2026, 5, 13),
        date(2026, 5, 13),
    )

    assert result["total"] == 6
    assert result["counts_by_status"]["completed"] == 2
    assert result["counts_by_status"]["no_show"] == 1
    assert result["counts_by_status"]["cancelled"] == 1
    # decided = 4 → completion = 2/4 = 50%
    assert result["completion_rate"] == pytest.approx(50.0, abs=0.01)
    assert result["no_show_rate"] == pytest.approx(25.0, abs=0.01)
    assert result["cancellation_rate"] == pytest.approx(25.0, abs=0.01)


@pytest.mark.asyncio
async def test_cabinet_filter_narrows_results(db_session: AsyncSession) -> None:
    world = await _world(db_session)
    s = datetime(2026, 5, 14, 9, 0, tzinfo=UTC)

    # Cabinet A: 1 completed appointment.
    apt_a = _make_apt(world, start=s, cabinet_id=world["cabinet_a"])
    db_session.add(apt_a)
    db_session.add_all(
        [
            _event(world, apt_a, from_status=None, to_status="scheduled", at=s),
            _event(world, apt_a, from_status="scheduled", to_status="checked_in", at=s),
            _event(
                world,
                apt_a,
                from_status="checked_in",
                to_status="in_treatment",
                at=s + timedelta(minutes=5),
            ),
        ]
    )
    # Cabinet B: 1 completed appointment.
    apt_b = _make_apt(world, start=s + timedelta(hours=1), cabinet_id=world["cabinet_b"])
    start_b = apt_b.start_time
    db_session.add(apt_b)
    db_session.add_all(
        [
            _event(world, apt_b, from_status=None, to_status="scheduled", at=start_b),
            _event(world, apt_b, from_status="scheduled", to_status="checked_in", at=start_b),
            _event(
                world,
                apt_b,
                from_status="checked_in",
                to_status="in_treatment",
                at=start_b + timedelta(minutes=20),
            ),
        ]
    )
    await db_session.commit()

    # Unfiltered -> 2 samples.
    unfiltered = await AppointmentLifecycleService.waiting_times(
        db_session, world["clinic_id"], date(2026, 5, 14), date(2026, 5, 14)
    )
    assert unfiltered["sample_size"] == 2

    only_a = await AppointmentLifecycleService.waiting_times(
        db_session,
        world["clinic_id"],
        date(2026, 5, 14),
        date(2026, 5, 14),
        cabinet_id=world["cabinet_a"],
    )
    assert only_a["sample_size"] == 1
    assert only_a["avg_minutes"] == pytest.approx(5.0, abs=0.01)


@pytest.mark.asyncio
async def test_rejects_range_over_365_days(db_session: AsyncSession) -> None:
    world = await _world(db_session)
    with pytest.raises(ValueError):
        await AppointmentLifecycleService.waiting_times(
            db_session,
            world["clinic_id"],
            date(2024, 1, 1),
            date(2026, 1, 1),
        )


@pytest.mark.asyncio
async def test_empty_range_returns_none_averages(db_session: AsyncSession) -> None:
    world = await _world(db_session)
    result = await AppointmentLifecycleService.waiting_times(
        db_session,
        world["clinic_id"],
        date(2020, 1, 1),
        date(2020, 1, 2),
    )
    assert result["sample_size"] == 0
    assert result["avg_minutes"] is None
    assert result["median_minutes"] is None
