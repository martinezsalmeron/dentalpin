"""End-to-end dry-run of the catalog mapper against a synthetic but
realistic Gesdén ``Tratamientos`` export.

No DPMF file is required: we feed the mapper the raw row shape that
``dental-bridge/src/dental_bridge/adapters/gesden/extractors/treatment_catalog_items.py``
yields, then assert each row ends up in the right destination — either
linked to a seeded DentalPin catalog item, created with the inferred
category, or routed to ``migrado_gesden`` only when that is the
clinically-correct outcome.

The fixture is the closest thing we have to "a real Gesdén catalog" —
30 rows covering every IdTipoODG bucket plus the abbreviation
flavours the matcher needs to survive.
"""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from sqlalchemy import select

from app.core.auth.models import Clinic, User
from app.modules.catalog.models import (
    TreatmentCatalogItem,
    TreatmentCategory,
)
from app.modules.catalog.seed import seed_catalog
from app.modules.migration_import.mappers.base import MapperContext, MappingResolver
from app.modules.migration_import.mappers.catalog import CatalogItemMapper
from app.modules.migration_import.models import ImportJob

# ---------------------------------------------------------------------------
# Synthetic Gesdén catalog — each row mirrors the schema dental-bridge
# emits: ``(payload, raw)`` where ``raw`` carries the SQL column names
# verbatim (Codigo, DescripMed, DescripAgd, IdTipoODG, …).
# ---------------------------------------------------------------------------
GESDEN_ROWS: list[dict] = [
    # ── Restauradora: obturaciones (debe enlazar a REST-COMP / REST-AMAL) ──
    {
        "codigo": "0001",
        "agd": "OBTUR. COMP.",
        "med": "Obturación composite",
        "tipo_odg": 22,
        "expect": "link",
        "expect_code": "REST-COMP",
    },
    {
        "codigo": "0002",
        "agd": "OBT. AMALG.",
        "med": "Obturación amalgama",
        "tipo_odg": 22,
        "expect": "link",
        "expect_code": "REST-AMAL",
    },
    {
        "codigo": "0003",
        "agd": "OBT TEMP",
        "med": "Obturación temporal",
        "tipo_odg": 22,
        "expect": "link",
        "expect_code": "REST-TEMP",
    },
    # ── Coronas (alias MC, ZIRC) ──
    {
        "codigo": "0010",
        "agd": "CORONA MC",
        "med": "Corona metal-cerámica",
        "tipo_odg": 26,
        "expect": "link",
        "expect_code": "REST-CROWN-MC",
    },
    {
        "codigo": "0011",
        "agd": "CORONA ZIRC",
        "med": "Corona zirconio",
        "tipo_odg": 26,
        "expect": "link",
        "expect_code": "REST-CROWN-ZIR",
    },
    {
        "codigo": "0012",
        "agd": "CORONA PROV",
        "med": "Corona provisional",
        "tipo_odg": 26,
        "expect": "link",
        "expect_code": "REST-CROWN-PROV",
    },
    # ── Puentes (multi-tooth) ──
    {
        "codigo": "0020",
        "agd": "PUENTE MC",
        "med": "Puente metal-cerámica",
        "tipo_odg": 27,
        "expect": "link",
        "expect_code": "REST-BRIDGE-MC",
    },
    # ── Carillas ──
    {
        "codigo": "0030",
        "agd": "CARILLA PORC",
        "med": "Carilla porcelana",
        "tipo_odg": 33,
        "expect": "link",
        "expect_code": "REST-VEN-PORC",
    },
    # ── Endodoncia (alias UNI, BI, MOLAR) ──
    {
        "codigo": "0040",
        "agd": "ENDO UNI",
        "med": "Endodoncia unirradicular",
        "tipo_odg": 21,
        "expect": "link",
        "expect_code": "ENDO-UNI",
    },
    {
        "codigo": "0041",
        "agd": "ENDO BI",
        "med": "Endodoncia birradicular",
        "tipo_odg": 21,
        "expect": "link",
        "expect_code": "ENDO-BI",
    },
    {
        "codigo": "0042",
        "agd": "ENDO MOLAR",
        "med": "Endodoncia molar",
        "tipo_odg": 21,
        "expect": "link",
        "expect_code": "ENDO-MULTI",
    },
    # ── Pernos ──
    {
        "codigo": "0050",
        "agd": "PERNO FIBRA",
        "med": "Perno de fibra",
        "tipo_odg": 25,
        "expect": "link",
        "expect_code": "ENDO-POST-FIBER",
    },
    # ── Cirugía: extracciones ──
    {
        "codigo": "0060",
        "agd": "EXT SIMPLE",
        "med": "Extracción simple",
        "tipo_odg": 37,
        "expect": "link",
        "expect_code": "SURG-EXT-SIMPLE",
    },
    {
        "codigo": "0061",
        "agd": "EXT 3 MOLAR",
        "med": "Extracción tercer molar",
        "tipo_odg": 37,
        "expect": "link",
        "expect_code": "SURG-EXT-3MOLAR",
    },
    {
        "codigo": "0062",
        "agd": "EXTRACCION PIEZA INCLUIDA",
        "med": "Extracción de pieza incluida",
        "tipo_odg": 37,
        "expect": "link",
        "expect_code": "SURG-EXT-INCLUIDO",
    },
    # ── Implantes ──
    {
        "codigo": "0070",
        "agd": "IMPL TI",
        "med": "Implante de titanio",
        "tipo_odg": 24,
        "expect": "link",
        "expect_code": "SURG-IMP-TI",
    },
    {
        "codigo": "0071",
        "agd": "IMPL ZIRC",
        "med": "Implante de zirconio",
        "tipo_odg": 24,
        "expect": "link",
        "expect_code": "SURG-IMP-ZIR",
    },
    {
        "codigo": "0072",
        "agd": "APICEC.",
        "med": "Apicectomía",
        "tipo_odg": 23,
        "expect": "link",
        "expect_code": "SURG-APEC",
    },
    # ── Preventivo / higiene ──
    {
        "codigo": "0080",
        "agd": "LIMPIEZA DENTAL",
        "med": "Limpieza dental",
        "tipo_odg": 38,
        "expect": "link",
        "expect_code": "PREV-CLEAN",
    },
    {
        "codigo": "0081",
        "agd": "FLUOR",
        "med": "Fluorización",
        "tipo_odg": 41,
        "expect": "link",
        "expect_code": "PREV-FLUOR",
    },
    {
        "codigo": "0082",
        "agd": "SELLADOR FOSAS",
        "med": "Sellador de fosas y fisuras",
        "tipo_odg": 32,
        "expect": "link",
        "expect_code": "PREV-SEAL",
    },
    # ── Ortodoncia ──
    {
        "codigo": "0090",
        "agd": "BRACKET INDIVIDUAL",
        "med": "Bracket individual",
        "tipo_odg": 8,
        "expect": "link",
        "expect_code": "ORTO-BRACK",
    },
    {
        "codigo": "0091",
        "agd": "ORTO METAL",
        "med": "Ortodoncia brackets metálicos",
        "tipo_odg": 8,
        "expect": "link",
        "expect_code": "ORTO-METAL",
    },
    {
        "codigo": "0092",
        "agd": "RETENEDOR FIJO",
        "med": "Retenedor fijo",
        "tipo_odg": 8,
        "expect": "link",
        "expect_code": "ORTO-RET-FIX",
    },
    # ── Diagnóstico ──
    {
        "codigo": "0100",
        "agd": "PRIMERA VISITA",
        "med": "Primera visita",
        "tipo_odg": 13,
        "expect": "link",
        "expect_code": "DX-VISIT",
    },
    {
        "codigo": "0101",
        "agd": "RX PAN",
        "med": "Radiografía panorámica",
        "tipo_odg": 39,
        "expect": "link",
        "expect_code": "DX-RXPAN",
    },
    {
        "codigo": "0102",
        "agd": "RX PERIAPICAL",
        "med": "Radiografía periapical",
        "tipo_odg": 39,
        "expect": "link",
        "expect_code": "DX-RXPA",
    },
    # ── Gesdén-only que NO existe en seed: debe crear en su categoría ──
    {
        "codigo": "0200",
        "agd": "TTO ESPECIAL DR X",
        "med": "Tratamiento especial Dr X (composite avanzado)",
        "tipo_odg": 22,
        "expect": "create",
        "expect_category": "restauradora",
    },
    {
        "codigo": "0201",
        "agd": "ANOTACION COL",
        "med": "Anotación colaborador",
        "tipo_odg": 11,
        "expect": "create",
        "expect_category": "migrado_gesden",
    },
    {
        "codigo": "0202",
        "agd": "BONO JUNIO",
        "med": "Bono de junio",
        "tipo_odg": 14,
        "expect": "create",
        "expect_category": "migrado_gesden",
    },
]


@pytest.mark.asyncio
async def test_catalog_dryrun_against_synthetic_gesden_export(db_session) -> None:
    """End-to-end dry-run. Every Gesdén row lands where we expect.

    Reports a summary table at the end so the operator running this
    test can eyeball the link / create distribution against a real
    clinic export.
    """
    clinic, admin = await _bootstrap(db_session)
    ctx = await _ctx(db_session, clinic.id, admin.id)
    mapper = CatalogItemMapper()

    # Pre-resolve seed item ids per internal_code for the assertions.
    seed_index: dict[str, UUID] = {}
    for item in (
        await db_session.execute(
            select(TreatmentCatalogItem).where(
                TreatmentCatalogItem.clinic_id == clinic.id,
                TreatmentCatalogItem.is_system.is_(True),
            )
        )
    ).scalars():
        seed_index[item.internal_code] = item.id

    report: list[tuple[str, str, str, str]] = []
    failures: list[str] = []

    for row in GESDEN_ROWS:
        canonical = str(uuid4())
        result_id = await mapper.apply(
            ctx,
            entity_type="treatment_catalog_item",
            payload={
                "short_name": row["agd"],
                "description": row["med"],
                "code": row["codigo"],
                "reference_price": "100.00",
            },
            raw={
                "Codigo": row["codigo"],
                "DescripMed": row["med"],
                "DescripAgd": row["agd"],
                "IdTipoODG": row["tipo_odg"],
            },
            canonical_uuid=canonical,
            source_id=row["codigo"],
            source_system="gesden",
        )
        await db_session.flush()

        # Inspect the destination
        item = (
            await db_session.execute(
                select(TreatmentCatalogItem).where(TreatmentCatalogItem.id == result_id)
            )
        ).scalar_one()
        category = (
            await db_session.execute(
                select(TreatmentCategory).where(TreatmentCategory.id == item.category_id)
            )
        ).scalar_one()
        outcome = "link" if item.is_system else "create"

        # Per-row assertions
        if row["expect"] == "link":
            expected_id = seed_index[row["expect_code"]]
            if result_id != expected_id:
                failures.append(
                    f"{row['agd']!r}: expected link to {row['expect_code']}, "
                    f"got {item.internal_code} ({category.key})"
                )
        else:  # create
            if outcome != "create":
                failures.append(
                    f"{row['agd']!r}: expected create, got link to {item.internal_code}"
                )
            elif category.key != row["expect_category"]:
                failures.append(
                    f"{row['agd']!r}: created in {category.key}, expected {row['expect_category']}"
                )

        report.append((row["agd"], outcome, item.internal_code, category.key))

    # Pretty-print the summary so the operator can read the result
    # without parsing assertion output.
    print()
    print(f"{'Gesdén label':<30} {'outcome':<8} {'DentalPin code':<24} {'category':<20}")
    print("-" * 88)
    for label, outcome, code, cat in report:
        print(f"{label[:30]:<30} {outcome:<8} {code[:24]:<24} {cat:<20}")
    link_count = sum(1 for r in report if r[1] == "link")
    create_count = sum(1 for r in report if r[1] == "create")
    print("-" * 88)
    print(f"link: {link_count}   create: {create_count}   total: {len(report)}")

    assert not failures, "\n".join(failures)


async def _bootstrap(db_session):
    clinic = Clinic(id=uuid4(), name="C", tax_id=f"B{uuid4().hex[:8]}")
    admin = User(
        id=uuid4(),
        email=f"admin-{uuid4().hex[:8]}@test.local",
        password_hash="x",
        first_name="A",
        last_name="A",
    )
    db_session.add_all([clinic, admin])
    await db_session.flush()
    await seed_catalog(db_session, clinic.id)
    await db_session.flush()
    return clinic, admin


async def _ctx(db_session, clinic_id, admin_id):
    job = ImportJob(
        clinic_id=clinic_id,
        created_by=admin_id,
        status="executing",
        original_filename="t.dpm",
        file_path="/tmp/t.dpm",
        file_size=0,
    )
    db_session.add(job)
    await db_session.flush()
    return MapperContext(
        db=db_session,
        clinic_id=clinic_id,
        job_id=job.id,
        resolver=MappingResolver(db=db_session, clinic_id=clinic_id, job_id=job.id),
        import_fiscal_compliance=False,
        created_by=admin_id,
    )
