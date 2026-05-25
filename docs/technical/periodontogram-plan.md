# Plan Técnico — Módulo `periodontogram`

> **Status:** plan técnico aprobado para implementación. Acompaña al plan de diseño previo.
> **Issue tracker:** (pendiente abrir issue principal).
> **Fecha:** 2026-05-25.
> **Autor:** Ramon Martinez + Claude.
> **Phase B precondición:** ninguna — `periodontogram` puede arrancar en paralelo a otros módulos abiertos.

---

## 1. Resumen ejecutivo

Nuevo módulo **opcional, removable** que añade diagnóstico y seguimiento periodontal SEPA dentro de la ficha del paciente. Vive como sub-tab dentro del modo *Diagnóstico* del `ClinicalTab`. Reutiliza SVG de dientes y `TimelineSlider` del odontograma. Persiste snapshots inmutables fechados con un solo `draft` activo por paciente.

| Aspecto | Decisión |
|---------|----------|
| Nombre módulo | `periodontogram` |
| Backend path | `backend/app/modules/periodontogram/` |
| Frontend layer | `backend/app/modules/periodontogram/frontend/` |
| API prefix | `/api/v1/periodontogram/` |
| Permisos namespaced | `periodontogram.read`, `periodontogram.write` |
| Rama Alembic | `branch_labels=("periodontogram",)`, anchor `down_revision="0001"` |
| `installable / auto_install / removable` | `True / False / True` |
| `depends` | `["patients", "odontogram"]` |
| Tablas creadas | `periodontogram_snapshots`, `periodontogram_teeth`, `periodontogram_sites` |
| Slot consumido | `patient.diagnosis.subtabs` (nuevo, expuesto por `patients`) |
| Slot interno | reúsa `useModuleSlots` existente |
| Eventos consumidos | `odontogram.treatment.performed`, `patient.archived` |
| Eventos publicados | `periodontogram.snapshot.closed` |
| Notas | Campo `notes` en snapshot (NO polimórficas — ver §13) |

---

## 2. Auditoría arquitectónica previa

Verificado contra el código actual:

| Componente | Archivo | Hallazgo |
|------------|---------|----------|
| `BaseModule` contrato | `backend/app/core/plugins/base.py` | Métodos abstractos `get_models`, `get_router`; opcionales `get_event_handlers`, `get_permissions`, `get_tools`, `get_agents`, lifecycle hooks `install`/`uninstall`/`post_upgrade`. |
| Manifest fields | `backend/app/core/plugins/manifest.py` + ejemplos schedules/odontogram | `name, version, summary, author, license, category, depends, installable, auto_install, removable, role_permissions, frontend{layer_path, navigation}`. |
| Patrón removable | `backend/app/modules/schedules/__init__.py` | `installable=True, auto_install=True, removable=True`. Nuestro caso: `auto_install=False`. |
| Migración inicial removable | `backend/app/modules/schedules/migrations/versions/sch_0001_initial.py` | `revision="sch_0001"`, `down_revision="0001"`, `branch_labels=("schedules",)`. |
| Lifecycle hooks | `backend/app/modules/schedules/lifecycle.py` | Funciones módulo-level con logging. BaseModule también acepta métodos en la subclase. |
| Slot registry | `frontend/app/composables/useModuleSlots.ts` | `registerSlot(name, entry)`, `useModuleSlots().resolve(name, ctx)`. Permission gating built-in. |
| ClinicalTab modos | `backend/app/modules/patients/frontend/components/patient/ClinicalTab.vue:115` | Modos hard-coded en `v-if`. Diagnosis renderiza `<DiagnosisMode>` (componente de odontogram). |
| `DiagnosisMode` | `backend/app/modules/odontogram/frontend/components/clinical/DiagnosisMode.vue` | Vive en odontogram. Patients NO depende de odontogram (importación cruzada vía slots/layer). |
| TimelineSlider | `backend/app/modules/odontogram/frontend/components/odontogram/TimelineSlider.vue` | Props: `dates`, `currentDate`. Reusable sin tocar. Auto-import vía Nuxt layer. |
| ToothSVGPaths | `backend/app/modules/odontogram/frontend/components/odontogram/ToothSVGPaths.ts` | Vista lateral con 8 posiciones + quadrant transforms (`getToothTransform`). Reusable sin tocar. |
| clinical_notes matrix | `backend/app/modules/clinical_notes/models.py` | `removable=False`. Añadir `periodontogram_snapshot` a su CHECK constraint requeriría cambio en un módulo core desde uno removable → **rechazado**. Usamos `notes` Text en snapshot. |
| Cross-module FK | `manifest.depends` enforcement vía `manifest_validator` | FK solo a `patients`/`odontogram`/`clinics`/`users` (todos en deps o core). |

---

## 3. Estructura de archivos a crear

```
backend/app/modules/periodontogram/
├── __init__.py                     # PeriodontogramModule(BaseModule)
├── CLAUDE.md                       # Doc agente
├── CHANGELOG.md
├── constants.py                    # SITE_CODES, FDI_PERMANENT, scales
├── models.py                       # PeriodontogramSnapshot, …Tooth, …Site
├── schemas.py                      # Pydantic in/out
├── service.py                      # PeriodontogramService
├── router.py                       # Endpoints REST
├── events.py                       # Handlers de eventos externos
├── indices.py                      # Cálculo BoP, PI, CAL, bolsas≥5mm
├── lifecycle.py                    # install/uninstall hooks (logging)
├── migrations/
│   └── versions/
│       └── perio_0001_initial.py   # branch_labels=("periodontogram",)
└── frontend/
    ├── nuxt.config.ts              # capa Nuxt
    ├── i18n/
    │   └── locales/
    │       ├── en.json
    │       └── es.json
    ├── composables/
    │   ├── usePeriodontogram.ts    # estado + API
    │   ├── usePeriodontogramSession.ts  # draft management + autosave
    │   └── usePerioHeatmap.ts      # color tokens según sondaje
    ├── plugins/
    │   └── slots.client.ts         # registra patient.diagnosis.subtabs entry
    ├── components/
    │   ├── PeriodontogramView.vue          # entry-point del slot
    │   ├── PeriodontogramChart.vue         # orquestador 4 filas + tablas
    │   ├── PerioArchBlock.vue              # bloque superior o inferior (tabla + 2 filas dientes)
    │   ├── PerioMetricsTable.vue           # 9 filas SEPA
    │   ├── PerioToothRow.vue               # 1 fila de dientes (vestibular o palatino)
    │   ├── PerioToothLateral.vue           # 1 diente lateral (SVG flippable)
    │   ├── PerioSiteMarker.vue             # marcador 1 sitio con color heatmap
    │   ├── PerioSiteInputPopover.vue       # popover de edición por sitio
    │   ├── PerioIndicesBanner.vue          # BoP/PI/CAL banner
    │   ├── PerioSessionActions.vue         # botonera draft/close
    │   ├── PerioHistoryBanner.vue          # banner "viendo histórico"
    │   └── PerioEmptyState.vue             # CTA crear primera sesión
    └── types.ts                            # tipos compartidos

backend/tests/modules/periodontogram/
├── conftest.py
├── test_uninstall_roundtrip.py     # round-trip Alembic
├── test_snapshot_lifecycle.py      # draft → closed
├── test_indices_calc.py            # BoP/PI/CAL/bolsas
├── test_acoplamiento_odontogram.py # pre-relleno desde tooth_records
├── test_permissions.py             # RBAC por rol
└── test_api_validation.py          # rangos sondaje, FDI, etc.

docs/
├── adr/
│   └── 0014-periodontogram-snapshot-model.md   # inmutable vs event-sourcing
├── modules/
│   └── periodontogram.md
├── technical/
│   ├── periodontogram-plan.md      # este archivo
│   └── periodontogram/
│       ├── overview.md
│       ├── events.md
│       └── permissions.md
├── user-manual/
│   ├── es/periodontogram/
│   │   ├── index.md
│   │   └── screens/
│   │       └── periodontograma-view.md
│   └── en/periodontogram/
│       ├── index.md
│       └── screens/
│           └── periodontogram-view.md
└── screenshots/periodontogram/

# Archivos a tocar en módulos existentes:
backend/app/modules/patients/frontend/components/patient/ClinicalTab.vue   # expone slot
backend/app/modules/patients/CLAUDE.md                                       # documenta nuevo slot
frontend/app/config/permissions.ts                                           # añade periodontogram.*
```

---

## 4. Modelo de datos — schema SQL exacto

### 4.1 `periodontogram_snapshots`

Una fila por sesión de exploración (draft o cerrada).

```sql
CREATE TABLE periodontogram_snapshots (
    id              UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    clinic_id       UUID            NOT NULL REFERENCES clinics(id),
    patient_id      UUID            NOT NULL REFERENCES patients(id),
    status          VARCHAR(10)     NOT NULL,                  -- 'draft' | 'closed'
    recorded_at     TIMESTAMPTZ     NOT NULL DEFAULT now(),    -- fecha clínica de la sesión
    recorded_by     UUID            NOT NULL REFERENCES users(id),
    closed_at       TIMESTAMPTZ,                               -- NULL mientras draft
    closed_by       UUID            REFERENCES users(id),
    notes           TEXT,                                      -- nota libre de la sesión (MVP, NO polimórfica)
    -- snapshot de índices computados al cerrar (frozen para queries rápidas)
    indices         JSONB,                                     -- { bop_pct, pi_pct, cal_mean_mm, deep_pockets_count }
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT now(),

    CONSTRAINT ck_perio_snap_status      CHECK (status IN ('draft', 'closed')),
    CONSTRAINT ck_perio_snap_closed_pair CHECK (
        (status = 'draft'  AND closed_at IS NULL AND closed_by IS NULL) OR
        (status = 'closed' AND closed_at IS NOT NULL AND closed_by IS NOT NULL)
    )
);

CREATE INDEX ix_perio_snap_clinic         ON periodontogram_snapshots (clinic_id);
CREATE INDEX ix_perio_snap_patient        ON periodontogram_snapshots (patient_id);
CREATE INDEX ix_perio_snap_patient_status ON periodontogram_snapshots (patient_id, status);
CREATE INDEX ix_perio_snap_patient_closed_at
       ON periodontogram_snapshots (patient_id, closed_at DESC)
       WHERE status = 'closed';

-- Unicidad blanda: máximo un draft por paciente.
CREATE UNIQUE INDEX uq_perio_snap_one_draft_per_patient
       ON periodontogram_snapshots (patient_id)
       WHERE status = 'draft';
```

### 4.2 `periodontogram_teeth`

Una fila por diente presente en el snapshot. Si la columna `is_present=false`, las filas hijas de sitios no aplican (se omite su escritura).

```sql
CREATE TABLE periodontogram_teeth (
    id                      UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    snapshot_id             UUID        NOT NULL REFERENCES periodontogram_snapshots(id) ON DELETE CASCADE,
    tooth_number            INTEGER     NOT NULL,            -- FDI permanente 11..48
    is_present              BOOLEAN     NOT NULL DEFAULT true,
    is_implant              BOOLEAN     NOT NULL DEFAULT false,
    mobility                INTEGER,                          -- 0..3 (Miller)
    prognosis               VARCHAR(10),                      -- 'good' | 'fair' | 'poor' | 'hopeless'
    furcation_buccal        VARCHAR(4),                       -- '0' | 'I' | 'II' | 'III'
    furcation_lingual       VARCHAR(4),
    keratinized_gingiva_mm  INTEGER,                          -- anchura encía queratinizada
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT ck_perio_tooth_fdi
        CHECK (tooth_number BETWEEN 11 AND 48
               AND (tooth_number % 10) BETWEEN 1 AND 8
               AND (tooth_number / 10) BETWEEN 1 AND 4),
    CONSTRAINT ck_perio_tooth_mobility    CHECK (mobility IS NULL OR mobility BETWEEN 0 AND 3),
    CONSTRAINT ck_perio_tooth_prognosis   CHECK (prognosis IS NULL OR prognosis IN ('good','fair','poor','hopeless')),
    CONSTRAINT ck_perio_tooth_furcation_b CHECK (furcation_buccal  IS NULL OR furcation_buccal  IN ('0','I','II','III')),
    CONSTRAINT ck_perio_tooth_furcation_l CHECK (furcation_lingual IS NULL OR furcation_lingual IN ('0','I','II','III')),
    CONSTRAINT ck_perio_tooth_kg_range    CHECK (keratinized_gingiva_mm IS NULL OR keratinized_gingiva_mm BETWEEN 0 AND 20),

    UNIQUE (snapshot_id, tooth_number)
);

CREATE INDEX ix_perio_teeth_snapshot ON periodontogram_teeth (snapshot_id);
```

### 4.3 `periodontogram_sites`

Una fila por sitio (6 por diente). Se crea lazy: solo cuando el clínico introduce el primer valor en ese sitio.

```sql
CREATE TABLE periodontogram_sites (
    id                    UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    snapshot_id           UUID        NOT NULL REFERENCES periodontogram_snapshots(id) ON DELETE CASCADE,
    tooth_id              UUID        NOT NULL REFERENCES periodontogram_teeth(id) ON DELETE CASCADE,
    tooth_number          INTEGER     NOT NULL,                -- denormalizado para queries directas
    site_code             VARCHAR(2)  NOT NULL,                -- 'MV'|'V'|'DV'|'ML'|'L'|'DL'
    probing_depth_mm      INTEGER,                             -- 0..15
    gingival_margin_mm    INTEGER,                             -- -5..10 (negativo = hiperplasia)
    bleeding_on_probing   BOOLEAN     NOT NULL DEFAULT false,
    plaque                BOOLEAN     NOT NULL DEFAULT false,
    suppuration           BOOLEAN     NOT NULL DEFAULT false,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT ck_perio_site_code     CHECK (site_code IN ('MV','V','DV','ML','L','DL')),
    CONSTRAINT ck_perio_site_pd_range CHECK (probing_depth_mm   IS NULL OR probing_depth_mm   BETWEEN 0 AND 15),
    CONSTRAINT ck_perio_site_gm_range CHECK (gingival_margin_mm IS NULL OR gingival_margin_mm BETWEEN -5 AND 10),

    UNIQUE (snapshot_id, tooth_number, site_code)
);

CREATE INDEX ix_perio_sites_snapshot ON periodontogram_sites (snapshot_id);
CREATE INDEX ix_perio_sites_tooth    ON periodontogram_sites (tooth_id);
-- Index para agregados rápidos (BoP %, bolsas ≥5mm).
CREATE INDEX ix_perio_sites_pd_bop   ON periodontogram_sites (snapshot_id, probing_depth_mm, bleeding_on_probing);
```

### 4.4 Sin FK a `odontogram.tooth_records`

Aunque `periodontogram` declare `depends=["patients","odontogram"]`, **no creamos FK** a tablas del odontograma. Solo guardamos `tooth_number` (entero FDI). Razones:

- El acoplamiento odontograma→periodontograma es por *lectura*, no integridad referencial.
- Permite que el odontograma cambie su modelo interno sin migración del periodontograma.
- Aunque odontograma hoy es `removable=False`, no asumimos integridad estructural.

---

## 5. Migración Alembic — esqueleto

```python
# backend/app/modules/periodontogram/migrations/versions/perio_0001_initial.py

"""periodontogram module — initial schema.

Revision ID: perio_0001
Revises: 0001
Create Date: 2026-05-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "perio_0001"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = ("periodontogram",)
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "periodontogram_snapshots",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("patient_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.String(length=10), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("recorded_by", sa.UUID(), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_by", sa.UUID(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("indices", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("status IN ('draft','closed')", name="ck_perio_snap_status"),
        sa.CheckConstraint(
            "(status='draft' AND closed_at IS NULL AND closed_by IS NULL) "
            "OR (status='closed' AND closed_at IS NOT NULL AND closed_by IS NOT NULL)",
            name="ck_perio_snap_closed_pair",
        ),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"]),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"]),
        sa.ForeignKeyConstraint(["recorded_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["closed_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_perio_snap_clinic", "periodontogram_snapshots", ["clinic_id"])
    op.create_index("ix_perio_snap_patient", "periodontogram_snapshots", ["patient_id"])
    op.create_index(
        "ix_perio_snap_patient_status",
        "periodontogram_snapshots",
        ["patient_id", "status"],
    )
    op.create_index(
        "ix_perio_snap_patient_closed_at",
        "periodontogram_snapshots",
        ["patient_id", sa.text("closed_at DESC")],
        postgresql_where=sa.text("status = 'closed'"),
    )
    op.create_index(
        "uq_perio_snap_one_draft_per_patient",
        "periodontogram_snapshots",
        ["patient_id"],
        unique=True,
        postgresql_where=sa.text("status = 'draft'"),
    )

    op.create_table(
        "periodontogram_teeth",
        # ... ver §4.2 para detalle de columnas/constraints
    )
    op.create_table(
        "periodontogram_sites",
        # ... ver §4.3 para detalle de columnas/constraints
    )


def downgrade() -> None:
    op.drop_table("periodontogram_sites")
    op.drop_table("periodontogram_teeth")
    op.drop_table("periodontogram_snapshots")
```

---

## 6. Backend — módulo y servicio

### 6.1 `__init__.py`

```python
class PeriodontogramModule(BaseModule):
    manifest = {
        "name": "periodontogram",
        "version": "0.1.0",
        "summary": "Periodontogram SEPA — diagnóstico y seguimiento periodontal.",
        "author": "DentalPin Core Team",
        "license": "BSL-1.1",
        "category": "official",
        "depends": ["patients", "odontogram"],
        "installable": True,
        "auto_install": False,            # política módulos opcionales (memoria)
        "removable": True,
        "role_permissions": {
            "admin":     ["*"],
            "dentist":   ["*"],
            "hygienist": ["read", "write"],
            "assistant": ["read"],
            "receptionist": [],
        },
        "frontend": {"layer_path": "frontend"},
    }

    def get_models(self) -> list:
        return [PeriodontogramSnapshot, PeriodontogramTooth, PeriodontogramSite]

    def get_router(self) -> APIRouter:
        return router

    def get_permissions(self) -> list[str]:
        return ["read", "write"]

    def get_event_handlers(self) -> dict:
        return {
            "odontogram.treatment.performed": on_odontogram_treatment_performed,
            "patient.archived":               on_patient_archived,
        }
```

### 6.2 `service.py` — interfaz pública

```python
class PeriodontogramService:
    @staticmethod
    async def list_snapshots(db, clinic_id, patient_id) -> list[Snapshot]: ...

    @staticmethod
    async def get_snapshot(db, clinic_id, snapshot_id) -> Snapshot: ...

    @staticmethod
    async def get_or_create_draft(db, clinic_id, patient_id, user_id) -> Snapshot:
        """
        Idempotente. Si ya existe un draft para el paciente, lo devuelve.
        Si no, crea snapshot draft pre-rellenando is_present / is_implant
        leyendo odontogram.ToothRecord + Treatment (servicio público).
        """

    @staticmethod
    async def update_tooth(db, ctx, snapshot_id, tooth_number, payload) -> Tooth: ...

    @staticmethod
    async def update_site(db, ctx, snapshot_id, tooth_number, site_code, payload) -> Site: ...

    @staticmethod
    async def close_snapshot(db, ctx, snapshot_id) -> Snapshot:
        """
        Calcula índices, los persiste en snapshot.indices, marca status='closed',
        publica evento periodontogram.snapshot.closed.
        """

    @staticmethod
    async def discard_draft(db, ctx, snapshot_id) -> None: ...

    @staticmethod
    async def get_timeline(db, clinic_id, patient_id) -> list[TimelineEntry]:
        """Devuelve snapshots cerrados con fecha + change_count (= sitios poblados)."""

    @staticmethod
    async def compute_indices(db, snapshot_id) -> dict:
        """Re-calcula índices (uso interno + recomputar histórico si fuera necesario)."""
```

Multi-tenancy: TODOS los queries filtran por `clinic_id` (regla CLAUDE.md). El parámetro viene del `ClinicContext`.

### 6.3 `indices.py` — fórmulas

```python
def compute_bop_pct(sites: list[Site]) -> float:
    """% de sitios con sangrado. Solo sitios con probing_depth_mm NOT NULL cuentan."""
    measured = [s for s in sites if s.probing_depth_mm is not None]
    if not measured: return 0.0
    return 100.0 * sum(1 for s in measured if s.bleeding_on_probing) / len(measured)

def compute_pi_pct(sites: list[Site]) -> float:
    """% de sitios con placa. Mismo denominador que BoP."""
    measured = [s for s in sites if s.probing_depth_mm is not None]
    if not measured: return 0.0
    return 100.0 * sum(1 for s in measured if s.plaque) / len(measured)

def compute_cal_mean_mm(sites: list[Site]) -> float:
    """CAL medio. CAL = probing_depth + gingival_margin. Ignora sitios incompletos."""
    cals = [
        s.probing_depth_mm + s.gingival_margin_mm
        for s in sites
        if s.probing_depth_mm is not None and s.gingival_margin_mm is not None
    ]
    return sum(cals) / len(cals) if cals else 0.0

def count_deep_pockets(sites: list[Site], threshold: int = 5) -> int:
    """Número de DIENTES con al menos un sitio con probing_depth_mm ≥ threshold."""
    teeth_with_deep = {
        s.tooth_number for s in sites
        if s.probing_depth_mm is not None and s.probing_depth_mm >= threshold
    }
    return len(teeth_with_deep)
```

### 6.4 `events.py`

```python
async def on_odontogram_treatment_performed(data: dict) -> None:
    """
    Cuando se performa un tratamiento que cambia el estado físico del diente
    (implant, extraction, crown, bridge), si el paciente tiene un draft activo,
    invalidamos el caché frontend disparando un re-fetch. No mutamos el draft
    automáticamente — el clínico decide si refrescar los flags.
    """
    # MVP: solo logging. Caché front se invalida vía polling cada 30s.

async def on_patient_archived(data: dict) -> None:
    """Si se archiva un paciente con drafts, los descartamos automáticamente."""
```

---

## 7. API REST — endpoints

Base path: `/api/v1/periodontogram/`. Todos exigen `get_clinic_context` + permiso correspondiente. Todos devuelven `ApiResponse[T]` o `PaginatedApiResponse[T]` salvo `204`.

| Método | Path | Permiso | Body | Response | Status |
|--------|------|---------|------|----------|--------|
| `GET`  | `/patients/{patient_id}/snapshots` | `periodontogram.read` | — | `PaginatedApiResponse[SnapshotSummary]` | 200 |
| `GET`  | `/patients/{patient_id}/timeline` | `periodontogram.read` | — | `ApiResponse[TimelineResponse]` | 200 |
| `GET`  | `/patients/{patient_id}/draft` | `periodontogram.read` | — | `ApiResponse[SnapshotDetail \| null]` | 200 |
| `POST` | `/patients/{patient_id}/draft` | `periodontogram.write` | `{ recorded_at? }` | `ApiResponse[SnapshotDetail]` | 201 (or 200 si ya existía) |
| `GET`  | `/snapshots/{snapshot_id}` | `periodontogram.read` | — | `ApiResponse[SnapshotDetail]` | 200 |
| `PATCH` | `/snapshots/{snapshot_id}/teeth/{tooth_number}` | `periodontogram.write` | `ToothPatch` | `ApiResponse[Tooth]` | 200 |
| `PATCH` | `/snapshots/{snapshot_id}/teeth/{tooth_number}/sites/{site_code}` | `periodontogram.write` | `SitePatch` | `ApiResponse[Site]` | 200 |
| `POST` | `/snapshots/{snapshot_id}/close` | `periodontogram.write` | `{ notes? }` | `ApiResponse[SnapshotDetail]` | 200 |
| `DELETE` | `/snapshots/{snapshot_id}` | `periodontogram.write` | — | — | 204 (solo si `status=draft`) |
| `GET`  | `/snapshots/{snapshot_id}/indices` | `periodontogram.read` | — | `ApiResponse[IndicesResponse]` | 200 |

### 7.1 Shapes principales (Pydantic)

```python
class SiteValue(BaseModel):
    site_code: Literal["MV","V","DV","ML","L","DL"]
    probing_depth_mm: int | None = Field(None, ge=0, le=15)
    gingival_margin_mm: int | None = Field(None, ge=-5, le=10)
    bleeding_on_probing: bool = False
    plaque: bool = False
    suppuration: bool = False

class ToothValue(BaseModel):
    tooth_number: int = Field(..., ge=11, le=48)
    is_present: bool = True
    is_implant: bool = False
    mobility: int | None = Field(None, ge=0, le=3)
    prognosis: Literal["good","fair","poor","hopeless"] | None = None
    furcation_buccal:  Literal["0","I","II","III"] | None = None
    furcation_lingual: Literal["0","I","II","III"] | None = None
    keratinized_gingiva_mm: int | None = Field(None, ge=0, le=20)
    sites: list[SiteValue] = Field(default_factory=list)

class SnapshotDetail(BaseModel):
    id: UUID
    patient_id: UUID
    status: Literal["draft","closed"]
    recorded_at: datetime
    recorded_by: UUID
    closed_at: datetime | None
    closed_by: UUID | None
    notes: str | None
    indices: IndicesResponse | None
    teeth: list[ToothValue]

class IndicesResponse(BaseModel):
    bop_pct: float
    pi_pct: float
    cal_mean_mm: float
    deep_pockets_count: int     # nº de dientes con bolsas ≥5mm

class TimelineEntry(BaseModel):
    snapshot_id: UUID
    date: date                  # alineado con TimelineSlider (YYYY-MM-DD)
    change_count: int           # nº de sitios con datos (proxy de"actividad")

class TimelineResponse(BaseModel):
    dates: list[TimelineEntry]
    draft: SnapshotSummary | None    # draft activo si existe
```

### 7.2 Reglas de validación cruzada

- `PATCH /sites/...` falla con 409 si `snapshot.status='closed'`.
- `PATCH /teeth/...` falla con 409 si `snapshot.status='closed'`.
- `POST /draft` es idempotente: si hay draft activo, retorna el existente con `200`.
- `POST /close` falla con 422 si no hay ningún sitio con `probing_depth_mm` (avisa al cliente; el frontend valida soft antes).
- `DELETE /snapshots/{id}` solo permite borrar drafts.

---

## 8. Frontend — componentes Vue

### 8.1 Slot point nuevo en `patients`

Exponer en `ClinicalTab.vue` (módulo `patients`) un slot `patient.diagnosis.subtabs` con contrato:

```ts
type DiagnosisSubtabCtx = { patientId: string; readonly?: boolean }
```

Refactor mínimo en `ClinicalTab.vue:115-156`:

```vue
<DiagnosisModeContainer
  v-else-if="currentMode === 'diagnosis'"
  :patient-id="patientId"
  :readonly="readonly"
  @create-plan="handleCreatePlan"
  @continue-plan="handleContinuePlan"
/>
```

Nuevo componente `DiagnosisModeContainer.vue` en `patients/frontend/components/patient/`:

```vue
<script setup lang="ts">
const { resolve } = useModuleSlots()
const props = defineProps<{ patientId: string; readonly?: boolean }>()
const emit = defineEmits<{ ... }>()

const subtabs = computed(() =>
  resolve<DiagnosisSubtabCtx>('patient.diagnosis.subtabs', {
    patientId: props.patientId,
    readonly: props.readonly,
  })
)

const activeKey = ref<'odontogram' | string>('odontogram')

// Sync con URL ?diagnosisView=
const route = useRoute()
onMounted(() => {
  const v = route.query.diagnosisView as string
  if (v && (v === 'odontogram' || subtabs.value.some(s => s.id === v))) {
    activeKey.value = v
  }
})
watch(activeKey, (v) => {
  useRouter().replace({ query: { ...route.query, diagnosisView: v } })
})
</script>

<template>
  <!-- Sin sub-tabs si no hay módulos opcionales: render directo -->
  <DiagnosisMode
    v-if="subtabs.length === 0"
    :patient-id="patientId"
    :readonly="readonly"
    @create-plan="..."
    @continue-plan="..."
  />
  <!-- Con sub-tabs: bar + slot activo -->
  <div v-else class="space-y-3">
    <UTabs
      v-model="activeKey"
      :items="[{ slot: 'odontogram', label: t('clinical.diagnosis.odontogram') },
               ...subtabs.map(s => ({ slot: s.id, label: t(s.labelKey ?? s.id) }))]"
    >
      <template #odontogram>
        <DiagnosisMode
          :patient-id="patientId"
          :readonly="readonly"
          @create-plan="..."
          @continue-plan="..."
        />
      </template>
      <template
        v-for="entry in subtabs"
        :key="entry.id"
        #[entry.id]
      >
        <component
          :is="entry.component"
          :patient-id="patientId"
          :readonly="readonly"
        />
      </template>
    </UTabs>
  </div>
</template>
```

**Importante**: si el módulo `periodontogram` no está instalado, el slot está vacío y la UI **es exactamente la actual** — sin tab bar, sin churn visual. Esto preserva la promesa de uninstall limpio.

### 8.2 Registro del slot en `periodontogram`

```ts
// backend/app/modules/periodontogram/frontend/plugins/slots.client.ts
import { defineAsyncComponent } from 'vue'
import { registerSlot } from '~~/app/composables/useModuleSlots'

export default defineNuxtPlugin(() => {
  registerSlot('patient.diagnosis.subtabs', {
    id: 'periodontogram',
    component: defineAsyncComponent(
      () => import('../components/PeriodontogramView.vue')
    ),
    order: 20,
    permission: 'periodontogram.read',
    labelKey: 'periodontogram.tab.label',
  })
})
```

### 8.3 Componentes principales

| Componente | Responsabilidad | Props principales |
|------------|-----------------|-------------------|
| `PeriodontogramView.vue` | Entry-point del slot. Decide entre EmptyState / Chart. Carga timeline. | `patientId`, `readonly?` |
| `PeriodontogramChart.vue` | Orquestador. Render banner + slider + 2 arch blocks + acciones. | `patientId`, `snapshot` (current view), `isDraft`, `readonly?` |
| `PerioArchBlock.vue` | Bloque superior o inferior: tabla métricas + 2 filas de dientes. | `archSide: 'upper' \| 'lower'`, `teeth: ToothValue[]`, `sites: SiteValue[]`, `readonly` |
| `PerioMetricsTable.vue` | 9 filas SEPA. Cada celda input numérico inline o popover trigger. | `teeth`, `sites`, `archSide`, `readonly`, `@update` |
| `PerioToothRow.vue` | 1 fila de dientes con flip CSS según face. | `teeth`, `face: 'vestibular' \| 'palatal' \| 'lingual'`, `archSide` |
| `PerioToothLateral.vue` | 1 diente lateral SVG + 3 marcadores de sitio. | `tooth`, `sites: SiteValue[3]`, `face`, `quadrant` |
| `PerioSiteMarker.vue` | Círculo coloreado según heatmap. | `pd?`, `bop`, `plaque` |
| `PerioSiteInputPopover.vue` | Popover edición sitio: PD/GM/BoP/PI/Sup. | `tooth_number`, `site_code`, `current: SiteValue`, `@save` |
| `PerioIndicesBanner.vue` | Banner BoP/PI/CAL/bolsas. | `indices: IndicesResponse`, `meta: { date, by, status }` |
| `PerioSessionActions.vue` | Botonera sticky. Discard / Close. | `snapshot`, `@close`, `@discard` |
| `PerioHistoryBanner.vue` | Banner amarillo "Viendo histórico". | `date`, `@returnToCurrent` |
| `PerioEmptyState.vue` | CTA "Iniciar primera exploración". | `@start` |

### 8.4 Composables

```ts
// usePeriodontogram.ts
export function usePeriodontogram(patientId: Ref<string>) {
  const api = useApi()
  const timeline = ref<TimelineEntry[]>([])
  const draft    = ref<SnapshotSummary | null>(null)
  const current  = ref<SnapshotDetail | null>(null)
  const viewingDate = ref<string | null>(null)  // null = vivo (draft o último closed)

  async function fetchTimeline() { ... }
  async function fetchSnapshot(snapshotId: string) { ... }
  async function loadDraftOrLatest() { ... }
  function setViewingDate(date: string | null) { ... }

  return { timeline, draft, current, viewingDate, fetchTimeline, fetchSnapshot, loadDraftOrLatest, setViewingDate }
}

// usePeriodontogramSession.ts — gestión draft + autosave
export function usePeriodontogramSession(snapshotId: Ref<string | null>) {
  const api = useApi()
  const dirty = ref(false)
  const saving = ref(false)

  const enqueueToothPatch    = useDebounceFn(async (toothNumber: number, patch) => { ... }, 600)
  const enqueueSitePatch     = useDebounceFn(async (toothNumber: number, siteCode: string, patch) => { ... }, 600)
  async function closeSession(notes?: string) { ... }
  async function discardDraft() { ... }

  return { dirty, saving, enqueueToothPatch, enqueueSitePatch, closeSession, discardDraft }
}

// usePerioHeatmap.ts — mapping color
export function pdColor(pd: number | null | undefined): string {
  if (pd == null) return 'neutral-300'
  if (pd <= 3)  return 'success-500'
  if (pd === 4) return 'warning-400'
  if (pd <= 6)  return 'warning-600'
  return 'error-500'
}
```

### 8.5 Permisos en `frontend/app/config/permissions.ts`

Añadir:

```ts
export const PERMISSIONS = {
  // ... existentes
  periodontogram: {
    read:  'periodontogram.read',
    write: 'periodontogram.write',
  },
} as const
```

---

## 9. Acoplamiento con `odontogram` — sin FK

### 9.1 Pre-relleno al abrir draft

`PeriodontogramService.get_or_create_draft`:

```python
# 1) Lee odontogram tooth_records del paciente vía servicio público.
from app.modules.odontogram.service import OdontogramService

odo = await OdontogramService.get_patient_odontogram(db, clinic_id, patient_id)

# 2) Para cada diente FDI permanente (11..48):
for tooth_number in PERMANENT_TEETH_FDI:
    tooth_record = odo.teeth.get(tooth_number)
    is_present = not (tooth_record and tooth_record.general_condition == 'missing')
    is_implant = bool(tooth_record and any(
        t.clinical_type == 'implant' and t.status == 'performed'
        for t in tooth_record.treatments
    ))
    db.add(PeriodontogramTooth(
        snapshot_id=snapshot.id,
        tooth_number=tooth_number,
        is_present=is_present,
        is_implant=is_implant,
    ))
```

### 9.2 Import permitido por `depends`

`periodontogram.depends = ["patients","odontogram"]` autoriza el `from app.modules.odontogram.service import OdontogramService`. CI (`manifest_validator`) lo respeta.

### 9.3 Eventos

Suscripción a `odontogram.treatment.performed`: en MVP solo logging. El cliente refresca el draft cada vez que se monta (no pulling).

---

## 10. Tests

### 10.1 Round-trip uninstall (obligatorio)

`backend/tests/modules/periodontogram/test_uninstall_roundtrip.py` — copia del patrón en `test_uninstall_roundtrip.py` adaptando:

```python
PERIODONTOGRAM_TABLES = {
    "periodontogram_snapshots",
    "periodontogram_teeth",
    "periodontogram_sites",
}

def test_periodontogram_uninstall_roundtrip_is_branch_scoped() -> None:
    _alembic("upgrade", "heads")
    before = _list_tables()
    assert PERIODONTOGRAM_TABLES.issubset(before)
    baseline = before - PERIODONTOGRAM_TABLES

    _alembic("downgrade", "periodontogram@-1")
    after_down = _list_tables()
    assert PERIODONTOGRAM_TABLES.isdisjoint(after_down)
    assert baseline <= after_down

    _alembic("upgrade", "periodontogram@head")
    after_up = _list_tables()
    assert before <= after_up
```

### 10.2 Snapshot lifecycle

- Crear draft idempotente (2 calls → 1 draft).
- Solo 1 draft por paciente (constraint DB).
- PATCH a tooth/site en closed devuelve 409.
- Cerrar calcula índices y persiste en `indices`.
- DELETE sobre closed devuelve 405/422.
- Cerrar publica evento `periodontogram.snapshot.closed`.

### 10.3 Cálculo de índices

Casos canónicos con datos sintéticos:
- 28 dientes presentes × 6 sitios = 168 sitios. 42 sitios con BoP → BoP %=25%.
- CAL medio con valores conocidos.
- `deep_pockets_count`: 5 dientes con al menos un sitio ≥5mm.

### 10.4 Acoplamiento odontograma

- Paciente con diente 46 `missing` → draft nuevo trae `is_present=false` en 46.
- Paciente con implante performed en 14 → `is_implant=true` en 14.
- Odontograma no instalado / sin datos: `is_present=true, is_implant=false` por defecto.

### 10.5 Permisos

- Hygienist puede crear+cerrar.
- Assistant solo GET.
- Receptionist 403 incluso en GET.

### 10.6 Validación API

- `probing_depth_mm > 15` → 422.
- `tooth_number = 51` (deciduo) → 422.
- `site_code = 'XY'` → 422.
- PATCH a snapshot de OTRA clínica → 404 (multi-tenancy).

### 10.7 Fixture / DB de tests aislada

Atención (memoria `feedback_pytest_drops_db.md`): los tests deben correr contra DB de tests, no `dental_clinic`. Reusar fixtures existentes `db_session`, `client`, `auth_headers` de `conftest.py`.

---

## 11. Trabajo paralelo / orden de PRs

Sugerencia de PRs secuenciales (cada uno verde antes del siguiente):

1. **PR-1 backend skeleton**: módulo + manifest + migración + modelos + schemas + tests round-trip uninstall.
2. **PR-2 backend service + endpoints**: `get_or_create_draft`, `update_tooth`, `update_site`, `close`, `discard`, `list_snapshots`, `timeline`. Tests lifecycle + API validation.
3. **PR-3 backend índices + acoplamiento**: `compute_indices`, pre-relleno desde odontogram, evento `periodontogram.snapshot.closed`. Tests cálculo + acoplamiento.
4. **PR-4 frontend slot + EmptyState + skeleton**: refactor `ClinicalTab` → `DiagnosisModeContainer`, registro del slot, `PerioEmptyState`. No render de exploración aún.
5. **PR-5 frontend chart desktop**: layout 4 filas SEPA, `PerioMetricsTable`, `PerioToothLateral`, heatmap, popover sitio, banner índices.
6. **PR-6 frontend sesión + slider**: autosave, close/discard, TimelineSlider integrado, historyBanner.
7. **PR-7 mobile + i18n + docs**: layout por cuadrante <1024px, locales es/en, user-manual MD, screenshots, ADR 0014.
8. **PR-8 polish**: estados loading/error, accesibilidad teclado, smoke E2E en CI.

Cada PR debe pasar:
- `docker-compose exec backend python -m pytest -v`
- `cd backend && ruff check . && ruff format --check .`
- `cd frontend && npm run lint && npm run typecheck`
- `python backend/scripts/generate_catalogs.py` (sin diff).

---

## 12. Telemetría y observabilidad

| Métrica | Cómo |
|---------|------|
| Sessions creadas / cerradas / descartadas | Logs estructurados en `service.py` (level=info). |
| Duración media de sesión | `closed_at - recorded_at` (consulta ad-hoc). |
| Drafts huérfanos > 30 días | Job de housekeeping (fase 2). |
| Errores de validación API | Log warning con clinic_id + patient_id. |

No instrumentamos métricas Prometheus en MVP — DentalPin aún no tiene infra. Documentar en `events.md` como TODO.

---

## 13. Decisiones específicas con racional

### 13.1 Snapshots inmutables vs event sourcing

**Decisión:** snapshots inmutables (cada sesión = una unidad atómica).

**Por qué no event sourcing** (como hace odontogram con `OdontogramHistory`):
- Clínicamente una exploración periodontal es un acto **en bloque** — se interpreta como una foto en un día concreto, no como un stream de cambios.
- Comparar evolución requiere comparar fotos completas (2 snapshots). Reconstruir un estado intermedio entre exploraciones no tiene sentido clínico.
- Simplifica queries: índices se calculan en el cierre y se guardan en JSONB para evitar recomputar.
- Simplifica UX del slider: cada nodo es un snapshot real, no una reconstrucción.

Trade-off aceptado: imposible "editar" un snapshot después de cerrado. Para corregir, abrir nueva sesión. Documentado en ADR 0014.

### 13.2 Sin notas polimórficas en MVP

**Decisión:** campo `notes` TEXT en `periodontogram_snapshots`.

**Por qué no `clinical_notes` polimórficas:**
- `clinical_notes` es `removable=False` (core). Si `periodontogram` (removable) añade un `owner_type` al CHECK constraint, contamina un módulo core con conocimiento de uno opcional.
- Si se desinstala periodontogram, quedarían rows huérfanas con `owner_type='periodontogram_snapshot'` y owner inexistente — viola la invariante de uninstall limpio.
- Las notas SEPA suelen ser una observación global por sesión, no múltiples comentarios datados → un Text basta.

Si en fase 2 se necesitan notas múltiples atadas a un snapshot/diente: re-evaluar y considerar:
1. Tabla `periodontogram_notes` propia (queda aislada en la rama Alembic del módulo).
2. Promover `clinical_notes` a aceptar owner_types declarados por módulos opcionales vía registry (cambio mayor en `clinical_notes`).

### 13.3 6 sitios × FDI permanente solo (no deciduos)

**Decisión:** solo dentición permanente.

**Por qué:** SEPA y la práctica clínica periodontal real se hacen sobre permanentes. Pacientes con dentición temporal/mixta no son target de un periodontograma SEPA. Si llega esa necesidad, ampliable sin migración (campos ya soportan FDI extendido si relajamos el CHECK).

### 13.4 `auto_install=False`

**Decisión:** módulo opcional, activación manual desde admin.

**Por qué:** memoria `feedback_module_install.md` — política de módulos no-core. Coherente con `verifactu` (también opcional).

### 13.5 Edición libre por celda (no auto-avance)

**Decisión:** click → popover → guardar. Sin foco automático al siguiente sitio.

**Por qué:** confirmado por el usuario en la fase de diseño. Auto-avance queda para fase 2 (junto con captura por voz).

### 13.6 Heatmap con tokens Nuxt UI existentes

**Decisión:** reutilizar tokens `success-500 / warning-400 / warning-600 / error-500`.

**Por qué:** coherencia visual con el resto de la app, no requiere extender el design system.

---

## 14. Riesgos identificados

| Riesgo | Severidad | Mitigación |
|--------|-----------|------------|
| Flip CSS vertical sobre lateral SVG genera vista palatina anatómicamente imprecisa | Baja | Aceptado en MVP (clínicos del piloto lo verán y darán feedback). ADR documenta. Fase 2 puede añadir paths palatinos reales en `ToothSVGPaths.ts`. |
| Densidad de datos en mobile (96 sitios visibles) | Media | Layout por cuadrante <1024px (swipe). Validar con prototipo antes de PR-7. |
| Performance al renderizar 32 dientes × 6 marcadores | Baja | SVG inline cacheado por `ToothSVGPaths`. Marcadores como divs absolutamente posicionados. Mínimo de re-renders vía `markRaw` y memo en `useMemo`. |
| Conflicto con futuro odontograma "diagnosis" sub-tabs (issue futuro de re-org) | Baja | El slot `patient.diagnosis.subtabs` ya está pensado como pluggable — odontogram puede registrarse como sub-tab adicional en el futuro sin breaking change. |
| Driftearse del estándar SEPA por simplificación | Media | Cubrir todas las 9 métricas desde MVP. Antes de hacer público a piloto, validar layout con dentista. |
| Tests dropean DB real | Alta | Memoria documentada. Tests SIEMPRE contra DB de tests (`TESTING=true`). Conftest existente ya cubre, reusarlo. |
| Eventos del odontograma se publican en momentos no críticos y refrescan UI con lag | Baja | MVP: refresh manual al re-montar componente. Fase 2: WebSocket / SSE si hace falta. |

---

## 15. ADR a crear

Crear `docs/adr/0014-periodontogram-snapshot-model.md` antes o durante PR-1:

**Título:** Periodontograma — snapshots inmutables fechados (no event sourcing).
**Contexto:** una exploración periodontal SEPA es un acto en bloque clínicamente interpretado como una foto.
**Decisión:** persistencia en 3 tablas relacionales (`snapshot` 1:N `teeth` 1:N `sites`) con estado `draft|closed`, único draft activo por paciente.
**Consecuencias:** sin reconstrucción de estados intermedios; índices precomputados; UX del slider más directa; correcciones requieren nueva sesión.

---

## 16. Documentación obligatoria asociada (CLAUDE.md)

Cuando se mergee el módulo, se debe crear/actualizar:

- `backend/app/modules/periodontogram/CLAUDE.md` (template `docs/checklists/module-claude-template.md`).
- `backend/app/modules/periodontogram/CHANGELOG.md` (entry `## Unreleased` → `## 0.1.0`).
- `docs/technical/periodontogram/overview.md`, `events.md`, `permissions.md`.
- `docs/modules/periodontogram.md`.
- `docs/user-manual/{en,es}/periodontogram/index.md` + `screens/periodontograma-view.md`.
- `docs/screenshots/periodontogram/*.png`.
- `docs/modules-catalog.md`, `docs/events-catalog.md`: auto-regenerar con `python backend/scripts/generate_catalogs.py`.
- Actualizar `backend/app/modules/patients/CLAUDE.md` añadiendo el nuevo slot `patient.diagnosis.subtabs` al listado de slots estables.

---

## 17. Verificación end-to-end final

Comandos de validación al cerrar la implementación:

```bash
# Backend
docker-compose exec backend python -m pytest backend/tests/modules/periodontogram/ -v
docker-compose exec backend alembic upgrade heads
docker-compose exec backend alembic downgrade periodontogram@-1   # uninstall scoped
docker-compose exec backend alembic upgrade periodontogram@head   # reinstall

# Lint + format
cd backend && ruff check . && ruff format --check .
cd frontend && npm run lint && npm run typecheck

# Catálogos
python backend/scripts/generate_catalogs.py  # debe quedar sin diff

# Smoke manual
# 1. Login demo
# 2. Activar módulo periodontogram desde admin
# 3. Ir a paciente → Clínica → Diagnóstico → tab Periodontograma
# 4. Iniciar sesión, rellenar 5 sitios, recargar página → datos persisten
# 5. Cerrar sesión → aparece en slider
# 6. Marcar diente missing en odontograma → nueva sesión perio lo refleja
# 7. Desinstalar módulo desde admin → tab desaparece, odontograma intacto
```

---

## 18. Próximo paso operativo

1. Crear issue principal en GitHub: "feat(periodontogram): nuevo módulo SEPA opcional".
2. Crear branch `feat/periodontogram-module`.
3. Comenzar por PR-1 (backend skeleton). Mantener round-trip uninstall test verde desde la primera línea de código.
