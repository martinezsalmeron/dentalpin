# Plan Técnico: Tratamientos Globales y Reorder del Plan

**Fecha:** 2026-04-18
**Estado:** Listo para ejecutar
**Documento de diseño:** [`treatment-addition.md`](../features/treatment-addition.md) v2

---

## 0. Resumen ejecutivo

Dos entregables:

- **G — Tratamientos globales** (`global_mouth`, `global_arch`) como ciudadanos de primera clase del modelo, catálogo, plan y odontograma.
- **R — Reorder** de items del plan con drag & drop (ratón + teclado).

Sin datos en producción: se redefinen enums limpiamente. Se entrega en **7 PRs pequeños** (3 backend + 4 frontend) con dependencias explícitas.

---

## 1. Estado inicial (verificado en el código)

- `backend/app/modules/odontogram/models.py::Treatment` **no tiene** `scope` ni `arch`. El concepto `mode` vive solo en `schemas.py` (`single | bridge | uniform`) y guía la construcción en servicio.
- `TreatmentTooth` **ya es opcional** a nivel DB (no hay constraint de count ≥ 1). La creación de treatments sin dientes ya está permitida por schema (comentario explícito en `TreatmentCreate.validate_shape`).
- `backend/app/modules/catalog/models.py::TreatmentCatalogItem.treatment_scope` usa strings `surface` / `whole_tooth`.
- `backend/app/modules/catalog/seed.py` tiene ~30 items con `whole_tooth` / `surface`. Sin globales.
- `PlannedTreatmentItem.sequence_order` existe. El endpoint para reordenar **no existe**.
- Frontend **no tiene** librería de drag & drop (`package.json` revisado). Decisión en §2.1.

---

## 2. Decisiones transversales previas

### 2.1 Librería de drag & drop

**Decisión:** `vue-draggable-plus` (activa, mantenida, tipos TS, API Vue 3 compositional).

Alternativas evaluadas:
- HTML5 nativo: funciona pero boilerplate excesivo (ghost, drop indicator, focus mgmt). Evitar.
- `vuedraggable`: basada en SortableJS pero estancada en Vue 3. Evitar.

Añadir a `frontend/package.json`:
```
"vue-draggable-plus": "^0.5.x"
```

Importación con tree-shaking:
```ts
import { VueDraggable } from 'vue-draggable-plus'
```

### 2.2 Nombres finales de enum `scope`

**Treatment.scope** y **TreatmentCatalogItem.treatment_scope** comparten los 4 valores:

```
tooth          → 0..1 TreatmentTooth, surfaces opcional dentro
multi_tooth    → 2..N TreatmentTooth, role opcional (pillar/pontic/cantilever)
global_mouth   → 0 TreatmentTooth
global_arch    → 0 TreatmentTooth, arch = upper | lower (NOT NULL)
```

El schema `TreatmentCreate.mode` se **elimina** — se deriva de `scope` en el servidor.

### 2.3 Regla de borrado de `Treatment` huérfano

Encapsulada en `TreatmentPlanService.remove_item`. Al quitar un `PlannedTreatmentItem`:

1. ¿`Treatment` referenciado por otro `PlannedTreatmentItem` activo? → no tocar.
2. ¿Huérfano + `status == 'planned'`? → `delete_treatment()` (soft delete).
3. ¿Huérfano + `status == 'performed'`? → mantener (historia clínica).

---

## 3. PRs

### PR 1 · Backend — `scope` / `arch` en Treatment y catálogo (base)

**Objetivo:** redefinir enums limpios. Bloqueante para todo lo demás.

**Archivos:**
- `backend/app/modules/odontogram/models.py`
  - `Treatment`: añadir `scope: Mapped[str]` (4 valores), `arch: Mapped[str | None]`.
  - Check constraint: `scope == 'global_arch' → arch IS NOT NULL`. Resto `arch IS NULL`.
- `backend/app/modules/catalog/models.py`
  - `TreatmentCatalogItem.treatment_scope` cambia valores válidos a los 4 nuevos. Mantener tipo `String`, validar en schemas.
- `backend/app/modules/odontogram/schemas.py`
  - `TreatmentCreate`: eliminar `mode`. Añadir `scope` (default derivable) y `arch`.
  - `validate_shape`:
    - `scope == 'tooth'`: teeth count ≤ 1.
    - `scope == 'multi_tooth'`: teeth count ≥ 2.
    - `scope == 'global_mouth'`: teeth vacío, arch vacío.
    - `scope == 'global_arch'`: teeth vacío, arch requerido.
  - Si cliente no envía `scope`, derivar: 0 teeth → error (pedir scope), 1 → `tooth`, 2+ → `multi_tooth`. Los globales siempre requieren `scope` explícito.
  - `TreatmentResponse`: exponer `scope` y `arch`.
- `backend/app/modules/catalog/schemas.py`
  - Literal de `treatment_scope` a `tooth | multi_tooth | global_mouth | global_arch`.
- `backend/app/modules/odontogram/service.py`
  - `TreatmentService.create_treatment`: reemplazar lógica basada en `mode` por lógica basada en `scope`. Bridge → `multi_tooth` + role auto. Uniform → `multi_tooth` sin roles. Globals → saltar lógica de teeth.
  - `build_treatment_response`: incluir `scope` y `arch`.
- Alembic migration nueva (única): `add_scope_and_arch_to_treatments`
  - `ALTER TABLE treatments ADD COLUMN scope VARCHAR(20) NOT NULL DEFAULT 'tooth'`. Luego quitar default.
  - `ALTER TABLE treatments ADD COLUMN arch VARCHAR(10) NULL`.
  - Add check constraint.
  - No rehacer `TreatmentTooth` (ya es opcional).
  - Catalog: no cambia columna, pero añadir check constraint en `treatment_scope` con los 4 valores nuevos (opcional: usar un tipo Enum si Postgres, o CHECK `scope IN (...)`).

**Tests:**
- `tests/test_treatments.py` (nuevo o ampliado):
  - `create_tooth_treatment` (1 diente + surfaces).
  - `create_multi_tooth_bridge` (con roles auto).
  - `create_multi_tooth_uniform` (carillas).
  - `create_global_mouth_treatment` (cero dientes).
  - `create_global_arch_treatment` (cero dientes + arch).
  - `reject_global_arch_without_arch`.
  - `reject_tooth_scope_with_two_teeth`.
  - `reject_multi_tooth_with_one_tooth`.

**Criterio de aceptación:**
- `ruff check`, `ruff format --check`, `pytest` verdes.
- `GET /patients/{id}/treatments` devuelve `scope` y `arch`.
- `POST /patients/{id}/treatments` acepta `scope: global_mouth` y `scope: global_arch` con validaciones.

---

### PR 2 · Backend — endpoint reorder items del plan

**Objetivo:** reordenación atómica, un round-trip.

**Archivos:**
- `backend/app/modules/treatment_plan/schemas.py`
  - `ReorderItemsRequest { item_ids: list[UUID] }`.
- `backend/app/modules/treatment_plan/service.py`
  - `TreatmentPlanService.reorder_items(db, clinic_id, plan_id, item_ids)`:
    - Valida que `plan_id` existe y pertenece a la clínica.
    - Valida que `set(item_ids) == set(current_item_ids_of_plan)` (todos los items del plan, sin faltar ni sobrar).
    - Actualiza `sequence_order` según el orden de `item_ids` (`0, 1, 2, …`).
    - Una sola transacción.
- `backend/app/modules/treatment_plan/router.py`
  - `PATCH /treatment-plans/{plan_id}/items/reorder`
  - Permission: `treatment_plan.items.write`.
  - Response: `ApiResponse[TreatmentPlanDetailResponse]` (el plan completo actualizado, evita re-fetch en cliente).

**Tests:**
- `tests/test_treatment_plans.py`:
  - `reorder_items_happy_path` (3 items, invertir orden).
  - `reorder_items_rejects_missing_item`.
  - `reorder_items_rejects_foreign_item`.
  - `reorder_items_persists_across_fetch`.

**Criterio de aceptación:** plan devuelto con `items` en el orden pedido; persiste.

---

### PR 3 · Backend — seeder de catálogo con globales

**Objetivo:** el catálogo por defecto refleja la taxonomía real.

**Archivos:**
- `backend/app/modules/catalog/seed.py`
  - Reemplazar todos los `"treatment_scope": "whole_tooth"` por `"tooth"` y `"surface"` por `"tooth"` con `"requires_surfaces": True`.
  - Añadir bloque de globales:
    ```python
    {
      "internal_code": "cleaning",
      "names": {"es": "Limpieza dental", "en": "Dental cleaning"},
      "treatment_scope": "global_mouth",
      "default_price": 60,
      "pricing_strategy": "flat",
      "requires_surfaces": False,
      ...
    }
    ```
  - Globales a incluir mínimo: limpieza, blanqueamiento, fluorización, revisión, férula de descarga superior, férula de descarga inferior.
  - Para férula de descarga: `treatment_scope: "global_arch"` + un campo hint `default_arch` si se quiere autoseleccionar (opcional).
- `scripts/reset-db.sh` ya aplica seeder al final; verificar.

**Tests:**
- `tests/test_catalog_seed.py`:
  - `seed_creates_global_items`.
  - `seed_items_have_valid_treatment_scope`.

**Criterio de aceptación:** tras `./scripts/reset-db.sh`, `GET /catalog/items?treatment_scope=global_mouth` devuelve ≥ 4 items.

**Depende de:** PR 1.

---

### PR 4 · Frontend — tipos y composables

**Objetivo:** cimiento frontend. Sin cambios visibles.

**Archivos:**
- `frontend/app/types/index.ts`
  - `Treatment.scope: 'tooth' | 'multi_tooth' | 'global_mouth' | 'global_arch'`.
  - `Treatment.arch: 'upper' | 'lower' | null`.
  - `TreatmentCatalogItem.treatment_scope` al mismo literal.
- `frontend/app/composables/useTreatments.ts`
  - `createTreatment` acepta `scope` y `arch`, elimina `mode`. Deriva `scope` en llamadas actuales (1 diente → `tooth`, N → `multi_tooth`) para no romper callers existentes en este PR.
  - Helper `createGlobalTreatment(catalogItemId, scope, arch?)`.
- `frontend/app/composables/useTreatmentPlans.ts`
  - `reorderItems(planId: string, itemIds: string[]): Promise<TreatmentPlanDetail>`.
  - Mutación optimista: reordenar lista local antes del PATCH; revertir si falla.
- `frontend/app/composables/useTreatmentCatalog.ts`
  - Exponer `globalItems: ComputedRef<TreatmentCatalogItem[]>` filtrando `treatment_scope in ['global_mouth','global_arch']`.
  - `byArchScope` split auxiliar.

**Tests:** `vitest` sobre composables (mock de `useApi`):
- `useTreatments.createTreatment.derivesScope`.
- `useTreatmentPlans.reorderItems.optimisticRollback`.

**Depende de:** PR 1, PR 2.

---

### PR 5 · Frontend — UI globales en `TreatmentBar`

**Objetivo:** añadir globales al plan en 1-2 clics.

**Archivos:**
- `frontend/app/components/odontogram/TreatmentBar.vue`
  - Nuevo toggle/sección **"Boca completa ▸"** junto a las categorías, solo visible cuando `mode === 'planning'`.
  - Al abrir: panel vertical flotante con `globalItems` agrupados en "Boca completa" y "Arcada".
  - Clic en item de boca completa → `useTreatments.createGlobalTreatment(id, 'global_mouth')` y linkeo al plan con `useTreatmentPlans.addItem`.
  - Clic en item de arcada → banner flotante sobre el odontograma con dos botones grandes "Superior" / "Inferior" → crea con `scope: 'global_arch', arch: <elegido>`.
  - Mismo pipeline de feedback (toast + emit `treatment-applied`).
- `frontend/app/components/odontogram/OdontogramChart.vue`
  - Prop nueva opcional: `showGlobalArchPicker: boolean` con emit `arch-selected`.
- i18n (`frontend/i18n/locales/es.json`, `en.json`):
  - `treatmentBar.wholeMouth`, `treatmentBar.arch`, `treatmentBar.upperArch`, `treatmentBar.lowerArch`.

**Tests manuales (QA):**
- Abrir plan vacío → "Boca completa ▸" → añadir limpieza → item aparece con icono 🌐 en la lista y subtotal actualiza.
- Férula superior: "Arcada" → "Superior" → item aparece con la arcada en el detalle.

**Depende de:** PR 4.

---

### PR 6 · Frontend — visualización de globales en odontograma

**Objetivo:** el dentista ve en el odontograma que el plan tiene globales, sin abrir la lista.

**Archivos:**
- `frontend/app/components/odontogram/OdontogramChart.vue`
  - Bajo el chart, renderizar una **cinta inferior** (`GlobalTreatmentsStrip`) con los treatments del plan actual con `scope in ['global_mouth','global_arch']`.
  - Cada global se muestra como chip con:
    - Icono del `catalog_item` (si existe) o `🌐`.
    - Nombre corto.
    - Badge de estado (`planned` vs `existing`) — reutilizar estilos existentes.
  - Hover del chip → emite `tooth-hover` con un identificador especial; en plan detail se ilumina el item correspondiente de la lista.
  - Para `global_arch`: además, pintar un halo sutil sobre la arcada afectada (capa SVG con bajo opacity).
  - Si la cinta está vacía, no ocupa espacio (`v-if`).
- Nuevo componente `GlobalTreatmentsStrip.vue` para encapsular.
- `PlanDetailView.vue`
  - Hover linking: aceptar IDs de globales en `highlightedItems` (no `toothNumber`).

**Tests manuales:**
- Plan con limpieza + férula superior → chart muestra cinta con 2 chips.
- Hover en chip de férula → halo en arcada superior.
- Hover en item de limpieza en la lista → chip de limpieza resaltado.

**Depende de:** PR 5.

---

### PR 7 · Frontend — drag & drop reorder

**Objetivo:** reordenar items del plan con ratón y teclado.

**Archivos:**
- `frontend/package.json` (+ `package-lock` o `pnpm-lock`):
  - `vue-draggable-plus` añadido.
- `frontend/app/components/treatment-plans/PlanTreatmentList.vue` (si no existe con ese nombre, buscar el componente que renderiza `plan.items` dentro de `PlanDetailView`):
  - Envolver la sección "Pendientes" en `<VueDraggable v-model="pendingItems" handle=".drag-handle" @end="onReorder">`.
  - Añadir handle `i-lucide-grip-vertical` a la izquierda de cada fila (clase `.drag-handle`, cursor grab).
  - `onReorder` llama a `useTreatmentPlans.reorderItems(planId, newOrderIds)`.
  - Mutación optimista ya incluida en composable (PR 4).
  - Animación de entrada/salida: CSS `transition-group` o las utilidades de la lib.
- Teclado:
  - Cada fila `tabindex="0"`. Al foco, tooltip "Alt+↑ / Alt+↓ para mover".
  - Handler teclado: `Alt+ArrowUp/Down` swap con vecino y disparar reorder.
- i18n:
  - `treatmentPlans.reorderHint`, `treatmentPlans.dragToReorder`.

**Tests (vitest + E2E manual):**
- Unitario del handler de teclado (swap de array).
- Manual: drag item 3 → pos 1, recargar, orden persiste.
- Manual: foco en item 2, `Alt+↓`, recargar, orden persiste.
- Drag no afecta a completados.

**Depende de:** PR 4.

---

## 4. Orden de ejecución y paralelización

```
PR 1 (backend base scope+arch)  ──┬──▶ PR 3 (seed globales)
                                  ├──▶ PR 4 (frontend tipos+composables)
PR 2 (backend reorder endpoint) ──┘            │
                                               ├──▶ PR 5 (UI globales TreatmentBar)
                                               │        │
                                               │        ▼
                                               │    PR 6 (viz globales odontograma)
                                               │
                                               └──▶ PR 7 (drag&drop reorder)
```

- **PR 1 y PR 2** pueden ir en paralelo (tocan áreas distintas del backend).
- **PR 3** solo requiere PR 1.
- **PR 4** requiere PR 1 y PR 2 (tipos completos).
- **PR 5, 6, 7** pueden ir en paralelo una vez está PR 4.
- **PR 6** depende de PR 5 porque consume el modelo que PR 5 termina de integrar en la UI del plan.

Ruta crítica: PR 1 → PR 4 → PR 5 → PR 6. ~4 PRs secuenciales. PR 2/3/7 se insertan en huecos.

---

## 5. Riesgos de ejecución

| Riesgo | Mitigación |
|--------|------------|
| Código que asume `treatment.teeth` no vacío | Grep previo (`teeth[0]`, `teeth.length > 0`, `first tooth`) en backend y frontend; añadir a PR 1 ajustes defensivos donde haga falta |
| Bridge auto-role se rompe al cambiar lógica `mode`→`scope` | Tests existentes en `test_odontogram_bridges` deben pasar sin tocar (fixture con scope `multi_tooth` + `clinical_type='bridge'`) |
| Drag&drop en Nuxt UI con transición rompe layout | Usar componente de `vue-draggable-plus` que soporta `<TransitionGroup>` nativo; verificar con QA manual |
| Reorder con plan vacío o 1 item | Guarda temprana en el composable (no llamar al PATCH) |
| i18n faltante | Checklist al final de cada PR de frontend |

---

## 6. Checklist final pre-merge de cada PR

- [ ] Lint backend (`ruff check`, `ruff format --check`) y frontend (`npm run lint`).
- [ ] Typecheck frontend (`npm run typecheck`).
- [ ] Tests backend verdes (`pytest -v`).
- [ ] Tests frontend verdes (`vitest`).
- [ ] `./scripts/reset-db.sh` funciona y deja base utilizable.
- [ ] Demo login `admin@demo.clinic / demo1234` operativo.
- [ ] Sin `console.log` ni `print` residuales.
- [ ] i18n (es + en) cubre todas las strings nuevas.

---

## 7. Fuera de alcance (no en estos PRs)

Reconfirmado para evitar scope creep:

- Búsqueda por nombre en `TreatmentBar`.
- Presupuesto en vivo en el panel lateral del plan.
- Plantillas, fases, alternativas, sugerencias desde diagnóstico, vista paciente.
- Selector de superficies inline (sigue modal).
- Accesibilidad de teclado general (solo la específica de drag&drop en PR 7).

Cualquier de lo anterior debe entrar por un nuevo ciclo de diseño.
