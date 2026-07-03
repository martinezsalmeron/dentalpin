"""The `patient.archived` → document soft-archive cascade (audit #95).

Two regressions are covered:

* the publisher must include ``clinic_id`` in the payload (it didn't);
* the media handler must accept the bus calling convention
  ``handler(data)`` — its old ``(self, db, data)`` signature raised
  ``TypeError`` on every archive.

The end-to-end "documents actually get archived" path is not asserted
here: the handler opens its own ``async_session_maker`` session (bound to
the import-time event loop), which pytest-asyncio's per-test loop can't
drive. That path is covered by ``DocumentService.archive_patient_documents``'s
own tests; the two regressions above are what broke.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.models import Clinic
from app.core.events import EventType, event_bus
from app.modules.media import MediaModule
from app.modules.patients.models import Patient
from app.modules.patients.service import PatientService


@pytest.mark.asyncio
async def test_archive_patient_payload_includes_clinic_id(
    test_clinic: Clinic,
    test_patient: Patient,
    db_session: AsyncSession,
) -> None:
    captured: list[dict] = []

    async def _spy(data: dict) -> None:
        captured.append(data)

    event_bus.subscribe(EventType.PATIENT_ARCHIVED, _spy)
    try:
        await PatientService.archive_patient(db_session, test_patient)
    finally:
        event_bus.unsubscribe(EventType.PATIENT_ARCHIVED, _spy)

    assert captured, "patient.archived was not published"
    assert captured[0]["patient_id"] == str(test_patient.id)
    assert captured[0]["clinic_id"] == str(test_clinic.id)


@pytest.mark.asyncio
async def test_media_handler_accepts_bus_calling_convention(
    db_session: AsyncSession,
) -> None:
    # The bus calls ``handler(data)``. Under the old ``(self, db, data)``
    # signature this passed the dict as ``db`` and raised TypeError for
    # the missing ``data``. A payload without ``clinic_id`` returns early
    # before touching a session, so this isolates the signature fix.
    module = MediaModule()
    await module._on_patient_archived({"patient_id": str(uuid4())})
