# Plan de UX: Añadir Tratamientos al Plan de Tratamiento

**Fecha:** 2026-04-18
**Estado:** Propuesta (v2 — reescritura post-refactor, alcance reducido)
**Autor:** Análisis UX
**Reemplaza:** v1 (2026-04-17)

---

## 0. Cambios respecto a v1

La v1 se escribió antes de la refactorización del odontograma y del catálogo. Buena parte de la **PARTE A** original (multi-diente, estados visuales, roles de puente) ya está implementada. Este documento:

1. Reconoce qué quedó cubierto por la refactorización.
2. Es crítico con decisiones de v1 que no envejecieron bien (los "tres modos de añadir", la separación artificial "por diente / global / catálogo").
3. **Reduce el alcance** a dos mejoras que aportan valor inmediato sin sobrecargar el modelo:
   - Tratamientos globales como ciudadanos de primera clase.
   - Reordenar items del plan por drag & drop.
4. Documenta huecos menores del odontograma y los pospone explícitamente.

---

## Índice

1. [Estado actual tras la refactorización](#1-estado-actual-tras-la-refactorización)
2. [Reflexión crítica sobre v1 y reducción de alcance](#2-reflexión-crítica-sobre-v1-y-reducción-de-alcance)
3. [Principios de UX](#3-principios-de-ux)
4. [Tratamientos globales (arcada / boca completa)](#4-tratamientos-globales-arcada--boca-completa)
5. [Reordenar items del plan con drag & drop](#5-reordenar-items-del-plan-con-drag--drop)
6. [Huecos pendientes del odontograma (pospuestos)](#6-huecos-pendientes-del-odontograma-pospuestos)
7. [Cambios en datos y API](#7-cambios-en-datos-y-api)
8. [Prioridades y fases](#8-prioridades-y-fases)
9. [Riesgos](#9-riesgos)

---

## 1. Estado actual tras la refactorización

### 1.1 Lo que **ya está implementado**

| Área | Cobertura | Archivos clave |
|------|-----------|----------------|
| **Multi-diente (puentes, férulas, carillas/coronas múltiples)** | ✅ Completo con roles (pilar/póntico/cantilever), arcada, mínimos por tipo | `OdontogramChart.vue`, `MultiToothConfirmPopup.vue`, `odontogramConstants.ts` |
| **Catálogo con pricing strategies** | ✅ flat / per_tooth / per_surface / per_role + mapping odontograma | `catalog/models.py`, `catalog/pricing.py`, `CatalogItemModal.vue` |
| **TreatmentBar modos** | ✅ `full` / `diagnosis` / `planning` (filtra terapéuticas) | `TreatmentBar.vue` |
| **Estados visuales `existing` vs `planned`** | ✅ Con reglas de visualización (pulp fill, occlusal, lateral icon, pattern) | `VISUALIZATION_RULES` |
| **Sincronización PlannedTreatmentItem ↔ Treatment** | ✅ 1:1 FK, `perform` marca completado, sync a `existing` | `treatment_plan/models.py`, `useTreatments.ts` |
| **Hover bidireccional plan ↔ odontograma** | ✅ | `PlanDetailView.vue` |
| **Timeline / vista histórica** | ✅ | `useOdontogramTimeline.ts`, `TimelineSlider.vue` |
| **Vinculación Plan ↔ Presupuesto** | ✅ `link-budget`, `sync-budget`, `generate-budget` | `treatment_plan/router.py` |
| **ClinicalTab con 4 modos** | ✅ `history` / `diagnosis` / `plans` / `appointments` | `ClinicalTab.vue` |
| **ConditionsList (bloque diagnosticadas)** | ✅ Rediseñado, agrupa por diente con hover-link | `ConditionsList.vue` |

### 1.2 Gaps reales

| Gap | Decisión |
|-----|----------|
| No hay tratamientos globales (limpieza, blanqueamiento) como first-class | **En alcance** (§4) |
| Reordenar items del plan no es posible | **En alcance** (§5) |
| No hay búsqueda por nombre en catálogo desde editor | Fuera de alcance |
| No hay presupuesto en vivo en la vista de plan | Fuera de alcance (se resuelve con Budget actual) |
| No hay plantillas, alternativas, fases, sugerencias desde diagnóstico | Fuera de alcance (ver v1 archivada en git) |
| Selector superficies modal, no inline | Pospuesto (§6) |
| Micro-feedback y teclado | Pospuesto (§6) |

---

## 2. Reflexión crítica sobre v1 y reducción de alcance

### 2.1 Decisiones de v1 que descartamos

- **"Tres modos de añadir (🦷 Por Diente / 🌐 Boca Completa / 📋 Del Catálogo)".** Obliga al usuario a clasificar la intención antes de saber el tratamiento. El catálogo ya determina `treatment_scope` y `pricing_strategy`; la UI debería derivar el modo de interacción del item seleccionado, no al revés. El "modo catálogo" es en realidad cómo funciona el sistema siempre, no un modo aparte.
- **"Panel lateral fijo al 35%".** El layout actual (odontograma 3/5, lista 2/5, barra abajo) funciona. Reabrirlo sin razón ergonómica concreta es churn.
- **"Sincronización dura: eliminar item del plan elimina ToothTreatment".** Un `Treatment` `planned` puede ser referenciado por otros planes futuros. La regla correcta: borrar item solo limpia el `Treatment` si queda huérfano y está en `planned`. Si está `performed`, se conserva como historia clínica. Ver §7.

### 2.2 Por qué reducimos el alcance a dos features

Los grandes añadidos que barajamos (plantillas, fases, sugerencias, alternativas, búsqueda, presupuesto vivo, vista paciente) aportan valor, pero:

- Requieren nuevas entidades y endpoints.
- Empujan complejidad conceptual a la UI (fases colapsables, alternativas agrupadas, etc.).
- No los valida nadie aún con uso real.

Las **dos mejoras que sí conservamos** desbloquean casos reales frecuentes (limpieza = la mayoría de pacientes; reordenar = esperable en cualquier lista larga) sin inflar el modelo.

Todo lo demás queda documentado en el historial de git (v1 y primera versión de v2) por si se quiere recuperar.

### 2.3 Sin datos a preservar

La aplicación aún no está en producción. Esto libera decisiones:

- Podemos **redefinir enums** limpiamente en lugar de extender con valores nuevos por compatibilidad.
- Podemos **cambiar columnas a opcionales** sin migración condicionada.
- El seeder de catálogo puede rehacerse desde cero con la taxonomía correcta (incluyendo globales).
- No se escribe código de compatibilidad hacia atrás en servicios ni en el frontend.

Las reglas de borrado de `Treatment` al quitar items del plan (§7.3) no son legacy — son corrección arquitectónica: un tratamiento ya realizado es historia clínica y no se borra aunque se quite del plan. Eso se conserva.

---

## 3. Principios de UX

Guías que resuelven ambigüedades:

1. **Una sola vía, contextual.** El modo de interacción se deriva del tratamiento elegido. Limpieza no pide diente; puente pide rango. Sin botones para clasificar intención por adelantado.
2. **Catálogo como fuente de verdad.** No crear conceptos de UI que dupliquen lo que ya modela el catálogo.
3. **Odontograma es visualización, no formulario.** Cualquier acción que lleve más de dos clics en el odontograma sugiere que el punto de entrada correcto es otro.
4. **Reversibilidad por defecto.** Añadir, quitar y reordenar en el plan no requieren confirmación. Completar un tratamiento (cambia historia clínica) sí.
5. **Planning ≠ Diagnóstico.** Estados `planned` vs `existing` no se mezclan en los mismos controles; ya están separados por modo.

---

## 4. Tratamientos globales (arcada / boca completa)

### 4.1 Problema

Limpieza, blanqueamiento, flúor, férula de descarga, ortodoncia global no encajan en el modelo actual: `Treatment` requiere al menos un `TreatmentTooth`. El dentista acaba añadiéndolos como notas sueltas al budget o fuera del sistema.

### 4.2 Decisión de modelo

**Extender `Treatment.scope`** con dos valores nuevos: `global_mouth` y `global_arch`.

- `global_mouth` → 0 `TreatmentTooth`. Aplica a todo.
- `global_arch` → 0 `TreatmentTooth`; campo `arch` (`upper` / `lower`) indica la arcada.

`TreatmentTooth` pasa a ser opcional (count 0 válido cuando el scope es global).

**Alternativa descartada:** entidad `GlobalTreatment` separada. Duplica precios, estados y pertenencia al plan; rompe la unificación actual.

### 4.3 UI

En la barra de tratamientos, botón **"Boca completa ▸"** despliega un panel vertical con los items globales del catálogo:

```
┌────────────────────────────────┐
│ BOCA COMPLETA                  │
│                                │
│ 🪥 Limpieza dental       €60   │
│ ✨ Blanqueamiento       €180   │
│ 🦷 Fluorización          €25   │
│ 📋 Revisión             €30   │
│                                │
│ ARCADA                         │
│ 🔧 Férula descarga sup. €120   │
│ 🔧 Férula descarga inf. €120   │
└────────────────────────────────┘
```

**Interacciones:**

- Clic en item global de boca completa → se añade directamente al plan, sin interactuar con el odontograma. Feedback: toast + item con icono 🌐 en la lista.
- Clic en item de arcada → banner pide seleccionar arcada con dos botones grandes sobre el odontograma (Superior / Inferior). No requiere selección diente a diente.

**Visualización en odontograma:**

- Items `global_mouth` no se pintan sobre dientes concretos. Aparecen en una cinta inferior del odontograma con el icono del tratamiento y un badge numérico si hay varios. Hover del item en la lista → parpadeo sutil de todo el odontograma (o de la arcada) para indicar pertenencia.
- Items `global_arch` pintan una línea/cinta sobre la arcada afectada.

### 4.4 Catálogo

Los items de catálogo globales ya pueden existir con `treatment_scope` apropiado; añadir `global` (y opcionalmente `global_arch`) al enum del catálogo y permitir su creación desde `CatalogItemModal`. El seeder de catálogo por defecto debería incluir limpieza, blanqueamiento, fluorización y revisión como globales de boca completa.

---

## 5. Reordenar items del plan con drag & drop

### 5.1 Problema

El orden de los items del plan no se puede modificar desde la UI. El campo `sequence_order` existe en `PlannedTreatmentItem` pero no se expone en el frontend. El orden importa cuando el plan se usa como guía de ejecución.

### 5.2 UI

En la lista del plan (`PlanTreatmentList`):

- Cada fila de **pendientes** muestra un handle de arrastre (`⋮⋮` o `i-lucide-grip-vertical`) a la izquierda.
- Drag para reordenar dentro de la sección "Pendientes". Mientras se arrastra, fila semitransparente + drop indicator entre filas.
- Los items completados **no se reordenan** (orden por `completed_at`).
- Soltar → `PATCH` al backend con el nuevo orden.

**Accesibilidad:** no abandonar teclado. Flechas `Alt+↑` / `Alt+↓` sobre una fila enfocada la mueven una posición.

**Feedback:** sin toast (sería ruido). Animación de reacomodo de la lista.

### 5.3 Backend

Nuevo endpoint:

```
PATCH /treatment-plans/{id}/items/reorder
Body: { "item_ids": ["...", "...", "..."] }
```

Recalcula `sequence_order` para los items listados (persistente). Valida que todos los `item_ids` pertenecen al plan. Un solo round-trip por reordenación.

Alternativa: mandar `PATCH` por cada item movido. Descartada: varios round-trips, estado inconsistente en fallos parciales.

### 5.4 Ordenación por defecto

`GET /treatment-plans/{id}` ya devuelve items ordenados por `sequence_order`. Al crear un item, `sequence_order = max(siblings) + 1`. Sin cambios aquí.

---

## 6. Huecos pendientes del odontograma (pospuestos)

Puntos menores de v1 que siguen abiertos. Se documentan para trazabilidad; **no se incluyen en este alcance**. Revisitar tras uso real si generan fricción.

- **Selector de superficies inline.** Actual: `SurfaceSelectorPopup` modal. Ideal: popover anclado al diente, sin bloquear el resto del odontograma.
- **Accesibilidad de teclado.** `/` buscador (no aplica hasta que exista búsqueda), `Esc` cancela modo armado (existe parcialmente), `Tab` ordenado.
- **Micro-feedback al añadir / eliminar.** Slide-in animado y deshacer rápido en toast.

---

## 7. Cambios en datos y API

Sin legacy, redefiniciones limpias.

### 7.1 Backend — modelos

**`odontogram.Treatment`**

Redefinir `scope` como enum unificado (reemplaza el actual `mode: single/bridge/uniform`):

| Valor | Dientes asociados | Uso |
|-------|-------------------|-----|
| `tooth` | 1 `TreatmentTooth`, `surfaces` opcional | Empaste, corona, endo, implante, etc. |
| `multi_tooth` | N `TreatmentTooth` con `role` opcional | Puente, férula, carillas/coronas múltiples |
| `global_mouth` | 0 `TreatmentTooth` | Limpieza, blanqueamiento, flúor, revisión |
| `global_arch` | 0 `TreatmentTooth`, `arch` requerido (`upper`/`lower`) | Férula de descarga, ortodoncia global por arcada |

Cambios concretos:

- Nueva columna `scope` (enum arriba). Reemplaza `mode`.
- Nueva columna `arch` (enum nullable `upper`/`lower`). Obligatoria si `scope == global_arch`.
- `TreatmentTooth` ya no es obligatorio (cero filas válido).
- `TreatmentTooth.surfaces` sigue siendo el único portador de superficies; no se añade campo `surface` a nivel `Treatment`.

**`catalog.TreatmentCatalogItem`**

Redefinir `treatment_scope` con los mismos 4 valores (`tooth` / `multi_tooth` / `global_mouth` / `global_arch`). Sustituye los actuales `surface` / `whole_tooth`. El flag `requires_surfaces` se mantiene como bool independiente (aplicable solo a `tooth`).

### 7.2 Backend — endpoints nuevos

| Endpoint | Propósito |
|----------|-----------|
| `PATCH /treatment-plans/{id}/items/reorder` `{ item_ids: [...] }` | Reordenar items del plan |

El flujo de añadir tratamiento global reusa `POST /patients/{id}/treatments` con `scope` y `arch`, sin `teeth`. El `POST /treatment-plans/{id}/items` existente basta para enlazar al plan.

### 7.3 Regla de borrado de `Treatment` al quitar item del plan

- Si el `Treatment` está referenciado por otro `PlannedTreatmentItem` activo → no tocar.
- Si es huérfano y `status == 'planned'` → borrar `Treatment`.
- Si es huérfano y `status == 'performed'` → mantener (historia clínica).

Encapsular en `TreatmentPlanService.remove_item`, no en el router.

### 7.4 Frontend — composables y tipos

- `useTreatmentPlans` → añadir `reorderItems(planId, itemIds)`.
- `useTreatments` → ajustar `createTreatment` para aceptar `scope` global y `arch` sin `tooth_numbers`.
- `TreatmentBar` → nuevo botón "Boca completa" con panel desplegable de items globales.
- `PlanTreatmentList` → handle de drag, lógica de reorder con librería drag & drop ya usada en el proyecto si existe (buscar antes de añadir dep nueva).
- `OdontogramChart` → cinta inferior para globales (`global_mouth`) y highlight de arcada (`global_arch`).
- Tipos `Treatment`, `TreatmentCatalogItem` y `PlannedTreatmentItem` en `types/index.ts` → ampliar `scope` y añadir `arch`.

---

## 8. Prioridades y fases

| ID | Feature | Valor | Esfuerzo | Orden |
|----|---------|-------|----------|-------|
| G1 | Tratamientos globales en modelo + catálogo | Alto | Medio | 1 |
| G2 | UI de globales en TreatmentBar + visualización en odontograma | Alto | Medio | 2 |
| G3 | Seeder de catálogo con globales por defecto | Medio | Bajo | 3 |
| R1 | Endpoint `reorder` + `reorderItems` en composable | Alto | Bajo | 4 |
| R2 | Drag & drop en `PlanTreatmentList` (handle, animación, atajos teclado) | Alto | Medio | 5 |

**Fase única**, sin paralelización estricta. G1–G3 y R1–R2 pueden hacerse en PRs independientes. G2 depende de G1; R2 depende de R1.

---

## 9. Riesgos

- **Código que asume `TreatmentTooth` no vacío.** Servicios, response builders, visualización y reportes. Auditar usos y ajustar a listas posiblemente vacías. No es un tema de datos (no hay prod), es de corrección de código.
- **Dep de drag & drop.** Si no hay librería ya en el proyecto, evaluar `vue-draggable-plus` o HTML5 nativo. Preferir nativo si el caso es simple (lista plana, sin anidamiento); librería si aparece complejidad.
- **Reorder con carrera en red.** Si dos usuarios reordenan a la vez, el último gana. Aceptable por el volumen esperado; no invertir en locking optimista.

---

## Siguientes pasos

1. Plan técnico con desglose de PRs (G1 aislado, G2+G3 juntos, R1+R2 juntos).
2. Decidir librería drag & drop antes de empezar R2.
3. Rehacer el seeder de catálogo con la taxonomía de `treatment_scope` nueva, incluyendo globales por defecto.
