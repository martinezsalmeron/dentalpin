---
module: patients
screen: detail
route: /patients/[id]
related_endpoints:
  - GET /api/v1/patients/{patient_id}
  - PUT /api/v1/patients/{patient_id}
  - DELETE /api/v1/patients/{patient_id}
  - GET /api/v1/patients/{patient_id}/extended
  - PUT /api/v1/patients/{patient_id}/extended
related_permissions:
  - patients.read
  - patients.write
related_paths:
  - backend/app/modules/patients/router.py
  - backend/app/modules/patients/frontend/pages/patients/[id].vue
last_verified_commit: 0e9a0ac
---

# Ficha del paciente

Vista completa de un único paciente. Combina identidad, demografía
extendida, contenido clínico que aportan otros módulos y un slot de
acciones al que se enganchan módulos hermanos.

## Diseño

- **Cabecera resumen** — nombre, foto, cumpleaños, contacto y avisos
  clave (`do_not_contact`, archivado, etc.).
- **Slot de acciones** — botones aportados por módulos hermanos:
  - **Recalls** → *Programar recall*
  - **Notificaciones** → *Enviar mensaje*
  - Aparecen automáticamente conforme se registran nuevos módulos.
- **Pestañas** — contenido clínico (notas, tratamientos, fotos,
  planes, presupuestos…) suministrado por otros módulos. Cada pestaña
  respeta sus propios permisos.

## Editar identidad

> Requiere `patients.write`.

1. Pulsa el icono del lápiz en la cabecera, o el botón **Editar** de
   la sub-pestaña *Identidad*.
2. Actualiza nombre, contacto, documento, demografía. Los datos
   extendidos viven detrás de *Identidad → Extendido* y se guardan
   por el endpoint `/extended`.
3. **Guardar** publica un evento `patient.updated` con los campos
   modificados, para que los dependientes (recalls, notificaciones…)
   puedan reaccionar.

## Archivar un paciente

> Requiere `patients.write`. **Nunca** se borra físicamente.

1. Abre el menú **⋮ Más** en la cabecera resumen.
2. Pulsa **Archivar paciente**.
3. Confirma. El `status` del paciente pasa a `archived`, la fila se
   oculta del listado por defecto y se publica un evento
   `patient.archived`.
4. Para restaurar, ejecuta un `UPDATE` SQL sobre la columna `status` —
   no hay flujo en la app para des-archivar todavía.

## "No contactar"

El flag `do_not_contact` es la opción de exclusión operativa. Cuando
está activo:

- El módulo de recalls excluye al paciente de cualquier cola.
- Futuros módulos de comunicación (email, SMS) DEBEN respetarlo.
- El paciente sigue apareciendo en el listado y se puede abrir con
  normalidad — solo deja de recibir contactos automatizados.

## Permisos

| Lo que ves / puedes hacer | Permiso |
|---------------------------|---------|
| Ver la ficha | `patients.read` |
| Editar identidad / extendido | `patients.write` |
| Archivar | `patients.write` |
| Acciones de módulos hermanos (recalls, notificaciones…) | El permiso del módulo hermano. |

## Resolución de problemas

- **No veo los botones Editar y Archivar.** Tu rol no tiene
  `patients.write`. Un administrador puede concederlo en
  *Ajustes → Usuarios → Roles*.
- **Falta una pestaña que esperaba.** Esa pestaña la aporta un módulo
  hermano (p. ej., *Planes de tratamiento*). Asegúrate de que ese
  módulo está instalado y de que tienes su permiso de lectura.
