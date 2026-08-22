---
module: expenses
last_verified_commit: 0000000
---

# expenses — overview

Fixed/recurring office expense tracking (rent, utilities, salaries,
supplies, equipment, insurance, maintenance, other). Custom community
module.

## What it is

Standard clinic-scoped CRUD over a flat `Expense` list: create, list
(filterable by category and date range, paginated), get, update (partial
via `exclude_unset`), delete. A monthly-totals-by-category summary
endpoint aggregates for a given year+month.

`category` is a closed `Literal` set on the Pydantic schemas (422 on an
invalid value), stored as a plain `String(20)` column rather than a
Postgres enum, so adding a category later is a code-only change with no
migration.

No cross-module reads or writes. No events emitted or subscribed.

## Data model

- `expenses` — `id`, `clinic_id`, `category`, `amount` (numeric 10,2),
  `expense_date`, `description` (nullable), `created_by` (nullable FK to
  `users.id`).

## Lifecycle

`installable=True`, `auto_install=False` (ships inactive, the admin
activates it from the module admin UI), `removable=True`. Own Alembic
branch (`expenses`), rooted independently on core `"0001"` — no
cross-branch FK, so no `depends_on` needed.
