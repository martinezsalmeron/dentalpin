---
module: payments
last_verified_commit: 74a12b8
---

# Patient ledger subtab — technical plan

Companion to [`docs/features/patient-payments-subtab.md`](../../features/patient-payments-subtab.md) (design spec). This file is the engineering contract: what gets built, where it lives, which dependencies cross, how it's verified.

## Goal

Render a patient-centric ledger view (balance + timeline) as a new sub-mode inside the existing `AdministrationTab` on the patient detail page. Built entirely from existing primitives — **no new endpoints, no new permissions, no new slot infra, no migrations**.

## Architecture audit (verified against `feat/payments-module`)

| Claim | Verified |
|---|---|
| Ledger endpoint exists | `backend/app/modules/payments/router.py` `GET /patients/{patient_id}/ledger`, permission `payments.record.read` |
| Returns `PatientLedger` with `total_paid`, `total_earned`, `patient_credit`, `clinic_receivable`, `on_account_balance`, `timeline[]` | `frontend/app/types/index.ts:1388-1397` |
| TS types stable | `PatientLedger`, `PatientLedgerEntry`, `PaymentRefundCreate`, `PaymentRecord` already in `frontend/app/types/index.ts:1339-1397` |
| Composable | `usePayments().fetchPatientLedger(id)` `backend/app/modules/payments/frontend/composables/usePayments.ts:106` |
| Refund composable | `usePayments().refund(id, payload)` `…/usePayments.ts:87` — payload requires `{amount, method, reason_code, reason_note?}` |
| Slot registry | `frontend/app/composables/useModuleSlots.ts` — `resolveSlot(name, ctx, {can})` already filters by permission |
| `<ModuleSlot>` host renderer | `frontend/app/components/ModuleSlot.vue` — passes `ctx` verbatim to each registered component as `:ctx` prop |
| Provider self-registration pattern | `backend/app/modules/payments/frontend/plugins/slots.client.ts` (existing `budget.detail.sidebar` + `reports.categories`) |
| `AdministrationTab` mode-switch shape | `backend/app/modules/patients/frontend/components/patient/AdministrationTab.vue:26,67-82,79` (URL sync via `adminMode`, validation list hardcoded) |
| `AdministrationMode` union | `…/AdministrationModeToggle.vue:5` (`'budgets' \| 'billing' \| 'documents'`) |
| `payments.removable = False` | `backend/app/modules/payments/CLAUDE.md` — uninstall is blocked. The "module gone" branch in the design becomes a no-op; permission-denied is the only realistic empty case |
| `PaymentCreateModal` pre-fill contract | `…/PaymentCreateModal.vue:17-29` — `defaultPatientId`, `defaultBudgetId`, `defaultAmount`, `budgetLabel` props |
| Shared totals/banner components | `frontend/app/components/shared/EntityTotalsCard.vue` (`lines: TotalLine[]`), `EntityCriticalBanner.vue` (`role`, `title`, optional `cta`) |

## Slot name (locked)

`patient.detail.administracion.payments` — **mixed-case allowed once**: matches the user-facing tab label "Administración" so the contract reads naturally in both modules, and the registry has no name-case constraint. Other slot names in the repo (`patient.detail.tabs`, `budget.detail.sidebar`) use English; we accept the inconsistency here because "administración" is the tab label users see. The qualifier `.payments` is English (matches `category` semantics). Alternative `patient.detail.administration.payments` is equally valid — **chosen `administracion` to mirror the URL `adminMode` value chain and the i18n key namespace `patientDetail.tabs.administracion` used today**.

Ctx contract:
```ts
{ patient: PatientExtended | null, patientId: string }
```

## File map (exhaustive)

### `patients` module (host) — 2 edits

#### 1. `backend/app/modules/patients/frontend/components/patient/AdministrationModeToggle.vue`
- Extend `AdministrationMode` union: `'budgets' | 'billing' | 'payments' | 'documents'`.
- Convert `options` from a static computed list to one filtered by **slot availability**. Use `useModuleSlots().resolve('patient.detail.administracion.payments', { patient: null, patientId: '' })`. If `.length === 0` → omit the `payments` option. Permission gating happens inside `resolve` (slot entry's `permission: 'payments.record.read'`).
- Accept a new prop `patientId?: string` (or refactor to pass ctx). **Decision**: keep toggle stateless — it doesn't need the patientId, just the *availability*. Slot resolution is global, not per-patient. Pass an empty-ctx probe.
- i18n key: `patientDetail.tabs.payments` (add to `frontend/app/i18n/locales/{en,es}.json`).

#### 2. `backend/app/modules/patients/frontend/components/patient/AdministrationTab.vue`
- Extend validation list at line 79: `['budgets', 'billing', 'payments', 'documents']`.
- Add the new render branch between `billing` and `documents`:
  ```vue
  <div v-else-if="currentMode === 'payments'">
    <ModuleSlot
      name="patient.detail.administracion.payments"
      :ctx="{ patient: patientExtended, patientId }"
    />
  </div>
  ```
- **Problem**: `AdministrationTab` today only receives `patientId`, not the full `Patient` object. Two options:
  - **A. Accept it as a new prop** (recommended) — parent `[id].vue` already has `patient` loaded; pass it down. Minimal change. Ctx becomes `{ patient, patientId }`.
  - **B. Pass only `patientId`** in ctx and let the panel re-fetch — wasteful, adds a hop, and the panel already calls `fetchPatientLedger`.
  - Choose **A**.
- **URL fallback**: when `adminMode=payments` is in URL but the option is absent (no slot providers / permission denied), the initial `onMounted` reads queryMode, validates against the list, and falls back to `'budgets'` if invalid. The list check at line 79 must also re-validate against actual toggle availability. Cleanest: compute `availableModes` once, include `'payments'` only if `resolveSlot(...).length > 0`, then both the toggle and the initialiser use the same source.

#### 3. `backend/app/modules/patients/frontend/pages/patients/[id].vue`
- Pass `patient` (the already-loaded `PatientExtended`) down to `<AdministrationTab :patient :patient-id="patientId" />`. Trivial wire-through.

#### 4. `backend/app/modules/patients/CHANGELOG.md`
Add to `## Unreleased`:
```
### Added
- Slot `patient.detail.administracion.payments` (ctx: `{ patient, patientId }`) — extension point for a per-patient ledger view inside the Administración tab.
```

### `payments` module (provider) — 2 new files + 2 edits

#### 5. `backend/app/modules/payments/frontend/components/PatientPaymentsPanel.vue` (NEW)
The actual panel. Receives `ctx = { patient, patientId }` via `defineProps<{ ctx: PatientPaymentsCtx }>()`. Layout per design spec:

```
<EntityCriticalBanner v-if="debt || credit" … />   // warning OR info, single line
<grid lg:cols-3>
  <EntityTotalsCard :lines="[ totalPagado, adeudadoClinica, aCuenta ]" class="lg:col-span-2" />
  <UCard>  <!-- sidebar -->
    sidebar lines (a cuenta, crédito, último pago)
    + sticky <UButton @click="openCobrar">Registrar pago</UButton>
  </UCard>
</grid>

<UCard>
  <SectionHeader>Movimientos</SectionHeader>
  <USkeleton v-if="isLoading" />
  <EmptyState v-else-if="!ledger?.timeline?.length" … />
  <ul v-else>
    <li v-for="entry in timeline" :key="entry.reference_id">
      <icon by entry_type />
      <type label + amount tabular-nums>
      <fecha + description muted>
      <UDropdownMenu v-if="entry.entry_type === 'payment' && (canRefund || canRead)">
        Ver detalle / Reembolsar (gated by payments.record.refund)
      </UDropdownMenu>
    </li>
  </ul>
</UCard>

<PaymentCreateModal v-model:open="showCobrar" :default-patient-id="patientId" @created="refresh" />
<RefundConfirmModal v-model:open="showRefund" :payment-id="refundTarget" @refunded="refresh" />
```

State (composition API):
```ts
const { fetchPatientLedger, refund } = usePayments()
const { can } = usePermissions()
const { format: formatCurrency } = useCurrency()
const ledger = ref<PatientLedger | null>(null)
const isLoading = ref(false)
const showCobrar = ref(false)
const showRefund = ref(false)
const refundTarget = ref<{ id: string, amount: number, method: PaymentMethod } | null>(null)

async function refresh() {
  if (!props.ctx.patientId) return
  isLoading.value = true
  try { ledger.value = await fetchPatientLedger(props.ctx.patientId) }
  finally { isLoading.value = false }
}
onMounted(refresh)
watch(() => props.ctx.patientId, refresh)
```

Computed:
- `debt = ledger?.clinic_receivable ?? 0`
- `credit = ledger?.patient_credit ?? 0`
- `banner` → one of three roles (`warning` / `info` / null)
- `timeline` → `ledger?.timeline.slice().reverse()` (endpoint returns chronological asc; UI shows newest first)
- `canCollect = can('payments.record.write')`
- `canRefund = can('payments.record.refund')`

Refund flow:
- Click "Reembolsar" in row overflow → set `refundTarget = { id: entry.reference_id, amount: entry.amount, method: 'cash' }` → open `RefundConfirmModal`.
- Modal confirms, posts `refund(targetId, { amount, method, reason_code, reason_note })` via `usePayments`.
- On success → `refresh()` (re-fetch ledger, KPIs and timeline auto-update).
- On error → inline error in modal; modal stays open.

Responsive:
- Mobile (`<768 px`): grid collapses to single column; `Registrar pago` becomes sticky bottom bar (Tailwind: `lg:hidden fixed bottom-0 left-0 right-0 p-3 bg-default border-t z-10`). Sidebar card hides at `<lg`.
- Tablet (`md`–`lg`): KPIs 3-col, sidebar full-width under KPIs.
- Desktop (`lg+`): KPIs span 2 cols, sidebar 1 col.

i18n: All strings under `payments.patientPanel.*` namespace (`title`, `kpis.totalPaid`, `kpis.debt`, `kpis.onAccount`, `sidebar.credit`, `sidebar.lastPayment`, `banner.debt`, `banner.credit`, `cobrar`, `timeline.title`, `timeline.empty`, `timeline.types.payment|refund|earned`, `row.menu.detail`, `row.menu.refund`). Both `en` and `es` locale files (per `user_manual_bilingual` policy — but this is i18n strings, not user-manual docs).

#### 6. `backend/app/modules/payments/frontend/components/RefundConfirmModal.vue` (NEW)
Wraps `UModal` with a small form:
- `amount` (number, prefilled with payment amount, editable to allow partial)
- `method` (select from `PaymentMethod` — default to payment's original method)
- `reason_code` (select — values from existing `RefundReason` type)
- `reason_note` (text, optional)
- "Confirmar reembolso" primary button (danger color)
- "Cancelar" ghost

Posts via `usePayments().refund(paymentId, payload)`. Emits `refunded` on success.

**Decision**: separate modal (not inline `confirm()`) because refund needs method + reason fields; a confirm dialog isn't enough.

#### 7. `backend/app/modules/payments/frontend/plugins/slots.client.ts`
Append a third registration:
```ts
registerSlot('patient.detail.administracion.payments', {
  id: 'payments.patient.detail.administracion.panel',
  component: defineAsyncComponent(
    () => import('../components/PatientPaymentsPanel.vue')
  ),
  permission: 'payments.record.read',
  order: 10
})
```

#### 8. `backend/app/modules/payments/CHANGELOG.md`
Add to `## Unreleased`:
```
### Added
- `PatientPaymentsPanel` registered to slot `patient.detail.administracion.payments`. Surfaces patient ledger (balance + timeline) inside the patient-detail "Administración" tab.
- `RefundConfirmModal` — small form (amount, method, reason_code, reason_note) used from the ledger timeline overflow menu.
```

#### 9. `backend/app/modules/payments/CLAUDE.md`
Update "Frontend slots consumed" table with the new entry.

### Documentation — 3 files

#### 10. `docs/technical/payments/overview.md`
Document the slot consumption in the existing overview (or create if absent — check before editing).

#### 11. `docs/user-manual/{en,es}/patients/screens/patient-detail.md`
Bump `last_verified_commit`. Add a section "Pagos sub-mode" under Administración tab. Screenshot pending (deferred until UI runs locally — note in PR).

#### 12. i18n — `frontend/app/i18n/locales/{en,es}.json`
Add `patientDetail.tabs.payments` + entire `payments.patientPanel.*` tree. Spanish strings per design spec wording ("Adeuda **{amount}**", "Tiene **{amount}** a su favor", etc.).

## Module-isolation receipts

- `patients/manifest.depends` stays `[]`. Slot consumption is inverted — `patients` exposes the name, `payments` self-registers. No cross-module FE import from `patients` to `payments` code.
- `payments/manifest.depends` already `["patients", "budget"]`. No change.
- `PatientPaymentsPanel` uses only `usePayments` (own module), `usePermissions` (core), `useCurrency` (core), `useI18n` (core), shared `Entity*` components (core). It never imports from `~~/.../patients/...`.
- Ctx shape `{ patient, patientId }` is a contract — `patient` is optional / nullable, never required for core function (the panel re-fetches its own ledger by `patientId`).

## Non-functional

- **Loading**: skeleton rows for KPIs and timeline. Match `BudgetPaymentsCard` skeleton pattern.
- **Errors**: `fetchPatientLedger` already swallows errors and returns `null` (`usePayments.ts:111`). Panel shows an inline error card + retry button when `ledger === null` after load. Don't crash the tab.
- **Empty timeline**: `EmptyState` shared component with primary CTA "Registrar primer pago" (gated by `payments.record.write`).
- **A11y**: timeline row is a `<li>` with semantic role; `UDropdownMenu` ships ARIA. Sticky CTA on mobile must not overlap content — add `pb-20 lg:pb-0` to outer container.
- **Performance**: ledger response is small (one row per movement, typical patient < 100). No pagination needed v1. If we hit very-long-history clinics, add `?limit=50` to endpoint later — out of scope.
- **Currency**: use `useCurrency().format` (already snapshot-aware per ADR 0010). `ledger.currency` is the source of truth from backend.

## Verification

End-to-end:

```bash
docker-compose up -d
./scripts/reset-db.sh && ./scripts/seed-demo.sh
docker-compose exec backend python -m pytest backend/app/modules/payments -v
cd frontend && npm run lint
```

Manual:

1. Login `admin@demo.clinic / demo1234`, open a patient with payment history (use one returned by `GET /api/v1/payments?patient_id=…` already).
2. Ficha → tab Administración → click "Pagos". URL: `?tab=administration&adminMode=payments`.
3. Hit `GET /api/v1/payments/patients/{id}/ledger` directly (Network panel) — KPIs in the UI must match `total_paid`, `clinic_receivable`, `on_account_balance`. Banner shows if `clinic_receivable > 0` or `patient_credit > 0`.
4. Click "Registrar pago" → modal opens with `patient_id` pre-filled, default allocation `on_account`. Submit a small payment → modal closes, KPIs + timeline refresh.
5. Click overflow `(...)` on a payment row → "Reembolsar" → modal pre-fills amount + method → submit → refund appears in timeline, `total_paid` decreases.
6. Verify URL fallback: in DevTools, navigate to `?adminMode=payments` without permission (use a non-admin user with no `payments.record.read`) → toggle has no "Pagos" pill, default `budgets` is selected.
7. Mobile (Chrome devtools 375 px): banner + KPIs stack, sticky bottom CTA visible, overflow menu tappable, no horizontal scroll.
8. Type-check passes: `cd frontend && npm run typecheck` (if script exists, else `npx vue-tsc --noEmit`).
9. Tests: existing payments tests must stay green; no new backend tests required (no backend changes).

## Out of scope

- Frontend tests for the new panel — defer; codebase doesn't have a Vue test suite wired today (verified).
- Pagination of the ledger timeline.
- Filtering by date range / method inside the panel.
- Bulk refund operations.
- Exporting the timeline to PDF/CSV.

## Risk register

| Risk | Likelihood | Mitigation |
|---|---|---|
| `AdministrationTab` consumer pages break when `patient` prop is added required | low | Make `patient?: PatientExtended \| null` optional with `null` default; only `[id].vue` calls it today |
| Slot resolution at `<ModuleSlot>` returns 0 entries but toggle still shows "Pagos" pill (race / HMR) | low | Toggle computes availability from `useModuleSlots().resolve` reactively; same `useState` source, no race |
| `i18n` keys missing in `en` | medium | Add both locales in same commit; lint will catch |
| Currency mismatch when patient has historical payments in different currencies | very low | Out of scope — payments snapshot currency per record, `ledger.currency` returns clinic-current. Document the edge case in PR description |
| Refund double-submit | low | `isSubmitting` flag in `RefundConfirmModal` disables button until response |

## Estimated diff size

- 2 new components (~250 + ~120 LoC)
- 2 small edits (~30 LoC total in `AdministrationTab.vue` + `AdministrationModeToggle.vue`)
- 1 trivial wire-through in `[id].vue` (~3 LoC)
- 1 plugin registration (~10 LoC)
- i18n keys (~20 lines × 2 locales)
- CHANGELOGs + CLAUDE.md (~15 lines)
- 1 user-manual section bump (~30 lines × 2 locales)

Total: ~600 LoC net, ~80% in the new panel component.

No tech debt introduced. No CLAUDE.md "When adding X" trigger fires that we haven't satisfied above.
