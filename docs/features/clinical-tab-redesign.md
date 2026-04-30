# Rediseño UI/UX: Tab Clínico del Paciente

## Problema Actual

El tab clínico mezcla tres contextos diferentes sin guía clara:
- **Odontograma** con tratamientos diagnósticos
- **Barra de tratamientos** flotante sin contexto
- **Planes de tratamiento** como bloque separado

**Resultado:** Usuario no sabe si está diagnosticando o planificando.

---

## Flujo Propuesto

```
┌─────────────────────────────────────────────────────────────┐
│  FASE 1: DIAGNÓSTICO                                        │
│  "¿Qué tiene el paciente?"                                  │
│                                                              │
│  → Marcar condiciones existentes en odontograma             │
│  → Caries, fracturas, ausencias, prótesis existentes...     │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  FASE 2: PLANIFICACIÓN                                      │
│  "¿Qué vamos a hacer?"                                      │
│                                                              │
│  → Crear plan de tratamiento                                │
│  → Añadir tratamientos al plan (vinculados a dientes)       │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  FASE 3: EJECUCIÓN                                          │
│  "¿Qué hemos hecho?"                                        │
│                                                              │
│  → Marcar tratamientos como realizados                      │
│  → Actualiza automáticamente odontograma                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Propuesta de Diseño: "Modos de Trabajo"

### Concepto Core

Reemplazar la UI mezclada por **tres modos de trabajo** ordenados cronológicamente:

```
┌────────────────────────────────────────────────────────────────┐
│  [ 📜 HISTÓRICO ]  [ 🔍 DIAGNÓSTICO ]  [ 📋 PLANES ]          │
│      Pasado            Presente           Futuro               │
└────────────────────────────────────────────────────────────────┘
```

Cada modo tiene su propia UI optimizada para su propósito.

---

## Modo 1: Histórico

### Propósito
Ver la evolución del paciente a lo largo del tiempo. **Solo lectura.**

### Layout

```
┌────────────────────────────────────────────────────────────────┐
│  [ 📜 HISTÓRICO ]  [ 🔍 DIAGNÓSTICO ]  [ 📋 PLANES ]          │
│       ↑ activo                                                 │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  LÍNEA TEMPORAL                                          │ │
│  │                                                           │ │
│  │  ○───────○───────○───────●───────○───────○               │ │
│  │  Ene     Feb     Mar     Abr     May     Jun             │ │
│  │                          ↑                                │ │
│  │                 Viendo: 15/03/2024                        │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  ODONTOGRAMA (solo lectura)                              │ │
│  │                                                           │ │
│  │  Estado del paciente a fecha 15/03/2024                  │ │
│  │  (Vista oclusal + Vista lateral)                         │ │
│  │                                                           │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  CAMBIOS EN ESTA FECHA                                   │ │
│  │                                                           │ │
│  │  ✓ Empaste composite realizado - Diente 16 (M,O)         │ │
│  │    Plan: "Rehabilitación Sector 1"                       │ │
│  │                                                           │ │
│  │  + Diagnóstico añadido: Caries - Diente 25               │ │
│  │                                                           │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  [← Anterior]                           [Siguiente →]    │ │
│  │                    [Ir a Hoy]                            │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### Características

1. **Solo lectura**: No se puede modificar nada
2. **Timeline interactivo**: Click o drag para navegar entre fechas
3. **Cambios destacados**: Qué ocurrió en cada fecha
4. **Navegación rápida**: Botones anterior/siguiente, ir a hoy

---

## Modo 2: Diagnóstico

### Layout

```
┌────────────────────────────────────────────────────────────────┐
│  [ 📜 HISTÓRICO ]  [ 🔍 DIAGNÓSTICO ]  [ 📋 PLANES ]          │
│                          ↑ activo                              │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │                    ODONTOGRAMA                            │ │
│  │                                                           │ │
│  │     Vista oclusal + Vista lateral                         │ │
│  │     (4 cuadrantes interactivos)                          │ │
│  │                                                           │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  DIAGNÓSTICOS                                             │ │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐        │ │
│  │  │ Caries  │ │Fractura │ │ Ausente │ │Corona   │ ...    │ │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘        │ │
│  │                                                           │ │
│  │  Selecciona diagnóstico → Click en diente/superficie     │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  CONDICIONES REGISTRADAS                                 │ │
│  │  • Caries - Diente 16 (M,O)                    Hoy       │ │
│  │  • Corona existente - Diente 21           10/01/2024     │ │
│  │  • Ausencia - Diente 36                   (histórico)    │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  💡 ¿Diagnóstico completo?                               │ │
│  │                                                           │ │
│  │  Si NO hay plan borrador:  [Crear Plan de Tratamiento]   │ │
│  │  Si hay 1 plan borrador:   [Continuar Plan "Nombre..."]  │ │
│  │  Si hay N planes borrador: [Continuar Plan ▼] (dropdown) │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### Características

1. **Solo diagnósticos**: Barra muestra solo categorías de diagnóstico (no tratamientos)
2. **Flujo claro**: Seleccionar → Click → Registrado
3. **Lista de condiciones**: Resumen visual de todo lo diagnosticado
4. **CTA contextual**:
   - Sin planes borrador → "Crear Plan de Tratamiento"
   - Con 1 plan borrador → "Continuar Plan [nombre]"
   - Con varios borradores → Dropdown para elegir cuál continuar

### Categorías de Diagnóstico

| Categoría | Elementos |
|-----------|-----------|
| **Caries** | Caries inicial, Caries profunda, Caries secundaria |
| **Periodontal** | Gingivitis, Periodontitis leve/moderada/severa |
| **Estado dental** | Fractura, Movilidad, Desgaste, Erosión |
| **Ausencias** | Ausente, Raíz retenida |
| **Existente** | Corona, Puente, Implante, Empaste, Endodoncia previa |

---

## Modo 3: Planes de Tratamiento

### Layout Principal (Lista de Planes)

```
┌────────────────────────────────────────────────────────────────┐
│  [ 📜 HISTÓRICO ]  [ 🔍 DIAGNÓSTICO ]  [ 📋 PLANES ]          │
│                                            ↑ activo            │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  PLANES DE TRATAMIENTO              [+ Nuevo Plan]        │ │
│  │                                                           │ │
│  │  ┌─────────────────────────────────────────────────────┐ │ │
│  │  │ ⭐ Plan Rehabilitación Sector 1     ACTIVO          │ │ │
│  │  │    3/8 tratamientos completados                     │ │ │
│  │  │    [████████░░░░░░░░] 37%                          │ │ │
│  │  │    Presupuesto: #BDG-001 (Aceptado)                │ │ │
│  │  │                                         [Ver Plan →]│ │ │
│  │  └─────────────────────────────────────────────────────┘ │ │
│  │                                                           │ │
│  │  ┌─────────────────────────────────────────────────────┐ │ │
│  │  │    Plan Mantenimiento Periodontal    BORRADOR       │ │ │
│  │  │    0/4 tratamientos                                 │ │ │
│  │  │                                         [Ver Plan →]│ │ │
│  │  └─────────────────────────────────────────────────────┘ │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  ODONTOGRAMA (Vista reducida/resumen)                    │ │
│  │  Muestra condiciones diagnosticadas como referencia       │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### Layout Detalle del Plan (Vista Expandida)

```
┌────────────────────────────────────────────────────────────────┐
│  ← Volver a Planes         Plan Rehabilitación Sector 1       │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌───────────────────────────────┬────────────────────────────┐│
│  │                               │                            ││
│  │     ODONTOGRAMA               │   TRATAMIENTOS DEL PLAN   ││
│  │     (Interactivo)             │                            ││
│  │                               │   [+ Añadir Tratamiento]   ││
│  │     Los dientes con           │                            ││
│  │     tratamientos en este      │   1. □ Empaste composite   ││
│  │     plan se muestran          │      Diente 16 (M,O)       ││
│  │     resaltados                │      €80                   ││
│  │                               │                            ││
│  │     Al hacer hover en un      │   2. □ Endodoncia          ││
│  │     diente, se resaltan       │      Diente 25             ││
│  │     los tratamientos          │      €250                  ││
│  │     correspondientes          │                            ││
│  │                               │   3. ✓ Corona metal-cer.   ││
│  │                               │      Diente 16             ││
│  │                               │      €450 (completado)     ││
│  │                               │                            ││
│  │                               │   ─────────────────────    ││
│  │                               │   Total: €780              ││
│  │                               │                            ││
│  └───────────────────────────────┴────────────────────────────┘│
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  BARRA DE TRATAMIENTOS                                    │ │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐        │ │
│  │  │Empaste  │ │Endodon. │ │ Corona  │ │Extrac.  │ ...    │ │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘        │ │
│  │                                                           │ │
│  │  Selecciona tratamiento → Click en diente →               │ │
│  │  Se añade al plan actual                                  │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  [Generar Presupuesto]  [Activar Plan]  [Agendar Cita]   │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### Interacción Odontograma ↔ Lista de Tratamientos

| Acción | Resultado |
|--------|-----------|
| Hover en diente (odontograma) | Resalta tratamientos de ese diente en lista |
| Hover en tratamiento (lista) | Resalta diente(s) en odontograma |
| Click en tratamiento (barra) + Click diente | Añade tratamiento al plan con ese diente |
| Click en tratamiento existente (lista) | Abre modal de edición |
| Drag tratamiento en lista | Reordena prioridad |

### Visualización en Odontograma

```
Diente sin tratamiento:     ○  (color base)
Diente con diagnóstico:     ● (relleno según condición)
Diente en plan actual:      ◉ (borde destacado + badge número)
Diente con tto completado:  ✓ (marca de completado)
```

---

## Añadir Tratamiento a Plan

### Tratamiento vinculado a diente(s)

```
1. Usuario en vista detalle del plan
2. Selecciona tratamiento en barra inferior
3. Click en diente (o superficie)
4. Toast: "Empaste añadido a diente 16" [Deshacer]
5. Aparece en lista de tratamientos del plan
```

### Tratamiento general (sin diente)

```
1. Usuario en vista detalle del plan
2. Click en tratamiento en barra (ej: "Limpieza", "Fluorización")
3. Se abre modal con:
   - Nombre del tratamiento (readonly)
   - Precio (auto-rellenado, editable)
   - Notas (opcional)
4. Click [Añadir al Plan]
5. Aparece en lista de tratamientos
```

**Nota:** El sistema debe distinguir qué tratamientos requieren diente y cuáles no (configuración en catálogo de tratamientos). 

## Flujo Completo: Ejemplo Práctico

### Escenario: Paciente con dolor en molar

```
FASE 1: DIAGNÓSTICO
═══════════════════

1. Profesional abre tab "Clínico"
2. Por defecto está en modo [🔍 Diagnóstico]
3. Examina al paciente
4. En barra de diagnósticos, selecciona "Caries profunda"
5. Click en diente 16, superficie oclusal
6. Registrado: "Caries profunda - 16(O)"
7. Selecciona "Fractura"
8. Click en diente 15, cara vestibular
9. Registrado: "Fractura - 15(V)"

Lista de condiciones muestra:
• Caries profunda - Diente 16 (O) - Hoy
• Fractura - Diente 15 (V) - Hoy

10. Click en [Crear Plan de Tratamiento]


FASE 2: PLANIFICACIÓN
════════════════════

11. Se abre modal "Nuevo Plan"
    - Título: "Tratamiento sector 1 superior derecho"
    - Diagnóstico: "Caries profunda en 16, fractura en 15"
    - [Crear]

12. Vista cambia a detalle del plan
    - Odontograma a la izquierda (con 16 y 15 marcados como diagnosticados)
    - Lista de tratamientos vacía a la derecha

13. En barra de tratamientos, selecciona "Empaste composite"
14. Click en diente 16 (O)
15. Añadido: "Empaste composite - 16(O) - €80"

16. Selecciona "Corona cerámica"
17. Click en diente 15
18. Añadido: "Corona cerámica - 15 - €450"

19. Odontograma ahora muestra:
    - Diente 16: badge "1" (empaste)
    - Diente 15: badge "2" (corona)

20. Click [Generar Presupuesto]
21. Presupuesto creado y vinculado

22. Click [Activar Plan]
23. Plan pasa de "Borrador" a "Activo"


FASE 3: EJECUCIÓN (en cita posterior)
═════════════════════════════════════

24. Abre plan activo del paciente
25. Realiza el empaste
26. En lista de tratamientos, marca "Empaste composite" como completado
27. Odontograma actualiza:
    - Diente 16: cambia de "badge 1" a "✓ completado"
28. Progreso del plan: 1/2 (50%)
```

---

## Estados Visuales del Diente

### En Modo Diagnóstico

```
┌─────────────────────────────────────────────────────────────┐
│  Estado              │  Visual                              │
├─────────────────────────────────────────────────────────────┤
│  Sano                │  ○ Blanco/Gris claro                │
│  Caries              │  ● Rojo/Naranja (según severidad)   │
│  Fractura            │  ⚡ Línea diagonal                   │
│  Ausente             │  ✕ Tachado o vacío                  │
│  Corona existente    │  🔲 Borde azul                       │
│  Endodoncia previa   │  ● Centro oscuro                    │
└─────────────────────────────────────────────────────────────┘
```

### En Modo Plan (Vista Detalle)

```
┌─────────────────────────────────────────────────────────────┐
│  Estado              │  Visual                              │
├─────────────────────────────────────────────────────────────┤
│  Sin tratamiento     │  Según diagnóstico base             │
│  Tto. planificado    │  Borde verde + badge número         │
│  Hover (relacionado) │  Borde amarillo brillante           │
│  Tto. completado     │  ✓ Verde + relleno actualizado      │
└─────────────────────────────────────────────────────────────┘
```

---

## Componentes Nuevos Necesarios

| Componente | Propósito |
|------------|-----------|
| `ClinicalModeToggle` | Toggle entre Histórico / Diagnóstico / Planes |
| `HistoryMode` | Vista de histórico con timeline y odontograma readonly |
| `TimelineSlider` | Navegación temporal interactiva |
| `ChangesList` | Lista de cambios en fecha seleccionada |
| `DiagnosisBar` | Barra específica para diagnósticos |
| `TreatmentPlanDetail` | Vista expandida del plan con odontograma |
| `TreatmentItemList` | Lista de tratamientos con hover linking |
| `OdontogramMini` | Vista reducida para referencia |
| `ToothBadge` | Indicador visual de tratamiento en diente |

---

## Responsividad

### Desktop (≥1024px)
- Layout de dos columnas en vista detalle del plan
- Odontograma completo visible
- Timeline horizontal completo

### Tablet (768-1024px)
- Layout apilado: odontograma arriba, lista abajo
- Odontograma con zoom ligero
- Timeline horizontal con scroll

### Mobile (<768px)
- Modo histórico: Timeline vertical + odontograma compacto
- Modo diagnóstico: Odontograma scrolleable + barra fija abajo
- Modo plan: Tabs para alternar odontograma/lista
- Acciones principales en bottom sheet

---

## Beneficios del Rediseño

| Aspecto | Antes | Después |
|---------|-------|---------|
| **Claridad** | Todo mezclado | Tres modos distintos (pasado/presente/futuro) |
| **Flujo** | Sin guía | Histórico → Diagnóstico → Plan → Ejecución |
| **Contexto** | Ambiguo | Siempre claro dónde estás |
| **Vinculación** | Manual | Visual (hover linking) |
| **Aprendizaje** | Confuso | Progresivo y guiado |
| **Histórico** | Timeline mezclado con edición | Vista dedicada de solo lectura |

---

## Decisiones de Diseño

| Aspecto | Decisión | Razón |
|---------|----------|-------|
| **Estructura** | 3 modos: Histórico → Diagnóstico → Planes | Orden cronológico (pasado → presente → futuro) |
| **Timeline/Historial** | Modo dedicado (solo lectura) | No mezclar con flujo de diagnóstico activo |
| **CTA en Diagnóstico** | Contextual según planes borrador | Si hay borrador: "Continuar Plan", si no: "Crear Plan" |
| **Tratamientos sin plan** | No permitir | Consistencia de datos. Todo tratamiento pertenece a un plan |
| **Múltiples planes activos** | Sí | Clínicas con especialistas pueden tener planes paralelos |
| **Tratamientos multi-diente** | Fase posterior | Puentes, prótesis removibles → añadir a docs/technical/todos.md |
| **Citas desde tratamiento** | No | Citas se crean desde el plan completo, no por tratamiento individual |

---

## Fuera de Alcance (Fase Posterior)

- Tratamientos que abarcan múltiples dientes (puentes, prótesis)
- Drag & drop para reordenar tratamientos en plan

---

## Siguiente Paso

Diseño validado. Proceder con plan técnico de implementación.
