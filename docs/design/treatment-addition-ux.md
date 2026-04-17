# Plan de UX: Sistema de Tratamientos Dentales

**Fecha:** 2026-04-17
**Estado:** Propuesta
**Autor:** Análisis UX

---

## Índice

1. [Contexto y Alcance](#1-contexto-y-alcance)
2. [Análisis del Estado Actual](#2-análisis-del-estado-actual)
3. [Taxonomía de Tratamientos](#3-taxonomía-de-tratamientos)
4. [PARTE A: Mejoras del Módulo Odontograma](#4-parte-a-mejoras-del-módulo-odontograma)
5. [PARTE B: Mejoras de la Ficha de Plan de Tratamiento](#5-parte-b-mejoras-de-la-ficha-de-plan-de-tratamiento)
6. [Flujos de Usuario](#6-flujos-de-usuario)
7. [Sincronización Odontograma ↔ Plan](#7-sincronización-odontograma--plan)
8. [Estados y Feedback](#8-estados-y-feedback)
9. [Consideraciones de Accesibilidad](#9-consideraciones-de-accesibilidad)
10. [Resumen y Priorización](#10-resumen-y-priorización)

---

## 1. Contexto y Alcance

### 1.1 Dos Contextos de Uso del Odontograma

El odontograma se usa en DOS contextos diferentes con necesidades distintas:

| Contexto | Ubicación | Propósito | Status de tratamientos |
|----------|-----------|-----------|------------------------|
| **Diagnóstico** | Pestaña "Diagnóstico" en ficha paciente | Registrar estado actual de la boca | Solo `existing` |
| **Planificación** | Ficha de Plan de Tratamiento | Planificar tratamientos futuros | Solo `planned` |

### 1.2 Modelo de Sincronización

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CICLO DE VIDA                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  DIAGNÓSTICO (existing)              PLANIFICACIÓN (planned)        │
│  ─────────────────────               ─────────────────────          │
│                                                                     │
│  Usuario registra:                   Usuario planifica:             │
│  • Caries existente                  • Empaste para caries          │
│  • Puente existente                  • Nuevo puente                 │
│  • Corona vieja                      • Corona a reemplazar          │
│         │                                     │                     │
│         │                                     │                     │
│         ▼                                     ▼                     │
│  ToothTreatment                      ToothTreatment                 │
│  status: "existing"                  status: "planned"              │
│                                             │                       │
│                                             │                       │
│                                             ▼                       │
│                                      PlannedTreatmentItem           │
│                                      status: "pending"              │
│                                             │                       │
│                                             │ [Marcar completado]   │
│                                             ▼                       │
│                                      PlannedTreatmentItem           │
│                                      status: "completed"            │
│                                             │                       │
│                                             │ [Auto-sync]           │
│                                             ▼                       │
│                                      ToothTreatment                 │
│                                      status: "existing" ◄───────────┘
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Regla clave:** Al marcar un tratamiento como "completado" en el plan, el ToothTreatment cambia de `planned` a `existing`, reflejando que ya se realizó.

### 1.3 Alcance de Este Documento

| Sección | Aplica a | Descripción |
|---------|----------|-------------|
| **PARTE A** | Odontograma (Diagnóstico + Plan) | Mejoras del componente base |
| **PARTE B** | Solo Ficha de Plan | Mejoras específicas de planificación |

---

## 2. Análisis del Estado Actual

### 2.1 Problemas del Módulo Odontograma (afectan Diagnóstico Y Plan)

| Problema | Impacto | Severidad |
|----------|---------|-----------|
| No hay soporte para tratamientos multi-diente | No se pueden registrar puentes existentes ni planificar nuevos | **Crítica** |
| Modal de superficies interrumpe el flujo | Fatiga de clics, pérdida de contexto | Media |
| Sin feedback visual claro al aplicar tratamiento | Usuario no sabe si funcionó | Alta |
| Barra de tratamientos no indica estado de selección | Confusión sobre qué está activo | Alta |

### 2.2 Problemas Específicos de la Ficha de Plan

| Problema | Impacto | Severidad |
|----------|---------|-----------|
| Desconexión: crear tratamiento no lo añade al plan | Tratamientos creados no aparecen en lista | **Crítica** |
| No hay integración con catálogo de precios | Presupuesto no se calcula automáticamente | Alta |
| Sin guía al usuario para empezar | No hay instrucciones claras | Alta |
| Sin tratamientos globales (limpieza, etc.) | Funcionalidad incompleta | Alta |
| Lista del plan no muestra preview de presupuesto | Usuario no ve valor monetario | Media |

### 2.3 Lo Que Funciona Bien

- Categorías de tratamientos organizadas
- Iconos visuales intuitivos
- Modo "planning" que filtra tratamientos terapéuticos
- Existe catálogo de tratamientos con precios

---

## 3. Taxonomía de Tratamientos

### 3.1 Clasificación por Selección de Dientes

```
TRATAMIENTOS
│
├── DIENTE ÚNICO (tooth_number: number)
│   ├── Diente Completo (sin superficies)
│   │   ├── Extracción
│   │   ├── Implante
│   │   ├── Corona unitaria
│   │   └── Endodoncia
│   │
│   └── Superficie(s) de Diente (surfaces: string[])
│       ├── Empaste/Obturación
│       ├── Sellador
│       └── Incrustación
│
├── MULTI-DIENTE (tooth_numbers: number[])
│   ├── Rango Continuo (dientes adyacentes)
│   │   ├── Puente fijo metal-cerámica
│   │   ├── Puente fijo zirconio
│   │   └── Puente Maryland
│   │
│   ├── Selección Libre (cualquier combinación)
│   │   ├── Férula periodontal
│   │   ├── Carillas múltiples
│   │   └── Coronas múltiples
│   │
│   └── Arcada Completa
│       ├── Férula de descarga
│       └── Prótesis parcial removible
│
└── GLOBALES (is_global: true) ─── Solo en Plan, no en Diagnóstico
    ├── Boca Completa
    │   ├── Limpieza/Profilaxis
    │   ├── Blanqueamiento
    │   └── Fluorización
    │
    └── Por Arcada
        ├── Ortodoncia
        └── Prótesis completa
```

### 3.2 Matriz de Interacción

| Tipo | Contextos | Selección | Superficies | Precio |
|------|-----------|-----------|-------------|--------|
| **DIENTE ÚNICO** |
| Extracción | Diagnóstico + Plan | 1 clic | No | Catálogo |
| Corona unitaria | Diagnóstico + Plan | 1 clic | No | Catálogo |
| Empaste | Diagnóstico + Plan | 1 clic + superficies | Sí | Catálogo × nº |
| **MULTI-DIENTE** |
| Puente existente | Solo Diagnóstico | Clic inicio + fin | No | — |
| Puente planificado | Solo Plan | Clic inicio + fin | No | Catálogo × piezas |
| Carillas múltiples | Diagnóstico + Plan | Clics múltiples | No | Catálogo × piezas |
| Férula | Diagnóstico + Plan | Clics múltiples | No | Catálogo |
| **GLOBALES** |
| Limpieza | Solo Plan | Ninguno | No | Catálogo |
| Blanqueamiento | Solo Plan | Ninguno | No | Catálogo |

### 3.3 Modos de Selección Multi-Diente

| Patrón | Descripción | Uso | Interacción |
|--------|-------------|-----|-------------|
| **Rango Continuo** | Dientes adyacentes | Puentes | Clic inicio + clic fin |
| **Selección Libre** | Cualquier combinación | Carillas, férulas | Clics múltiples + confirmar |
| **Arcada Completa** | Todos de una arcada | Férula descarga | Botón "Arcada superior/inferior" |

**Validaciones:**

| Tratamiento | Mínimo | Máximo | Restricción |
|-------------|--------|--------|-------------|
| Puente fijo | 3 | 14 | Dientes contiguos, misma arcada |
| Férula periodontal | 2 | 14 | Misma arcada |
| Carillas | 2 | 10 | Zona estética recomendada |

---

## 4. PARTE A: Mejoras del Módulo Odontograma

> **Estas mejoras aplican TANTO a la pestaña Diagnóstico COMO a la ficha de Plan de Tratamiento.**

### 4.1 A1: Soporte Multi-Diente

**Estado actual:** No existe forma de registrar tratamientos que abarcan varios dientes.

**Propuesta:**

#### Modo Rango Continuo (Puentes)

```
┌────────────────────────────────────────────────────────────────┐
│ 🌉 Puente fijo                    Seleccionados: 14, 15, 16    │
│    Clic en diente inicial, luego en diente final   [Cancelar] │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│     [18][17][16][15][14][13][12][11] [21][22][23]...          │
│            ███ ─── ███ ─── ███                                 │
│            │       │       │                                   │
│           FIN    (auto)  INICIO                                │
│            │               │                                   │
│            └───────┬───────┘                                   │
│                    │                                           │
│             ┌──────┴──────┐                                    │
│             │ Puente      │                                    │
│             │ 14 ─ 15 ─ 16│                                    │
│             │             │                                    │
│             │ Pilares: 14, 16                                  │
│             │ Póntico: 15 │                                    │
│             │             │                                    │
│             │[Cancel][OK] │                                    │
│             └─────────────┘                                    │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

**Flujo:**
1. Usuario selecciona "Puente fijo" en barra de tratamientos
2. Banner indica: "Clic en diente inicial, luego en diente final"
3. Clic en diente 14 → se marca como "inicio" (borde azul)
4. Dientes adyacentes muestran línea guía punteada
5. Clic en diente 16 → sistema auto-selecciona 14, 15, 16
6. Popup confirma: pilares (14, 16) y póntico (15)
7. Confirmar → ToothTreatment creado con `tooth_numbers: [14, 15, 16]`

#### Modo Selección Libre (Carillas, Férulas)

```
┌────────────────────────────────────────────────────────────────┐
│ 😁 Carillas                       4 dientes seleccionados      │
│    Clic para añadir/quitar dientes             [Cancelar]     │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│     [...][13][12][11] [21][22][23][...]                        │
│              ███  ███  ███  ███                                │
│               ↑    ↑    ↑    ↑                                 │
│             Seleccionados (clic para quitar)                   │
│                                                                │
│     ┌─────────────────────────────────────────────┐            │
│     │ Selección: 11, 12, 21, 22    [Listo]        │            │
│     └─────────────────────────────────────────────┘            │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

**Flujo:**
1. Usuario selecciona "Carillas" en barra de tratamientos
2. Banner: "Clic para añadir/quitar dientes"
3. Clic en 11 → seleccionado (contador: 1)
4. Clic en 12 → seleccionado (contador: 2)
5. Clic en 21, 22 → seleccionados (contador: 4)
6. Clic en 12 de nuevo → deseleccionado (contador: 3)
7. Barra flotante muestra selección actual + botón "Listo"
8. Clic "Listo" → confirmar → ToothTreatment creado

### 4.2 A2: Selector de Superficies Inline

**Estado actual:** Modal que interrumpe el flujo y oculta el odontograma.

**Propuesta:** Popup inline junto al diente seleccionado.

```
                        ┌─────────────────────┐
                        │  Empaste - Diente 16│
     [14][15][16]       │  ─────────────────  │
           ↑            │                     │
           └────────────│  [M] [O] [D]        │
                        │  [V]     [L]        │
                        │                     │
                        │  Seleccionadas: MOD │
                        │                     │
                        │  [Cancelar] [OK]    │
                        └─────────────────────┘
```

**Beneficios:**
- No pierde contexto visual del odontograma
- Puede ver dientes adyacentes mientras selecciona
- Flujo más rápido (menos transiciones modales)
- Clic fuera cierra el popup

### 4.3 A3: Estados Visuales del Odontograma

| Estado | Indicadores Visuales |
|--------|---------------------|
| **Inactivo** | Dientes neutros, cursor default |
| **Tratamiento seleccionado** | Banner superior, cursor crosshair, dientes válidos con borde punteado |
| **Superficie seleccionando** | Diente destacado, popup visible, otros dientes atenuados |
| **Multi-diente seleccionando** | Banner con contador, dientes seleccionados con borde azul, línea de conexión |

### 4.4 A4: Colores y Representación Visual

| Elemento | Color/Estilo | Uso |
|----------|--------------|-----|
| Diente sano | Blanco/Gris claro | Sin tratamientos |
| Tratamiento existente | Azul sólido | Ya realizado |
| Tratamiento planificado | Azul rayado (patrón diagonal) | Por hacer |
| Diente seleccionado | Amarillo | Actualmente editando |
| Multi-diente: inicio | Azul + badge "1" | Primer diente |
| Multi-diente: fin | Azul + badge "2" | Último diente |
| Multi-diente: conexión | Línea azul entre dientes | Puente |
| Hover en modo aplicar | Verde suave | Preview |

### 4.5 A5: Barra de Tratamientos Mejorada

**Mejoras aplicables a ambos contextos:**

```
┌─────────────────────────────────────────────────────────────┐
│ TRATAMIENTOS                                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ [Diagnóstico] [Restauradora] [Protésica] [Quirúrgica]       │
│                     ▲                                       │
│                 activa                                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐           │
│  │ 🦷  │ │ 👑  │ │ 🌉  │ │ 😁  │ │ 🔧  │ │ ... │           │
│  │Empa.│ │Coron│ │Puent│ │Caril│ │Endod│ │     │           │
│  └─────┘ └─────┘ └─────┘ └─────┘ └─────┘ └─────┘           │
│     │                                                       │
│     └── Seleccionado: borde azul + fondo claro              │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ ✓ Empaste seleccionado                                      │
│   Haz clic en el diente a tratar                           │
│                                         [Cancelar selección]│
└─────────────────────────────────────────────────────────────┘
```

**Cambios:**
- Indicador visual claro del tratamiento seleccionado
- Mensaje de ayuda contextual
- Botón "Cancelar selección" visible
- Categorías filtradas según contexto (Diagnóstico muestra "Diagnóstico", Plan no)

### 4.6 A6: Atajos de Teclado (Odontograma)

| Tecla | Acción |
|-------|--------|
| `Escape` | Cancelar selección / Salir del modo |
| `Enter` | Confirmar selección actual |
| `1-5` | Superficies: M=1, O=2, D=3, V=4, L=5 |
| `Ctrl+Z` | Deshacer último tratamiento |
| `Shift+Clic` | Multi-diente: seleccionar rango |
| `Ctrl+Clic` | Multi-diente: añadir/quitar de selección |

---

## 5. PARTE B: Mejoras de la Ficha de Plan de Tratamiento

> **Estas mejoras son ESPECÍFICAS de la ficha de plan. No aplican a Diagnóstico.**

### 5.1 B1: Layout con Panel Lateral

**Estado actual:** Odontograma arriba, barra de tratamientos abajo, sin lista de plan visible.

**Propuesta:** Panel lateral derecho integrado.

```
┌────────────────────────────────────────────────────────────────┐
│ ← Paciente    Plan: Restauración completa          [Borrador] │
├────────────────────────────────────────────────────────────────┤
│                                         │                      │
│  ┌───────────────────────────────────┐  │  ┌────────────────┐  │
│  │                                   │  │  │ AÑADIR         │  │
│  │         ODONTOGRAMA               │  │  │ ────────────── │  │
│  │                                   │  │  │                │  │
│  │         (65% ancho)               │  │  │ [🦷 Diente   ] │  │
│  │                                   │  │  │ [🌐 Global   ] │  │
│  │                                   │  │  │ [📋 Catálogo ] │  │
│  │                                   │  │  │                │  │
│  └───────────────────────────────────┘  │  │ ────────────── │  │
│                                         │  │ PLAN (3)  €595 │  │
│  ┌───────────────────────────────────┐  │  │ ────────────── │  │
│  │ Empaste seleccionado              │  │  │ □ Empaste  €85 │  │
│  │ Clic en diente para aplicar       │  │  │ □ Corona  €450 │  │
│  └───────────────────────────────────┘  │  │ □ Limpiez  €60 │  │
│                                         │  │ ────────────── │  │
│                                         │  │ [Presupuesto →]│  │
│                                         │  └────────────────┘  │
│                                         │        (35%)         │
└────────────────────────────────────────────────────────────────┘
```

### 5.2 B2: Tres Modos de Añadir Tratamiento

El panel lateral ofrece tres formas de añadir tratamientos al plan:

#### Modo 1: Por Diente (🦷)

```
Clic en "🦷 Por Diente"
    ↓
Se despliega selector de tratamientos (usa TreatmentBar)
    ↓
Usuario selecciona tipo → Odontograma entra en modo aplicar
    ↓
Clic en diente(s) → Selección superficies si aplica
    ↓
Confirmar
    ↓
✓ ToothTreatment creado (status: "planned")
✓ PlannedTreatmentItem creado (status: "pending")
✓ Item aparece en lista con precio del catálogo
✓ Total se actualiza
```

#### Modo 2: Boca Completa (🌐)

```
Clic en "🌐 Boca Completa"
    ↓
Lista de tratamientos globales:
• Limpieza dental - €60
• Blanqueamiento - €180
• Fluorización - €25
    ↓
Clic en "Limpieza dental"
    ↓
✓ PlannedTreatmentItem creado (is_global: true)
✓ Item aparece en lista
✓ Total se actualiza
```

**Nota:** Los tratamientos globales NO crean ToothTreatment porque no se asocian a dientes específicos.

#### Modo 3: Del Catálogo (📋)

```
Clic en "📋 Del Catálogo"
    ↓
Modal de búsqueda del catálogo
Barra de búsqueda + filtros por categoría
    ↓
Usuario busca "corona zirconio"
    ↓
Selecciona "Corona de zirconio - €550"
    ↓
Si requiere diente: "¿En qué diente?" → clic en odontograma
Si es global: se añade directamente
    ↓
✓ Tratamiento añadido con precio del catálogo
```

### 5.3 B3: Lista del Plan en Tiempo Real

```
┌──────────────────────────────────────┐
│ TRATAMIENTOS DEL PLAN        3 items │
├──────────────────────────────────────┤
│                                      │
│ ┌──────────────────────────────────┐ │
│ │ □ Empaste                        │ │
│ │   Diente 16 - MOD                │ │
│ │   €85                        [×] │ │
│ └──────────────────────────────────┘ │
│                                      │
│ ┌──────────────────────────────────┐ │
│ │ 🌉 Puente fijo                   │ │
│ │   Dientes 14-15-16 (3 piezas)    │ │
│ │   Pilares: 14, 16                │ │
│ │   €1,200                     [×] │ │
│ └──────────────────────────────────┘ │
│                                      │
│ ┌──────────────────────────────────┐ │
│ │ 🌐 Limpieza                      │ │
│ │   Boca completa                  │ │
│ │   €60                        [×] │ │
│ └──────────────────────────────────┘ │
│                                      │
├──────────────────────────────────────┤
│ SUBTOTAL:                    €1,345  │
├──────────────────────────────────────┤
│                                      │
│ [    Guardar borrador     ]          │
│ [    Generar presupuesto →]          │
│                                      │
└──────────────────────────────────────┘
```

**Representación por tipo:**

| Tipo | Icono | Formato |
|------|-------|---------|
| Diente único | — | "Diente 16" |
| Diente + superficies | — | "Diente 16 - MOD" |
| Puente | 🌉 | "Dientes 14-15-16 (3)" + "Pilares: X, Y" |
| Grupo | ×N | "Dientes 11, 12, 21, 22" |
| Global | 🌐 | "Boca completa" |

### 5.4 B4: Interacción Odontograma ↔ Lista

**Hover en lista → Resalta diente(s):**

```
Hover sobre "Empaste (16-MOD)"
    → Diente 16 resaltado, superficies MOD iluminadas

Hover sobre "Puente (14-15-16)"
    → Dientes 14, 15, 16 resaltados con línea de conexión
    → Tooltips: "Pilar" en 14 y 16, "Póntico" en 15

Hover sobre "Limpieza"
    → Todos los dientes parpadean suavemente (es global)
```

**Hover en diente → Resalta items:**

```
Hover sobre diente 16
    → "Empaste (16-MOD)" resaltado en lista
    → Tooltip: "Empaste MOD - Planificado"

Hover sobre diente 15 (póntico)
    → "Puente (14-15-16)" resaltado en lista
    → Tooltip: "Póntico - Parte de puente 14-15-16"
```

### 5.5 B5: Estado Vacío del Plan

```
┌──────────────────────────────────────┐
│                                      │
│           📋                         │
│                                      │
│     Este plan está vacío             │
│                                      │
│     Añade tratamientos usando        │
│     los botones de arriba o          │
│     haciendo clic en el              │
│     odontograma.                     │
│                                      │
│     [🦷 Empezar añadiendo]           │
│                                      │
└──────────────────────────────────────┘
```

### 5.6 B6: Integración con Catálogo de Precios

Cuando el usuario añade un tratamiento:

1. Sistema busca en catálogo por tipo de tratamiento
2. Si hay match único → usa ese precio
3. Si hay múltiples opciones (ej: "Corona metal" vs "Corona zirconio") → muestra selector
4. Precio se calcula automáticamente:
   - Superficies: precio base × número de superficies
   - Multi-diente: precio base × número de piezas
   - Puentes: puede tener precio distinto por pilar vs póntico

```
┌────────────────────────────────────────┐
│ Selecciona el tipo de corona          │
├────────────────────────────────────────┤
│ ○ Corona metal-cerámica      €350     │
│ ● Corona zirconio            €550     │
│ ○ Corona composite           €280     │
├────────────────────────────────────────┤
│                        [Cancelar] [OK] │
└────────────────────────────────────────┘
```

---

## 6. Flujos de Usuario

### 6.1 Flujo: Registrar Puente Existente (Diagnóstico)

```
┌─────────────────────────────────────────────────────────────┐
│ CONTEXTO: Pestaña Diagnóstico en ficha paciente             │
│ OBJETIVO: Registrar que el paciente tiene un puente 14-15-16│
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ PASO 1: Seleccionar tratamiento                             │
│ En barra de tratamientos, categoría "Protésica"             │
│ Clic en "Puente fijo"                                       │
│ Banner: "Puente fijo - Clic en diente inicial y final"      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ PASO 2: Seleccionar rango                                   │
│ Clic en diente 14 → marcado como inicio                     │
│ Clic en diente 16 → marcado como fin                        │
│ Sistema auto-selecciona 14, 15, 16                          │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ PASO 3: Confirmar                                           │
│ Popup: "Puente 14-15-16 | Pilares: 14, 16 | Póntico: 15"    │
│ Clic "Confirmar"                                            │
│                                                             │
│ ✓ ToothTreatment creado con status: "existing"              │
│ ✓ Odontograma muestra puente con color sólido               │
│ ✓ Toast: "Puente (14-15-16) registrado"                     │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 Flujo: Planificar Puente Nuevo (Plan de Tratamiento)

```
┌─────────────────────────────────────────────────────────────┐
│ CONTEXTO: Ficha de Plan de Tratamiento                      │
│ OBJETIVO: Añadir puente 24-25-26 al plan                    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ PASO 1: Iniciar desde panel lateral                         │
│ Clic en "🦷 Por Diente"                                     │
│ Categoría "Protésica" → Clic en "Puente fijo"               │
│ Banner: "Puente fijo - Clic en diente inicial y final"      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ PASO 2: Seleccionar rango                                   │
│ Clic en diente 24 → marcado como inicio                     │
│ Clic en diente 26 → marcado como fin                        │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ PASO 3: Seleccionar material (integración catálogo)         │
│ Sistema detecta múltiples opciones en catálogo              │
│ Modal: "Selecciona tipo de puente"                          │
│ • Puente metal-cerámica - €900 (3 piezas)                   │
│ • Puente zirconio - €1,500 (3 piezas)                       │
│ Usuario selecciona "Puente zirconio"                        │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ PASO 4: Confirmar                                           │
│ Popup: "Puente zirconio 24-25-26 (3 piezas) - €1,500"       │
│ Clic "Añadir al plan"                                       │
│                                                             │
│ ✓ ToothTreatment creado con status: "planned"               │
│ ✓ PlannedTreatmentItem creado (links ToothTreatment +       │
│   CatalogItem)                                              │
│ ✓ Item aparece en lista del plan con precio                 │
│ ✓ Odontograma muestra puente con patrón rayado              │
│ ✓ Total se actualiza                                        │
└─────────────────────────────────────────────────────────────┘
```

### 6.3 Flujo: Añadir Empaste con Superficies (Plan)

```
┌─────────────────────────────────────────────────────────────┐
│ PASO 1: Seleccionar tipo                                    │
│ Panel lateral → "🦷 Por Diente" → "Empaste"                 │
│ Banner: "Empaste seleccionado - Clic en diente"             │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ PASO 2: Seleccionar diente                                  │
│ Clic en diente 36                                           │
│ Popup inline aparece junto al diente                        │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ PASO 3: Seleccionar superficies                             │
│ Clic en M (mesial) → se ilumina                             │
│ Clic en O (oclusal) → se ilumina                            │
│ Preview: "Empaste 36-MO - €60"                              │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ PASO 4: Confirmar                                           │
│ Clic "Añadir"                                               │
│ Popup se cierra                                             │
│                                                             │
│ ✓ ToothTreatment + PlannedTreatmentItem creados             │
│ ✓ Item aparece en lista: "Empaste - Diente 36 MO - €60"     │
│ ✓ Modo aplicar sigue activo para añadir más empastes        │
└─────────────────────────────────────────────────────────────┘
```

### 6.4 Flujo: Añadir Limpieza (Global)

```
┌─────────────────────────────────────────────────────────────┐
│ PASO 1: Abrir tratamientos globales                         │
│ Panel lateral → Clic en "🌐 Boca Completa"                  │
│ Lista se despliega:                                         │
│ • Limpieza dental - €60                                     │
│ • Blanqueamiento - €180                                     │
│ • Fluorización - €25                                        │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ PASO 2: Seleccionar y confirmar                             │
│ Clic en "Limpieza dental - €60"                             │
│ (No requiere selección de dientes)                          │
│                                                             │
│ ✓ PlannedTreatmentItem creado (is_global: true)             │
│ ✓ Item aparece en lista: "🌐 Limpieza - Boca completa - €60"│
│ ✓ Total se actualiza                                        │
│ ✓ Toast: "Limpieza dental añadida al plan"                  │
└─────────────────────────────────────────────────────────────┘
```

### 6.5 Flujo: Marcar Tratamiento como Completado

```
┌─────────────────────────────────────────────────────────────┐
│ CONTEXTO: Plan aprobado, paciente en cita                   │
│ OBJETIVO: Marcar empaste como realizado                     │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ PASO 1: Localizar tratamiento                               │
│ En lista del plan, localizar "Empaste - Diente 36 MO"       │
│ Checkbox a la izquierda del item                            │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ PASO 2: Marcar como completado                              │
│ Clic en checkbox                                            │
│ Confirmación: "¿Marcar empaste 36-MO como completado?"      │
│ Clic "Confirmar"                                            │
│                                                             │
│ ✓ PlannedTreatmentItem.status → "completed"                 │
│ ✓ PlannedTreatmentItem.completed_at → fecha actual          │
│ ✓ ToothTreatment.status → "existing" (auto-sync)            │
│ ✓ Item se mueve a sección "Completados"                     │
│ ✓ Odontograma: patrón rayado → color sólido                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 7. Sincronización Odontograma ↔ Plan

### 7.1 Reglas de Sincronización

| Acción | Odontograma | Plan |
|--------|-------------|------|
| Añadir tratamiento al plan | ToothTreatment creado (planned) | PlannedTreatmentItem creado (pending) |
| Marcar tratamiento completado | ToothTreatment → existing | PlannedTreatmentItem → completed |
| Eliminar item del plan (no completado) | ToothTreatment eliminado | PlannedTreatmentItem eliminado |
| Eliminar item del plan (completado) | ToothTreatment permanece (existing) | PlannedTreatmentItem eliminado |

### 7.2 Visualización en Odontograma

El odontograma debe mostrar TODOS los tratamientos del paciente, tanto existentes como planificados:

```
┌─────────────────────────────────────────────────────────────┐
│                      ODONTOGRAMA                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Diente 14: ████ (puente existente - sólido)                │
│  Diente 15: ████ (puente existente - sólido)                │
│  Diente 16: ████ (puente existente - sólido)                │
│                                                             │
│  Diente 36: ░░░░ (empaste planificado - rayado)             │
│  Diente 37: ░░░░ (corona planificada - rayado)              │
│                                                             │
│  ─────────────────────────────────────────────              │
│  Leyenda:                                                   │
│  ████ = Existente (ya realizado)                            │
│  ░░░░ = Planificado (por hacer)                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 7.3 Vista en Ficha de Plan

En la ficha de plan, el odontograma muestra:
- Tratamientos existentes (para contexto)
- Tratamientos planificados de ESTE plan (destacados)
- Tratamientos planificados de OTROS planes (atenuados, opcional)

---

## 8. Estados y Feedback

### 8.1 Feedback al Añadir Tratamiento

```
1. Item aparece en lista con animación slide-in
2. Item tiene fondo verde claro por 2 segundos
3. Total se actualiza con animación de contador
4. Toast: "✓ [Tratamiento] añadido al plan"
5. Odontograma actualiza visualización
```

### 8.2 Feedback al Eliminar Tratamiento

```
1. Confirmación: "¿Eliminar [tratamiento] del plan?"
2. Item tiene fondo rojo claro por 500ms
3. Item desaparece con animación slide-out
4. Toast: "[Tratamiento] eliminado" + botón "Deshacer" (5s)
5. Total se actualiza
6. Odontograma actualiza visualización
```

### 8.3 Estados del Plan

| Estado | Badge | Acciones Disponibles |
|--------|-------|---------------------|
| `draft` | Gris "Borrador" | Añadir, editar, eliminar items |
| `budgeted` | Azul "Presupuestado" | Editar, aprobar, rechazar |
| `approved` | Verde "Aprobado" | Completar tratamientos |
| `in_progress` | Amarillo "En progreso" | Completar tratamientos |
| `completed` | Verde oscuro "Completado" | Solo lectura |
| `cancelled` | Rojo "Cancelado" | Solo lectura |

### 8.4 Validaciones y Errores

| Error | Mensaje | Acción |
|-------|---------|--------|
| Tratamiento duplicado | "El diente 36 ya tiene un empaste planificado" | [Ver existente] [Reemplazar] |
| Dientes no contiguos (puente) | "Los dientes de un puente deben ser adyacentes" | Mostrar dientes válidos |
| Mínimo no alcanzado | "Un puente requiere mínimo 3 dientes" | Deshabilitar confirmar |
| Error de red | "No se pudo añadir. Reintentando..." | Reintentar automático |

---

## 9. Consideraciones de Accesibilidad

### 9.1 Navegación por Teclado

- Tab order: Panel lateral → Odontograma → Lista
- Dientes navegables con flechas
- Focus visible con outline

### 9.2 Screen Readers

- ARIA labels en todos los botones
- Live regions para actualizaciones
- Anuncios: "Empaste añadido al plan. Total: 85 euros"

### 9.3 Responsive

**Tablet:** Panel lateral colapsable
**Móvil:** Layout vertical, panel como bottom sheet

---

## 10. Resumen y Priorización

### 10.1 Mejoras del Módulo Odontograma (PARTE A)

| ID | Mejora | Prioridad | Complejidad |
|----|--------|-----------|-------------|
| A1 | Soporte multi-diente (puentes, férulas) | **P0** | Alta |
| A2 | Selector superficies inline | P1 | Media |
| A3 | Estados visuales claros | P1 | Baja |
| A4 | Colores/representación multi-diente | P1 | Media |
| A5 | Barra tratamientos mejorada | P2 | Baja |
| A6 | Atajos de teclado | P3 | Baja |

### 10.2 Mejoras de la Ficha de Plan (PARTE B)

| ID | Mejora | Prioridad | Complejidad |
|----|--------|-----------|-------------|
| B1 | Layout con panel lateral | **P0** | Alta |
| B2 | Tres modos de añadir | **P0** | Media |
| B3 | Lista del plan en tiempo real | **P0** | Media |
| B4 | Interacción hover bidireccional | P1 | Media |
| B5 | Estado vacío | P2 | Baja |
| B6 | Integración catálogo precios | **P0** | Alta |

### 10.3 Orden de Implementación Sugerido

**Fase 1: Funcionalidad Core**
1. B1 + B2 + B3: Panel lateral con lista y modos de añadir
2. A1: Soporte multi-diente
3. B6: Integración catálogo

**Fase 2: Polish UX**
4. A2: Selector superficies inline
5. A3 + A4: Estados visuales y colores
6. B4: Hover bidireccional

**Fase 3: Refinamiento**
7. A5 + A6: Barra mejorada y atajos
8. B5: Estado vacío

---

## Próximos Pasos

1. **Validar con usuarios:** Test con 3-5 dentistas
2. **Prototipo:** Figma para flujos multi-diente
3. **Plan técnico:** Definir cambios en modelos y API
4. **Implementar Fase 1:** Comenzar por panel lateral
