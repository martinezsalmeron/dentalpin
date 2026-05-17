---
module: migration_import
last_verified_commit: HEAD
locale: es
screen: data-migration
path: /settings/workspace/data-migration
related_endpoints:
  - POST /api/v1/migration-import/jobs
  - POST /api/v1/migration-import/jobs/{id}/validate
  - POST /api/v1/migration-import/jobs/{id}/preview
  - POST /api/v1/migration-import/jobs/{id}/execute
  - GET  /api/v1/migration-import/jobs/{id}
  - POST /api/v1/migration-import/jobs/{id}/binaries
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
| **Casilla Verifactu** | Solo se muestra si Verifactu está instalado Y el archivo contiene hashes legales. |
| **Botón Confirmar**   | Lanza `POST /execute`. Requiere `migration_import.job.execute`. |
| **Progreso**          | Mientras `status = executing`, muestra *X de Y entidades*. Refresca cada 2 s. |

## Permisos

La página requiere `migration_import.job.read`. El botón **Confirmar**
queda deshabilitado para roles sin `migration_import.job.execute`.

## Capturas

_(pendientes — capturar tras el primer despliegue)_
