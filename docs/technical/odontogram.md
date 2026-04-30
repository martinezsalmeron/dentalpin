# Plan Técnico: Mejoras del Módulo Odontograma (PARTE A)

**Fecha:** 2026-04-17
**Estado:** Propuesta técnica (v3 — verificada contra código real)
**Documento relacionado:** [treatment-addition (UX brief)](../features/treatment-addition.md)

---

## Índice

1. [Alcance y Prioridades](#1-alcance-y-prioridades)
2. [Estado Actual (Verificado)](#2-estado-actual-verificado)
3. [Decisiones de Diseño](#3-decisiones-de-diseño)
4. [Cambios Backend](#4-cambios-backend)
5. [Cambios Frontend](#5-cambios-frontend)
6. [Refactor Oportunista](#6-refactor-oportunista)
7. [Migración](#7-migración)
8. [Plan de Implementación](#8-plan-de-implementación)
9. [Tests](#9-tests)
10. [Riesgos](#10-riesgos)

---

## 1. Alcance y Prioridades

El odontograma se usa en `DiagnosisMode.vue` (modo `diagnosis`), `PlanDetailView.vue` (modo `planning`) y `HistoryMode.vue` (modo `view-only`).

| ID | Mejora | Prioridad | En este PR |
|----|--------|-----------|------------|
| **A1** | Multi-diente (puentes, férulas, múltiples) | P0 | **Sí (núcleo)** |
| **A3** | Estados visuales + banner modo aplicar | P1 | Sí |
| **A4** | Conexión visual entre dientes del grupo | P1 | Sí |
| **A5** | Indicador de selección en `TreatmentBar` | P2 | Sí |
| **A6** | Atajos de teclado | P3 | Sí (barato) |
| **A2** | Superficies inline (quitar UModal) | P1 | **No** — PR separado |

**A2 sale del alcance** porque `SurfaceSelectorPopup` hoy es `<UModal>` centrado (línea 161). Convertirlo a popup anclado al diente requiere refactor de posicionamiento (usePopper, refs al SVG del diente, z-index) independiente del multi-diente. Se hará después, sin bloquear A1.

---

## 2. Estado Actual (Verificado)

### 2.1 Modelos (`backend/app/modules/odontogram/models.py`)

- `ToothRecord` — 1 por diente-paciente. Fields: `surfaces` JSONB, `general_condition`, flags orto.
- `ToothTreatment` — 1 por tratamiento. Fields relevantes: `treatment_type`, `treatment_category` (`surface`|`whole_tooth`), `surfaces` (list|null), `status` (`existing`|`planned`), `catalog_item_id`, `budget_item_id`, `deleted_at` (soft-delete), `performed_at`, `performed_by`, `source_module`.
- `OdontogramHistory` — audit.

### 2.2 Constantes (`backend/app/modules/odontogram/constants.py`)

- `TreatmentStatus` = `StrEnum { EXISTING="existing", PLANNED="planned" }` (líneas 122-127).
- `get_treatment_category(type) → TreatmentCategory.SURFACE|WHOLE_TOOTH` (líneas 386-390).
- Ya existen: `pontic`, `bridge_abutment` (whole_tooth, pattern_fill).
- **No existe** `splint` — hay que añadirlo.

### 2.3 Service y Router (`service.py`, `router.py`)

- `TreatmentService.create_treatment` contiene inline (líneas 563-570) el patrón "get or create tooth record":
  ```python
  tooth_record = await OdontogramService.get_tooth_record(db, clinic_id, patient_id, tooth_number)
  if not tooth_record:
      tooth_record = await OdontogramService.create_or_update_tooth(db, clinic_id, patient_id, tooth_number, user_id)
  ```
- `ClinicContext` (`dependencies.py:23-31`) expone `user_id`, `clinic_id`, `user`, `clinic`, `role`.
- Permisos registrados (`__init__.py:42-48`): `read`, `write`, `treatments.read`, `treatments.write` → namespaced a `odontogram.*`.
- `TreatmentResponse` (`schemas.py:323-343`) tiene campo `performed_by_name: str | None = None`. **Se puebla en 4 sitios del router** (410-412, 449-450, 482-483, 584-586). No tiene `catalog_item_id` (aunque el modelo sí).
- `GET /patients/{id}/treatments` acepta query params: `status`, `treatment_type`, `tooth_number`, `page`, `page_size` (router.py:417-431).

### 2.4 Eventos (`service.py`, `treatment_plan/events.py`)

- `ODONTOGRAM_TREATMENT_ADDED` emitido en `create_treatment` (597-611).
- `ODONTOGRAM_TREATMENT_STATUS_CHANGED` en `update_treatment` (720-735).
- `ODONTOGRAM_TREATMENT_PERFORMED` en `perform_treatment` (811-826).
- `treatment_plan/events.py:on_treatment_performed` busca `PlannedTreatmentItem` por `tooth_treatment_id`. **Por tanto emitir N eventos PERFORMED (uno por miembro del grupo) es correcto**: completa N items del plan.

### 2.5 Frontend

- `useTreatments.ts` usa `ref<Treatment[]>([])` **local al llamador** (no `useState`). Cada sitio que lo llama tiene su propia lista. Se hidrata llamando `fetchTreatments()`.
- `OdontogramChart.vue` define `handleToothClick` **inline en línea 235** como método del componente. Se inyecta vía `@tooth-click` en los 4 cuadrantes (461, 480, 504, 523).
- Coordinación `TreatmentBar ↔ OdontogramChart`: parent-holds-state. El contenedor (`DiagnosisMode`, `PlanDetailView`) guarda `selectedTreatmentType` y pasa como prop. Nuestra lógica multi-diente irá **dentro de `OdontogramChart`** — no toca el contrato con el padre.
- `TreatmentEditModal.vue` props: `treatment: Treatment | null`, `open: boolean`. Muy orientado a single-treatment. **No reutilizable** para confirmación multi-diente sin rework.
- `useTreatmentCatalog.getTreatmentByType()` soporta lookup por `treatment_type`. Fallback a constantes si catálogo vacío. `splint` y `multiple_veneers` irán por fallback hasta que se seeden en catálogo.

---

## 3. Decisiones de Diseño

### 3.1 Estructura de datos: una columna, sin tabla nueva

```
ToothTreatment
  + treatment_group_id: UUID | NULL   (indexed, sin FK — es un bucket id opaco)
```

Un puente 14-15-16:
```
ToothTreatment(tooth=14, type=bridge_abutment, group_id=G1)
ToothTreatment(tooth=15, type=pontic,          group_id=G1)
ToothTreatment(tooth=16, type=bridge_abutment, group_id=G1)
```

Una férula 31-41:
```
ToothTreatment(tooth=31, type=splint, group_id=G2)
ToothTreatment(tooth=41, type=splint, group_id=G2)
```

**Rol clínico (pilar/póntico) ya encodeado en `treatment_type`** (`bridge_abutment`/`pontic` existen). Sin campo `group_role`.

### 3.2 API: modo declarativo, no flag booleano

Rechazado `grouped: bool`. Adoptado `mode: Literal["bridge", "uniform"]`:

| `mode` | Mínimo dientes | `treatment_type` | Asignación de tipos |
|--------|----------------|------------------|---------------------|
| `bridge` | 3 | **No se envía** (prohibido) | Primer y último diente → `bridge_abutment`. Intermedios → `pontic`. Backend lo asigna según posición ordenada en arcada. |
| `uniform` | 2 | **Requerido** | Todos los dientes reciben el mismo `treatment_type` (ej: `splint`, `crown`, `veneer`). |

Ventajas:
- Cliente no puede crear grupos incoherentes (ej: puente con dos pónticos consecutivos sin pilares).
- Semántica clara en el payload: el nombre del modo dice qué se está creando.
- `treatment_type` opcional/prohibido según modo — validado en schema.

### 3.3 Ciclo de vida del grupo: operaciones atómicas

- **Crear** → `POST /treatment-groups` crea N tratamientos con `treatment_group_id` compartido.
- **Realizar** → `PATCH /treatment-groups/{id}/perform` marca los N como `existing` atómicamente (un puente no puede estar "a medias"). Emite N eventos `ODONTOGRAM_TREATMENT_PERFORMED`, uno por miembro.
- **Borrar** → `DELETE /treatment-groups/{id}` soft-deletea los N miembros atómicamente. Un puente con un pilar borrado es clínicamente inconsistente.
- **Listar** → filtro `?treatment_group_id=<id>` en `GET /treatments` existente.
- **Editar miembro individual** (ej: cambiar notas de un diente concreto) → `PUT /treatments/{id}` existente sigue funcionando. Intencionadamente no hay `PUT /treatment-groups/{id}` — cambios de status atómicos se exponen solo vía `/perform`.

### 3.4 `mode=bridge` con `status=existing` permitido

Caso real: dentista registra en diagnóstico un puente ya existente en boca del paciente. Mismo endpoint, mismo modo, `status="existing"`. El servicio asigna `performed_at=now` y `performed_by=user_id` igual que hace hoy `create_treatment`.

---

## 4. Cambios Backend

### 4.1 Modelo

`backend/app/modules/odontogram/models.py`:

```python
class ToothTreatment(Base, TimestampMixin):
    # ... campos existentes ...
    treatment_group_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
```

### 4.2 Constantes

`backend/app/modules/odontogram/constants.py`:

- Añadir `splint` a `WHOLE_TOOTH_TREATMENTS` y a la categoría terapéutica correspondiente (probablemente `restauradora` o crear subcategoría `prótesis removible` si aplica — confirmar con catálogo).
- Verificar que los tipos multi-diente aceptados en `mode=uniform` están todos en `WHOLE_TOOTH_TREATMENTS`: `crown`, `veneer`, `splint`. Si algún día se permite grupo de superficie (raro) habrá que abrir la validación.

### 4.3 Migración Alembic

```python
def upgrade():
    op.add_column(
        "tooth_treatments",
        sa.Column("treatment_group_id", UUID(as_uuid=True), nullable=True),
    )
    op.create_index(
        "ix_tooth_treatments_group",
        "tooth_treatments",
        ["treatment_group_id"],
    )

def downgrade():
    op.drop_index("ix_tooth_treatments_group", "tooth_treatments")
    op.drop_column("tooth_treatments", "treatment_group_id")
```

Sin backfill. Datos históricos quedan con `group_id = NULL` = tratamientos individuales.

### 4.4 Schemas

`backend/app/modules/odontogram/schemas.py`:

```python
class TreatmentGroupCreate(BaseModel):
    """Crea un grupo atómico de tratamientos multi-diente."""
    mode: Literal["bridge", "uniform"]
    tooth_numbers: list[int]
    treatment_type: str | None = None           # prohibido si mode=bridge; requerido si mode=uniform
    surfaces: list[str] | None = None           # opcional para uniform con tipos de superficie
    status: Literal["existing", "planned"] = "planned"
    notes: str | None = None
    catalog_item_id: UUID | None = None
    budget_item_id: UUID | None = None

    @model_validator(mode="after")
    def validate(self):
        if len(self.tooth_numbers) != len(set(self.tooth_numbers)):
            raise ValueError("Duplicate tooth numbers not allowed")
        if self.mode == "bridge":
            if len(self.tooth_numbers) < 3:
                raise ValueError("Bridge requires at least 3 teeth")
            if self.treatment_type is not None:
                raise ValueError("treatment_type not allowed in bridge mode (auto-assigned)")
        elif self.mode == "uniform":
            if len(self.tooth_numbers) < 2:
                raise ValueError("Uniform group requires at least 2 teeth")
            if not self.treatment_type:
                raise ValueError("treatment_type required in uniform mode")
        return self


# Añadir a TreatmentResponse existente:
class TreatmentResponse(BaseModel):
    # ... campos existentes ...
    treatment_group_id: UUID | None = None
```

### 4.5 Service Layer

`backend/app/modules/odontogram/service.py`:

**Extraer** nuevo método en `OdontogramService` (elimina la duplicación inline de 4.1 del estado actual):

```python
@staticmethod
async def get_or_create_tooth_record(
    db: AsyncSession, clinic_id: UUID, patient_id: UUID,
    tooth_number: int, user_id: UUID,
) -> ToothRecord:
    record = await OdontogramService.get_tooth_record(
        db, clinic_id, patient_id, tooth_number
    )
    if record:
        return record
    return await OdontogramService.create_or_update_tooth(
        db, clinic_id, patient_id, tooth_number, user_id
    )
```

Refactorizar `TreatmentService.create_treatment` para usarlo.

**Añadir al `TreatmentService`:**

```python
@staticmethod
async def create_group(
    db: AsyncSession, clinic_id: UUID, patient_id: UUID,
    user_id: UUID, data: TreatmentGroupCreate,
) -> list[ToothTreatment]:
    group_id = uuid.uuid4()
    now = datetime.now(UTC)
    teeth_sorted = sorted(data.tooth_numbers)

    # Resolver treatment_type por diente según modo
    if data.mode == "bridge":
        first, last = teeth_sorted[0], teeth_sorted[-1]
        def type_for(t: int) -> str:
            return "bridge_abutment" if t in (first, last) else "pontic"
    else:  # uniform
        assert data.treatment_type is not None
        tt = data.treatment_type
        def type_for(_t: int) -> str:
            return tt

    created: list[ToothTreatment] = []
    for tooth_number in teeth_sorted:
        tooth_record = await OdontogramService.get_or_create_tooth_record(
            db, clinic_id, patient_id, tooth_number, user_id
        )
        ttype = type_for(tooth_number)
        category = get_treatment_category(ttype).value
        t = ToothTreatment(
            clinic_id=clinic_id, patient_id=patient_id,
            tooth_record_id=tooth_record.id, tooth_number=tooth_number,
            treatment_type=ttype, treatment_category=category,
            surfaces=data.surfaces if category == "surface" else None,
            status=data.status, recorded_at=now,
            performed_at=now if data.status == TreatmentStatus.EXISTING.value else None,
            performed_by=user_id if data.status == TreatmentStatus.EXISTING.value else None,
            catalog_item_id=data.catalog_item_id,
            budget_item_id=data.budget_item_id,
            source_module="odontogram",
            notes=data.notes,
            treatment_group_id=group_id,
        )
        db.add(t)
        created.append(t)

    await db.flush()
    for t in created:
        event_bus.publish(EventType.ODONTOGRAM_TREATMENT_ADDED, {
            "clinic_id": str(clinic_id),
            "patient_id": str(patient_id),
            "treatment_id": str(t.id),
            "tooth_number": t.tooth_number,
            "treatment_type": t.treatment_type,
            "status": t.status,
            "budget_item_id": str(t.budget_item_id) if t.budget_item_id else None,
            "source_module": t.source_module,
            "created_by": str(user_id),
            "created_at": now.isoformat(),
        })
    return created


@staticmethod
async def perform_group(
    db: AsyncSession, clinic_id: UUID, group_id: UUID,
    user_id: UUID, notes: str | None = None,
) -> list[ToothTreatment]:
    result = await db.execute(
        select(ToothTreatment)
        .options(selectinload(ToothTreatment.performer))
        .where(
            ToothTreatment.clinic_id == clinic_id,
            ToothTreatment.treatment_group_id == group_id,
            ToothTreatment.deleted_at.is_(None),
        )
    )
    members = list(result.scalars())
    if not members:
        return []

    now = datetime.now(UTC)
    for t in members:
        previous_status = t.status
        t.status = TreatmentStatus.EXISTING.value
        t.performed_at = now
        t.performed_by = user_id
        if notes:
            t.notes = f"{t.notes or ''}\n[Realizado]: {notes}".strip()
        event_bus.publish(EventType.ODONTOGRAM_TREATMENT_PERFORMED, {
            "clinic_id": str(clinic_id),
            "patient_id": str(t.patient_id),
            "treatment_id": str(t.id),
            "tooth_number": t.tooth_number,
            "treatment_type": t.treatment_type,
            "budget_item_id": str(t.budget_item_id) if t.budget_item_id else None,
            "performed_by": str(user_id),
            "performed_at": now.isoformat(),
            "previous_status": previous_status,
        })
    await db.flush()
    return members


@staticmethod
async def delete_group(
    db: AsyncSession, clinic_id: UUID, group_id: UUID, user_id: UUID,
) -> int:
    result = await db.execute(
        select(ToothTreatment).where(
            ToothTreatment.clinic_id == clinic_id,
            ToothTreatment.treatment_group_id == group_id,
            ToothTreatment.deleted_at.is_(None),
        )
    )
    members = list(result.scalars())
    if not members:
        return 0
    now = datetime.now(UTC)
    for t in members:
        t.deleted_at = now
        event_bus.publish(EventType.ODONTOGRAM_TREATMENT_DELETED, {
            "clinic_id": str(clinic_id),
            "patient_id": str(t.patient_id),
            "treatment_id": str(t.id),
            "deleted_by": str(user_id),
        })
    await db.flush()
    return len(members)
```

### 4.6 Endpoints

`backend/app/modules/odontogram/router.py`:

```python
@router.post(
    "/patients/{patient_id}/treatment-groups",
    response_model=ApiResponse[list[TreatmentResponse]],
    status_code=201,
)
async def create_treatment_group(
    patient_id: UUID,
    data: TreatmentGroupCreate,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("odontogram.treatments.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[list[TreatmentResponse]]:
    treatments = await TreatmentService.create_group(
        db, ctx.clinic_id, patient_id, ctx.user_id, data
    )
    return ApiResponse(data=[_to_response(t) for t in treatments])


@router.patch(
    "/treatment-groups/{group_id}/perform",
    response_model=ApiResponse[list[TreatmentResponse]],
)
async def perform_treatment_group(
    group_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("odontogram.treatments.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    body: PerformGroupBody = Body(default_factory=lambda: PerformGroupBody()),
) -> ApiResponse[list[TreatmentResponse]]:
    treatments = await TreatmentService.perform_group(
        db, ctx.clinic_id, group_id, ctx.user_id, body.notes
    )
    if not treatments:
        raise HTTPException(404, "Treatment group not found")
    return ApiResponse(data=[_to_response(t) for t in treatments])


@router.delete("/treatment-groups/{group_id}", status_code=204)
async def delete_treatment_group(
    group_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("odontogram.treatments.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    deleted = await TreatmentService.delete_group(
        db, ctx.clinic_id, group_id, ctx.user_id
    )
    if deleted == 0:
        raise HTTPException(404, "Treatment group not found")
```

**Ampliar filtro en endpoint existente** `GET /patients/{patient_id}/treatments`:

```python
treatment_group_id: UUID | None = Query(default=None),
```

Pasar a `TreatmentService.list_patient_treatments` como filtro SQL.

`_to_response(t)` es el helper del refactor 6.1 que puebla `performed_by_name` en el service (elimina las 4 poblaciones manuales del router).

### 4.7 Permisos

Ya existen (`odontogram.treatments.read` / `odontogram.treatments.write`). Los 3 endpoints nuevos los reutilizan. Sin cambios en `permissions.py`.

---

## 5. Cambios Frontend

### 5.1 Tipos

`frontend/app/types/index.ts`:

```typescript
export interface Treatment {
  // ... campos existentes ...
  treatment_group_id?: string | null
}

export type TreatmentGroupMode = 'bridge' | 'uniform'

export interface TreatmentGroupCreate {
  mode: TreatmentGroupMode
  tooth_numbers: number[]
  treatment_type?: string          // requerido si mode='uniform'
  surfaces?: string[]
  status?: 'existing' | 'planned'
  notes?: string
  catalog_item_id?: string
  budget_item_id?: string
}

export interface MultiToothTreatmentConfig {
  /** Clave del tipo en catálogo/constantes. Para 'bridge' es ficticia: se traduce a mode='bridge' al enviar. */
  key: string
  labelKey: string                 // i18n key
  mode: TreatmentGroupMode
  selectionMode: 'range' | 'free'
  minTeeth: number
  maxTeeth: number
  requiresSameArch: boolean
}
```

### 5.2 Extender `useTreatments.ts`

```typescript
async function createTreatmentGroup(
  patientId: string, payload: TreatmentGroupCreate
): Promise<Treatment[]> {
  const res = await api.post<ApiResponse<Treatment[]>>(
    `/api/v1/odontogram/patients/${patientId}/treatment-groups`, payload
  )
  treatments.value.push(...res.data)
  return res.data
}

async function performTreatmentGroup(
  groupId: string, notes?: string
): Promise<Treatment[]> {
  const res = await api.patch<ApiResponse<Treatment[]>>(
    `/api/v1/odontogram/treatment-groups/${groupId}/perform`,
    notes ? { notes } : {}
  )
  for (const updated of res.data) {
    const i = treatments.value.findIndex(t => t.id === updated.id)
    if (i !== -1) treatments.value[i] = updated
  }
  return res.data
}

async function deleteTreatmentGroup(groupId: string): Promise<void> {
  await api.del(`/api/v1/odontogram/treatment-groups/${groupId}`)
  treatments.value = treatments.value.filter(t => t.treatment_group_id !== groupId)
}

function getGroupMembers(groupId: string): Treatment[] {
  return treatments.value.filter(t => t.treatment_group_id === groupId)
}

function getGroupIdForTooth(toothNumber: number): string | null {
  return treatments.value
    .find(t => t.tooth_number === toothNumber && t.treatment_group_id)
    ?.treatment_group_id ?? null
}
```

Sin composable nuevo. `treatments` sigue siendo `ref` local al llamador (mismo patrón actual).

### 5.3 Config multi-diente

`frontend/app/config/odontogramConstants.ts`:

```typescript
export const MULTI_TOOTH_TREATMENTS: Record<string, MultiToothTreatmentConfig> = {
  bridge: {
    key: 'bridge', labelKey: 'odontogram.multiTooth.bridge.label',
    mode: 'bridge', selectionMode: 'range',
    minTeeth: 3, maxTeeth: 14, requiresSameArch: true,
  },
  splint: {
    key: 'splint', labelKey: 'odontogram.multiTooth.splint.label',
    mode: 'uniform', selectionMode: 'free',
    minTeeth: 2, maxTeeth: 14, requiresSameArch: true,
  },
  multiple_veneers: {
    key: 'veneer', labelKey: 'odontogram.multiTooth.veneers.label',
    mode: 'uniform', selectionMode: 'free',
    minTeeth: 2, maxTeeth: 10, requiresSameArch: false,
  },
  multiple_crowns: {
    key: 'crown', labelKey: 'odontogram.multiTooth.crowns.label',
    mode: 'uniform', selectionMode: 'free',
    minTeeth: 2, maxTeeth: 28, requiresSameArch: false,
  },
}

export const UPPER_ARCH_ORDER = [18,17,16,15,14,13,12,11, 21,22,23,24,25,26,27,28]
export const LOWER_ARCH_ORDER = [48,47,46,45,44,43,42,41, 31,32,33,34,35,36,37,38]

export function getArchOrder(toothNumber: number): number[] | null {
  if (UPPER_ARCH_ORDER.includes(toothNumber)) return UPPER_ARCH_ORDER
  if (LOWER_ARCH_ORDER.includes(toothNumber)) return LOWER_ARCH_ORDER
  return null
}

export function calculateToothRange(start: number, end: number): number[] {
  const arch = getArchOrder(start)
  if (!arch || !arch.includes(end)) throw new Error('same_arch_required')
  const i = arch.indexOf(start), j = arch.indexOf(end)
  const [a, b] = i <= j ? [i, j] : [j, i]
  return arch.slice(a, b + 1)
}

export function isSameArch(teeth: number[]): boolean {
  if (teeth.length <= 1) return true
  const first = getArchOrder(teeth[0])
  return teeth.every(t => getArchOrder(t) === first)
}

export function getMultiToothConfig(treatmentKey: string): MultiToothTreatmentConfig | null {
  return MULTI_TOOTH_TREATMENTS[treatmentKey] ?? null
}
```

Dos arrays FDI por arcada + `slice` = fin del problema de cuadrantes. Sin aritmética frágil.

### 5.4 `OdontogramChart.vue`

Modificaciones sobre el componente existente (sin cambios al contrato con el padre):

```typescript
const multiConfig = computed(() =>
  selectedTreatmentType.value
    ? getMultiToothConfig(selectedTreatmentType.value)
    : null
)
const multiSel = ref<{ teeth: number[]; anchor: number | null }>({ teeth: [], anchor: null })
const showMultiConfirm = ref(false)

function handleToothClick(toothNumber: number) {
  if (isReadonly.value || !isClickToApplyMode.value) return
  if (multiConfig.value) return handleMultiToothClick(toothNumber)

  // Comportamiento existente
  if (isSurfaceTreatment(selectedTreatmentType.value!)) {
    selectedTooth.value = toothNumber
    showSurfaceSelector.value = true
  } else {
    applyTreatment(toothNumber)
  }
}

function handleMultiToothClick(tooth: number) {
  const cfg = multiConfig.value!
  if (cfg.selectionMode === 'range') {
    if (multiSel.value.anchor === null) {
      multiSel.value = { anchor: tooth, teeth: [tooth] }
      return
    }
    try {
      const range = calculateToothRange(multiSel.value.anchor, tooth)
      if (range.length < cfg.minTeeth) {
        toast.error(t('odontogram.multiTooth.errors.tooFew', { n: cfg.minTeeth }))
        return
      }
      if (range.length > cfg.maxTeeth) {
        toast.error(t('odontogram.multiTooth.errors.tooMany', { n: cfg.maxTeeth }))
        return
      }
      multiSel.value.teeth = range
      showMultiConfirm.value = true
    } catch {
      toast.error(t('odontogram.multiTooth.errors.sameArchRequired'))
    }
    return
  }

  // free mode
  const i = multiSel.value.teeth.indexOf(tooth)
  if (i === -1) {
    const candidate = [...multiSel.value.teeth, tooth]
    if (cfg.requiresSameArch && !isSameArch(candidate)) {
      toast.error(t('odontogram.multiTooth.errors.sameArchRequired'))
      return
    }
    multiSel.value.teeth = candidate
  } else {
    multiSel.value.teeth.splice(i, 1)
  }
}

async function confirmMultiTooth() {
  const cfg = multiConfig.value!
  const payload: TreatmentGroupCreate = {
    mode: cfg.mode,
    tooth_numbers: [...multiSel.value.teeth].sort((a, b) => a - b),
    status: selectedTreatmentStatus.value,
    ...(cfg.mode === 'uniform' ? { treatment_type: cfg.key } : {}),
  }
  const created = await createTreatmentGroup(props.patientId, payload)
  pushUndoEntry({ type: 'group', groupId: created[0]?.treatment_group_id! })
  resetMultiSelection()
  emit('treatment-add', created)
}

function resetMultiSelection() {
  multiSel.value = { teeth: [], anchor: null }
  showMultiConfirm.value = false
}
```

Teclas (A6) — añadir listener:

```typescript
useEventListener(window, 'keydown', (e: KeyboardEvent) => {
  if (e.key === 'Escape' && multiConfig.value) resetMultiSelection()
  if (e.key === 'Enter' && showMultiConfirm.value) confirmMultiTooth()
})
```

### 5.5 Componente nuevo: `MultiToothConfirmPopup.vue` (~80 líneas)

Pequeño, dedicado. NO reutiliza `TreatmentEditModal` (sus props `treatment: Treatment | null` no encajan sin hack).

```vue
<script setup lang="ts">
const props = defineProps<{
  open: boolean
  config: MultiToothTreatmentConfig
  teeth: number[]
  status: 'existing' | 'planned'
}>()
const emit = defineEmits<{
  'update:open': [value: boolean]
  'confirm': []
}>()

const pillars = computed(() =>
  props.config.mode === 'bridge'
    ? [props.teeth[0], props.teeth[props.teeth.length - 1]]
    : []
)
const pontics = computed(() =>
  props.config.mode === 'bridge' ? props.teeth.slice(1, -1) : []
)
</script>

<template>
  <UModal :open="open" @update:open="emit('update:open', $event)">
    <div class="p-6 space-y-4">
      <h3 class="text-lg font-semibold">{{ t(config.labelKey) }}</h3>
      <div class="flex flex-wrap gap-2">
        <UBadge v-for="t in teeth" :key="t"
          :color="pillars.includes(t) ? 'primary' : 'neutral'">
          {{ t }}
          <span v-if="pillars.includes(t)" class="ml-1 text-xs">({{ t('odontogram.multiTooth.pillar') }})</span>
          <span v-else-if="pontics.includes(t)" class="ml-1 text-xs">({{ t('odontogram.multiTooth.pontic') }})</span>
        </UBadge>
      </div>
      <div class="flex justify-end gap-2">
        <UButton variant="ghost" @click="emit('update:open', false)">
          {{ t('common.cancel') }}
        </UButton>
        <UButton color="primary" @click="emit('confirm')">
          {{ t('common.confirm') }}
        </UButton>
      </div>
    </div>
  </UModal>
</template>
```

### 5.6 `TreatmentBar.vue` — banner (A5)

Añadir sección contextual mostrando selección actual:

```vue
<div v-if="multiConfig" class="multi-tooth-hint">
  <UIcon name="i-lucide-link" />
  <span>{{ t(multiConfig.labelKey) }}</span>
  <span class="hint-text">
    {{ multiConfig.selectionMode === 'range'
      ? t('odontogram.multiTooth.hints.range')
      : t('odontogram.multiTooth.hints.free') }}
  </span>
  <UBadge v-if="selectedTeethCount > 0">{{ selectedTeethCount }}</UBadge>
  <UButton size="xs" variant="ghost" @click="emit('cancel')">
    {{ t('common.cancel') }}
  </UButton>
</div>
```

`multiConfig` y `selectedTeethCount` se pasan como props desde el padre (sigue el patrón actual de parent-holds-state).

### 5.7 Conexión visual (A4)

Capa SVG dentro de `OdontogramChart.vue`:

```typescript
const bridgeConnections = computed(() => {
  const byGroup = new Map<string, Treatment[]>()
  for (const t of treatments.value) {
    if (!t.treatment_group_id) continue
    if (t.treatment_type !== 'bridge_abutment' && t.treatment_type !== 'pontic') continue
    const arr = byGroup.get(t.treatment_group_id) ?? []
    arr.push(t)
    byGroup.set(t.treatment_group_id, arr)
  }
  const segments: Array<{ from: number; to: number; status: string; groupId: string }> = []
  for (const [groupId, members] of byGroup) {
    const sorted = [...members].sort((a, b) => a.tooth_number - b.tooth_number)
    for (let i = 0; i < sorted.length - 1; i++) {
      segments.push({
        from: sorted[i].tooth_number,
        to: sorted[i + 1].tooth_number,
        status: sorted[i].status,
        groupId,
      })
    }
  }
  return segments
})
```

Template: `<svg>` overlay con `<line>` por cada segmento. `stroke-dasharray` si `status === 'planned'`.

### 5.8 i18n

`frontend/i18n/locales/es.json` y `en.json` — añadir bajo `odontogram`:

```json
"multiTooth": {
  "bridge": { "label": "Puente fijo" },
  "splint": { "label": "Férula" },
  "veneers": { "label": "Carillas múltiples" },
  "crowns": { "label": "Coronas múltiples" },
  "pillar": "pilar",
  "pontic": "póntico",
  "hints": {
    "range": "Clic en diente inicial, luego en diente final",
    "free": "Clic para añadir/quitar dientes"
  },
  "errors": {
    "tooFew": "Requiere mínimo {n} dientes",
    "tooMany": "Máximo {n} dientes",
    "sameArchRequired": "Los dientes deben estar en la misma arcada"
  }
}
```

---

## 6. Refactor Oportunista

Incluido en el mismo PR porque toca los mismos archivos:

| # | Refactor | Archivo | Razón |
|---|----------|---------|-------|
| 6.1 | Mover población de `performed_by_name` a `TreatmentService._to_response` (o eager-load en el query + `@computed_field` en Pydantic) | `service.py` + `router.py:410,449,482,584` | Duplicado en 4 sitios. `create_group` y `perform_group` necesitan la misma lógica. Concentrar en un solo punto. |
| 6.2 | Extraer `OdontogramService.get_or_create_tooth_record` | `service.py:563-570` | Eliminar duplicación inline. Requerido por `create_group`. |
| 6.3 | Helper `_active_treatments_filter()` para el patrón `deleted_at.is_(None)` | `service.py:632-633, 667-668` y nuevas queries de grupo | Legibilidad. |

**Fuera de alcance** (NO en este PR):
- Limpieza de aliases legacy (`filling`, `root_canal`, `bridge_pontic`) — separar si y cuando aplique.
- Reescritura de `bulk_update_teeth` — no hay evidencia de problema de perf.
- A2 (superficies inline) — PR separado.

---

## 7. Migración

**No destructiva.** Una columna nueva nullable + un índice. Sin backfill. Sin cambios en endpoints existentes. Datos históricos siguen funcionando como tratamientos individuales (`group_id = NULL`).

Si más adelante se quiere agrupar retroactivamente puentes huérfanos (`treatment_type in ('bridge_abutment','pontic')` sin grupo), se puede hacer con un script ad-hoc que detecte rangos contiguos en la misma arcada. No está en este PR.

---

## 8. Plan de Implementación

### Fase 1 — Backend (~2 días)

1. Añadir columna + migración Alembic. Aplicar.
2. Añadir `splint` a `constants.py` (categoría y lista `WHOLE_TOOTH_TREATMENTS`).
3. Refactor 6.2: extraer `get_or_create_tooth_record`. Adaptar `create_treatment`.
4. Refactor 6.1: centralizar `performed_by_name` (elige la opción que menos toque el resto).
5. Implementar `TreatmentGroupCreate` + `create_group`, `perform_group`, `delete_group`.
6. Ampliar filtro `treatment_group_id` en `list_patient_treatments`.
7. Añadir 3 endpoints (`POST /treatment-groups`, `PATCH .../perform`, `DELETE .../{id}`).
8. Tests backend (sección 9.1).

### Fase 2 — Frontend core (~2 días)

9. Tipos + `MULTI_TOOTH_TREATMENTS` + `calculateToothRange`/`isSameArch`.
10. Extender `useTreatments` con `createTreatmentGroup`, `performTreatmentGroup`, `deleteTreatmentGroup`, helpers de grupo.
11. Modificar `handleToothClick` en `OdontogramChart.vue` + handler multi + reset + atajos de teclado.
12. Crear `MultiToothConfirmPopup.vue`.
13. i18n en ambos locales.

### Fase 3 — Visual (~1.5 días)

14. Capa SVG de conexiones (A4).
15. Banner en `TreatmentBar.vue` (A5) + plumbing del padre (`DiagnosisMode`, `PlanDetailView`).
16. Estados visuales CSS para dientes seleccionados en modo multi (A3).

### Fase 4 — Validación e2e (~0.5 día)

17. Dogfood con dev server: puente 14-15-16, férula 31-41, carillas 12-22, borrado de grupo, marcar grupo como realizado, ver sincronización con plan.

**Total:** 5-6 días efectivos.

---

## 9. Tests

### 9.1 Backend (`backend/tests/test_treatment_groups.py`)

Reutilizar fixture `odontogram_setup` (devuelve `clinic_id`, `user_id`, `patient_id`).

```python
async def test_create_bridge_auto_assigns_roles(client, auth_headers, odontogram_setup):
    pid = odontogram_setup["patient_id"]
    r = await client.post(
        f"/api/v1/odontogram/patients/{pid}/treatment-groups",
        json={"mode": "bridge", "tooth_numbers": [14, 15, 16], "status": "planned"},
        headers=auth_headers,
    )
    assert r.status_code == 201
    data = r.json()["data"]
    assert len(data) == 3
    group_ids = {t["treatment_group_id"] for t in data}
    assert len(group_ids) == 1 and None not in group_ids
    by_tooth = {t["tooth_number"]: t["treatment_type"] for t in data}
    assert by_tooth == {14: "bridge_abutment", 15: "pontic", 16: "bridge_abutment"}


async def test_bridge_rejects_less_than_3_teeth(client, auth_headers, odontogram_setup):
    r = await client.post(
        f"/api/v1/odontogram/patients/{odontogram_setup['patient_id']}/treatment-groups",
        json={"mode": "bridge", "tooth_numbers": [14, 15]},
        headers=auth_headers,
    )
    assert r.status_code == 422


async def test_bridge_rejects_treatment_type_param(client, auth_headers, odontogram_setup):
    r = await client.post(
        f"/api/v1/odontogram/patients/{odontogram_setup['patient_id']}/treatment-groups",
        json={"mode": "bridge", "tooth_numbers": [14,15,16], "treatment_type": "crown"},
        headers=auth_headers,
    )
    assert r.status_code == 422


async def test_uniform_splint_creates_same_type_all(client, auth_headers, odontogram_setup):
    r = await client.post(
        f"/api/v1/odontogram/patients/{odontogram_setup['patient_id']}/treatment-groups",
        json={"mode": "uniform", "tooth_numbers": [31, 32, 33, 41],
              "treatment_type": "splint", "status": "existing"},
        headers=auth_headers,
    )
    assert r.status_code == 201
    assert all(t["treatment_type"] == "splint" for t in r.json()["data"])
    assert all(t["status"] == "existing" for t in r.json()["data"])
    assert all(t["performed_at"] for t in r.json()["data"])


async def test_uniform_requires_treatment_type(client, auth_headers, odontogram_setup):
    r = await client.post(
        f"/api/v1/odontogram/patients/{odontogram_setup['patient_id']}/treatment-groups",
        json={"mode": "uniform", "tooth_numbers": [14, 15]},
        headers=auth_headers,
    )
    assert r.status_code == 422


async def test_duplicate_teeth_rejected(client, auth_headers, odontogram_setup):
    r = await client.post(
        f"/api/v1/odontogram/patients/{odontogram_setup['patient_id']}/treatment-groups",
        json={"mode": "bridge", "tooth_numbers": [14, 14, 16]},
        headers=auth_headers,
    )
    assert r.status_code == 422


async def test_perform_group_marks_all_existing(client, auth_headers, odontogram_setup):
    pid = odontogram_setup["patient_id"]
    create = await client.post(
        f"/api/v1/odontogram/patients/{pid}/treatment-groups",
        json={"mode": "bridge", "tooth_numbers": [14,15,16], "status": "planned"},
        headers=auth_headers,
    )
    gid = create.json()["data"][0]["treatment_group_id"]
    r = await client.patch(
        f"/api/v1/odontogram/treatment-groups/{gid}/perform",
        json={"notes": "Colocado hoy"}, headers=auth_headers,
    )
    assert r.status_code == 200
    for t in r.json()["data"]:
        assert t["status"] == "existing"
        assert t["performed_at"] is not None


async def test_delete_group_soft_deletes_all(client, auth_headers, odontogram_setup):
    pid = odontogram_setup["patient_id"]
    create = await client.post(
        f"/api/v1/odontogram/patients/{pid}/treatment-groups",
        json={"mode": "uniform", "tooth_numbers": [12,13],
              "treatment_type": "veneer", "status": "planned"},
        headers=auth_headers,
    )
    gid = create.json()["data"][0]["treatment_group_id"]
    d = await client.delete(
        f"/api/v1/odontogram/treatment-groups/{gid}", headers=auth_headers,
    )
    assert d.status_code == 204

    listing = await client.get(
        f"/api/v1/odontogram/patients/{pid}/treatments?treatment_group_id={gid}",
        headers=auth_headers,
    )
    assert listing.json()["total"] == 0


async def test_list_filter_by_group(client, auth_headers, odontogram_setup):
    # crear grupo + un tratamiento individual
    # filtrar por group_id devuelve solo los 3 miembros del grupo
    ...


async def test_perform_group_emits_event_per_member(...):
    # Verificar que on_treatment_performed del treatment_plan se invoca N veces
    # (requiere setup de PlannedTreatmentItem linkeados)
    ...
```

### 9.2 Frontend

```typescript
// frontend/tests/unit/calculateToothRange.test.ts
describe('calculateToothRange', () => {
  it('expands upper arch range', () => {
    expect(calculateToothRange(14, 16)).toEqual([14, 15, 16])
  })
  it('crosses midline in upper arch', () => {
    expect(calculateToothRange(13, 23)).toEqual([13, 12, 11, 21, 22, 23])
  })
  it('throws on cross-arch range', () => {
    expect(() => calculateToothRange(14, 34)).toThrow('same_arch_required')
  })
  it('returns same result regardless of order', () => {
    expect(calculateToothRange(16, 14)).toEqual([14, 15, 16])
  })
})

describe('isSameArch', () => {
  it('true for upper only', () => expect(isSameArch([14, 23])).toBe(true))
  it('false mixing arches', () => expect(isSameArch([14, 34])).toBe(false))
})

describe('useTreatments group helpers', () => {
  it('getGroupMembers filters by group_id', () => {
    const { treatments, getGroupMembers } = useTreatments()
    treatments.value = [
      { id: '1', tooth_number: 14, treatment_group_id: 'G1' },
      { id: '2', tooth_number: 15, treatment_group_id: 'G1' },
      { id: '3', tooth_number: 22, treatment_group_id: null },
    ] as Treatment[]
    expect(getGroupMembers('G1').map(t => t.id)).toEqual(['1', '2'])
  })
})
```

---

## 10. Riesgos

| Riesgo | Mitigación |
|--------|------------|
| Eventos N emitidos al `perform_group` saturan al handler del plan | Ya es per-treatment hoy; mitigado. Si hay contención, agrupar en una transacción DB única (ya es el caso en `perform_group`). |
| Conflicto de `treatment_group_id` entre clientes simultáneos | UUID v4, probabilidad despreciable. |
| `splint`/`multiple_veneers` no en catálogo → sin precio | Fallback a constantes (ya existe en `useTreatmentCatalog`). Seeding de catálogo es tarea de producto separada. |
| Usuario intenta crear grupo encima de dientes con tratamiento existente | Comportamiento actual: se crea otro tratamiento. No bloqueamos. Futuro: validar conflicts. Fuera de alcance. |
| Re-render del SVG de conexiones con N grupos grandes | `computed` cacheado; N << 50 en la práctica. No medimos ahora. |

---

## Resumen

| Aspecto | v1 (rechazado) | v3 (este doc) |
|---------|----------------|---------------|
| Tabla nueva | `treatment_groups` | Ninguna |
| Columnas nuevas | 2 (`treatment_group_id`, `group_role`) | 1 (`treatment_group_id`) |
| Estado duplicado grupo/hijos | 4 campos | 0 |
| Endpoints nuevos | 6 | 3 + 1 filtro |
| Schemas nuevos | 3 | 1 (`TreatmentGroupCreate`) |
| Composables nuevos | 1 | 0 |
| Componentes nuevos | 1 popup modal + 1 confirm | 1 (`MultiToothConfirmPopup`, ~80 líneas) |
| Algoritmo FDI | Pendiente (cuadrant math) | Resuelto (2 arrays + slice) |
| Refactor oportunista | No | Sí (`performed_by_name`, `get_or_create_tooth_record`) |
| Alcance A2 (superficies inline) | Incluido | Diferido a PR propio |
| Tiempo estimado | 4-5 semanas | 5-6 días |
