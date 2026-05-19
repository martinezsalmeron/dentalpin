# Quick patient creation from the agenda's "Nueva cita" modal

> Status: draft (design). Module: `agenda` (UI) + `patients` (API reuse). Spec last updated: 2026-05-19.

## Why

Recepcionista en la agenda. Suena el teléfono. Llama un paciente **nuevo** para reservar primera cita. Hoy el modal *Nueva cita* obliga a elegir un paciente existente — hay que abandonar la agenda, ir a `/patients`, crear paciente, volver, reabrir el modal de cita. 1–2 minutos perdidos con alguien al teléfono.

Necesitamos que **crear paciente + cita** lleve **≤30 segundos** sin salir del modal, con una sola mano y sin pensar. Es el flujo más sensible al tiempo de toda la recepción.

## Success criteria

- Reloj en mano: clic en hueco de agenda → cita guardada con paciente nuevo en **≤30 s** dado nombre + teléfono.
- Cero cambios de pantalla / modales anidados.
- Cero campos obligatorios más allá de nombre y apellido (lo que el backend ya exige).
- Mobile-first: el flujo funciona igual de rápido en iPhone SE (375 × 667) que en desktop.
- Sin pacientes duplicados creados de forma accidental: aviso soft cuando el teléfono ya existe.

## Principio de diseño

> **"Buscar es crear"**. La recepcionista ya teclea el nombre para buscarlo. Si no existe, crearlo es **un clic más**, no una pantalla nueva.

Reutilizamos el mismo selector de paciente: si la búsqueda no encuentra coincidencia, la última fila del dropdown es la acción de crear, con el texto tecleado pre-rellenado.

## Flujo objetivo

1. Clic en hueco de agenda → modal *Nueva cita* abierto, foco automático en selector de paciente.
2. Recepcionista teclea el nombre dictado: `María García López`.
3. Dropdown muestra coincidencias (si hay) + última fila destacada:

   ```
   ┌──────────────────────────────────────────┐
   │ 👤+  Crear paciente "María García López" │
   └──────────────────────────────────────────┘
   ```

4. Clic (o Enter cuando no hay match exacto) → la fila se expande **en el mismo dropdown** a un mini-form de 3 campos:
   - **Nombre** / **Apellidos** — pre-rellenados con split heurístico (primera palabra = nombre, resto = apellidos), siempre editables.
   - **Teléfono** — foco automático, `inputmode="tel"`, opcional con microcopy *"Lo puedes añadir después en la ficha del paciente."*
   - CTA primaria `Crear y seleccionar` · secundaria `Cancelar`.
5. Enter o tap → `POST /api/v1/patients` → paciente queda seleccionado en la card del selector, badge sutil `Nuevo` durante la sesión.
6. Recepcionista termina la cita (profesional + duración) y guarda. Fin.

## Salvaguardas

- **Soft anti-duplicado por teléfono.** Mientras teclea el teléfono, lookup debounced contra `GET /api/v1/patients?search=<phone>`. Si hay match, banner amarillo inline sobre el campo:

  > ⚠ Ya existe **Juan Pérez** con este teléfono · *Usar este paciente*

  Un clic abandona la creación y selecciona el existente. No bloquea — la clínica decide.

- **Split de nombre nunca silencioso.** La heurística rellena los dos campos pero siempre se muestran editables antes de confirmar. Apellidos compuestos como "García López" se respetan si el usuario los corrige.

- **Sin teléfono permitido.** Backend ya lo acepta. No bloquea casos atípicos (paciente cuyo familiar gestiona la cita).

- **Permisos.** Si el usuario no tiene `patients.write`, la fila `+ Crear` no aparece en el dropdown. Receptionist ya tiene este permiso vía `clinical.patients.*`.

- **Errores de servidor.** Toast rojo inline dentro del modal de cita: *"No se pudo crear el paciente · Reintentar"*. El mini-form conserva los valores tecleados.

## Mobile

- Dropdown se transforma en **bottom sheet** full-width (comportamiento `inModal` ya soportado por `PatientVisualSelector` — verificar).
- Fila `+ Crear` **sticky** abajo del sheet (siempre accesible con el pulgar).
- Al tap, el mini-form **sustituye** el contenido del sheet (no popover encima): más espacio, sin doble-capa.
- Inputs: tap target ≥ 44 pt, `autocapitalize="words"` en nombre/apellido, `inputmode="tel"` en teléfono → teclado numérico nativo.
- Viewports validados: 375 × 667 (iPhone SE), 390 × 844 (iPhone 14), 768 × 1024 (iPad).

## Estados visuales

| Estado | Tratamiento |
|---|---|
| Fila `+ Crear` en dropdown | Icono `i-lucide-user-plus`, color primario, separador superior, peso semibold |
| Mini-form abierto | Reemplaza la lista de resultados en el mismo dropdown, header `Nuevo paciente` con flecha "volver a búsqueda" |
| Guardando | Spinner en CTA `Crear y seleccionar`, campos disabled |
| Creado | Card del paciente seleccionada con badge gris `Nuevo` durante la sesión |
| Error red/servidor | Toast inline rojo, mini-form conserva valores |
| Soft duplicado por teléfono | Banner amarillo inline sobre el campo phone, CTA "Usar este paciente" |

## Fuera del alcance

- Email, fecha de nacimiento, NIF, dirección, datos de facturación, foto, avatar → se completan en el detalle del paciente después.
- Validación internacional de teléfono — guardamos lo tecleado.
- Búsqueda fuzzy / "quizás quisiste decir" — si la búsqueda actual no lo encuentra, asumimos nuevo.
- Auto-creación al pulsar Enter sin pasar por el mini-form — siempre paso de confirmación para evitar pacientes basura.

## Alternativas consideradas y descartadas

| Alternativa | Por qué no |
|---|---|
| Tab `Buscar` ⇄ `Nuevo` arriba del selector | 2 clics más, fuerza decidir antes de saber si existe |
| Card `+ Nuevo paciente` como primera de la grid de recientes | Compite visualmente con pacientes reales; ruido en el 95 % de casos donde el paciente sí existe |
| Modal anidado a pantalla completa | Rompe contexto de la cita en curso |
| Crear "fantasma" solo en cliente y persistir al guardar la cita | Riesgo de inconsistencias y pacientes sin `clinic_id` si la cita falla |

## Componentes implicados (referencia, no diseño técnico)

- `frontend/app/components/shared/PatientVisualSelector.vue` — orquesta el flujo, mini-form, llama a `POST /patients`, autoselecciona resultado.
- `frontend/app/components/shared/VisualSelector.vue` — slot/footer opcional para acción "crear".
- `backend/app/modules/agenda/frontend/components/clinical/AppointmentModal.vue` — sin cambios funcionales relevantes.
- Backend: **sin cambios**. Reutilizamos `POST /api/v1/patients` y `GET /api/v1/patients?search=`.

## Verificación end-to-end

1. `docker-compose up`, login `admin@demo.clinic / demo1234` (y luego receptionist para validar permisos).
2. Agenda → clic en hueco vacío → modal abierto, selector enfocado.
3. Teclear nombre que no existe → ver fila `+ Crear "..."`.
4. Clic → mini-form pre-rellenado → corregir split, añadir teléfono → `Crear y seleccionar`.
5. Verificar: paciente queda seleccionado, badge `Nuevo`.
6. Completar profesional + duración → Guardar cita.
7. Ir a `/patients`, abrir el recién creado → verificar persistencia + `clinic_id`.
8. Repetir tecleando un teléfono ya existente → banner soft-duplicado, clic "Usar este paciente" → mini-form cierra, paciente existente seleccionado.
9. Repetir TODO en viewport 375 × 667 → sheet, sticky `+ Crear`, tap targets, teclado.
10. Login receptionist sin `patients.write` (si existe) → verificar que la fila `+ Crear` no aparece.

## Siguiente paso

Plan técnico (fase 2): estados internos del componente, contrato de props/emits del nuevo modo "create", manejo de race condition (usuario teclea mientras crea), invalidación de cache de recientes, tests unitarios + e2e. Pendiente de aprobar este diseño primero.
