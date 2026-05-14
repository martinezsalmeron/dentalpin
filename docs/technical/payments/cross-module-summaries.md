---
module: payments
last_verified_commit: 74a12b8
---

# Payments cross-module summary + filter endpoints

Companion to [`docs/features/lists-redesign.md`](../../features/lists-redesign.md) and [`docs/technical/lists-redesign.md`](../lists-redesign.md). This file is the long-term reference for the four payments-side endpoints that let other modules' list pages enrich and filter without importing payments code.

## Why these endpoints

The `/patients` and `/budgets` list pages want to show debt and payment-progress columns and to filter "patients with debt > 0" / "unpaid budgets". Both belong to modules that **must not depend on payments** (`patients.depends = []`, `budget.depends = ["patients", "catalog", "odontogram"]`). Payments owns the data; payments must own the endpoints. The host pages call these endpoints from the page-level fetcher, exactly as the `invoice.list.row.meta` compliance slot already does for verifactu.

## Endpoint contracts

### 1. `POST /api/v1/payments/summary/by-budgets`

Bulk per-budget payment summary. Returns `collected`, `pending`, `payment_status` for each requested budget id.

**Permission**: `payments.record.read`.

**Request body**:

```json
{ "budget_ids": ["uuid", "uuid", "..."] }
```

Constraints:
- 1 ≤ `len(budget_ids)` ≤ 100. >100 returns 422 with `detail: "budget_ids cap is 100"`.
- All ids must belong to the caller's clinic; ids from other clinics are silently omitted from the result (multi-tenancy via `clinic_id` filter).

**Response** (`ApiResponse[BudgetSummariesByIds]`):

```ts
{
  data: {
    summaries: {
      [budget_id: string]: {
        collected: string,       // Decimal serialised as string
        pending: string,         // total_with_tax - collected, clamped >= 0
        payment_status: 'unpaid' | 'partial' | 'paid'
      }
    }
  }
}
```

Budgets without any allocation appear in the map with `collected="0.00"`, `pending=<total>`, `payment_status="unpaid"`. Ids missing from `payments.budgets` queries simply don't appear (e.g. cross-clinic).

**`payment_status` derivation** (off-books safe — pure payments axis):

```python
collected = Σ PaymentAllocation.amount
            where target_type = 'budget' AND budget_id = <id>
total = budget.total_with_tax        # read via SELECT on budgets table, allowed
                                     # because payments.depends includes budget
if collected <= 0:           payment_status = 'unpaid'
elif collected >= total:     payment_status = 'paid'
else:                        payment_status = 'partial'
```

**Example**:

```bash
curl -X POST /api/v1/payments/summary/by-budgets \
  -H "Authorization: Bearer ..." \
  -H "Content-Type: application/json" \
  -d '{"budget_ids": ["c8a...", "9b2..."]}'

# 200 OK
{
  "data": {
    "summaries": {
      "c8a...": { "collected": "1840.00", "pending":   "0.00", "payment_status": "paid" },
      "9b2...": { "collected":  "500.00", "pending": "300.00", "payment_status": "partial" }
    }
  }
}
```

### 2. `POST /api/v1/payments/summary/by-patients`

Bulk per-patient payment summary. Returns the same data shape the existing `PatientLedger` exposes but trimmed to what a list cell needs.

**Permission**: `payments.record.read`.

**Request body**:

```json
{ "patient_ids": ["uuid", "uuid", "..."] }
```

Cap 100; same clinic-scoping as above.

**Response**:

```ts
{
  data: {
    summaries: {
      [patient_id: string]: {
        total_paid: string,           // net of refunds
        debt: string,                 // clinic_receivable = max(0, earned - net_paid)
        on_account_balance: string    // Σ allocations target_type='on_account'
      }
    }
  }
}
```

Patients with zero activity (no payments, no earned entries) appear with all values `"0.00"`.

**Off-books invariant**: `debt` is computed strictly from `(earned − paid_net)` per the existing `LedgerService` logic. It is **never** computed against invoiced totals. Reviewers check this: the implementation reuses or mirrors `LedgerService.get_patient_ledger` aggregation logic exactly.

### 3. `GET /api/v1/payments/filters/budgets-by-status`

Returns the set of budget ids in the clinic whose current payment status matches the requested values. Used by `/budgets` to translate the "Cobro" filter into a `budget_ids` intersection on `/budgets`.

**Permission**: `payments.record.read`.

**Query params**:
- `status` (repeatable): `unpaid` | `partial` | `paid`. At least one required.
- Optional filter narrowing: `patient_id: UUID`, `assigned_professional_id: UUID`. These let the page reduce the candidate set before hitting the cap. Implementation-wise the endpoint joins `budgets` (legal — budget is in payments.depends) and applies them server-side.

**Response**:

```ts
{
  data: {
    budget_ids: string[],   // capped at 1000
    truncated: boolean      // true if there were more
  }
}
```

**Truncation policy**: if the candidate set exceeds 1000, return the first 1000 by `budget.created_at DESC` and set `truncated=true`. The frontend surfaces a toast: *"Resultados truncados; refina los filtros."* (i18n key `lists.truncatedWarning`).

**Example**:

```bash
curl '/api/v1/payments/filters/budgets-by-status?status=unpaid&status=partial'
# 200 OK
{ "data": { "budget_ids": ["...", "..."], "truncated": false } }
```

### 4. `GET /api/v1/payments/filters/patients-with-debt`

Returns the set of patient ids in the clinic with `debt >= min_debt`. Used by `/patients` to translate the "Con deuda" toggle into `patient_ids` on `/patients`.

**Permission**: `payments.record.read`.

**Query params**:
- `min_debt: Decimal` — default `0.01`. The threshold above which a patient counts as "with debt". `0.01` means "any positive debt"; we don't use `>0` strictly because Decimal comparisons need a concrete number.

**Response**:

```ts
{
  data: {
    patient_ids: string[],   // capped at 1000
    truncated: boolean
  }
}
```

Same truncation policy as endpoint 3.

## Schemas

Add to `backend/app/modules/payments/schemas.py`:

```python
class BudgetSummaryByIds(BaseModel):
    collected: Decimal
    pending: Decimal
    payment_status: Literal["unpaid", "partial", "paid"]


class BudgetSummariesByIds(BaseModel):
    summaries: dict[UUID, BudgetSummaryByIds]


class PatientSummaryByIds(BaseModel):
    total_paid: Decimal
    debt: Decimal
    on_account_balance: Decimal


class PatientSummariesByIds(BaseModel):
    summaries: dict[UUID, PatientSummaryByIds]


class BudgetIdsRequest(BaseModel):
    budget_ids: list[UUID] = Field(..., min_length=1, max_length=100)


class PatientIdsRequest(BaseModel):
    patient_ids: list[UUID] = Field(..., min_length=1, max_length=100)


class FilterIdsResponse(BaseModel):
    budget_ids: list[UUID] | None = None
    patient_ids: list[UUID] | None = None
    truncated: bool
```

## Service-layer signatures

Add to `backend/app/modules/payments/service.py` under `PaymentReadService`:

```python
class PaymentReadService:
    # ... existing methods ...

    @staticmethod
    async def summaries_by_budgets(
        db: AsyncSession,
        clinic_id: UUID,
        budget_ids: list[UUID],
    ) -> dict[UUID, BudgetSummaryByIds]:
        """Return collected/pending/payment_status per budget id.

        Reads from PaymentAllocation (own table) and budgets.total_with_tax
        (legal cross-read: budget is in payments.depends). Off-books safe:
        never touches invoice totals.
        """

    @staticmethod
    async def summaries_by_patients(
        db: AsyncSession,
        clinic_id: UUID,
        patient_ids: list[UUID],
    ) -> dict[UUID, PatientSummaryByIds]:
        """Per-patient total_paid/debt/on_account_balance.

        Mirrors LedgerService.get_patient_ledger aggregation but in bulk
        and without the timeline. debt = max(0, earned - net_paid).
        """

    @staticmethod
    async def budget_ids_by_payment_status(
        db: AsyncSession,
        clinic_id: UUID,
        statuses: list[Literal["unpaid", "partial", "paid"]],
        *,
        patient_id: UUID | None = None,
        assigned_professional_id: UUID | None = None,
        cap: int = 1000,
    ) -> tuple[list[UUID], bool]:
        """Return (budget_ids, truncated). At-most `cap` ids."""

    @staticmethod
    async def patient_ids_with_debt(
        db: AsyncSession,
        clinic_id: UUID,
        min_debt: Decimal = Decimal("0.01"),
        cap: int = 1000,
    ) -> tuple[list[UUID], bool]:
        """Return (patient_ids, truncated). At-most `cap` ids."""
```

## Router additions

In `backend/app/modules/payments/router.py`, mount under the existing `/` prefix:

```python
@router.post("/summary/by-budgets", response_model=ApiResponse[BudgetSummariesByIds])
async def summary_by_budgets(
    payload: BudgetIdsRequest,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("payments.record.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[BudgetSummariesByIds]:
    summaries = await PaymentReadService.summaries_by_budgets(
        db, ctx.clinic_id, payload.budget_ids
    )
    return ApiResponse(data=BudgetSummariesByIds(summaries=summaries))


@router.post("/summary/by-patients", response_model=ApiResponse[PatientSummariesByIds])
async def summary_by_patients(
    payload: PatientIdsRequest,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("payments.record.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[PatientSummariesByIds]:
    summaries = await PaymentReadService.summaries_by_patients(
        db, ctx.clinic_id, payload.patient_ids
    )
    return ApiResponse(data=PatientSummariesByIds(summaries=summaries))


@router.get("/filters/budgets-by-status", response_model=ApiResponse[FilterIdsResponse])
async def filter_budgets_by_status(
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("payments.record.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    status: list[Literal["unpaid", "partial", "paid"]] = Query(..., min_length=1),
    patient_id: UUID | None = None,
    assigned_professional_id: UUID | None = None,
) -> ApiResponse[FilterIdsResponse]:
    ids, truncated = await PaymentReadService.budget_ids_by_payment_status(
        db, ctx.clinic_id, status,
        patient_id=patient_id,
        assigned_professional_id=assigned_professional_id,
    )
    return ApiResponse(data=FilterIdsResponse(budget_ids=ids, truncated=truncated))


@router.get("/filters/patients-with-debt", response_model=ApiResponse[FilterIdsResponse])
async def filter_patients_with_debt(
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("payments.record.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    min_debt: Decimal = Query(default=Decimal("0.01"), ge=Decimal("0")),
) -> ApiResponse[FilterIdsResponse]:
    ids, truncated = await PaymentReadService.patient_ids_with_debt(
        db, ctx.clinic_id, min_debt=min_debt
    )
    return ApiResponse(data=FilterIdsResponse(patient_ids=ids, truncated=truncated))
```

## Off-books invariants (reviewer checklist)

Every reviewer of these endpoints must verify:

1. **`debt` is computed from earned − paid, never invoiced − paid.** The endpoint must use `PatientEarnedEntry` aggregation, identical to `LedgerService.get_patient_ledger`. Grep the implementation for `Invoice` references — there should be **zero**.
2. **`payment_status` for a budget is computed from allocations to the budget vs `budget.total_with_tax`.** Never compared to invoice totals tied to the same budget.
3. **No endpoint joins billing tables.** `Invoice`, `InvoiceItem`, `InvoicePayment` must not appear in this file.
4. **Multi-tenancy.** Every query filters `clinic_id = ctx.clinic_id`. The cap means a malicious caller passing 100 ids of another clinic's budgets just gets an empty map, not a 403 (intentional — no information leak).

## Performance bounds

| Endpoint | Worst-case rows scanned | Bounded by |
|---|---|---|
| `/summary/by-budgets` | `100` budgets × allocations per budget | `len(budget_ids) ≤ 100` |
| `/summary/by-patients` | `100` patients × (payments + refunds + earned) per patient | `len(patient_ids) ≤ 100` |
| `/filters/budgets-by-status` | All budgets of the clinic (`O(N_budgets)`) | Aggregation indexed via `(clinic_id, target_type, budget_id)` on `PaymentAllocation` |
| `/filters/patients-with-debt` | All patients of the clinic (`O(N_patients)`) | Same indexes as the existing aging-receivables report (`idx_payments_clinic_date`, `idx_earned_clinic_performed`) |

**Index audit during impl**: confirm `idx_payment_allocations_clinic_target_budget` (or equivalent) exists for `(clinic_id, target_type, budget_id)`. If absent, add a payments-branch Alembic migration in the same PR.

## Test plan

`backend/tests/modules/payments/test_cross_module_summaries.py` (new file):

1. **Happy path summary/by-budgets**: 3 budgets, 2 fully paid, 1 partial — assert exact payment_status, collected, pending values.
2. **Budget cross-clinic isolation**: caller from clinic A requests budget ids from clinic B → those ids absent from result.
3. **Cap**: 101 budget ids → 422.
4. **Empty list of ids**: 422 (min_length=1).
5. **Happy path summary/by-patients**: patient with earned 1000 + paid 600 → debt 400, total_paid 600, on_account 0.
6. **Refunds reduce total_paid**: payment 500 + refund 200 → total_paid 300, debt updates accordingly.
7. **filter-ids cap + truncated flag**: seed >1000 unpaid budgets → list length 1000, `truncated=true`.
8. **filter-ids status combination**: `status=partial&status=paid` returns intersect of allocations with both states.
9. **Off-books smoke**: patient has 0 invoices but 1 performed treatment with `unit_price=200` → `/filters/patients-with-debt` includes the patient. `/api/v1/billing/invoices?patient_id=...` returns 0. Two distinct truths coexist; no list cross-mixes them.
10. **Permission gate**: caller without `payments.record.read` → 403 on all four endpoints.

## Frontend types

Add to `frontend/app/types/index.ts` (host) — or per-module `frontend/types.ts` if the module organises types that way:

```ts
export interface BudgetPaymentSummary {
  collected: string
  pending: string
  payment_status: 'unpaid' | 'partial' | 'paid'
}

export interface PatientPaymentSummary {
  total_paid: string
  debt: string
  on_account_balance: string
}
```

Composable signatures in `backend/app/modules/payments/frontend/composables/usePayments.ts`:

```ts
async function fetchBudgetSummaries(
  ids: string[]
): Promise<Record<string, BudgetPaymentSummary>>

async function fetchPatientDebtSummaries(
  ids: string[]
): Promise<Record<string, PatientPaymentSummary>>

async function fetchBudgetIdsByPaymentStatus(
  status: Array<'unpaid' | 'partial' | 'paid'>,
  opts?: { patient_id?: string; assigned_professional_id?: string }
): Promise<{ budget_ids: string[]; truncated: boolean }>

async function fetchPatientIdsWithDebt(
  min_debt?: number
): Promise<{ patient_ids: string[]; truncated: boolean }>
```

## ADR refs

- [`docs/adr/0001-modular-plugin-architecture.md`](../../adr/0001-modular-plugin-architecture.md) — manifest depends as the only legal cross-module read direction.
- [`docs/adr/0003-event-bus-over-direct-imports.md`](../../adr/0003-event-bus-over-direct-imports.md) — when in doubt, events; here we use direct endpoints because the data is *queried*, not *reacted to*.
- [`docs/adr/0010-payments-as-primitive-module.md`](../../adr/0010-payments-as-primitive-module.md) — payments is downstream of nothing; billing depends on payments, never the reverse.

## CHANGELOG entry

`backend/app/modules/payments/CHANGELOG.md` under `## Unreleased`:

```
### Added
- `POST /summary/by-budgets` — bulk per-budget collected/pending/status (cap 100 ids).
- `POST /summary/by-patients` — bulk per-patient total_paid/debt/on_account (cap 100 ids).
- `GET  /filters/budgets-by-status` — clinic-wide budget id set by payment status (cap 1000 ids).
- `GET  /filters/patients-with-debt` — clinic-wide patient id set with debt >= min_debt (cap 1000 ids).
- Frontend slot fillers: `patients.list.row.financial`, `patients.list.filter`,
  `budget.list.row.payments`, `budget.list.filter`. Cross-module enrichment for
  the /patients and /budgets list pages without violating module isolation.
```
