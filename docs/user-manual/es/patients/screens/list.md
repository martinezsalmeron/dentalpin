---
module: patients
screen: list
route: /patients
related_endpoints:
  - GET /api/v1/patients
  - GET /api/v1/patients/recent
  - POST /api/v1/patients
related_permissions:
  - patients.read
  - patients.write
related_paths:
  - backend/app/modules/patients/router.py
  - backend/app/modules/patients/frontend/pages/patients/index.vue
last_verified_commit: 0e9a0ac
screenshots:
  - patients.png
---

# Listado de pacientes

Muestra todos los pacientes activos de la clínica. Desde aquí puedes
buscar, filtrar, abrir la ficha de un paciente o crear uno nuevo.

## De un vistazo

- **Vista por defecto:** solo pacientes activos. Los archivados quedan
  ocultos; el endpoint de listado no los devuelve por defecto.
- **Panel de recientes:** la barra lateral muestra los pacientes
  abiertos más recientemente — proviene del endpoint
  `GET /api/v1/patients/recent`.
- **Paginación:** 20 pacientes por página. El selector de tamaño de
  página permite ampliarlo; el backend admite hasta 100.

## Cómo encontrar un paciente

1. Escribe nombre, apellido o número de documento en la caja de
   búsqueda. La consulta filtra por coincidencias exactas y parciales.
2. Pulsa **Enter** o espera al debounce — los resultados se actualizan
   en sitio.
3. Haz clic en una fila para abrir la
   [ficha del paciente](./detail.md).

## Cómo crear un paciente

> Requiere el permiso `patients.write`.

1. Pulsa **Nuevo paciente** en la barra superior derecha.
2. Rellena los campos obligatorios de identidad (nombre, apellidos,
   fecha de nacimiento). El contacto y la demografía se pueden añadir
   ahora o más tarde desde la ficha.
3. Pulsa **Guardar**. El nuevo paciente aparece arriba del listado y
   el sistema publica un evento `patient.created` para que otros
   módulos (recalls, notificaciones…) reaccionen.

## Permisos

| Lo que ves / puedes hacer | Permiso |
|---------------------------|---------|
| Navegar y buscar el listado | `patients.read` |
| Ver el botón **Nuevo paciente** | `patients.write` |

## Resolución de problemas

- **El listado está vacío tras una instalación nueva.** Ejecuta
  `./scripts/seed-demo.sh` para cargar datos de demo.
- **Un paciente recién creado no aparece.** Comprueba el filtro activo:
  si activaste el conmutador *Mostrar archivados*, solo se ven filas
  archivadas.
