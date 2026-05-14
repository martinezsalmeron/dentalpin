# Listados de trabajo: `/patients`, `/budgets`, `/invoices`, `/payments`

> Status: draft — design plan aprobado 2026-05-14. Plan técnico en [`docs/technical/lists-redesign.md`](../technical/lists-redesign.md). Contrato cross-módulo en [`docs/technical/payments/cross-module-summaries.md`](../technical/payments/cross-module-summaries.md).

## Problema actual

Los cuatro listados centrales de la clínica funcionan hoy como vistas de inventario, no como herramientas de trabajo:

- **`/patients`** muestra nombre + teléfono + estado. Nada de ciudad, deuda, idioma, última visita ni "no contactar". Búsqueda por texto, sin filtros.
- **`/budgets`** muestra número + paciente + total + fecha + estado del presupuesto. Cero información de cobro — la dentista no sabe qué presupuesto está pagado y cuál no salvo abriendo uno por uno.
- **`/invoices`** ya tiene varios filtros (estado, vencidas, compliance). Falta rango de fechas en la barra principal, serie, orden, y la barra ocupa 4 líneas en móvil.
- **`/payments`** usa el peor patrón: cuatro `UFormField` en grid + text input pidiendo `patient_id` literal (UUID). Sin paginación visible, sin orden, sin chips.

Todos esconden columnas en móvil con `hidden sm:inline` en vez de re-componer la fila como card legible.

A nivel de código, cada listado reescribe lógica de paginación + debounce + watch + `URLSearchParams` (≈100 líneas repetidas por página). El estado vive en `ref()` locales: refrescar la página descarta filtros, los links no son compartibles.

## Propuesta

Una **capa de primitivos compartidos** (`DataListLayout`, `FilterBar`, `useListQuery`, ...) en host frontend que los cuatro listados consumen. Sobre esa capa, datos nuevos por listado y filtros que el día a día de la clínica necesita.

| Listado | Información nueva | Filtros nuevos |
|---|---|---|
| `/patients` | Avatar · ciudad · **deuda** (slot payments) | Estado · ciudad · **con deuda > 0** · no contactar |
| `/budgets` | Avatar paciente · **cobrado/pendiente** (slot payments) · "vence en Nd" | **Estado de cobro** (pagado/parcial/sin cobro) · profesional · vencimiento · rango fechas |
| `/invoices` | Serie · "vencida Nd" · pendiente más visible | Rango fechas · serie · sólo notas de crédito · rango importe |
| `/payments` | Método con icono · asignación visual desglosada · avatar paciente | Método (chips) · presets fecha · sin asignar · con reembolsos · paciente (autocomplete) |

Cross-módulo (deuda en /patients, cobro en /budgets) **vía slots + endpoints del módulo payments** — el patrón que ya conecta `BudgetPaymentsCard` con `budget.detail.sidebar` y `PatientPaymentsPanel` con `patient.detail.administracion.payments`. Cero cambios en `manifest.depends`.

## Por qué ahora

- La recepcionista necesita responder "¿quién me debe dinero?" sin abrir paciente por paciente.
- La dentista necesita "¿qué presupuestos aceptados están sin cobrar?" sin abrir uno por uno.
- Administración necesita "¿qué facturas están vencidas en serie A este trimestre?".
- En móvil, una fila tiene hoy 6 valores apretados — inviable en tareas reales.
- Los primitivos parciales que ya existen (`ListRow`, `SearchBar`, `PaginationBar`, `EmptyState`, `FilterChip`, `StatusBadge`, `Money`, `PageHeader`) están maduros. Buen momento para consolidar la capa que falta sin tocar la base.

## Reglas duras

- **Off-books rule.** Cero comparaciones entre eje "facturado" (`Invoice`) y eje "pagado" (`Payment`) en cualquier listado. Deuda del paciente = `clinic_receivable` del ledger = `total_earned − net_paid`. Estado de cobro del presupuesto = `Σ allocations a este budget / budget.total_with_tax`. Ambos son eje pagos puro. Ver ADR 0010 y `payments/CLAUDE.md` gotchas.
- **Aislamiento de módulos.** Nada importa fuera de su `manifest.depends`. Enriquecimiento cross-módulo via slots (frontend) + endpoints del módulo origen (backend). Cero cambios de manifest.
- **Mobile-first.** Card real en `<md`, tap targets ≥44 px, filtros en slide-over si pasan de 3 chips visibles.
- **URL como fuente de verdad** para filtros + page + sort. Pegar un link reproduce la vista exacta. Back/forward del navegador funcionan.
- **`do_not_contact`** se respeta: el filtro existe y se aplica como tri-state (todos / sólo contactables / sólo no contactar).

## `/patients`

### Columnas (desktop row)

| | Field | Notas |
|---|---|---|
| 1 | Avatar | Iniciales `last_name[0] + first_name[0]` sobre `UAvatar`. Color por hash estable. |
| 2 | Nombre | `last_name, first_name`. Línea principal. |
| 3 | Ciudad | `address.city`. Subtitle. Vacío → "—". |
| 4 | Contacto | `phone || email`. Subtitle, segundo bloque. Vacío → "—". |
| 5 | Deuda | Badge `€ X.XX` rojo si `>0`, gris si `=0`, oculto si paciente sin actividad económica. **Slot `patients.list.row.financial`** rellenado por payments. |
| 6 | Estado | `StatusBadge` active / archived. |
| 7 | No contactar | Icono `i-lucide-bell-off` warning si `do_not_contact=true`. Tooltip "No contactar". |

### Filtros visibles (chips en `FilterBar`)

- `Estado` (`FilterChipMulti` — active/archived, default: active)
- `Ciudad` (`FilterEntityPicker` async sobre lista distinct de ciudades del clinic; vacío = todas)
- **`Con deuda > 0`** (`FilterToggle`, slot `patients.list.filter` rellenado por payments)
- `No contactar` (tri-state)

### Filtros avanzados (popover "Más filtros")

- Rango de edad (slider min/max derivado de `date_of_birth`)
- Idioma preferido (`preferred_language`)
- Fecha de registro (`FilterDateRange`)
- Profesión (`profession`, autocomplete distinct)

### Orden (`SortMenu`)

- Nombre (asc/desc, default)
- Fecha registro (más recientes / más antiguos)
- Deuda (mayor / menor — sólo si filtro "con deuda" activo, server-side por `patient_id` set)

### Vista móvil (`<md`)

```
┌─────────────────────────────────────────┐
│ [A] Pérez Martínez, Lucía       [⛔]    │
│     Madrid · 600 555 333                │
│     Deuda: 342,50 €      [active]       │
└─────────────────────────────────────────┘
```

Card con avatar grande, deuda como segunda fila prominente (la métrica de trabajo), badges a la derecha.

## `/budgets`

### Columnas (desktop row)

| | Field | Notas |
|---|---|---|
| 1 | Avatar paciente + Nombre | Iniciales + `last_name, first_name`. |
| 2 | Nº presupuesto | `budget_number · v{version}`, tnum. |
| 3 | Estado | `BudgetStatusBadge` (draft/sent/accepted/rejected/expired/cancelled). |
| 4 | Total | `Money strong`. |
| 5 | **Cobro** | Mini-barra `cobrado / total` + chip `Pagado · Parcial · Sin cobro`. **Slot `budget.list.row.payments`** rellenado por payments. Oculto si presupuesto en draft. |
| 6 | Profesional asignado | Avatar mini si presente. |
| 7 | Válido hasta | Fecha o badge "Vence en 3d" warning / "Vencido" danger. |

### Filtros visibles

- `Estado` (`FilterChipMulti` — draft / sent / accepted / ...)
- **`Cobro`** (`FilterChipMulti` — Pagado / Parcial / Sin cobro, slot `budget.list.filter` rellenado por payments)
- `Profesional` (`FilterEntityPicker` — usuarios con rol dentist/hygienist del clinic)
- `Vencimiento` (`FilterChipMulti` — Vigente / Vence en 7d / Vencido) — preset puro frontend
- Búsqueda libre (número, paciente)

### Filtros avanzados

- Rango fechas creación
- Rango importe `total` (€)
- Paciente específico (autocomplete)

### Orden

- Fecha creación (default desc)
- Válido hasta
- Total
- Estado de cobro (sólo si filtro "Cobro" activo)

### Móvil

```
┌─────────────────────────────────────────┐
│ [A] García López, Juan                  │
│     PRES-2025-0184 · v2  [accepted]     │
│     1.840,00 €   ████░░░░  Parcial      │
│     Dra. Ruiz · Vence en 5d             │
└─────────────────────────────────────────┘
```

## `/invoices`

### Columnas (desktop row)

| | Field | Notas |
|---|---|---|
| 1 | Nº | `invoice_number` o "Borrador". |
| 2 | Serie | Si presente `series.code`. |
| 3 | Estado | Badge (draft/issued/partial/paid/cancelled/voided). |
| 4 | Compliance | Slot `invoice.list.row.meta` existente (verifactu, factur-x). |
| 5 | Emisión | `issue_date`. |
| 6 | Vencimiento | Fecha. Si vencida: rojo + "Vencida Nd" debajo. |
| 7 | Paciente | `last_name, first_name`. |
| 8 | Total | `Money strong`. |
| 9 | Pendiente | `balance_due` warning, sólo si > 0 y status ≠ draft. |

### Filtros visibles

- `Estado` (multi-select)
- `Vencidas` (toggle, ya existe)
- Compliance severity (slot `invoice.list.toolbar.filters` existente)
- **`Fechas emisión`** (`FilterDateRange` con presets) — nuevo en barra principal
- Búsqueda libre

### Filtros avanzados

- Rango vencimiento (`due_from` / `due_to` — ya en API)
- Serie (`FilterEntityPicker` con `InvoiceSeries`)
- Paciente
- Sólo notas de crédito (`is_credit_note=true`)
- Rango importe

### Orden

- Emisión (default desc)
- Vencimiento
- Total
- Pendiente

### Móvil

```
┌─────────────────────────────────────────┐
│ FAC-A-2025-0091          [paid]    [✓]  │
│ Ruiz Sánchez, Pedro                     │
│ Emitida 12 abr · Vencía 12 may          │
│ 1.230,00 €                              │
└─────────────────────────────────────────┘
```

Compliance badge inline al lado del estado (ya soportado).

## `/payments`

### Columnas (desktop row)

| | Field | Notas |
|---|---|---|
| 1 | Fecha | `payment_date`. |
| 2 | Avatar paciente + Nombre | |
| 3 | Método | Icono por método + label. |
| 4 | Importe | `Money strong`. |
| 5 | Asignación | Desglose visual: `1.000 € presupuesto + 200 € a cuenta` con icons. |
| 6 | Reembolsado | Badge rojo `−X €` si `refunded_total > 0`. |
| 7 | Referencia | `reference` truncado, mono. |

### Filtros visibles

- **`Método`** (`FilterChipMulti` con icons — efectivo, tarjeta, transferencia, ...)
- **`Fechas`** (`FilterDateRange` con presets: Hoy / 7d / 30d / Este mes / Trimestre / Año)
- `Con reembolsos` (`FilterToggle`)
- `Sin asignar` (`FilterToggle` — `has_unallocated=true`)
- `Paciente` (`FilterEntityPicker` autocomplete — sustituye al text input de UUID)

### Filtros avanzados

- Rango importe
- Presupuesto específico (autocomplete)

### Orden

- Fecha (default desc)
- Importe

### Móvil

```
┌─────────────────────────────────────────┐
│ [💳] Ruiz Sánchez, Pedro     1.200 €    │
│      12 may 2026 · Tarjeta · ref XYZ    │
│      1.000 € presupuesto + 200 € cta    │
└─────────────────────────────────────────┘
```

## Primitivos compartidos

Capa nueva en host `frontend/app/components/shared/` y `app/composables/`. Los detalles de props/contratos viven en el [plan técnico](../technical/lists-redesign.md). Vista panorámica:

| Primitivo | Reemplaza |
|---|---|
| `DataListLayout.vue` | Wrappers manuales (`<UCard>` + estados + paginación) en las 4 páginas |
| `DataListItem.vue` | Esconder-columnas en móvil; render dual row/card |
| `FilterBar.vue` | `<div class="flex flex-wrap gap-...">` con UInput+USelectMenu hand-rolled |
| `FilterChipMulti.vue` | `USelectMenu multiple` con label "Estado" inerte |
| `FilterDateRange.vue` | Dos `UInput type="date"` separados |
| `FilterToggle.vue` | `UCheckbox` plano |
| `FilterEntityPicker.vue` | Text input pidiendo UUID literal (payments hoy) |
| `SortMenu.vue` | Inexistente: ningún listado tiene orden hoy |
| `useListQuery<F>()` | Tres veces el patrón `searchTimeout + watch + URLSearchParams` |

## Mobile-first

- `DataListItem` renderiza `row` slot en `≥md`, `card` slot en `<md`. Switch en CSS (`@container` o `md:` Tailwind) — sin remontar.
- Tap targets ≥44 px (`min-h-[var(--density-row-height)]` ya existe en `ListRow`).
- `FilterBar` colapsa: ≤3 chips visibles + botón "Filtros (Nactivos)" que abre `USlideover` con todos.
- Cero tooltips — no funcionan táctil. La info crítica está en el card.

## URL como fuente de verdad

`useListQuery` sincroniza filtros↔URL en ambos sentidos:

```
/budgets?status=accepted,sent&payment_status=partial,unpaid&page=2&sort=valid_until:asc
```

- Filtros simples → `?status=draft,accepted`
- Booleanos → `?overdue=1`
- Date ranges → `?date_from=2026-01-01&date_to=2026-03-31` o preset `?date_preset=this_quarter`
- Cross-módulo (filtros slot) → param propio (`?with_debt=1`, `?payment_status=unpaid`) que el composable convierte en llamada al endpoint payments + `?budget_ids[]=` / `?patient_ids[]=` sobre el listado nativo.

Back/forward del navegador funcionan. Compartir el link reproduce la vista. Zero storage.

## Aislamiento de módulos

| Host listado | Slot expone | Provider rellena | Permiso |
|---|---|---|---|
| `patients` | `patients.list.row.financial` (ctx `{ patient_id, summary }`) | payments | `payments.record.read` |
| `patients` | `patients.list.filter` (ctx `{ value, onChange }`) | payments | `payments.record.read` |
| `budget` | `budget.list.row.payments` (ctx `{ budget_id, summary }`) | payments | `payments.record.read` |
| `budget` | `budget.list.filter` (ctx `{ value, onChange }`) | payments | `payments.record.read` |
| `billing` | `invoice.list.row.meta` ya existe (compliance) | verifactu / factur-x | varía |
| `billing` | `invoice.list.toolbar.filters` ya existe | verifactu / factur-x | varía |

- `patients` y `budget` NUNCA importan código de `payments`. El registro se hace via `frontend/plugins/slots.client.ts` del módulo payments.
- `payments.depends = ["patients", "budget"]` — legal importar tipos/conceptos de ambos.
- `billing.depends = ["patients", "catalog", "budget", "payments"]` — sin cambios.
- Endpoints nuevos del cross-módulo todos en `/api/v1/payments/...` (ver [contrato](../technical/payments/cross-module-summaries.md)).

## Permisos

| Acción | Permission | Si falta |
|---|---|---|
| Ver listado `/patients` | `patients.read` | 403 |
| Ver columna deuda + filtro "con deuda" | `payments.record.read` | Slot resuelve vacío → no se renderiza nada (ni columna ni filtro). Listado funciona sin la enriquecimiento. |
| Ver listado `/budgets` | `budget.read` | 403 |
| Ver mini-progreso + filtro "Cobro" | `payments.record.read` | Igual: slot vacío, listado nativo intacto. |
| Ver listado `/invoices` | `billing.read` | 403 |
| Ver listado `/payments` | `payments.record.read` | 403 |

## Off-books safeguard (revisión obligatoria en PR)

Tres invariantes que el reviewer comprueba:

1. **Deuda del paciente = ledger `clinic_receivable`**, calculado en `payments/service.py:LedgerService.get_patient_ledger` como `max(0, total_earned − net_paid)`. NO se calcula nunca como `Σ invoice.balance_due` y NO se compara contra ningún campo de billing.
2. **Estado de cobro del presupuesto = `Σ allocations a este budget / budget.total_with_tax`**, derivado en payments. NO se compara con facturas emitidas del mismo presupuesto.
3. **Listados de invoices y payments siguen separados**. Cero fila que mezcle ambos ejes en la misma row, cero KPI agregado que muestre la diferencia.

Test backend asegura que `clinic_receivable` ≠ `Σ invoice.balance_due` cuando hay tratamientos earned sin invoice (caso típico off-books).

## Cómo se valida

1. `docker-compose up` + `./scripts/reset-db.sh && ./scripts/seed-demo.sh`. Login `admin@demo.clinic`.
2. **Smoke** en cada listado: columnas nuevas visibles, filtros aplicables, URL refleja estado.
3. **Cross-módulo**: en `/budgets`, ver mini-progress por fila; aplicar "Cobro: Sin pagar" → URL incluye `?payment_status=unpaid` y la lista filtra. Idéntico en `/patients` con "Con deuda".
4. **Off-books guard**: crear paciente con tratamiento performed (`earned > 0`) sin invoice → /patients muestra deuda en la fila, /invoices del paciente queda vacío, ningún listado mezcla los ejes.
5. **Permission gating**: revocar `payments.record.read` a un usuario → /patients y /budgets renderizan sin la columna nueva ni el filtro; los listados nativos intactos.
6. **Módulo desinstalado** (`payments` es `removable=False`, pero permission-denied es la práctica): mismo comportamiento que gating.
7. **Mobile**: viewport 375 × 667 — cards visibles, filtros colapsados en slide-over, tap-target medidos.
8. **URL state**: pegar URL con filtros + sort + page en otra pestaña, listado abre con el mismo estado. Back/forward conservan filtros.
9. **Aislamiento**: `rg "from app.modules.billing" backend/app/modules/payments/` → 0. Idéntico para `from app.modules.payments` dentro de `backend/app/modules/patients/` y `backend/app/modules/budget/`.

## Lo que esta feature NO añade

- **Vistas guardadas por usuario** (modelo `SavedView`). URL-only cubre 90% del valor; vistas guardadas se valoran como fase 2.
- **Bulk actions** (multi-select de filas + acción masiva).
- **Swipe-actions** en card móvil (delete/archive).
- **Tags/segmentos custom** de pacientes (VIP, aseguradora, ...).
- **Slot `last_visit`** desde schedules — fuera salvo que el módulo schedules ya exponga la query.
- **Exportar CSV**.
- **Sort por column-header clickable** — sustituido por `SortMenu` dropdown por consistencia móvil.
- **Manifest changes**. Ninguno.
- **Permisos nuevos**. Ninguno.
- **Migraciones**. Ninguna.

## Cross-links

- Plan técnico: [`docs/technical/lists-redesign.md`](../technical/lists-redesign.md).
- Contrato cross-módulo payments: [`docs/technical/payments/cross-module-summaries.md`](../technical/payments/cross-module-summaries.md).
- ADR 0010 (payments primitive): [`docs/adr/0010-payments-as-primitive-module.md`](../adr/0010-payments-as-primitive-module.md).
- Sistema de slots: `frontend/app/composables/useModuleSlots.ts`, `frontend/app/components/ModuleSlot.vue`.
- Componentes shared existentes: `frontend/app/components/shared/`.
- Precedente cross-módulo: [`docs/features/patient-payments-subtab.md`](./patient-payments-subtab.md).
