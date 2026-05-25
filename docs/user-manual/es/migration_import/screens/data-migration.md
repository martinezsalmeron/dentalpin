---
module: migration_import
last_verified_commit: HEAD
locale: es
screen: data-migration
route: /settings/workspace/data-migration
related_endpoints:
  - POST /api/v1/migration_import/jobs
  - POST /api/v1/migration_import/jobs/{id}/validate
  - POST /api/v1/migration_import/jobs/{id}/preview
  - POST /api/v1/migration_import/jobs/{id}/proposals
  - GET  /api/v1/migration_import/jobs/{id}/proposals
  - PATCH /api/v1/migration_import/jobs/{id}/proposals/{canonical_uuid}
  - POST /api/v1/migration_import/jobs/{id}/proposals/bulk_accept
  - POST /api/v1/migration_import/jobs/{id}/execute
  - GET  /api/v1/migration_import/jobs/{id}
  - POST /api/v1/migration_import/jobs/{id}/binaries
permissions:
  - migration_import.job.read
  - migration_import.job.write
  - migration_import.job.execute
---

# Pantalla — Migración de datos

Asistente de una sola página en **Configuración → Workspace →
Migración de datos**.

## Estructura

| Sección               | Qué muestra |
|-----------------------|-------------|
| **Tarjeta de subida** | Selector de archivo + contraseña. Visible solo hasta la primera subida. |
| **Cabecera del job**  | Nombre del archivo, sistema de origen, versión de formato, tamaño y estado. |
| **Vista previa**      | Contadores por tipo de entidad. |
| **Resumen de archivos** | Total de binarios esperados vs. los que traen sha256. |
| **Advertencias**      | Lista de advertencias emitidas por el extractor + por el propio importador. |
| **Revisar mapeos del catálogo** | Calcula propuestas por cada `Tratamientos` de Gesdén (POST `/proposals`), muestra una tabla con la propuesta automática (enlazar / similitud + score / crear nuevo) y permite aceptar, ignorar o re-enlazar por fila. Incluye atajo "Aceptar todos los matches ≥ 0.9". |
| **Panel de filtrado de profesionales** | Visible solo si el archivo declara filas `professional`. Muestra un desglose (total / inactivos en origen / columnas solo de agenda / sin actividad en 24m), un input numérico para *actividad mínima en meses* (por defecto 24) y tres casillas: excluir columnas solo de agenda, excluir profesionales inactivos en origen y un opcional "importar solo dentistas e higienistas". Los profesionales filtrados se importan igualmente como usuarios (para que las citas, tratamientos, presupuestos y pagos históricos sigan resolviendo) pero con `is_active=False` y rol `assistant`, que los oculta del listado de profesionales de la agenda. Después se pueden reactivar individualmente desde **Ajustes → Usuarios**. |
| **Casilla Verifactu** | Solo se muestra si Verifactu está instalado Y el archivo contiene hashes legales. |
| **Botón Confirmar**   | Lanza `POST /execute`. Requiere `migration_import.job.execute`. |
| **Progreso**          | Mientras `status = executing`, muestra *X de Y entidades*. Refresca cada 2 s. |

## Qué se importa y dónde

- **Filas con enlace al catálogo destino** se importan como
  tratamientos del odontograma + items del plan.
- **Apuntes libres y entradas no clínicas** (filas `TtosMed` de
  Gesdén sin `IdTto`, además de los tipos *Anotación*, *Nota
  Económica*, *Higiene*, *Panorámica*, *Bonos*, *Primera Visita*…)
  se importan como **notas administrativas en la pestaña Resumen del
  paciente**, no como tarjetas "Tratamiento general" en el
  odontograma. El texto original se conserva tal cual; la autoría va
  al clínico de origen cuando se puede resolver, y al administrador
  que lanzó el import en otro caso.

## Permisos

La página requiere `migration_import.job.read`. El botón **Confirmar**
queda deshabilitado para roles sin `migration_import.job.execute`.

## Capturas

_(pendientes — capturar tras el primer despliegue)_
