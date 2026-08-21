"""medical_reference: tenant isolation on get/get_interaction/
get_contraindication.

These three backed every write endpoint in the module (update/deactivate
for allergies, medications, surgeries, diseases, interactions, and
contraindications) with no clinic_id filter -- confirmed against current
code, not just the #157 review text. Any clinic could rename or
deactivate another clinic's reference data by guessing/enumerating an id.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.models import Clinic
from app.modules.medical_reference.models import (
    ReferenceAllergy,
    ReferenceDisease,
    ReferenceMedication,
)
from app.modules.medical_reference.service import MedicalReferenceService


@pytest.mark.asyncio
async def test_search_create_happy_path(db_session: AsyncSession, test_clinic: Clinic):
    allergy = await MedicalReferenceService.create(
        db_session, ReferenceAllergy, test_clinic.id, {"name": "Penicillin"}
    )
    await db_session.commit()

    rows = await MedicalReferenceService.search(
        db_session, ReferenceAllergy, test_clinic.id, None, active_only=True, limit=10
    )
    assert len(rows) == 1
    assert rows[0].id == allergy.id


@pytest.mark.asyncio
async def test_get_is_clinic_scoped_across_all_reference_types(
    db_session: AsyncSession, test_clinic: Clinic
):
    other_clinic = Clinic(
        id=uuid4(), name="Other Clinic", tax_id="B55555555", address={}, settings={}
    )
    db_session.add(other_clinic)
    await db_session.commit()

    for model, data in [
        (ReferenceAllergy, {"name": "Latex"}),
        (ReferenceMedication, {"name": "Amoxicillin"}),
        (ReferenceDisease, {"name": "Diabetes"}),
    ]:
        row = await MedicalReferenceService.create(db_session, model, other_clinic.id, data)
        await db_session.commit()

        # test_clinic must not be able to load another clinic's reference
        # row, even with a valid id -- this is what every write endpoint
        # (update/deactivate) depends on to stay clinic-scoped.
        result = await MedicalReferenceService.get(db_session, model, test_clinic.id, row.id)
        assert result is None, f"{model.__name__} leaked across clinics"

        # other_clinic can still load its own row.
        result = await MedicalReferenceService.get(db_session, model, other_clinic.id, row.id)
        assert result is not None


@pytest.mark.asyncio
async def test_get_interaction_and_contraindication_are_clinic_scoped(
    db_session: AsyncSession, test_clinic: Clinic
):
    other_clinic = Clinic(
        id=uuid4(), name="Other Clinic 2", tax_id="B44444444", address={}, settings={}
    )
    db_session.add(other_clinic)
    await db_session.commit()

    med_a = await MedicalReferenceService.create(
        db_session, ReferenceMedication, other_clinic.id, {"name": "Warfarin"}
    )
    med_b = await MedicalReferenceService.create(
        db_session, ReferenceMedication, other_clinic.id, {"name": "Aspirin"}
    )
    disease = await MedicalReferenceService.create(
        db_session, ReferenceDisease, other_clinic.id, {"name": "Hypertension"}
    )
    await db_session.commit()

    interaction = await MedicalReferenceService.create_interaction(
        db_session,
        other_clinic.id,
        {"medication_a_id": med_a.id, "medication_b_id": med_b.id, "risk_note": "Bleeding risk"},
    )
    contraindication = await MedicalReferenceService.create_contraindication(
        db_session,
        other_clinic.id,
        {"disease_id": disease.id, "medication_id": med_a.id, "risk_note": "Avoid"},
    )
    await db_session.commit()

    assert (
        await MedicalReferenceService.get_interaction(db_session, test_clinic.id, interaction.id)
        is None
    )
    assert (
        await MedicalReferenceService.get_interaction(db_session, other_clinic.id, interaction.id)
        is not None
    )

    assert (
        await MedicalReferenceService.get_contraindication(
            db_session, test_clinic.id, contraindication.id
        )
        is None
    )
    assert (
        await MedicalReferenceService.get_contraindication(
            db_session, other_clinic.id, contraindication.id
        )
        is not None
    )
