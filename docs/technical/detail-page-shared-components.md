# Detail-page shared components

Cross-cutting reference for the reusable building blocks that render
"detail" pages (budget, invoice, future rectificativas/recibos/etc.)
under a single visual language.

Status: **active** — any new detail page MUST consume these instead of
re-inventing headers, chips or totals cards.

Related: [ADR 0011 — Detail-page shared components](../adr/0011-detail-page-shared-components.md).

---

## Why

Before the extraction, budget detail and invoice detail had grown two
independent implementations of the same UI patterns: page header with
status chips, action bar with overflow menu, totals card, sidebar
metadata card. They drifted in behaviour (mobile wrapping, chip
colours, action priority) and in code (duplicated colour maps,
inline `getStatusBadgeColor()` helpers, hardcoded action lists).

Centralising them removes the duplication, makes the clinic UI feel
coherent across documents, and gives compliance modules (Verifactu,
factur-x, …) a stable contract to inject chips/banners without
touching billing/budget code.

---

## Components

All live under `frontend/app/components/shared/` and resolve to global
component names (`<DetailPageHeader/>`, `<EntityStatusChips/>`, …) via
Nuxt auto-imports.

### `DetailPageHeader`

Page header with title, optional version pill, status slot, subtitle
slot, and actions slot. Mobile-first: title row uses `flex-wrap`,
actions break to a new line below `sm`.

```vue
<DetailPageHeader
  :title="invoice.invoice_number"
  :version="invoice.version"
  :back-to="{ to: '/invoices', label: t('common.back') }"
  :loading="isLoading"
>
  <template #status>
    <EntityStatusChips :chips="statusChips" />
  </template>
  <template #subtitle>
    <NuxtLink :to="`/patients/${patient.id}`">{{ patient.full_name }}</NuxtLink>
  </template>
  <template #actions>
    <EntityActionBar :primary="primaryActions" :overflow="overflowActions" />
  </template>
</DetailPageHeader>
```

Props:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `title` | `string` | required | Document number or main heading. |
| `version` | `string \| number` | — | Rendered as `vN` next to the title. Omitted when empty. |
| `subtitle` | `string` | — | Plain-text fallback when `#subtitle` slot isn't used. |
| `backTo` | `{ to, label }` | — | Renders a back button when set. |
| `loading` | `boolean` | `false` | Skeleton placeholder for the whole header. |

Slots: `#status`, `#subtitle`, `#actions`.

### `EntityStatusChips`

Wrap-friendly group of `StatusBadge` chips. Each chip declares a
semantic role (`success` / `warning` / `danger` / …), label and
optional click handler. Clickable chips become focusable buttons with
a ≥44px touch target on mobile.

```ts
const statusChips = computed<EntityChip[]>(() => [
  { key: 'state', role: 'info', label: t('invoice.status.issued') },
  isOverdue.value && {
    key: 'overdue',
    role: 'warning',
    label: t('invoice.overdueDays', { n: daysOverdue.value })
  },
  hasAeatRejection.value && {
    key: 'verifactu',
    role: 'danger',
    label: t('verifactu.badge.rejected'),
    trailingIcon: 'i-lucide-external-link',
    ariaLabel: t('verifactu.badge.rejectedAria'),
    onClick: openVerifactuModal
  }
].filter(Boolean) as EntityChip[])
```

### `EntityActionBar`

Declarative action bar with adaptive primary/overflow split:

- `<sm`: 1 primary action visible, rest collapse into `⋯`.
- `sm–lg`: 2 primary actions visible.
- `≥lg`: 3 primary actions visible.

Destructive items render with `color: 'error'` in the overflow menu
and are placed in a separate group under a divider.

```ts
const primaryActions: EntityAction[] = [
  { key: 'recordPayment', label: t('invoice.actions.recordPayment'),
    icon: 'i-lucide-wallet', onClick: openPaymentModal },
  { key: 'sendEmail', label: t('invoice.actions.sendEmail'),
    icon: 'i-lucide-mail', variant: 'soft', onClick: openSendModal }
]
const overflowActions: EntityAction[] = [
  { key: 'downloadPdf', label: t('invoice.actions.downloadPdf'),
    icon: 'i-lucide-download', onClick: downloadPdf },
  { key: 'void', label: t('invoice.actions.void'),
    icon: 'i-lucide-x-octagon', destructive: true, onClick: confirmVoid }
]
```

### `EntityTotalsCard`

Declarative totals: each line carries a label, value, optional sign
(`+` / `-`), optional semantic role (e.g. pending balance highlighted
`warning`), and optional divider. The line marked
`emphasis: 'strong'` becomes the large bold total.

```ts
const totalsLines: TotalLine[] = [
  { key: 'subtotal', label: t('invoice.totals.subtotal'), value: invoice.subtotal },
  { key: 'discount', label: t('invoice.totals.discount'),
    value: invoice.discount, sign: '-' },
  { key: 'tax', label: t('invoice.totals.tax'), value: invoice.tax },
  { key: 'total', label: t('invoice.totals.total'),
    value: invoice.total, emphasis: 'strong', divider: 'above' },
  { key: 'paid', label: t('invoice.totals.paid'), value: invoice.total_paid },
  { key: 'pending', label: t('invoice.totals.pending'),
    value: invoice.balance_due,
    role: invoice.balance_due > 0 ? 'warning' : undefined }
]
```

Values pass through `useCurrency().format()` — no callsite should
pre-format the number.

### `EntityInfoCard`

Sidebar metadata card. Each item is a `{ label, value }` pair, with
optional `link` (renders as `<NuxtLink>`) and optional `copyable`
(adds a clipboard button).

### `EntityCriticalBanner`

Full-width banner for critical state (rejected AEAT submission,
severely overdue, blocking validation error). Renders with
`role="alert"`, optional CTA button and optional dismiss.

```vue
<EntityCriticalBanner
  v-if="aeatRejected"
  role="danger"
  :title="t('invoice.criticalBanner.aeatRejected.title')"
  :description="aeatRejectionReason"
  :cta="{
    label: t('invoice.criticalBanner.aeatRejected.cta'),
    icon: 'i-lucide-pencil',
    onClick: openVerifactuModal
  }"
/>
```

---

## `useEntityStatus` composable

Single helper that turns a status string + role map + i18n prefix into
reactive `{ role, label, uiColor }` refs.

```ts
import { INVOICE_STATUS_ROLE } from '~/config/severity'

const { role, label, uiColor } = useEntityStatus(
  computed(() => invoice.value?.status),
  INVOICE_STATUS_ROLE,
  'invoice.status'
)
```

The role maps live in `frontend/app/config/severity.ts`. **Never
inline a status→color map in a component.**

---

## Rules

1. **Every detail page uses `DetailPageHeader`**. No new ad-hoc
   `<h1>` + chip layouts inside `pages/`.
2. **Status colours come from `severity.ts`**. Add new entity maps
   there; never duplicate.
3. **Status labels go through `useEntityStatus`** (or `t()` keyed by
   the same prefix). No hardcoded strings.
4. **Action overflow is mandatory** when an entity has more than 3
   actions. Hide secondary actions behind `⋯`; do not stretch the
   header.
5. **Critical banners are reserved for blocking state**. Use them
   only when the user must act (rejected AEAT, blocking validation,
   etc.) — not for soft warnings.
6. **Permissions filter actions before passing to `EntityActionBar`**.
   Do not pass an action and rely on `disabled` — if the user lacks
   the permission, the action should not appear at all.

---

## Migrating a detail page

1. Build `statusChips`, `primaryActions`, `overflowActions`, and
   `totalsLines` as `computed` from your existing data.
2. Replace the header block with `<DetailPageHeader>` and slot the
   chips + actions.
3. Replace your local totals card with `<EntityTotalsCard>`.
4. Replace your local metadata card with `<EntityInfoCard>`.
5. Delete the local status-colour map and the inline
   `getXxxBadgeColor()` helpers.
6. Sanity-check at 360px, 768px and 1024px — the chips must wrap,
   and the action bar must collapse correctly.

---

## How to verify the rule still holds

- CI grep (proposed): no `getXxxBadgeColor` symbol under
  `backend/app/modules/*/frontend/`.
- CI grep (proposed): no `<h1[^>]*>[^<]*<UBadge` patterns in detail
  pages under `pages/`.
- Manual: every new detail page PR review checks that
  `DetailPageHeader` is used.
