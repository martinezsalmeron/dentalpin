---
module: migration_import
last_verified_commit: HEAD
locale: es
---

# Migración de datos (dental-bridge)

El módulo **migration_import** importa la base de datos de una clínica
extraída por [dental-bridge](https://github.com/dentaltix/dental-bridge)
— pacientes, citas, presupuestos, pagos, documentos y más — a tu
clínica de DentalPin.

El módulo es opcional. Un administrador lo activa desde
**Configuración → Módulos**, ejecuta la migración y puede desinstalarlo
cuando termine. Los datos importados sobreviven a la desinstalación —
pertenecen a los módulos habituales (`patients`, `payments`, `media`,
…), no a `migration_import`.

## Requisitos previos

- Un archivo `.dpm` generado por dental-bridge (acepta `.dpm`,
  `.dpm.zst`, `.dpm.enc`, `.dpm.zst.enc`).
- Si el archivo está cifrado, la contraseña usada durante la
  extracción.
- La clínica de destino debe estar seleccionada en la barra superior.
  La importación siempre se aplica a la clínica *actual*. **Elige una
  clínica vacía o casi vacía — no hay deshacer.**

## Pasos

1. Abre **Configuración → Workspace → Migración de datos**.
2. Sube el archivo `.dpm`. Si está cifrado, introduce la contraseña.
3. Espera a *Validando*. El módulo verifica el hash de integridad y
   rechaza cualquier archivo corrupto o con versión de formato
   superior a la soportada.
4. Revisa la **Vista previa**: contadores por entidad, filas de
   ejemplo, advertencias del extractor y el número de binarios
   adjuntos esperados.
5. Si el archivo contiene datos legales españoles (Verifactu) y el
   módulo Verifactu está instalado, marca *"Importar datos legales
   Verifactu"*. Para clínicas de PT / FR esa casilla está oculta.
6. Pulsa **Confirmar e importar**. El progreso se muestra en vivo.
7. El agente de sincronización sube radiografías y documentos en
   segundo plano. Aparecerán en la pestaña *Documentos* de cada
   paciente conforme lleguen.

## ¿Qué hago si algo falla?

- **Validación fallida**: el archivo no pasó la comprobación de
  integridad. Lo más habitual es una subida truncada o una contraseña
  incorrecta. Vuelve a subirlo.
- **Importación fallida**: abre *Advertencias* en la página del job.
  Cada fallo de mapper aparece con la entidad, el id de origen y el
  mensaje de error.
- **Sin deshacer**: la v1 no admite rollback. Si una importación
  parcial es irrecuperable, restaura la base de datos desde tu último
  backup.

## Ver también

- [Referencia de pantalla](./screens/data-migration.md)
- Técnico: `docs/technical/migration_import/`
