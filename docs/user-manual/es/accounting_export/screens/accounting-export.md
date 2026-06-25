---
module: accounting_export
screen: export
route: /accounting-export
related_endpoints:
  - GET /api/v1/accounting_export/preview
  - GET /api/v1/accounting_export/run
related_permissions:
  - accounting_export.export.read
  - accounting_export.export.run
related_paths:
  - backend/app/modules/accounting_export/frontend/pages/accounting-export.vue
  - backend/app/modules/accounting_export/router.py
last_verified_commit: 0f7fa8c
---

# Exportar a gestoría

Genera el fichero de facturas y cobros del periodo para enviárselo a tu
gestoría.

## Cómo se usa

> Ver y previsualizar requiere `accounting_export.export.read`.
> Descargar requiere `accounting_export.export.run`.

1. Elige el **periodo** en el desplegable: *mes actual*, *mes anterior*,
   *trimestre actual*, *trimestre anterior*, *año en curso* o
   *personalizado* (con fechas desde/hasta).
2. Pulsa **Previsualizar**. Verás el número de facturas y de cobros, los
   totales (base y total) y una muestra de las primeras filas.
3. Pulsa **Descargar (.zip)**. Se descarga un ZIP con `facturas.csv` y
   `cobros.csv`.

## Qué incluye el fichero

- Solo **facturas emitidas** (los borradores no se exportan) y los
  **cobros asignados** a esas facturas.
- Los CSV usan punto y coma (`;`) como separador y coma decimal, con
  codificación UTF-8 (BOM), de modo que Excel en español los abre con los
  acentos y los importes correctos.

## Permisos

| Lo que ves / puedes hacer | Permiso |
|---------------------------|---------|
| Ver la página y previsualizar | `accounting_export.export.read` |
| Descargar el export (ZIP) | `accounting_export.export.run` |

## Resolución de problemas

- **No aparece la opción en el menú.** El módulo es opcional: un
  administrador debe activarlo desde la administración de módulos.
- **Faltan cobros que esperabas.** Solo se exportan los cobros asignados
  a una factura. Un cobro suelto, sin factura, no se incluye por diseño.
- **El periodo sale vacío.** Comprueba que hay facturas **emitidas** (no
  en borrador) con fecha de emisión dentro del rango elegido.
