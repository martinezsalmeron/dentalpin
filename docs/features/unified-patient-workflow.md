# Plan: Flujo Unificado de Trabajo del Paciente

> **Issue relacionada:** [#38 - Link budgets, appointments, and treatment plans](https://github.com/martinezsalmeron/dentalpin/issues/38)
>
> **Estado:** ✅ Validado - Decisiones tomadas
>
> **Fecha:** 2026-04-15

---

## Índice

1. [Análisis del Estado Actual](#1-análisis-del-estado-actual)
2. [Problemas Identificados](#2-problemas-identificados)
3. [Propuesta de Arquitectura](#3-propuesta-de-arquitectura)
4. [Flujo de UX Propuesto](#4-flujo-de-ux-propuesto)
5. [Modelo de Datos](#5-modelo-de-datos)
6. [Plan de Implementación](#6-plan-de-implementación)
7. [Decisiones Tomadas](#7-decisiones-tomadas)

---

## 1. Análisis del Estado Actual

### Módulos Existentes y Relaciones

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ESTADO ACTUAL                                      │
└─────────────────────────────────────────────────────────────────────────────┘

TreatmentCatalogItem (Catálogo)
        │
        │ 1:1 (catalog_item_id)
        ▼
TreatmentOdontogramMapping ──────────► Reglas de visualización (SVG/color)
        │
        │ (No hay relación directa con ToothTreatment)
        │

ToothTreatment (Odontograma)
        │
        │ catalog_item_id (1:1)
        │ tooth_number (1 diente)
        │ surfaces (lista de superficies para ESE diente)
        │
        ▼
BudgetItem
        │
        │ tooth_treatment_id (1:1 con ToothTreatment)
        │ tooth_number (1 diente - redundante)
        │ surfaces (lista - redundante)
        │
        ▼
InvoiceItem
        │
        │ budget_item_id (trazabilidad)
        │ tooth_number, surfaces (snapshotted)

Appointment
        │
        │ AppointmentTreatment (tabla junction)
        │
        └──► catalog_item_id (solo referencia al catálogo, no tracking de estado)
```

### Flujo Actual del Usuario

1. **Odontograma:** Dentista marca tratamientos uno por uno en cada diente
2. **Presupuesto:** Se crea manualmente, puede referenciar ToothTreatment
3. **Factura:** Se crea desde presupuesto (parcial o total)
4. **Citas:** Se crean independientemente, solo referencian catálogo

### Lo que SÍ funciona

- ✅ Catálogo de tratamientos con precios y IVA
- ✅ Odontograma con estados (existing/planned)
- ✅ Presupuestos con firma digital y versionado
- ✅ Facturas con facturación parcial
- ✅ Snapshotting de precios en cada nivel
- ✅ Visualización de tratamientos en odontograma (TreatmentOdontogramMapping)

---

## 2. Problemas Identificados

### 2.1 Relación 1:1 entre Catálogo y Odontograma

**Problema:** Un `TreatmentCatalogItem` solo puede mapear a UN tipo de tratamiento visual.

**Ejemplo real:**
- "Rehabilitación completa" (30.000€) debería incluir:
  - 8 coronas (molares)
  - 4 implantes
  - 6 carillas (anteriores)

**Actualmente:** El dentista tendría que añadir 18 tratamientos individuales, cada uno referenciando un item diferente del catálogo.

### 2.2 Falta de concepto "Plan de Tratamiento"

**Problema:** No existe una entidad que agrupe tratamientos relacionados.

**Escenario:**
- Paciente necesita: endodoncia + poste + corona en diente #36
- Estos 3 tratamientos deberían estar agrupados como "unidad de trabajo"
- Deben seguir un orden específico
- El estado de uno afecta a los demás

**Actualmente:** Son 3 tratamientos inconexos.

### 2.3 Desconexión Citas ↔ Tratamientos

**Problema:** `AppointmentTreatment` solo referencia `catalog_item_id`, no el tratamiento específico del paciente.

**Consecuencia:**
- No se puede saber qué tratamientos específicos se realizaron en cada cita
- No hay actualización automática de estados
- No hay trazabilidad del progreso del plan

### 2.4 Falta de Tracking de Progreso

**Problema:** No hay forma de visualizar:
- ¿Qué tratamientos están pendientes?
- ¿Cuáles se han completado?
- ¿Cuántas citas faltan?
- ¿Cuánto del presupuesto se ha facturado?

### 2.5 Elementos Adicionales en Tratamientos

**Problema:** Los tratamientos no pueden incluir:
- Imágenes (antes/después, radiografías)
- Notas clínicas
- Múltiples dientes (tratamientos multi-diente)

---

## 3. Propuesta de Arquitectura

### 3.1 Nuevo Modelo Conceptual

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ARQUITECTURA PROPUESTA                             │
│                    (Reutilizando ToothTreatment existente)                   │
└─────────────────────────────────────────────────────────────────────────────┘

TreatmentCatalogItem (Catálogo)
        │
        │ Define: nombre, precio, IVA, duración, billing_mode
        │
        ▼
┌──────────────────────────────────────────────────────────────┐
│  ToothTreatment (EXISTENTE - EXTENDIDO)                      │
│  ─────────────────────────────────────────────────────────── │
│  - patient_id, catalog_item_id                               │
│  - tooth_number: int | null (null = global)                  │
│  - surfaces: ["M","O"]                                       │
│  - status: "existing" | "planned" (YA EXISTE)                │
│  + treatment_plan_id (NUEVO, opcional)                       │
│  + sequence_order (NUEVO)                                    │
│  + completed_without_appointment (NUEVO)                     │
└────────────────────────┬─────────────────────────────────────┘
                         │
        ┌────────────────┼─────────────────┐
        │                │                 │
        ▼                ▼                 ▼
┌─────────────┐  ┌──────────────┐  ┌────────────────────┐
│TreatmentPlan│  │TreatmentMedia│  │AppointmentTreatment│
│   (NUEVO)   │  │   (NUEVO)    │  │    (EXTENDIDO)     │
│             │  │              │  │                    │
│ Agrupa      │  │ Imágenes     │  │ tooth_treatment_id │
│ ToothTreat- │  │ antes/después│  │ (vincular cita con │
│ ments       │  │ rayos X      │  │  tratamiento)      │
└──────┬──────┘  └──────────────┘  └─────────┬──────────┘
       │                                     │
       ▼                                     ▼
┌─────────────┐                      ┌─────────────┐
│   Budget    │◄─────────────────────│ Appointment │
└─────────────┘   (budget_id)        └─────────────┘
```

### Tipos de ToothTreatment

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  DIAGNÓSTICOS (treatment_category = "diagnostico")                           │
│  ─────────────────────────────────────────────────────────────────────────  │
│  caries, pulpitis, fractura, diente rotado, periapical, etc.                │
│                                                                              │
│  ✓ status = "existing" (SIEMPRE)                                            │
│  ✓ treatment_plan_id = NULL (SIEMPRE)                                       │
│  ✓ Solo registran hallazgos, no son tratamientos a realizar                 │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  TRATAMIENTOS (treatment_category = restauradora|cirugia|endodoncia|ortod.) │
│  ─────────────────────────────────────────────────────────────────────────  │
│  empaste, corona, endodoncia, extracción, implante, bracket, etc.           │
│                                                                              │
│  ✓ status = "planned" → pendiente, aparece como PREVISTO en odontograma     │
│  ✓ status = "existing" → realizado, aparece como EXISTENTE en odontograma   │
│  ✓ treatment_plan_id → opcional, si está en un plan                         │
│  ✓ tooth_number = null → tratamiento global (fluorización, limpieza)        │
└─────────────────────────────────────────────────────────────────────────────┘

                    LÓGICA ÚNICA - SIN DUPLICACIÓN
```

### 3.2 Cambios Clave

#### A) `TreatmentPlan` (Nueva entidad)
- Agrupa tratamientos relacionados de un paciente
- Permite crear "casos" o "rehabilitaciones"
- Estado general del plan
- Vinculado a UN presupuesto

#### B) `ToothTreatment` (Extender existente - NO crear PlannedTreatment)

**Reutilizamos la lógica existente de `status: "existing" | "planned"`:**

| Tipo | Categoría | Status permitido | ¿En plan? |
|------|-----------|------------------|-----------|
| **Diagnóstico** | `diagnostico` | Solo `existing` | ❌ Nunca |
| **Tratamiento** | `restauradora`, `cirugia`, `endodoncia`, `ortodoncia` | `existing` o `planned` | ✅ Opcional |

**Campos nuevos:**
- `treatment_plan_id` (opcional, solo para tratamientos no-diagnósticos)
- `sequence_order` (orden dentro del plan)
- `tooth_number` → hacerlo nullable (para tratamientos globales)
- `completed_without_appointment` (flag para urgencias)

**Lógica de estados (sin cambios, ya existe):**
- `status = "planned"` → tratamiento pendiente, aparece como "previsto" en odontograma
- `status = "existing"` → tratamiento realizado o diagnóstico, aparece como "existente"
- Al completar tratamiento: `status` cambia de `"planned"` → `"existing"`

#### C) `TreatmentMedia` (Nueva entidad)
- Imágenes/documentos asociados a tratamientos
- Tipos: before/after/xray/reference
- Reutiliza módulo `media` existente
- FK a `ToothTreatment` (solo para tratamientos, no diagnósticos)

#### D) Cambios en otras entidades existentes

**BudgetItem:**
- Mantener: `tooth_treatment_id` (ya existe, apunta a ToothTreatment)
- Mantener: `tooth_number`, `surfaces` (snapshotted)

**AppointmentTreatment:**
- Añadir: `tooth_treatment_id` (vincular con tratamiento específico del plan)
- Añadir: `completed_in_appointment` (marcar si se completó aquí)
- Añadir: `notes` (notas de esta cita)
- Mantener: `catalog_item_id` (para casos sin plan)

---

## 4. Flujo de UX Propuesto

### 4.1 Flujo Principal: Creación de Plan de Tratamiento

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  FLUJO DEL PROFESIONAL                                                       │
└─────────────────────────────────────────────────────────────────────────────┘

1. EXAMINAR PACIENTE
   │
   ├── Opción A: Desde Odontograma
   │   └── Marcar hallazgos (caries, fracturas, etc.)
   │   └── Clic "Crear Plan de Tratamiento"
   │   └── Seleccionar hallazgos a incluir
   │
   └── Opción B: Desde ficha del paciente
       └── Clic "Nuevo Plan de Tratamiento"
       └── Añadir tratamientos manualmente

2. CONFIGURAR PLAN
   │
   ├── Añadir tratamientos del catálogo
   │   └── Seleccionar tratamiento
   │   └── Asignar dientes (picker visual)
   │   └── Asignar superficies si aplica
   │   └── Añadir notas
   │   └── Establecer prioridad/orden
   │
   ├── Añadir imágenes (opcional)
   │   └── Arrastrar/subir imágenes
   │   └── Clasificar: antes/rayos X/referencia
   │
   └── Vista previa en odontograma (automática)

3. GENERAR PRESUPUESTO (automático o manual)
   │
   ├── Un clic: "Crear presupuesto desde plan"
   │   └── Cada ToothTreatment del plan → BudgetItem(s)
   │   └── Precios desde catálogo
   │   └── Descuentos opcionales
   │
   └── Enviar a paciente / Firmar

4. PROGRAMAR CITAS
   │
   ├── Desde Plan: "Programar tratamiento"
   │   └── Seleccionar tratamiento(s)
   │   └── Crear cita con duración sugerida
   │
   └── Desde Agenda: Arrastrar tratamiento pendiente a slot

5. EJECUTAR TRATAMIENTO (durante cita)
   │
   ├── Ver tratamientos programados para hoy
   ├── Marcar como "En progreso"
   ├── Añadir notas de sesión
   ├── Subir imagen "después" (opcional)
   └── Marcar como "Completado"
       └── Auto-actualiza odontograma
       └── Auto-actualiza progreso del plan
       └── Opcional: Auto-facturar

6. SEGUIMIENTO
   │
   ├── Vista de progreso del plan (% completado)
   ├── Próximas citas
   ├── Tratamientos pendientes
   └── Estado de facturación
```

### 4.2 Vista del Plan de Tratamiento (UI)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Plan de Tratamiento: Rehabilitación Sector 1                    [Estado: Activo] │
│  Paciente: Juan García                                                       │
│  Creado: 15/04/2026 por Dr. Martínez                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  ODONTOGRAMA (Vista previa)                                          │   │
│  │  [Visualización de dientes con tratamientos coloreados]              │   │
│  │  Leyenda: 🔵 Pendiente  🟡 Programado  🟢 Completado                  │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  TRATAMIENTOS                                           Progreso: 2/5 (40%) │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                              │
│  ✅ 1. Endodoncia - Diente #16                                    Completado│
│     └── Completado: 01/04/2026                                              │
│     └── [📷 Ver imágenes]                                                   │
│                                                                              │
│  ✅ 2. Poste de fibra - Diente #16                                Completado│
│     └── Completado: 08/04/2026                                              │
│                                                                              │
│  🟡 3. Corona metal-cerámica - Diente #16                        Programado │
│     └── Próxima cita: 20/04/2026 10:00                                      │
│     └── [Reagendar] [Cancelar]                                              │
│                                                                              │
│  🔵 4. Limpieza profunda - Cuadrante 1 (#14-18)                   Pendiente │
│     └── Dientes: 14, 15, 16, 17, 18                                         │
│     └── [Programar cita]                                                    │
│                                                                              │
│  🔵 5. Empaste composite - Diente #15 (M,O)                       Pendiente │
│     └── Superficies: Mesial, Oclusal                                        │
│     └── [Programar cita]                                                    │
│                                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│  PRESUPUESTO ASOCIADO                                                        │
│  └── PRES-2024-0045 | Total: 2.350€ | Facturado: 890€ | Pendiente: 1.460€  │
│      [Ver presupuesto] [Facturar pendiente]                                 │
│                                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│  IMÁGENES                                                                    │
│  ┌────────┐  ┌────────┐  ┌────────┐                                         │
│  │ RX     │  │ Antes  │  │ Desp.  │  [+ Añadir imagen]                      │
│  │ inicial│  │ endo   │  │ endo   │                                         │
│  └────────┘  └────────┘  └────────┘                                         │
│                                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│  ACCIONES                                                                    │
│  [Añadir tratamiento] [Generar presupuesto] [Programar citas] [Archivar]    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.3 Interacción Odontograma ↔ Plan

#### Crear plan desde odontograma:
1. Dentista marca hallazgos en odontograma (caries en #16, #26, #36)
2. Clic derecho o botón "Crear plan"
3. Sistema sugiere tratamientos del catálogo basados en hallazgos
4. Dentista confirma/modifica selección
5. Plan creado con tratamientos vinculados

#### Visualizar plan en odontograma:
1. Al abrir odontograma con plan activo
2. Dientes con tratamientos muestran indicador de estado
3. Hover muestra detalle del tratamiento
4. Colores por estado: pendiente/programado/completado

---

## 5. Modelo de Datos

### 5.1 Nuevas Entidades

```python
# treatment_plan.py

class TreatmentPlan(Base):
    """Plan de tratamiento que agrupa tratamientos relacionados."""
    __tablename__ = "treatment_plans"

    id: Mapped[UUID]
    clinic_id: Mapped[UUID]  # Multi-tenancy
    patient_id: Mapped[UUID]  # FK patients

    # Estado del plan
    status: Mapped[str]  # draft, active, completed, archived, cancelled

    # Metadata
    name: Mapped[str | None]  # "Rehabilitación sector 1" (auto-generado si no se especifica)
    description: Mapped[str | None]

    # Presupuesto asociado (1:1)
    budget_id: Mapped[UUID | None]  # FK budgets (opcional, se genera después)

    # Profesional responsable
    assigned_professional_id: Mapped[UUID | None]
    created_by: Mapped[UUID]  # Usuario que creó

    # Fechas
    started_at: Mapped[datetime | None]
    completed_at: Mapped[datetime | None]
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]

    # Relationships
    treatments: Mapped[list["ToothTreatment"]]  # Solo los que tienen treatment_plan_id
    patient: Mapped["Patient"]
    budget: Mapped["Budget | None"]


class TreatmentMedia(Base):
    """Imágenes y documentos asociados a un tratamiento."""
    __tablename__ = "treatment_media"

    id: Mapped[UUID]
    clinic_id: Mapped[UUID]
    tooth_treatment_id: Mapped[UUID]  # FK tooth_treatments
    document_id: Mapped[UUID]  # FK documents (módulo media)

    # Tipo de media
    media_type: Mapped[str]  # "before", "after", "xray", "model", "reference"

    # Contexto
    captured_at: Mapped[datetime | None]  # Cuándo se tomó
    notes: Mapped[str | None]

    # Ordenación
    display_order: Mapped[int]

    created_at: Mapped[datetime]

    # Relationships
    tooth_treatment: Mapped["ToothTreatment"]
    document: Mapped["Document"]
```

### 5.2 Modificaciones a Entidades Existentes

```python
# ToothTreatment (odontogram) - EXTENDER
class ToothTreatment(Base):
    __tablename__ = "tooth_treatments"

    # ... campos existentes (id, clinic_id, patient_id, tooth_number, surfaces,
    #     treatment_type, treatment_category, status, catalog_item_id, etc.) ...

    # MODIFICAR: tooth_number ahora es opcional (null = tratamiento global)
    tooth_number: Mapped[int | None]  # Antes era requerido

    # NUEVOS CAMPOS:
    treatment_plan_id: Mapped[UUID | None]  # FK treatment_plans (solo para tratamientos, no diagnósticos)
    sequence_order: Mapped[int | None]  # Orden dentro del plan
    completed_without_appointment: Mapped[bool]  # Default False

    # VALIDACIÓN (en service layer):
    # - Si treatment_category == "diagnostico":
    #     status DEBE ser "existing"
    #     treatment_plan_id DEBE ser None
    # - Si tooth_number es None: tratamiento global (fluorización, limpieza)


# AppointmentTreatment - EXTENDER
class AppointmentTreatment(Base):
    __tablename__ = "appointment_treatments"

    # ... campos existentes (id, clinic_id, appointment_id, catalog_item_id) ...

    # NUEVOS CAMPOS:
    tooth_treatment_id: Mapped[UUID | None]  # FK tooth_treatments (vincular con tratamiento específico)
    notes: Mapped[str | None]  # Notas de esta cita
    completed_in_appointment: Mapped[bool]  # Default False, marca si se completó aquí


# BudgetItem - SIN CAMBIOS
# Ya tiene tooth_treatment_id que apunta a ToothTreatment


# Appointment - EXTENDER
class Appointment(Base):
    # ... campos existentes ...

    # NUEVO: Referencia al plan (opcional, para contexto)
    treatment_plan_id: Mapped[UUID | None]  # FK treatment_plans


# TreatmentCatalogItem - EXTENDER
class TreatmentCatalogItem(Base):
    # ... campos existentes ...

    # NUEVO: Modo de facturación
    billing_mode: Mapped[str]  # "on_completion" | "per_session" | "upfront"
    # Default: "on_completion"
```

### 5.3 Reglas de Validación

```python
# En ToothTreatmentService

DIAGNOSTIC_CATEGORIES = ["diagnostico"]

def validate_tooth_treatment(data: dict) -> None:
    """Valida reglas de negocio para ToothTreatment."""

    treatment_type = data.get("treatment_type")
    category = get_treatment_category(treatment_type)  # Lookup en constantes

    if category in DIAGNOSTIC_CATEGORIES:
        # Diagnósticos: siempre existing, nunca en plan
        if data.get("status") != "existing":
            raise ValidationError("Los diagnósticos deben tener status 'existing'")
        if data.get("treatment_plan_id") is not None:
            raise ValidationError("Los diagnósticos no pueden formar parte de un plan")

    # Tratamientos globales: tooth_number puede ser null
    if data.get("tooth_number") is None:
        if category in DIAGNOSTIC_CATEGORIES:
            raise ValidationError("Los diagnósticos requieren un diente específico")
```

### 5.4 Diagrama de Relaciones

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      MODELO DE DATOS SIMPLIFICADO                            │
│                   (ToothTreatment como entidad central)                      │
└─────────────────────────────────────────────────────────────────────────────┘

                    TreatmentCatalogItem
                           │
                           │ (catalog_item_id)
                           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      ToothTreatment (EXTENDIDA)                              │
│  ────────────────────────────────────────────────────────────────────────── │
│  Campos existentes: patient_id, tooth_number, surfaces, treatment_type,     │
│                     status ("existing"|"planned"), catalog_item_id          │
│  Campos nuevos:     treatment_plan_id, sequence_order,                      │
│                     completed_without_appointment                           │
└─────────────────────────────────────────────────────────────────────────────┘
        │                    │                    │
        │                    │                    │
        ▼                    ▼                    ▼
┌─────────────┐      ┌──────────────┐    ┌────────────────────┐
│TreatmentPlan│      │TreatmentMedia│    │AppointmentTreatment│
│   (NUEVA)   │      │   (NUEVA)    │    │   (EXTENDIDA)      │
│             │      │              │    │                    │
│ Agrupa      │      │ before/after │    │ tooth_treatment_id │
│ tratamientos│      │ xray/ref     │    │ completed_in_appt  │
└──────┬──────┘      └──────────────┘    └─────────┬──────────┘
       │                                           │
       │ (budget_id)                               │ (appointment_id)
       ▼                                           ▼
┌─────────────┐                           ┌─────────────┐
│   Budget    │                           │ Appointment │
│             │                           │             │
│ BudgetItem  │◄──────────────────────────│             │
│(tooth_treat-│   (tooth_treatment_id)    │             │
│ ment_id)    │                           │             │
└──────┬──────┘                           └─────────────┘
       │
       ▼
┌─────────────┐
│  Invoice    │
│ InvoiceItem │
└─────────────┘

TreatmentOdontogramMapping ──► Reglas visualización (SVG/color por treatment_type)
```

---

## 6. Plan de Implementación

### Fase 1: Modelo de Datos (Backend)

**Objetivo:** Crear nuevas entidades y extender existentes.

1. Crear modelos nuevos:
   - `TreatmentPlan` (agrupa tratamientos)
   - `TreatmentMedia` (imágenes asociadas)

2. Extender modelos existentes:
   - `ToothTreatment`: añadir `treatment_plan_id`, `sequence_order`, `completed_without_appointment`
   - `ToothTreatment`: hacer `tooth_number` nullable (para tratamientos globales)
   - `AppointmentTreatment`: añadir `tooth_treatment_id`, `completed_in_appointment`, `notes`
   - `Appointment`: añadir `treatment_plan_id`
   - `TreatmentCatalogItem`: añadir `billing_mode`

3. Migraciones:
   - Nuevas tablas: `treatment_plans`, `treatment_media`
   - Alteraciones a tablas existentes
   - NO hay migración de datos compleja (ToothTreatment ya existe)

### Fase 2: API de Planes de Tratamiento (Backend)

**Endpoints:**

```
# Planes de tratamiento
POST   /api/v1/treatment-plans                    # Crear plan
GET    /api/v1/treatment-plans                    # Listar planes
GET    /api/v1/treatment-plans/{id}               # Detalle plan
PUT    /api/v1/treatment-plans/{id}               # Actualizar plan
DELETE /api/v1/treatment-plans/{id}               # Archivar plan

# Tratamientos dentro del plan
POST   /api/v1/treatment-plans/{id}/treatments    # Añadir tratamiento
PUT    /api/v1/treatment-plans/{id}/treatments/{tid}  # Actualizar
DELETE /api/v1/treatment-plans/{id}/treatments/{tid}  # Eliminar
PATCH  /api/v1/treatment-plans/{id}/treatments/{tid}/status  # Cambiar estado

# Media de tratamientos
POST   /api/v1/tooth-treatments/{id}/media        # Añadir imagen
DELETE /api/v1/tooth-treatments/{id}/media/{mid}  # Eliminar

# Generación automática
POST   /api/v1/treatment-plans/{id}/generate-budget  # Crear presupuesto
POST   /api/v1/treatment-plans/from-odontogram    # Crear desde hallazgos

# Programación
POST   /api/v1/tooth-treatments/{id}/schedule     # Programar cita
```

### Fase 3: Integración Odontograma ↔ Plan (Backend + Frontend)

1. **Backend:**
   - Endpoint para crear plan desde hallazgos del odontograma
   - Al añadir ToothTreatment a plan → asignar `treatment_plan_id`
   - Validación: diagnósticos no pueden tener `treatment_plan_id`

2. **Frontend:**
   - Botón "Crear plan" en odontograma (selecciona tratamientos planned)
   - Toggle "mostrar plan" integrado con toggle existente (existentes/previstos)
   - Badges discretos por estado

### Fase 4: Integración con Presupuestos (Backend + Frontend)

1. **Backend:**
   - Generar BudgetItems desde ToothTreatments del plan
   - BudgetItem.tooth_treatment_id apunta a ToothTreatment
   - Auto-sync mientras presupuesto en borrador

2. **Frontend:**
   - Botón "Generar presupuesto" en vista de plan
   - Visualización de estado de presupuesto en plan

### Fase 5: Integración con Citas (Backend + Frontend)

1. **Backend:**
   - Vincular AppointmentTreatment con ToothTreatment via `tooth_treatment_id`
   - Al marcar `completed_in_appointment = True`:
     - Actualizar `ToothTreatment.status` → `"existing"`
   - Sugerir tratamientos pendientes al crear cita

2. **Frontend:**
   - Vista de cita muestra tratamientos a realizar
   - Checkbox para marcar completados
   - Campo de notas por tratamiento

### Fase 6: Vista Unificada del Plan (Frontend)

1. Página `/patients/{id}/treatment-plans`
2. Componente `TreatmentPlanView.vue`
3. Integración con odontograma (visualización)
4. Dashboard de progreso
5. Timeline de citas

### Fase 7: Facturación Automática (Backend + Frontend)

1. **Backend:**
   - Facturar tratamientos completados
   - Tracking de qué está facturado

2. **Frontend:**
   - Indicadores de facturación en plan
   - Botón "Facturar completados"

---

## 7. Decisiones Tomadas

> ✅ Todas las decisiones han sido validadas.

### 7.1 Tratamientos y dientes

**Decisión:** Tres tipos según scope del tratamiento:

| Tipo | Campo `teeth` | Ejemplo |
|------|---------------|---------|
| **Global** | `null` | Fluoración, limpieza bucal general |
| **Por diente** | `[16]` (un registro por diente) | Empaste, corona, endodoncia |
| **Multi-diente precio único** | `[14,15,16,17,18]` | Raspado cuadrante, férula |

- Tratamientos por diente: si hay 2 empastes (#16 y #26), se crean **2 ToothTreatment**.
- No hace falta `group_id` - el `TreatmentPlan` ya agrupa.

### 7.2 Sesiones múltiples

**Decisión:** Sin tracking de sesiones. Solo estado del tratamiento.

- El profesional marca manualmente cuando termina.
- Simplifica modelo. Sin `estimated_sessions` ni `completed_sessions`.
- `AppointmentTreatment` vincula cita con tratamiento realizado.

### 7.3 Sincronización Plan ↔ Presupuesto

**Decisión:** Auto-sincronizar mientras presupuesto esté en borrador.

| Estado presupuesto | Comportamiento |
|-------------------|----------------|
| `draft` | Cambios en plan actualizan presupuesto automáticamente |
| `sent` o posterior | Botón "Crear nueva versión del presupuesto" |

- Nunca auto-modificar presupuesto firmado.
- Nueva versión hereda items del plan actualizado.

### 7.4 Tratamientos sin cita

**Decisión:** Flag `completed_without_appointment`.

- Permitir marcar completado manualmente sin cita asociada.
- Campo `completed_without_appointment: bool` en `ToothTreatment`.
- Sin crear citas virtuales (más simple).

### 7.5 Facturación

**Decisión:** Flexible, configurable por tratamiento.

- Nuevo campo en `TreatmentCatalogItem`:
  ```python
  billing_mode: Mapped[str]  # "on_completion" | "per_session" | "upfront"
  ```
- `on_completion`: factura cuando tratamiento completo.
- `per_session`: permite facturación parcial/anticipada.
- `upfront`: facturar al aceptar presupuesto.

### 7.6 Notificaciones

**Decisión:** Fase posterior.

- Priorizar funcionalidad core primero.
- Integrar con módulo notificaciones existente después.

### 7.7 Plan obligatorio

**Decisión:** Plan automático implícito.

- Si usuario añade tratamiento sin plan, sistema crea plan automáticamente.
- Nombre auto-generado: "Plan {fecha}" o "Tratamiento {nombre_tratamiento}".
- Mantiene organización sin fricción.

### 7.8 Visualización en odontograma

**Decisión:** Badges discretos con toggle.

- Iconos/badges junto a cada diente afectado.
- Toggle on/off integrado con funcionalidad existente "existentes/previstos".
- No modifica visualización base del diente.
- Hover muestra detalle del tratamiento.

---

## Próximos Pasos

1. ~~**Validar este documento** con stakeholders~~ ✅
2. ~~**Resolver decisiones pendientes** (sección 7)~~ ✅
3. **Crear plan técnico detallado** con:
   - Definición exacta de modelos (SQLAlchemy)
   - Endpoints con schemas (Pydantic)
   - Migraciones
   - Tests
4. **Estimar y priorizar** fases de implementación
5. **Desarrollar** fase por fase con tests

---

## Resumen Ejecutivo

### Problema
Los módulos de odontograma, presupuesto, citas y facturas operan independientemente, forzando trabajo manual y perdiendo trazabilidad.

### Solución
Nueva entidad `TreatmentPlan` que:
- Agrupa tratamientos relacionados
- Soporta múltiples dientes/superficies
- Vincula con presupuesto, citas y odontograma
- Permite tracking de progreso
- Soporta imágenes y notas

### Beneficios
1. **Para el profesional:**
   - Un lugar para gestionar todo el caso
   - Auto-generación de presupuestos
   - Programación inteligente de citas
   - Vista de progreso

2. **Para la clínica:**
   - Trazabilidad completa
   - Menos errores de facturación
   - Mejor gestión de casos complejos

3. **Para el paciente:**
   - Visibilidad de su plan
   - Transparencia en costos
   - Tracking de su tratamiento
