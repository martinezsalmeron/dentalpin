# Subtab "Pagos" en la ficha del paciente (Administración)

> Status: draft — design approved 2026-05-13, pending technical plan.

## Problema actual

La información económica del paciente está fragmentada en la ficha:

- **Presupuestos** → muestra cobrado/pendiente por presupuesto, no agregado.
- **Facturación** → muestra facturas emitidas, no flujo de dinero real.

No existe una vista **centrada en el paciente** que responda a: *¿cuánto ha pagado este paciente en total?* *¿qué me debe?* *¿tiene saldo a favor?* *¿cuál es su histórico de movimientos?*

El módulo `payments` ya expone `PatientLedger` vía `GET /api/v1/payments/patients/{id}/ledger` con todos los datos necesarios, pero ninguna UI los consume desde la ficha.

## Propuesta

Nuevo sub-modo **"Pagos"** dentro del tab **Administración** existente. Una sola pantalla con balance, banner de estado y timeline completo. CTA "Registrar pago" siempre a un clic.

Toggle resultante: `[ presupuestos ] [ facturación ] [ pagos ] [ documentos ]`.

## Por qué aquí (y no en facturación)

Pagos ≠ facturas. En la realidad operativa de la clínica:
- Un pago puede no estar facturado todavía.
- Una factura puede no estar cobrada.
- El paciente puede tener saldo a cuenta sin presupuesto asignado.

Mostrar pagos dentro de facturación mezcla dos ejes contables y rompe la realidad off-books que muchas clínicas llevan. **Reglas de memoria del proyecto**: nunca exponer diferencias entre eje "pagado" y eje "facturado".

## KPIs que se muestran

Datos del endpoint `PatientLedger`:

| KPI | Campo | Cuándo mostrarlo |
|---|---|---|
| Total pagado | `total_paid` | Siempre |
| Adeudado a clínica | `clinic_receivable` | Siempre (0 € si saldado) |
| A cuenta (saldo) | `on_account_balance` | Siempre |
| Crédito del paciente | `patient_credit` | Sólo si > 0, sidebar |
| Total devengado | `total_earned` | Sidebar, informativo |

**Lo que NO se muestra** (por la regla off-books): diferencias entre `total_paid` y monto facturado, conciliación factura↔pago, ratio cobro/facturación.

## Banner de estado

| Situación | Disparador | Estilo | Texto |
|---|---|---|---|
| Deuda | `clinic_receivable > 0` | warning | "Adeuda **{amount}** a la clínica" |
| Crédito | `patient_credit > 0` | info | "Tiene **{amount}** a su favor" |
| Saldado | ambos 0 | oculto | — |

## Timeline

Cronológico inverso. Tres tipos de entrada vienen del endpoint:

- **payment** → icono positivo verde, monto + método de pago, menú overflow `(...)` con *Ver detalle* + *Reembolsar* (gated por `payments.record.refund`).
- **refund** → icono negativo rojo, monto + reason code, sólo *Ver detalle*.
- **earned** → icono neutro "Tratamiento realizado" + concepto. Sin acciones (los tratamientos viven en el tab clínico).

## CTA "Registrar pago"

Abre `PaymentCreateModal` existente con `patient_id` pre-cargado y allocation por defecto = **on_account**. Dentro del modal el usuario puede opcionalmente elegir un presupuesto. Refleja la realidad: cuando el paciente paga, la clínica primero recibe el dinero — la asignación es un segundo paso opcional.

## Responsive

**Desktop (≥1024 px)**
```
┌──────────────────────────────────────────────────────┐
│ [Banner: deuda / crédito]                            │
├──────────────────────────────┬───────────────────────┤
│ KPIs row (3 totales)         │ Sidebar               │
│ • Total pagado               │ • A cuenta            │
│ • Adeudado clínica           │ • Crédito             │
│ • A cuenta                   │ • Último pago         │
│                              │ [+ Registrar pago]    │
├──────────────────────────────┴───────────────────────┤
│ Timeline (pagos · reembolsos · devengados)            │
└──────────────────────────────────────────────────────┘
```

**Tablet (768–1023 px)**
KPIs grid 3-col compacto, sidebar baja debajo, resto igual.

**Móvil (<768 px)**
- Banner full-width arriba.
- KPIs en stack vertical (1 col).
- Sidebar se disuelve; CTA "Registrar pago" pasa a **barra inferior sticky** con tap target ≥48 px.
- Timeline en 2 líneas (tipo+monto / fecha+método muted).
- Overflow menu vía `UDropdownMenu`, accesible con tap.

## Permisos

| Acción | Permission | Comportamiento si falta |
|---|---|---|
| Ver pill "Pagos" | `payments.record.read` | Pill oculto (pestaña no aparece) |
| Abrir modal de pago | `payments.record.write` | CTA oculta |
| Reembolsar en menú | `payments.record.refund` | Item oculto del overflow |

## Aislamiento entre módulos

- **Host** = módulo `patients`. Expone **un único slot nuevo**: `patient.detail.administracion.pagos`. Nunca importa código de `payments`.
- **Provider** = módulo `payments`. Auto-registra `PatientPaymentsPanel.vue` en su `frontend/plugins/slots.client.ts`. Ya declara `depends: ["patients", "budget"]` — sin cambios.
- **Si `payments` se desinstala** o el usuario no tiene `payments.record.read`: el slot resuelve vacío, el toggle probe-ea `resolveSlot.length > 0` y oculta el pill por completo. Fallback de URL: si `adminMode=payments` pero no hay providers, vuelve a `budgets`.

`patients` no añade a `manifest.depends`. La inversión de dependencia (provider self-registers) es lo que hace que esto sea limpio.

## Cómo se valida

1. `docker-compose up`, login `admin@demo.clinic`, abrir paciente con histórico de pagos.
2. Ficha → Administración → click "Pagos". URL → `?tab=administration&adminMode=payments`.
3. KPIs deben coincidir con respuesta de `GET /api/v1/payments/patients/{id}/ledger`.
4. "Registrar pago" → modal pre-rellenado con paciente. Submit → KPIs y timeline refrescan.
5. Reembolso desde overflow de un pago → confirm → nueva fila refund visible, KPIs ajustan.
6. Quitar `payments.record.read` al usuario → pill desaparece; URL forzada `adminMode=payments` cae a `budgets`.
7. Viewport 375 px: banner + KPIs apilados, barra inferior sticky visible, overflow menu alcanzable.
8. Desinstalar módulo `payments` desde admin (si está soportado) → pill desaparece, sin errores en consola.

## Lo que esta feature NO añade

- No hay endpoints nuevos.
- No hay permisos nuevos.
- No hay migraciones.
- No hay infra de slots nueva — todo reutiliza `useModuleSlots` + `<ModuleSlot>`.
- `patients` no añade dependencia a `payments`.

Cero deuda técnica.

## Cross-links

- Plan técnico: [`docs/technical/payments/patient-ledger-subtab.md`](../technical/payments/patient-ledger-subtab.md).
- Módulo origen: `backend/app/modules/payments/`.
- Sistema de slots: `frontend/app/composables/useModuleSlots.ts`, `frontend/app/components/ModuleSlot.vue`.
- Componentes detail-page compartidos: `docs/technical/detail-page-shared-components.md`.
