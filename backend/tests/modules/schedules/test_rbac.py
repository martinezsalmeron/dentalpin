"""RBAC verification — ensures manifest-declared role permissions work.

This is the canary test for the new manifest-driven RBAC pattern. It
asserts that `has_permission` picks up the schedules manifest without
touching ``core/auth/permissions.ROLE_PERMISSIONS``.
"""

from __future__ import annotations

import pytest

from app.core.auth.permissions import has_permission


@pytest.mark.parametrize(
    "role,permission,expected",
    [
        # admin inherits "*" via wildcard in manifest and core.
        ("admin", "schedules.clinic_hours.write", True),
        ("admin", "schedules.analytics.read", True),
        # dentist can read clinic hours + edit own schedule.
        ("dentist", "schedules.clinic_hours.read", True),
        ("dentist", "schedules.professional.own.write", True),
        ("dentist", "schedules.professional.write", False),
        # hygienist — no analytics.
        ("hygienist", "schedules.analytics.read", False),
        # receptionist — no write on clinic hours.
        ("receptionist", "schedules.clinic_hours.write", False),
        ("receptionist", "schedules.availability.read", True),
        # assistant — view only for professional schedules.
        ("assistant", "schedules.professional.read", True),
        ("assistant", "schedules.professional.write", False),
    ],
)
def test_role_has_expected_schedules_permission(role: str, permission: str, expected: bool):
    assert has_permission(role, permission) is expected
