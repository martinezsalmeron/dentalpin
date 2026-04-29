# Rediseño UI para apariencia visual, legibilidad y diseño calmado

**Issue de referencia:** [#45 Redesign UI for visual appeal, readability, and calm design](https://github.com/martinezsalmeron/dentalpin/issues/45)

**Estado:** Plan técnico — sin cambios de comportamiento ni backend.

**Inspiración:** `DESIGN.md` (Notion) + Linear, Height. Adaptado críticamente para uso clínico de jornada completa.

---

## 1. Diagnóstico crítico

### 1.1 Estado actual

- **Tema Nuxt UI:** `primary: 'sky'`, `neutral: 'slate'` (gris frío azulado).
- **Fuente:** `Public Sans` (definida en `main.css`).
- **Tokens:** sólo existen variables CSS para el odontograma (light + dark). No hay tokens propios para color de texto, superficies, radios o sombras: todo se delega a las clases Tailwind por defecto (`bg-white`, `bg-gray-50`, `border-gray-200`).
- **Sombras y bordes:** uso intensivo de `border-gray-200` por todos los layouts y cards (sidebar, header, divisores). Densidad visual alta.
- **Modo oscuro:** funciona vía `UColorModeButton` y clase `.dark`, pero las superficies son `bg-gray-900` / `bg-gray-950` planas — sin jerarquía de elevación.
- **Densidad:** sólo una. Listas de tratamientos, calendario y odontograma comparten la misma escala que el resto.

### 1.2 Crítica al uso directo de DESIGN.md

`DESIGN.md` describe un sistema diseñado para una **landing pública** y para **lectura larga de documentos**. Aplicarlo tal cual a un software clínico tiene tres riesgos serios:

1. **Tamaños tipográficos hero (40–64 px)** no encajan en una vista densa de odontograma o agenda. Sirven sólo para encabezados de página y cards de KPI.
2. **Cuerpo a 16 px** es generoso para lectura prosa, pero infla en exceso tablas, listas de tratamientos y filas de calendario. Recomendación: cuerpo principal **14 px** (15 px en formularios y prosa larga), reservar 16 px para descripciones y ayudas.
3. **`NotionInter` es propietaria.** No se puede empaquetar. Usaremos **Inter Variable** (open-source y prácticamente idéntica) cargada localmente para evitar FOUT y dependencias CDN.
4. **Alertas pastelizadas, no apagadas.** Alertas médicas (alergias, contraindicaciones, ASA III/IV, anticoagulación), conflictos de horario y errores de cobro se renderizan con **fondo pastel + texto/icono en color pleno + rail de acento lateral**. Esto evita la agresividad de los rojos/naranjas saturados a pantalla completa, pero conserva la identidad semántica y el contraste WCAG AA. La saturación plena se reserva para iconos, rails, bordes finos y botones destructivos — nunca para llenados grandes.
5. **Modo oscuro real.** `DESIGN.md` apenas lo trata. En clínica, el dark mode se usa al final del día y en gabinetes con luz tenue — debe ser un sistema de primera clase, con superficies cálidas (no azul frío) para reducir fatiga visual.
6. **Pure white `#ffffff`** como canvas tras 8 h de uso es duro. Adoptaremos un *off-white* cálido (`#FBFAF8`) como fondo base — alineado con el principio de *warm neutrals* de Notion sin la dureza del blanco puro.

### 1.3 Principios derivados (orden de prioridad)

1. **Lo clínico manda.** Alertas, estados y datos de paciente nunca pierden contraste por estética.
2. **Calma por sustracción.** Quitar bordes, sombras y badges decorativos antes de añadir cualquier color.
3. **Una sola tinta saturada de chrome:** primario (azul). Todo lo demás (estados) en variantes *soft* salvo cuando codifiquen riesgo.
4. **Densidad ajustable por usuario.** Confort para administración, compacta para gabinete.
5. **Ritmo vertical generoso entre bloques, denso dentro.** Cards no rebosan padding interno innecesario, pero entre ellas respiran.
6. **Movimiento mínimo.** Transiciones ≤150 ms, sólo en estado (hover, expand). Sin animaciones decorativas. Respetar `prefers-reduced-motion`.

---

## 2. Sistema de tokens

Todos los tokens viven en `frontend/app/assets/css/main.css` como variables CSS dentro de `@theme static` (Tailwind 4) y en bloques `:root` / `.dark` para los que cambian con el tema. **No** se hardcodean colores en componentes; siempre se referencian vía clases Tailwind o `var(--token)`.

### 2.1 Color — paleta base (modo claro)

| Token | Valor | Rol |
|---|---|---|
| `--color-canvas` | `#FBFAF8` | Fondo de página (off-white cálido) |
| `--color-surface` | `#FFFFFF` | Cards, modales, popovers |
| `--color-surface-muted` | `#F4F2EF` | Filas alternas, secciones agrupadas, sidebar |
| `--color-surface-sunken` | `#EFEDE9` | Inputs, code blocks, áreas inactivas |
| `--color-border-subtle` | `rgba(15, 17, 22, 0.06)` | Divisores entre filas |
| `--color-border` | `rgba(15, 17, 22, 0.10)` | Bordes de cards, inputs |
| `--color-border-strong` | `rgba(15, 17, 22, 0.16)` | Hover de bordes, focus blando |
| `--color-text` | `rgba(15, 17, 22, 0.92)` | Cuerpo y encabezados |
| `--color-text-muted` | `#615D59` | Texto secundario, descripciones |
| `--color-text-subtle` | `#94908A` | Placeholder, metadatos |
| `--color-text-disabled` | `#BAB6B0` | Estados deshabilitados |

### 2.2 Color — paleta base (modo oscuro)

Inspirada en Linear y Height: superficies cálidas en lugar de azul frío. La progresión va de **fondo más oscuro → superficies elevadas más claras**, al revés que en claro. Esto crea jerarquía sin necesidad de sombras (que apenas se ven en oscuro).

| Token | Valor | Rol |
|---|---|---|
| `--color-canvas` | `#161513` | Fondo de página (warm dark) |
| `--color-surface` | `#1E1C19` | Cards, modales, sidebar |
| `--color-surface-muted` | `#252320` | Filas alternas |
| `--color-surface-sunken` | `#121110` | Inputs, áreas inactivas |
| `--color-border-subtle` | `rgba(255, 250, 240, 0.06)` | Divisores |
| `--color-border` | `rgba(255, 250, 240, 0.10)` | Bordes |
| `--color-border-strong` | `rgba(255, 250, 240, 0.18)` | Hover, focus blando |
| `--color-text` | `rgba(255, 250, 240, 0.92)` | Cuerpo |
| `--color-text-muted` | `#A39E97` | Secundario |
| `--color-text-subtle` | `#787570` | Placeholder |
| `--color-text-disabled` | `#525049` | Disabled |

### 2.3 Color — primario y semánticos

Mantenemos la familia `sky` de Tailwind como primario (compatibilidad con Nuxt UI 4 y conserva la identidad actual), **bajando** la saturación del 500 para que case con el tono calmado. La estrategia para los semánticos: **tres tokens por color** — `soft` (fondo pastel), `text` (texto/icono sobre soft, contraste AA garantizado) y `accent` (rail lateral, borde fino, botón destructivo).

| Rol | Light | Dark | Uso |
|---|---|---|---|
| Primary accent | `#0EA5E9` (`sky-500`) | `#38BDF8` (`sky-400`) | Botón primario, links, selección |
| Primary soft bg | `#E0F2FE` (`sky-100`) | `rgba(56,189,248,0.12)` | Badges activos, highlights |
| Primary text | `#0369A1` (`sky-700`) | `#7DD3FC` (`sky-300`) | Texto sobre soft |
| Success accent | `#0F9D58` | `#34D399` | Iconos, rail de éxito crítico |
| Success soft | `#E6F6EC` | `rgba(52,211,153,0.10)` | Badges "Realizado", "Pagado" |
| Success text | `#15803D` | `#86EFAC` | Texto sobre soft |
| Warning accent | `#D97706` | `#F59E0B` | Iconos, rail, botón de aviso |
| Warning soft | `#FEF3E2` | `rgba(245,158,11,0.12)` | Banner de cita en conflicto, plan vencido, badge "Pendiente" |
| Warning text | `#9A3412` | `#FCD34D` | Texto sobre soft (AA: 7:1 sobre `#FEF3E2`) |
| Danger accent | `#DC2626` | `#F87171` | Iconos, rail, botón destructivo, borde fino |
| Danger soft | `#FEE7E7` | `rgba(248,113,113,0.12)` | Banner de alergia, errores médicos, validación de form |
| Danger text | `#991B1B` | `#FCA5A5` | Texto sobre soft (AA: 7:1 sobre `#FEE7E7`) |
| Info accent | `#0284C7` | `#7DD3FC` | Iconos, rail informativo |
| Info soft | `#E0F2FE` | `rgba(125,211,252,0.10)` | Badges informativos |
| Info text | `#075985` | `#BAE6FD` | Texto sobre soft |

**Regla clínica:** todas las alertas usan el patrón `soft bg + text + accent rail`. Esto baja el ruido visual sin sacrificar identidad semántica ni contraste. Los pares text/soft están elegidos para cumplir **WCAG AA (≥ 4.5:1)** en cuerpo y **AAA donde es gratis**. La saturación plena (`accent`) sólo aparece en iconos pequeños, rails de 2–3 px, bordes finos de 1 px y botones de acción destructiva.

### 2.4 Tipografía

- **Familia:** `Inter Variable` (auto-hosted vía `@fontsource-variable/inter` o equivalente Nuxt). Fallback: `-apple-system, system-ui, Segoe UI, Helvetica, Arial`.
- **Features OpenType:** `"cv11"` (alternativa de `1`/`l`/`I` distinguibles — crítico en datos clínicos), `"ss01"`, `"tnum"` (cifras tabulares para dosis, importes y horarios).
- **Pesos cargados:** 400, 500, 600, 700 (variable axis suficiente).

| Token | Tamaño | Line-height | Tracking | Peso | Uso |
|---|---|---|---|---|---|
| `--text-display` | 28 px | 1.15 | -0.4 px | 700 | Título de página clínica |
| `--text-h1` | 22 px | 1.25 | -0.25 px | 700 | Título de modal, sección |
| `--text-h2` | 18 px | 1.30 | -0.15 px | 600 | Subsección, header de card |
| `--text-h3` | 15 px | 1.35 | normal | 600 | Mini-headers de panel |
| `--text-body` | 14 px | 1.50 | normal | 400 | **Cuerpo por defecto** |
| `--text-body-prose` | 15 px | 1.55 | normal | 400 | Notas clínicas, anamnesis (lectura larga) |
| `--text-ui` | 14 px | 1.30 | normal | 500 | Labels de form, items de nav |
| `--text-button` | 14 px | 1.20 | normal | 600 | Botones |
| `--text-caption` | 12 px | 1.40 | 0.1 px | 500 | Metadatos, timestamps, badges |
| `--text-micro` | 11 px | 1.30 | 0.2 px | 600 | Tags densos en odontograma |

**Cifras tabulares (`tnum`)** activadas globalmente para tablas de importes, dosis, horarios y números de diente (FDI). Evita saltos visuales al ordenar.

**Compatibilidad i18n:** las cadenas en español son ~20 % más largas que en inglés. Todos los headers usan `min-width` flexible y `text-wrap: pretty` (CSS) para evitar viudas.

### 2.5 Espaciado, radio y elevación

**Escala de espaciado** (rem, base 4 px — sigue Tailwind):

`0, 1 (4), 2 (8), 3 (12), 4 (16), 5 (20), 6 (24), 8 (32), 10 (40), 12 (48), 16 (64)`

**Radios**:

| Token | Valor | Uso |
|---|---|---|
| `--radius-xs` | 4 px | Inputs, botones pequeños |
| `--radius-sm` | 6 px | Botones estándar, chips |
| `--radius-md` | 8 px | Inputs de formulario, items de lista |
| `--radius-lg` | 12 px | Cards estándar |
| `--radius-xl` | 16 px | Modales, paneles destacados |
| `--radius-pill` | 9999 px | Badges, avatars |

**Sombras** (apiladas estilo Notion, opacidad acumulada ≤0.05 en claro; en oscuro la elevación se hace por color de superficie, no por sombra):

```css
--shadow-xs: 0 1px 1px rgba(15,17,22,0.02);
--shadow-sm: 0 1px 2px rgba(15,17,22,0.03), 0 1px 1px rgba(15,17,22,0.02);
--shadow-md: 0 4px 12px rgba(15,17,22,0.04), 0 1px 3px rgba(15,17,22,0.03);
--shadow-lg: 0 14px 28px rgba(15,17,22,0.05), 0 4px 12px rgba(15,17,22,0.03);
/* Modo oscuro: shadows desactivadas (opacity 0). Elevación = color de superficie. */
```

### 2.6 Densidad

Dos modos globales, persistidos en `localStorage` (`ui:density = comfortable | compact`) y aplicados como clase en `<html>`:

| Densidad | Padding cards | Altura fila tabla | Padding botón | Cuerpo |
|---|---|---|---|---|
| `comfortable` (default) | 16/20 px | 44 px | 8/14 px | 14 px |
| `compact` | 10/14 px | 32 px | 6/10 px | 13 px |

Vistas **forzadas a compact** independientemente de la preferencia: `OdontogramChart`, `AppointmentDailyView`, `AppointmentCalendar`, `TreatmentListSection` (son inherentemente densas). Vistas siempre en `comfortable`: `MedicalHistoryForm`, `PatientQuickInfo`, `index.vue` dashboard.

---

## 3. Mapeo a Nuxt UI 4

`app.config.ts` actual:

```ts
ui: { colors: { primary: 'sky', neutral: 'slate' } }
```

**Cambios:**

1. **Mantener `primary: 'sky'`** pero override de las variantes que usamos vía CSS variables (sin tocar el color base, sólo cómo se compone con superficies).
2. **Cambiar `neutral: 'slate'` → `neutral: 'stone'`** (Tailwind stone es la familia warm gray que casa con DESIGN.md). Este es el cambio de mayor impacto visual: arregla el azul frío del chrome.
3. Definir variantes de componentes globales en `app.config.ts` para `UButton`, `UCard`, `UInput`, `UModal`, `UBadge`, `USelect`, `UTable` — para no tener que tocar cada uso.

Ejemplo de override (esqueleto, se itera en fase 2):

```ts
ui: {
  colors: { primary: 'sky', neutral: 'stone' },
  card: {
    slots: {
      root: 'bg-[var(--color-surface)] ring-[var(--color-border)] shadow-[var(--shadow-sm)] rounded-[var(--radius-lg)]'
    }
  },
  button: {
    defaultVariants: { color: 'neutral', variant: 'soft' }
  }
}
```

---

## 4. Plan de implementación por fases

### Fase 0 — Inventario y baseline (1 día)

- Capturar **screenshots before** de todas las vistas mayores en claro y oscuro:
  - `/` (dashboard), `/patients`, `/patients/[id]` (cada modo del clinical tab), `/appointments` (semanal y diaria), `/budgets`, `/treatment-plans`, `/invoices`, `/settings`, `/login`.
  - Componentes en isolation: odontograma, modal de cita, modal de presupuesto, banner de alertas.
- Listar **todos los usos hardcodeados** de:
  - `bg-white`, `bg-gray-*`, `bg-slate-*`
  - `border-gray-*`, `border-slate-*`
  - `text-gray-*`, `text-slate-*`
  - `shadow-*`
  - `rounded-*`
  - `text-xs|sm|base|lg|xl|2xl|3xl`
- Output: `docs/technical/ui-redesign-baseline.md` con la matriz de archivos a tocar.

### Fase 1 — Tokens y tema base (1–2 días)

Archivos:

- `frontend/app/assets/css/main.css` — tokens completos, `:root` y `.dark`, font loading.
- `frontend/app/app.config.ts` — `neutral: 'stone'`, defaults de Nuxt UI.
- Nuevo `frontend/app/assets/css/typography.css` — utilidades `.text-display`, `.text-h1`, etc., y aplicar `font-feature-settings` global.
- `frontend/nuxt.config.ts` — registrar Inter Variable.
- Nuevo: `frontend/app/composables/useDensity.ts` — toggle `comfortable | compact`, persistido en `localStorage`, expuesto como clase en `<html>`.
- Nuevo: `frontend/app/components/shared/DensityToggle.vue` — control en header junto a `UColorModeButton`.

Criterio de salida: la app se renderiza con la nueva paleta, fuente y densidad sin que ningún componente se rompa visualmente (puede haber inconsistencias menores que se arreglan en fase 2).

### Fase 2 — Componentes compartidos (2–3 días)

Refactor visual sin cambios de API:

- `components/shared/ActionButton.vue` — alinear `variant`, `size`, espaciado a tokens.
- `layouts/default.vue` — sidebar:
  - Fondo `--color-surface-muted`, sin borde derecho (separación por color, no por línea).
  - Items activos: pill blando, sin background pleno saturado (`bg-primary-50` → tinte `primary soft`).
  - Header: borde inferior `border-subtle` en vez de `border-gray-200`.
  - Toggle de densidad junto al `UColorModeButton`.
- `layouts/guest.vue` — coherente con login.
- Crear `components/shared/PageHeader.vue` (no existe) — para reemplazar el patrón repetido `<h1>` + acciones que aparece en cada página. Slots `title`, `subtitle`, `actions`, `tabs`. Espaciado y tipografía consistentes.
- Crear `components/shared/EmptyState.vue` — el patrón `UCard > center > icon + text + button` se repite en dashboard, patients, appointments, budgets. Consolidar.
- `components/shared/PatientSearch.vue`, `PatientVisualSelector.vue`, `TreatmentVisualSelector.vue` — alinear radius, sombras y bordes.

### Fase 3 — Pase por módulo clínico (3–4 días)

**Dashboard (`pages/index.vue`):**
- Cards sin `border` redundante, sólo sombra `--shadow-sm`.
- Quitar `text-3xl font-bold` para el contador → `text-display` con `tnum` activado.
- "Próxima cita" pasa de `bg-primary-50` a `bg-surface-muted` con barra lateral primary 2 px.

**Lista de pacientes (`pages/patients/index.vue`):**
- Tabla con `border-subtle` en filas, sin borde exterior.
- Hover de fila: `bg-surface-muted` (no `bg-gray-100`).
- Avatar 28 px (compact) / 32 px (comfortable).

**Ficha de paciente (`pages/patients/[id].vue` + `components/patient/*`):**
- `PatientAlertsBanner` — patrón pastel: fondo `--color-danger-soft` (o `--color-warning-soft` según severidad), texto en `--color-danger-text`, icono de alerta en `--color-danger-accent`, rail izquierdo 3 px en `--color-danger-accent`. Sigue siendo inmediatamente percibible pero sin el muro de rojo saturado.
- `PatientQuickInfo`, `MedicalHistoryForm`, `EmergencyContactForm`, `LegalGuardianForm` — formularios densos pero comfortable.
- `ClinicalTab` — los segmented controls (`ClinicalModeToggle`, `AppointmentsMode`, etc.) usan pills planos en vez de tabs subrayados, mejor jerarquía con el odontograma debajo.

### Fase 4 — Odontograma (2 días)

Las variables CSS del odontograma ya existen en `main.css`. Re-armonizarlas con los nuevos tokens:

- `--odontogram-bg` → `--color-surface-muted`.
- `--odontogram-fill` → `--color-surface`.
- `--odontogram-outline` → derivar de `--color-text-muted` con alpha.
- `--odontogram-selected` → `--color-primary-500`.
- `TreatmentBar`, `TreatmentPanel`, `TreatmentListSection` — densidad `compact` forzada, separadores `border-subtle`, badges de estado en variante *soft*.
- `ToothTooltip` — fondo `--color-surface` con `--shadow-md` y `border` whisper.
- `OdontogramLegend` — chips compactos, gap 8 px.

**Cuidado:** los iconos de tratamiento (`TreatmentIcons.ts`) usan colores que codifican estado clínico. **No se tocan** salvo para verificar que cumplen WCAG AA contra el nuevo fondo del odontograma en ambos modos.

### Fase 5 — Calendario y agenda (2 días)

`AppointmentCalendar` (semanal) y `AppointmentDailyView` (diaria):
- Densidad `compact` forzada.
- Grid lines: `border-subtle`.
- Bloques de cita: fondo derivado del color del profesional con alpha 0.12, borde izquierdo 3 px del color pleno (en vez de fondo pleno que satura la vista).
- Estado `cancelled`: opacity 0.5 + tachado del título, no un color rojo intenso (no es alerta, es estado).
- Estado `conflict` o solapamiento: borde 1 px en `--color-danger-accent` + tinte de fondo `--color-danger-soft` con alpha bajo. Icono de aviso en `--color-danger-accent` arriba-derecha. Sigue siendo alerta clara, sin saturar la franja horaria.
- `AppointmentModal` — formulario en `comfortable`, ancho 480–560 px.

### Fase 6 — Presupuestos, planes, facturas, documentos (2–3 días)

- `BudgetFilters`, `BudgetItemModal`, `BudgetStatusBadge` — todos los badges en variante pastel (`soft bg + text`). "Vencido" añade rail/icono en `--color-danger-accent` para diferenciarse del resto sin saturar.
- `TreatmentPlanCard`, `TreatmentPlanDetail`, `TreatmentPlanMiniCard`, `TreatmentPlanModal`, `TreatmentPlanStatusBadge` — alineación con tokens.
- `InvoiceItemModal`, `NewInvoiceItemModal` — `tnum` en columnas de importe.
- Vistas de `pages/invoices`, `pages/budgets`, `pages/treatment-plans`, `pages/reports`, `pages/settings` — adoptar `PageHeader` y `EmptyState`.

### Fase 7 — QA, accesibilidad y screenshots after (2 días)

- Auditoría de contraste con axe-core o Lighthouse en cada vista mayor (claro y oscuro).
  - Texto cuerpo ≥ 4.5:1.
  - Texto grande ≥ 3:1.
  - Componentes UI (bordes activos, focus) ≥ 3:1.
- Verificar focus visible en **todos** los elementos interactivos (anillo `--color-primary-500` 2 px + offset 2 px).
- Verificar `prefers-reduced-motion`: deshabilitar transiciones de hover/expand.
- Verificar tamaños de tap targets ≥ 44 px en móvil.
- Capturar **screenshots after** equivalentes a fase 0. Generar `docs/technical/ui-redesign-comparison.md` con before/after.

---

## 5. Cambios concretos por archivo (resumen)

| Archivo | Acción |
|---|---|
| `frontend/app/assets/css/main.css` | Reemplazar contenido: tokens completos, dark/light, font loading |
| `frontend/app/assets/css/typography.css` | **NEW** — utilidades de tipografía |
| `frontend/app/app.config.ts` | `neutral: 'stone'`, defaults de Nuxt UI por componente |
| `frontend/nuxt.config.ts` | Importar typography.css; registrar fuente Inter Variable |
| `frontend/app/composables/useDensity.ts` | **NEW** |
| `frontend/app/components/shared/DensityToggle.vue` | **NEW** |
| `frontend/app/components/shared/PageHeader.vue` | **NEW** |
| `frontend/app/components/shared/EmptyState.vue` | **NEW** |
| `frontend/app/layouts/default.vue` | Refactor sidebar/header a tokens, integrar `DensityToggle` |
| `frontend/app/layouts/guest.vue` | Refactor a tokens |
| `frontend/app/components/shared/ActionButton.vue` | Defaults a tokens |
| `frontend/app/pages/index.vue` | `PageHeader`, cards a tokens, `tnum` en KPI |
| `frontend/app/pages/patients/**` | `PageHeader`, `EmptyState`, tabla a tokens |
| `frontend/app/pages/appointments/index.vue` | `PageHeader`, `EmptyState` |
| `frontend/app/pages/budgets/**`, `pages/invoices/**`, `pages/treatment-plans/**`, `pages/reports/**`, `pages/settings/**` | Adoptar primitivas compartidas |
| `frontend/app/components/clinical/**` | Pase visual por modo, banners conservan saturación clínica |
| `frontend/app/components/odontogram/**` | Re-armonizar variables CSS, densidad compacta forzada |
| `frontend/app/components/patient/PatientAlertsBanner.vue` | **No degradar** saturación danger |
| `frontend/app/components/patient/*` | Pase visual |
| `frontend/app/components/budget/*`, `treatment-plans/*`, `billing/*` | Badges a *soft*, tnum en importes |

---

## 6. Modo oscuro: notas críticas

- **Sin sombras visibles.** En oscuro, la elevación se comunica por **color de superficie más claro**, no por sombra. `--shadow-*` se sobrescribe a `none` dentro de `.dark`.
- **Bordes ligeramente más visibles** que en claro (alpha 0.10 vs 0.06) porque el contraste superficie/superficie es más sutil.
- **Texto evita el blanco puro.** `rgba(255, 250, 240, 0.92)` con tinte cálido — equivalente al "near-black" de DESIGN.md, en espejo.
- **Saturación de color primario** se sube ligeramente (`sky-400` en lugar de `sky-500`) — los azules pierden vivacidad sobre fondos oscuros y necesitan compensación.
- **Iconografía clínica** (alergias, contraindicaciones) mantiene contraste 4.5:1 mínimo en ambos modos. Si un color falla, se ajusta el del icono, no se baja la importancia visual.

---

## 7. Accesibilidad (WCAG AA, requisito clínico)

Mínimos no negociables:

- **Contraste**: cuerpo 4.5:1, grande 3:1, UI 3:1, en ambos modos.
- **Focus visible**: anillo 2 px + offset 2 px en cada interactivo. Nunca `outline: none` sin reemplazo.
- **Hit targets**: ≥ 44×44 px en móvil/tablet (gabinete suele usar tablet).
- **Motion**: `@media (prefers-reduced-motion: reduce) { * { transition: none !important; animation: none !important; } }`.
- **Alertas clínicas**: nunca codificadas sólo por color. Texto + icono + color.
- **Navegación por teclado** preservada en todos los flujos (no añadir trampas de foco con modales nuevos).
- **Semántica HTML**: usar `<button>`, `<nav>`, `<main>`, `<section>`, `<aside>` correctamente. `<h1>` único por página.
- **Densidad compact** no debe bajar tap targets en táctil. En móvil/tablet se fuerza `comfortable` independientemente de la preferencia.

---

## 8. Validación

### Visual
- Screenshots before/after por vista (claro y oscuro) → `docs/technical/ui-redesign-comparison.md`.
- Revisión cruzada en pantalla calibrada y en tablet (gabinete real).

### Automatizada
- `npm run lint` limpio.
- `npm run typecheck` limpio.
- `npm run test` — los tests existentes no deben romperse (cambios son visuales).
- Lighthouse Accessibility score ≥ 95 en `/`, `/patients`, `/patients/[id]`, `/appointments`.
- axe-core sin violaciones serias.

### Manual
- Probar 30 min de uso continuo en cada modo. Notar fatiga visual, click targets, legibilidad de cifras y nombres largos.
- Probar con copia más larga del español: nombres compuestos (`María del Carmen Fernández-González`), tratamientos largos (`Endodoncia multirradicular con reconstrucción protésica`).
- Verificar que el banner de alertas sigue siendo **inmediatamente percibido**.

---

## 9. Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Romper componentes Nuxt UI 4 al cambiar `neutral` | Cambio aislado en fase 1 con QA visual antes de fase 2 |
| Regresiones visuales en odontograma (ya tiene tokens propios) | Mantener variables actuales, sólo re-derivarlas de los nuevos tokens. Tests visuales manuales obligatorios |
| Inter Variable no se carga (red, CDN) | Auto-host vía `@fontsource-variable/inter` (NPM), no CDN |
| Densidad compact rompe layouts | Forzar `comfortable` en móvil/tablet; QA explícito por vista |
| Pastel demasiado tenue en alertas reales | Patrón `soft bg + text + accent rail` documentado: pares de color elegidos para WCAG AA mínimo (≥ 4.5:1), AAA donde es gratis. Iconos y rails en color pleno. QA visual obligatorio en `PatientAlertsBanner`, conflictos de cita y errores de validación |
| Alargamiento del PR (riesgo de churn) | Hazlo todo en la misma rama.
| Cambio de fuente afecta layouts existentes | Inter es muy similar a Public Sans en métricas; QA por vista. Si hay overflow, ajustar copia o ancho mínimo |

---

## 10. Out of scope (alineado con la issue)

- Cambios de comportamiento o navegación.
- Nuevas features, módulos o páginas.
- Cambios en backend, schemas o endpoints.
- Localización (i18n) — sólo verificar que las cadenas existentes encajan.
- Branding/logo.

---

## 11. Entregables

1. Tokens de diseño en `frontend/app/assets/css/main.css` y `typography.css`.
2. Configuración de tema Nuxt UI en `app.config.ts`.
3. Composables y componentes compartidos nuevos: `useDensity`, `DensityToggle`, `PageHeader`, `EmptyState`.
4. Refactor visual de layouts, ficha de paciente, dashboard, agenda, odontograma, presupuestos, planes, facturas, settings.
5. `docs/technical/ui-redesign-baseline.md` (inventario fase 0).
6. `docs/technical/ui-redesign-comparison.md` (before/after screenshots).
7. Una serie de PRs por fase, sin cambios de comportamiento, con visual QA documentado.
