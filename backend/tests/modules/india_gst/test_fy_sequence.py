"""FY-scoped GST document number allocation.

GST Rule 46(b): the serial must be consecutive and unique within the
financial year (April–March). Billing's sequential_number resets on the
calendar year, which is exactly why the module keeps its own counter —
these tests pin the two behaviours that reuse of billing's number broke:
no reset at January 1st, and a fresh series every April 1st.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.models import Clinic
from app.modules.india_gst.service import allocate_fy_document_number


async def test_serial_continues_across_calendar_year_boundary(
    db_session: AsyncSession, india_gst_clinic: Clinic
):
    dec = await allocate_fy_document_number(
        db_session, india_gst_clinic.id, "GST", date(2026, 12, 31)
    )
    jan = await allocate_fy_document_number(
        db_session, india_gst_clinic.id, "GST", date(2027, 1, 15)
    )
    assert dec == "GST/FY26-27/0001"
    # Same FY → the serial keeps counting; with billing's calendar-year
    # sequence this came back as .../0001 again (a duplicate).
    assert jan == "GST/FY26-27/0002"


async def test_serial_restarts_each_april(db_session: AsyncSession, india_gst_clinic: Clinic):
    march = await allocate_fy_document_number(
        db_session, india_gst_clinic.id, "GST", date(2027, 3, 31)
    )
    april = await allocate_fy_document_number(
        db_session, india_gst_clinic.id, "GST", date(2027, 4, 1)
    )
    assert march == "GST/FY26-27/0001"
    assert april == "GST/FY27-28/0001"


async def test_prefixes_count_independently(db_session: AsyncSession, india_gst_clinic: Clinic):
    when = date(2026, 8, 21)
    inv = await allocate_fy_document_number(db_session, india_gst_clinic.id, "GST", when)
    cn = await allocate_fy_document_number(db_session, india_gst_clinic.id, "CN", when)
    assert inv == "GST/FY26-27/0001"
    assert cn == "CN/FY26-27/0001"
