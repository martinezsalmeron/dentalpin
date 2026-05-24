# Notas en citas — plan técnico

> Plan técnico ejecutable. Diseño aprobado en `~/.claude/plans/quiero-que-en-las-staged-scone.md`. Toca `clinical_notes`, `agenda`, `migration_import` y `core/events`. Una sola PR end-to-end.

## Resumen

- Extender el modelo polimórfico de `clinical_notes` con `owner_type='appointment'` + dos `note_type`: `appointment_clinical`, `appointment_administrative`.
- Eliminar el campo libre `Appointment.notes` (drop limpio — app no en prod).
- UI: feed único con badge por tipo dentro del `AppointmentModal`, vía slot `appointment.detail.notes`.
- Migración Gesdén/DPMF: rutear `payload.notes` a `ClinicalNote(appointment_administrative)` siguiendo el patrón del commit `191c884`.

## Invariantes que no se rompen

- `agenda` no importa nada de `clinical_notes` (ni backend ni frontend). Integración por slot + permisos compartidos (precedente: `PATCH /appointment-treatments/{id}` ya usa `clinical_notes.notes.write`).
- `clinical_notes.manifest.depends` ya incluye `agenda` — importar `Appointment` desde clinical_notes es legal.
- No se crean tablas, módulos ni dependencias nuevas.
- Sin FK físico clinical_notes.owner_id → appointments.id (sigue patrón polimórfico actual).

---

## Orden de ejecución

### Bloque A — Backend `clinical_notes`

#### A1. `models.py` — constantes + CHECKs

Archivo: `backend/app/modules/clinical_notes/models.py`

Cambios:

- Líneas 46–62: añadir constantes y ampliar tuplas.
  ```python
  NOTE_TYPE_APPOINTMENT_CLINICAL = "appointment_clinical"
  NOTE_TYPE_APPOINTMENT_ADMINISTRATIVE = "appointment_administrative"
  NOTE_TYPES = (
      NOTE_TYPE_ADMINISTRATIVE,
      NOTE_TYPE_DIAGNOSIS,
      NOTE_TYPE_TREATMENT,
      NOTE_TYPE_TREATMENT_PLAN,
      NOTE_TYPE_APPOINTMENT_CLINICAL,
      NOTE_TYPE_APPOINTMENT_ADMINISTRATIVE,
  )
  NOTE_OWNER_APPOINTMENT = "appointment"
  NOTE_OWNER_TYPES = (
      NOTE_OWNER_PATIENT,
      NOTE_OWNER_TREATMENT,
      NOTE_OWNER_PLAN,
      NOTE_OWNER_APPOINTMENT,
  )
  ```

- Líneas 100–116 (`__table_args__`): ampliar los 3 CHECKs.
  ```python
  CheckConstraint(
      "note_type IN ('administrative', 'diagnosis', 'treatment', "
      "'treatment_plan', 'appointment_clinical', 'appointment_administrative')",
      name="ck_clinical_notes_note_type",
  ),
  CheckConstraint(
      "owner_type IN ('patient', 'treatment', 'plan', 'appointment')",
      name="ck_clinical_notes_owner_type",
  ),
  CheckConstraint(
      "(note_type = 'administrative' AND owner_type = 'patient' AND tooth_number IS NULL) "
      "OR (note_type = 'diagnosis' AND owner_type = 'patient') "
      "OR (note_type = 'treatment' AND owner_type = 'treatment' AND tooth_number IS NULL) "
      "OR (note_type = 'treatment_plan' AND owner_type = 'plan' AND tooth_number IS NULL) "
      "OR (note_type = 'appointment_clinical' AND owner_type = 'appointment' AND tooth_number IS NULL) "
      "OR (note_type = 'appointment_administrative' AND owner_type = 'appointment' AND tooth_number IS NULL)",
      name="ck_clinical_notes_type_owner_matrix",
  ),
  ```

#### A2. `service.py` — resolver de appointment + event map

Archivo: `backend/app/modules/clinical_notes/service.py`

- Imports: añadir `from app.modules.agenda.models import Appointment` (legal por `depends`).
- Tras `_resolve_plan_owner` (línea ~118), añadir:
  ```python
  async def _resolve_appointment_owner(
      db: AsyncSession, clinic_id: UUID, appointment_id: UUID
  ) -> tuple[UUID, UUID]:
      result = await db.execute(
          select(Appointment.id, Appointment.patient_id).where(
              Appointment.id == appointment_id,
              Appointment.clinic_id == clinic_id,
          )
      )
      row = result.first()
      if row is None or row[1] is None:
          raise NoteOwnerError(f"appointment {appointment_id} not found or unbound")
      return row[0], row[1]
  ```
  Nota: la cita debe tener `patient_id` no nulo. Si no lo tiene (cita de bloqueo), no se permite nota.

- Ampliar `resolve_owner_patient` (líneas 134–149): añadir rama `appointment`.
  ```python
  if owner_type == NOTE_OWNER_APPOINTMENT:
      _, patient_id = await _resolve_appointment_owner(db, clinic_id, owner_id)
      return patient_id
  ```

- `_NOTE_TYPE_TO_EVENT` (líneas 76–81): añadir dos entradas.
  ```python
  NOTE_TYPE_APPOINTMENT_CLINICAL: EventType.CLINICAL_NOTE_APPOINTMENT_CLINICAL_CREATED,
  NOTE_TYPE_APPOINTMENT_ADMINISTRATIVE: EventType.CLINICAL_NOTE_APPOINTMENT_ADMINISTRATIVE_CREATED,
  ```

#### A3. `router.py` + `schemas.py` — regex

- `backend/app/modules/clinical_notes/schemas.py:21` — actualizar `NOTE_OWNER_PATTERN`:
  ```python
  NOTE_OWNER_PATTERN = "^(patient|treatment|plan|appointment)$"
  ```
- `backend/app/modules/clinical_notes/router.py:48` — actualizar `ATTACHMENT_OWNER_PATTERN`:
  ```python
  ATTACHMENT_OWNER_PATTERN = "^(patient|treatment|plan|appointment|clinical_note)$"
  ```
- Si hay `Literal[...]` para `note_type` en `schemas.py`, añadir los 2 nuevos valores.

#### A4. `owner_resolvers.py` — media registry

Archivo: `backend/app/modules/clinical_notes/owner_resolvers.py`

- Añadir resolver privado `_resolve_appointment(db, clinic_id, appointment_id) → UUID | None` siguiendo molde de `_resolve_treatment`. Importar `Appointment` igual que en service.
- En `register()` (líneas 81–93), añadir `OwnerSpec(owner_type="appointment", resolver=_resolve_appointment, label="Cita")`.
- En `_resolve_clinical_note` (líneas 59–78), añadir rama `if note_owner_type == "appointment": return await _resolve_appointment(...)`. Necesario para que adjuntos en notas de cita resuelvan al paciente.

#### A5. `_VALID_ATTACHMENT_OWNER_TYPES`

Ya es `(*NOTE_OWNER_TYPES, "clinical_note")` (línea 58 de service según report) → al ampliar `NOTE_OWNER_TYPES` queda hecho. Verificar.

#### A6. Alembic — `cn_0003_appointment_owner.py`

Archivo nuevo: `backend/app/modules/clinical_notes/migrations/versions/cn_0003_appointment_owner.py`

```python
"""Add appointment owner type to clinical_notes.

Revision ID: cn_0003
Revises: cn_0002
Create Date: 2026-05-24
"""
from collections.abc import Sequence

from alembic import op

revision: str = "cn_0003"
down_revision: str | None = "cn_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint("ck_clinical_notes_note_type", "clinical_notes", type_="check")
    op.create_check_constraint(
        "ck_clinical_notes_note_type",
        "clinical_notes",
        "note_type IN ('administrative', 'diagnosis', 'treatment', "
        "'treatment_plan', 'appointment_clinical', 'appointment_administrative')",
    )

    op.drop_constraint("ck_clinical_notes_owner_type", "clinical_notes", type_="check")
    op.create_check_constraint(
        "ck_clinical_notes_owner_type",
        "clinical_notes",
        "owner_type IN ('patient', 'treatment', 'plan', 'appointment')",
    )

    op.drop_constraint("ck_clinical_notes_type_owner_matrix", "clinical_notes", type_="check")
    op.create_check_constraint(
        "ck_clinical_notes_type_owner_matrix",
        "clinical_notes",
        "(note_type = 'administrative' AND owner_type = 'patient' AND tooth_number IS NULL) "
        "OR (note_type = 'diagnosis' AND owner_type = 'patient') "
        "OR (note_type = 'treatment' AND owner_type = 'treatment' AND tooth_number IS NULL) "
        "OR (note_type = 'treatment_plan' AND owner_type = 'plan' AND tooth_number IS NULL) "
        "OR (note_type = 'appointment_clinical' AND owner_type = 'appointment' AND tooth_number IS NULL) "
        "OR (note_type = 'appointment_administrative' AND owner_type = 'appointment' AND tooth_number IS NULL)",
    )


def downgrade() -> None:
    op.drop_constraint("ck_clinical_notes_type_owner_matrix", "clinical_notes", type_="check")
    op.create_check_constraint(
        "ck_clinical_notes_type_owner_matrix",
        "clinical_notes",
        "(note_type = 'administrative' AND owner_type = 'patient' AND tooth_number IS NULL) "
        "OR (note_type = 'diagnosis' AND owner_type = 'patient') "
        "OR (note_type = 'treatment' AND owner_type = 'treatment' AND tooth_number IS NULL) "
        "OR (note_type = 'treatment_plan' AND owner_type = 'plan' AND tooth_number IS NULL)",
    )
    op.drop_constraint("ck_clinical_notes_owner_type", "clinical_notes", type_="check")
    op.create_check_constraint(
        "ck_clinical_notes_owner_type",
        "clinical_notes",
        "owner_type IN ('patient', 'treatment', 'plan')",
    )
    op.drop_constraint("ck_clinical_notes_note_type", "clinical_notes", type_="check")
    op.create_check_constraint(
        "ck_clinical_notes_note_type",
        "clinical_notes",
        "note_type IN ('administrative', 'diagnosis', 'treatment', 'treatment_plan')",
    )
```

---

### Bloque B — Eventos

Archivo: `backend/app/core/events/types.py` (tras línea 170).

```python
CLINICAL_NOTE_APPOINTMENT_CLINICAL_CREATED = "clinical_notes.appointment_clinical_created"
CLINICAL_NOTE_APPOINTMENT_ADMINISTRATIVE_CREATED = "clinical_notes.appointment_administrative_created"
```

`patient_timeline/events.py:631-662` (`on_clinical_note_created`) ya construye el string `f"clinical_notes.{note_type}_created"` → los eventos se grabarán automáticamente sin tocar el módulo. Verificar suscripción si los maneja por nombre concreto; si no, añadir suscripción en el dispatch map.

---

### Bloque C — Backend `agenda` (drop legacy)

#### C1. Modelo

`backend/app/modules/agenda/models.py:110` — eliminar:
```python
notes: Mapped[str | None] = mapped_column(Text, nullable=True)
```

#### C2. Schemas

`backend/app/modules/agenda/schemas.py`:
- Línea 147 (`AppointmentCreate`): eliminar `notes: str | None = None`
- Línea 162 (`AppointmentUpdate`): eliminar `notes: str | None = None`
- Línea 272 (`AppointmentResponse`): eliminar `notes: str | None`

#### C3. Service

`backend/app/modules/agenda/service.py`:
- Línea 686 (payload de `transition()`): eliminar `"notes": appointment.notes,`
- `update_appointment()` (líneas 544–546): el loop `setattr(appointment, key, value)` ya no recibirá `notes` porque sale del schema. Sin cambios adicionales necesarios.

#### C4. Alembic — `ag_0005_drop_appointment_notes.py`

```python
"""Drop legacy Appointment.notes (moved to clinical_notes).

Revision ID: ag_0005
Revises: ag_0004
Create Date: 2026-05-24
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "ag_0005"
down_revision: str | None = "ag_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_column("appointments", "notes")


def downgrade() -> None:
    op.add_column("appointments", sa.Column("notes", sa.Text(), nullable=True))
```

#### C5. Tipo TypeScript

`frontend/app/types/index.ts:250` — eliminar `notes?: string` del interface `Appointment`.

---

### Bloque D — Frontend `agenda` (AppointmentModal)

Archivo: `backend/app/modules/agenda/frontend/components/clinical/AppointmentModal.vue`

#### D1. Script

- Línea 62 (`formData`): eliminar `notes: ''`.
- Línea 274 (carga en edit): eliminar `formData.notes = apt.notes || ''`.
- Línea 481 (save payload): eliminar `notes: formData.notes || undefined`.
- Añadir en setup:
  ```typescript
  const { resolve } = useModuleSlots()
  const appointmentNotesSlot = computed(() =>
    appointmentId.value
      ? resolve('appointment.detail.notes', {
          appointmentId: appointmentId.value,
          patientId: formData.patientId,
        })
      : []
  )
  ```
  Adaptar `appointmentId` y `formData.patientId` a los nombres reales del state local del modal (revisar al implementar; el modal ya tiene `appointmentId` reactivo para edit mode).

#### D2. Template

- Reemplazar bloque líneas 756–777 (sección "Notas") por:
  ```vue
  <!-- Section 4: Notas (slot — provided by clinical_notes module) -->
  <div v-if="appointmentId" class="space-y-2">
    <h4 class="flex items-center gap-2 text-caption uppercase tracking-wide text-subtle">
      <UIcon name="i-lucide-sticky-note" class="w-3.5 h-3.5" />
      {{ t('appointments.notesTitle') }}
    </h4>
    <div v-if="appointmentNotesSlot.length === 0" class="text-xs text-subtle">
      {{ t('appointments.notesEmptyHint') }}
    </div>
    <component
      v-for="entry in appointmentNotesSlot"
      :is="entry.component"
      :key="entry.id"
    />
  </div>
  ```
  El slot no se muestra al crear (no hay `appointmentId` todavía). Si el modal soporta "crear + guardar y luego ver notas", el usuario debe guardar primero. Documentar en i18n hint.

---

### Bloque E — Frontend `clinical_notes` (panel + registro de slot)

#### E1. Componente nuevo `AppointmentNotesPanel.vue`

Path: `backend/app/modules/clinical_notes/frontend/components/AppointmentNotesPanel.vue`

Responsabilidad:
- Recibe `appointmentId` y opcionalmente `patientId` por contexto del slot.
- Estado local: `selectedType` (`appointment_clinical` por defecto), `body`, lista cargada.
- Llama a `useApi`:
  - `GET /api/v1/clinical_notes/notes?owner_type=appointment&owner_id={appointmentId}` para listar.
  - `POST /api/v1/clinical_notes/notes` con `{owner_type:'appointment', owner_id, note_type, body}` para crear.
  - `PATCH /notes/{id}` y `DELETE /notes/{id}` para editar/soft-delete.
- Render: selector de tipo + `NoteComposer` (pasándole `noteType` dinámico) arriba, lista cronológica descendente con `NoteCard` debajo, con `badge` parametrizado por `note_type`.
- Permisos: si `can('clinical_notes.notes.write')` → muestra composer; si sólo `read` → sólo lista.

#### E2. Slots plugin de clinical_notes

Path: `backend/app/modules/clinical_notes/frontend/plugins/slots.client.ts` (crear o ampliar):

```typescript
import { defineAsyncComponent } from 'vue'
import { registerSlot } from '~~/app/composables/useModuleSlots'

export default defineNuxtPlugin(() => {
  registerSlot('appointment.detail.notes', {
    id: 'clinical_notes.appointment.detail.notesPanel',
    component: defineAsyncComponent(
      () => import('../components/AppointmentNotesPanel.vue')
    ),
    order: 10,
    permission: 'clinical_notes.notes.read',
  })
})
```

#### E3. `NoteCard.vue` — colores

Verificar el map de colores por `note_type`. Añadir entradas para `appointment_clinical` (reutilizar palette de diagnosis u otro distinguible) y `appointment_administrative` (reutilizar palette de administrative). Sin nuevos colores hard-coded fuera del map.

#### E4. `RecentNotesFeed.vue` — filtros

Si el feed de paciente expone filtros por tipo, añadir los 2 nuevos. Ubicación: `clinical_notes/frontend/components/RecentNotesFeed.vue` (`ALL_SOURCES` o equivalente).

---

### Bloque F — `migration_import` (DPMF → ClinicalNote)

Archivo: `backend/app/modules/migration_import/mappers/appointment.py`

Patrón: copia del `AppliedTreatmentMapper._record_non_clinical_note()` (líneas 727–789), adaptado.

Cambios:

- Import: `from app.modules.clinical_notes.models import ClinicalNote` (manifest ya declara `clinical_notes` en depends).
- Tras línea 138 (`appointment = await AppointmentService.create_appointment(...)`), añadir:
  ```python
  notes_body = (payload.get("notes") or "").strip()
  note_canonical = f"{canonical_uuid}:note"
  if notes_body and not await ctx.resolver.was_skipped("appointment_note", note_canonical):
      existing_note = await ctx.resolver.get("appointment_note", note_canonical)
      if existing_note is None:
          author_id = professional_id or ctx.created_by
          note = ClinicalNote(
              clinic_id=ctx.clinic_id,
              note_type="appointment_administrative",
              owner_type="appointment",
              owner_id=appointment.id,
              tooth_number=None,
              body=notes_body,
              author_id=author_id,
              created_at=appointment.created_at,
              updated_at=appointment.created_at,
          )
          ctx.db.add(note)
          await ctx.db.flush()
          await ctx.resolver.set(
              entity_type="appointment_note",
              canonical_uuid=note_canonical,
              source_system=source_system,
              dentalpin_table="clinical_notes",
              dentalpin_id=note.id,
          )
  elif not notes_body:
      await ctx.resolver.mark_skipped("appointment_note", note_canonical, source_system)
  ```
- Decisión: tipo por defecto = `appointment_administrative` (decisión usuario).
- Idempotencia: `resolver.get` + `resolver.was_skipped` antes de insertar; `resolver.set` después. Mismo patrón que `applied_treatment.py`.

---

### Bloque G — Tests

#### G1. `tests/modules/clinical_notes/test_appointment_owner.py` (nuevo)

Casos:
- `test_create_appointment_clinical_note_ok`: POST con `owner_type=appointment`, `note_type=appointment_clinical` → 201.
- `test_create_appointment_administrative_note_ok`.
- `test_create_with_invalid_combo_raises`: `note_type=appointment_clinical` + `owner_type=patient` → 422.
- `test_create_for_unbound_appointment_raises`: cita sin `patient_id` → 422.
- `test_create_cross_clinic_isolation`: cita de clínica B desde clínica A → 422.
- `test_list_filters_by_owner_appointment`.
- `test_resolve_owner_patient_via_appointment` (unit del service).
- `test_attachment_owner_appointment_resolves_to_patient` (unit del media registry).
- `test_event_published_on_create` (mock event_bus, assert tipo `CLINICAL_NOTE_APPOINTMENT_CLINICAL_CREATED`).

Reutilizar fixtures `db_session`, `client`, `auth_headers`, `clinic_factory`, `patient_factory`. Si no existe, crear `appointment_factory` mínimo o llamar al endpoint para crear cita.

#### G2. `tests/modules/agenda/test_appointment_notes_removed.py` (nuevo)

- `test_create_appointment_rejects_notes_field`: POST `/appointments` con `notes` en body → 422 (Pydantic extra forbidden si está activo; si no, 200 e ignorado — adaptar según `Config`).
- `test_appointment_response_has_no_notes_key`: GET `/appointments/{id}` no incluye clave `notes`.

#### G3. `tests/modules/migration_import/test_appointment_notes_routing.py` (nuevo)

Copiar estructura de `tests/modules/migration_import/test_applied_treatment_non_clinical_note.py`. Casos:
- `test_appointment_with_notes_creates_clinical_note`: payload con `notes` no vacío → 1 ClinicalNote `appointment_administrative` con `owner_id=appointment.id`.
- `test_appointment_without_notes_no_clinical_note`.
- `test_reimport_is_idempotent`: ejecutar 2× con mismo `canonical_uuid` → 1 sola nota.
- `test_author_id_from_professional`: si payload trae `professional_uuid` resoluble → `note.author_id = professional.id`.
- `test_author_id_fallback_to_created_by`: si no se puede resolver profesional → `note.author_id = ctx.created_by`.

#### G4. Smoke frontend (manual)

- Crear cita → guardar → reabrir → crear nota clínica → ver en feed del modal → ver en feed del paciente (filtro `appointment_clinical`).
- Importar dump DPMF con `notes` poblado en una cita → verificar ClinicalNote `appointment_administrative` creada y visible en feed del paciente.

---

### Bloque H — Docs + i18n + catálogos

#### H1. CHANGELOGs (`## Unreleased`)

- `backend/app/modules/agenda/CHANGELOG.md` — entrada: drop `Appointment.notes`, slot `appointment.detail.notes` añadido.
- `backend/app/modules/clinical_notes/CHANGELOG.md` — entrada: nuevo `owner_type='appointment'` + 2 `note_type` + 2 eventos.
- `backend/app/modules/migration_import/CHANGELOG.md` — entrada: appointment notes → ClinicalNote(appointment_administrative).

#### H2. Docs técnicas

- `docs/technical/clinical_notes/overview.md` — añadir fila `appointment` a la matriz.
- `docs/technical/clinical_notes/events.md` — 2 eventos nuevos.
- `docs/technical/clinical_notes/permissions.md` — confirmar reuso de `notes.read/write`.
- `docs/technical/agenda/events.md` — sin cambios (no se publica desde agenda).
- `docs/user-manual/en/agenda/screens/appointment-modal.md` + `es/` — actualizar sección notas con feed + tipos.
- Bump `last_verified_commit` en los screen MDs tocados.

#### H3. Catálogos

```bash
python backend/scripts/generate_catalogs.py
```

#### H4. i18n

`frontend/i18n/locales/en.json` + `es.json`:
- Eliminar `appointments.notes`, `appointments.notesPlaceholder`.
- Añadir:
  - `appointments.notesTitle` ("Notes" / "Notas")
  - `appointments.notesEmptyHint` ("Save the appointment to add notes." / "Guarda la cita para añadir notas.")
- En clinical_notes layer i18n (si existe), añadir labels para los 2 nuevos tipos:
  - `clinicalNotes.types.appointment_clinical` ("Clinical" / "Clínica")
  - `clinicalNotes.types.appointment_administrative` ("Administrative" / "Administrativa")

---

## Verificación end-to-end

```bash
# 1. Migraciones aplican
docker-compose exec backend alembic upgrade heads

# 2. Reset + reseed (datos dev se pierden, asumido por decisión)
./scripts/reset-db.sh && ./scripts/seed-demo.sh

# 3. Tests
docker-compose exec backend python -m pytest tests/modules/clinical_notes/test_appointment_owner.py -v
docker-compose exec backend python -m pytest tests/modules/agenda/test_appointment_notes_removed.py -v
docker-compose exec backend python -m pytest tests/modules/migration_import/test_appointment_notes_routing.py -v
docker-compose exec backend python -m pytest -v

# 4. Lint
cd backend && ruff check . && ruff format --check .
cd frontend && npm run lint
```

Checklist funcional (manual, en navegador):
1. Login como dentist → abrir cita existente → crear nota clínica → aparece en feed del modal.
2. Cambiar tipo a "Administrativa" → crear → aparece con badge distinto.
3. Soft-delete propia nota → desaparece del feed.
4. Login como receptionist → puede crear nota administrativa (permiso `notes.write` ya concedido).
5. Abrir ficha del paciente de esa cita → `RecentNotesFeed` muestra las notas con filtro `appointment_clinical`/`appointment_administrative`.
6. Adjuntar archivo a una nota de cita → galería del paciente lo lista.
7. Ejecutar import DPMF de prueba con `appointment.notes` → ClinicalNote(appointment_administrative) creada; re-import no duplica.
8. POST `/api/v1/appointments` con `notes` en body → falla validación (campo no existe).

---

## Riesgos y mitigaciones

| Riesgo | Mitigación |
|--------|-----------|
| Citas legacy de bloqueo (sin `patient_id`) → notas imposibles | `_resolve_appointment_owner` lanza si `patient_id` IS NULL. Documentado. |
| Cita borrada deja notas huérfanas | Agenda no hard-deletea hoy. Fuera de scope; TODO en CHANGELOG. |
| Cross-module FK física | NO se crea (patrón polimórfico). CI ok. |
| `patient_timeline` no escucha eventos nuevos | El dispatcher actual reconstruye el nombre del evento por convención (`clinical_notes.{note_type}_created`). Verificar al implementar; si requiere subscripción explícita, añadir 2 líneas en el module init. |
| `useModuleSlots` no expone `appointment.detail.notes` antes de guardar | Render condicional `v-if="appointmentId"`. Hint i18n explica al usuario. |
| Ruff/Format/CI docs layout | Pasar `scripts/check_docs_layout.py` localmente; el doc vive en `docs/technical/` (carpeta legal). |

---

## Decisiones (recap del plan de diseño)

| Fork | Elección |
|------|----------|
| Campo legacy `Appointment.notes` | Drop limpio sin backfill. Reset de dev. |
| Tipo por defecto al importar DPMF | `appointment_administrative` |
| UI | Feed único con badge por tipo + composer con selector |

---

## Archivos tocados (resumen)

Backend:
- `backend/app/modules/clinical_notes/models.py`
- `backend/app/modules/clinical_notes/schemas.py`
- `backend/app/modules/clinical_notes/service.py`
- `backend/app/modules/clinical_notes/router.py`
- `backend/app/modules/clinical_notes/owner_resolvers.py`
- `backend/app/modules/clinical_notes/migrations/versions/cn_0003_appointment_owner.py` *(nuevo)*
- `backend/app/modules/agenda/models.py`
- `backend/app/modules/agenda/schemas.py`
- `backend/app/modules/agenda/service.py`
- `backend/app/modules/agenda/migrations/versions/ag_0005_drop_appointment_notes.py` *(nuevo)*
- `backend/app/modules/migration_import/mappers/appointment.py`
- `backend/app/core/events/types.py`

Frontend:
- `backend/app/modules/agenda/frontend/components/clinical/AppointmentModal.vue`
- `backend/app/modules/clinical_notes/frontend/components/AppointmentNotesPanel.vue` *(nuevo)*
- `backend/app/modules/clinical_notes/frontend/plugins/slots.client.ts` *(nuevo o ampliado)*
- `backend/app/modules/clinical_notes/frontend/components/NoteCard.vue` (map colores)
- `backend/app/modules/clinical_notes/frontend/components/RecentNotesFeed.vue` (filtros)
- `frontend/app/types/index.ts`
- `frontend/i18n/locales/en.json`
- `frontend/i18n/locales/es.json`

Tests:
- `backend/tests/modules/clinical_notes/test_appointment_owner.py` *(nuevo)*
- `backend/tests/modules/agenda/test_appointment_notes_removed.py` *(nuevo)*
- `backend/tests/modules/migration_import/test_appointment_notes_routing.py` *(nuevo)*

Docs/CHANGELOG:
- `backend/app/modules/{agenda,clinical_notes,migration_import}/CHANGELOG.md`
- `docs/technical/clinical_notes/{overview,events,permissions}.md`
- `docs/user-manual/{en,es}/agenda/screens/appointment-modal.md`
- (este archivo: `docs/technical/appointment-notes.md`)
