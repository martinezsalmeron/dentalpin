---
module: expenses
screen: index
route: /expenses
related_endpoints:
  - GET /api/v1/expenses
  - GET /api/v1/expenses/monthly-totals
  - POST /api/v1/expenses
  - PATCH /api/v1/expenses/{expense_id}
  - DELETE /api/v1/expenses/{expense_id}
related_permissions:
  - expenses.read
  - expenses.write
related_paths:
  - backend/app/modules/expenses/frontend/pages/expenses/index.vue
last_verified_commit: 0000000
---

# /expenses

Seguimiento de gastos fijos y recurrentes de la clínica — alquiler,
suministros, salarios, material, equipamiento, seguro, mantenimiento y
otros.

## Permisos

- `expenses.read` — ver la lista (`admin` y el resto de roles por
  defecto).
- `expenses.write` — añadir, editar, eliminar (solo `admin` por
  defecto).

## Qué hace esta pantalla

- **Filtrar** la lista por categoría y rango de fechas.
- **Añadir gasto** — abre un modal para categoría, importe, fecha y una
  descripción opcional.
- **Editar / eliminar** por fila, restringido a `expenses.write`.
