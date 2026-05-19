# Agenda — quick patient creation (technical plan)

> Status: **planned**. Companion to the design spec
> [`docs/features/agenda-quick-patient-create.md`](../features/agenda-quick-patient-create.md).
> Plan last updated: 2026-05-19.

Implementation plan for the inline "create patient" UX inside the New Appointment modal. Backend stays untouched; all work is frontend.

---

## Architectural decisions

### A. `VisualSelector` stays generic; create UX lives in `PatientVisualSelector`

`VisualSelector` (`frontend/app/components/shared/VisualSelector.vue`) is a reusable, item-agnostic grid picker used by `PatientVisualSelector`, `TreatmentVisualSelector`, etc. We will **not** add patient-specific concepts to it.

What we add to `VisualSelector`:

1. A new optional `#footer` slot rendered **inside the dropdown panel, below the grid**, with slot props `{ query, hasResults, isSearching }` so the consumer can render whatever footer action it wants (typically a "+ Create" row).
2. A new emit `'footer-enter': [query: string]` fired when the user presses **Enter** while either
   - `displayItems.length === 0` and `searchQuery.length >= 2`, or
   - no item is highlighted and the footer slot is rendered.

   This is the only keyboard hook the parent needs: today Enter already selects the highlighted item; this new event covers the "no item to select, fire footer action instead" case.

The mini-form does **not** live inside `VisualSelector`. It is a sibling of `<VisualSelector>` in `PatientVisualSelector.vue`, rendered when `mode === 'create'`.

### B. State machine in `PatientVisualSelector`

```
                ┌─────────┐  user selects patient   ┌──────────┐
                │ search  │ ───────────────────────▶│ selected │
   mount  ────▶ │  (idle) │                          └──────────┘
                └────┬────┘
                     │ user clicks "+ Crear" row
                     ▼
                ┌─────────┐  POST success            ┌──────────┐
                │ create  │ ───────────────────────▶│ selected │
                │ (form)  │                          │ (+ badge)│
                └────┬────┘                          └──────────┘
                     │ Cancel / Back
                     ▼
                  search
```

`mode: 'search' | 'create' | 'selected'` is a local ref. `selected` is already implicit today via `selectedPatient`; we keep that branch unchanged.

### C. Mini-form panel — sibling, not nested in dropdown

The dropdown closes on blur after 200 ms (`VisualSelector.vue:91-97`). If the mini-form lived inside the dropdown, clicking the form would race the blur. Instead:

- When the user clicks the "+ Crear" footer row, `PatientVisualSelector` sets `mode = 'create'`. The `<VisualSelector>` element is `v-if="mode === 'search'"`, so it unmounts (closing its dropdown cleanly). The mini-form is a separate `<div v-else-if="mode === 'create'">` block.
- No race with blur, no Teleport gymnastics. Clean DOM, clean state.

### D. Recents cache update — local, no refetch

`GET /api/v1/patients/recent` is fetched once on mount into `recentPatients`. There's no shared cache (`useApi` is uncached). On successful create:

```ts
recentPatients.value = [created, ...recentPatients.value].slice(0, 8)
```

This keeps the recents grid fresh for the rest of the session without an extra request. (Other open selectors in other tabs will see stale recents until next mount — acceptable trade-off; we'll revisit if it becomes a real issue.)

### E. Soft-duplicate phone lookup

Reuse `GET /api/v1/patients?search=<phone>&page_size=5`. The backend already searches `phone` via case-insensitive ILIKE (`backend/app/modules/patients/service.py:130-138`).

- Trigger only when phone input ≥ **6 chars** (avoid hot loop on `+34`).
- Debounce 400 ms (slightly longer than the 300 ms used in `VisualSelector`).
- Abort previous request when a new keystroke arrives — use `AbortController`.
- Show banner only if any result has `phone === input` after both are normalized (strip spaces, dashes).

### F. Permissions gating

```ts
const { can } = usePermissions()
const canCreate = computed(() => can(PERMISSIONS.patients.write))
```

If `canCreate.value === false`, do not render the footer slot. Already-existing receptionists have `patients.write` (`backend/app/modules/patients/__init__.py:35`), so this is mainly a safety net.

---

## Component changes

### 1. `frontend/app/components/shared/VisualSelector.vue`

| Change | Where | Sketch |
|---|---|---|
| New `#footer` slot inside dropdown | After grid block, before closing `</div>` of the panel (line 231) | `<slot name="footer" :query="searchQuery" :has-results="displayItems.length > 0" :is-searching="isSearching" />` |
| New emit | line 13–16 | Add `'footer-enter': [query: string]` to the `defineEmits` generic |
| Keyboard Enter when no highlight | line 117–123 | If `highlightedIndex < 0 && searchQuery.length >= 2`, emit `footer-enter` instead of selecting |
| `mousedown.prevent` on footer | Slot wrapper | Mirror the same `@mousedown.prevent.stop` used on grid items (line 220) so clicking footer doesn't blur the input |

No prop additions. No breaking changes for existing callers — both additions are opt-in.

### 2. `frontend/app/components/shared/PatientVisualSelector.vue`

Net new logic:

- `mode: 'search' | 'create'` ref (the `selected` branch is already implicit).
- `lastQuery` ref — captures the search string at the moment the user clicks "+ Crear", used to pre-fill the mini-form.
- `splitName(query: string): { first: string; last: string }` — first whitespace-delimited token is `first_name`, rest is `last_name`. Trims. If only one token, `last_name = ''` (user must complete before submit).
- `form` reactive: `{ first_name, last_name, phone }`.
- `isSubmitting`, `createError` refs.
- `duplicateMatch: Patient | null` ref + `lookupDuplicate(phone)` with `AbortController`.

Template additions:

```vue
<!-- mode === 'search' branch already shown -->
<VisualSelector ...>
  <template #item>...</template>
  <template
    v-if="canCreate"
    #footer="{ query, hasResults }"
  >
    <button
      class="..."  // primary text, top border, user-plus icon
      @mousedown.prevent.stop
      @click="enterCreateMode(query)"
    >
      <UIcon name="i-lucide-user-plus" />
      {{ t('patientSelector.createOption', { query: query || '' }) }}
    </button>
  </template>
</VisualSelector>

<!-- mode === 'create' branch -->
<div v-else-if="mode === 'create'" class="border rounded-lg p-3 space-y-3">
  <header class="flex items-center justify-between">
    <UButton variant="ghost" icon="i-lucide-arrow-left" @click="cancelCreate">
      {{ t('patientSelector.createForm.back') }}
    </UButton>
    <span class="font-medium">{{ t('patientSelector.createForm.title') }}</span>
  </header>

  <UFormField :label="t('patientSelector.createForm.firstName')" required>
    <UInput v-model="form.first_name" autocapitalize="words" />
  </UFormField>
  <UFormField :label="t('patientSelector.createForm.lastName')" required>
    <UInput v-model="form.last_name" autocapitalize="words" />
  </UFormField>
  <UFormField
    :label="t('patientSelector.createForm.phone')"
    :hint="t('patientSelector.createForm.phoneHint')"
  >
    <UInput v-model="form.phone" inputmode="tel" />
  </UFormField>

  <div v-if="duplicateMatch" class="rounded bg-yellow-50 ...">
    {{ t('patientSelector.duplicateWarning', { name: duplicateName }) }}
    <UButton size="xs" @click="useExisting">
      {{ t('patientSelector.useExisting') }}
    </UButton>
  </div>

  <div v-if="createError" class="text-red-600 text-sm">{{ createError }}</div>

  <div class="flex gap-2 justify-end">
    <UButton variant="ghost" @click="cancelCreate">
      {{ t('patientSelector.createForm.cancel') }}
    </UButton>
    <UButton
      :disabled="!canSubmit"
      :loading="isSubmitting"
      @click="submitCreate"
    >
      {{ t('patientSelector.createForm.submit') }}
    </UButton>
  </div>
</div>
```

`canSubmit` is `form.first_name.trim() && form.last_name.trim() && !isSubmitting`.

`submitCreate` calls `api.post<ApiResponse<Patient>>('/api/v1/patients', payload)`, then `handleSelect(response.data)`, then pushes to `recentPatients` (decision D), then `mode = 'search'`. On error, set `createError` to a translated string and keep the form open.

`enterCreateMode(query)` sets `mode='create'`, `lastQuery=query`, splits the name into `form`, focuses `first_name` after `nextTick`.

### 3. `AppointmentModal.vue` — no changes

The modal already passes `:in-modal="true"` to `PatientVisualSelector` and listens to `@update:model-value`. When the new patient is selected after creation, the existing flow takes over with zero changes.

### 4. Optional "Nuevo" badge

When `mode` returns to `search`/`selected` after a successful create, set `newlyCreatedId.value = created.id` for the lifetime of the component. In the selected-patient card (`PatientVisualSelector.vue:81-104`), render a small `UBadge` next to the name when `selectedPatient.id === newlyCreatedId`. Cleared when the modal unmounts.

---

## API contracts

No backend changes. Reused as-is:

| Method | Path | Used for |
|---|---|---|
| `POST` | `/api/v1/patients` | Create the new patient. Payload: `{ first_name, last_name, phone? }`. Server returns `ApiResponse<Patient>`. |
| `GET` | `/api/v1/patients?search=<phone>&page_size=5` | Soft-duplicate phone lookup. |

`POST /api/v1/patients` requires `patients.write` (already enforced — `backend/app/modules/patients/router.py:84`). It publishes `EventType.PATIENT_CREATED` (`backend/app/modules/patients/service.py:170`); other modules' subscribers will receive it as if the patient had been created from the regular form.

---

## i18n keys

Add to `frontend/i18n/locales/en.json` and `frontend/i18n/locales/es.json` under a new `patientSelector` namespace:

| Key | ES | EN |
|---|---|---|
| `patientSelector.createOption` | `Crear paciente "{query}"` | `Create patient "{query}"` |
| `patientSelector.createForm.title` | `Nuevo paciente` | `New patient` |
| `patientSelector.createForm.firstName` | `Nombre` | `First name` |
| `patientSelector.createForm.lastName` | `Apellidos` | `Last name` |
| `patientSelector.createForm.phone` | `Teléfono` | `Phone` |
| `patientSelector.createForm.phoneHint` | `Lo puedes añadir después en la ficha` | `You can add it later on the patient record` |
| `patientSelector.createForm.submit` | `Crear y seleccionar` | `Create and select` |
| `patientSelector.createForm.cancel` | `Cancelar` | `Cancel` |
| `patientSelector.createForm.back` | `Volver a búsqueda` | `Back to search` |
| `patientSelector.duplicateWarning` | `Ya existe {name} con este teléfono` | `{name} already exists with this phone` |
| `patientSelector.useExisting` | `Usar este paciente` | `Use this patient` |
| `patientSelector.newBadge` | `Nuevo` | `New` |
| `patientSelector.errors.create` | `No se pudo crear el paciente. Reintentar.` | `Couldn't create patient. Retry.` |

---

## Edge cases and race conditions

| Case | Handling |
|---|---|
| User clicks "+ Crear" while dropdown is closing (blur 200 ms) | `@mousedown.prevent.stop` on the footer button prevents input blur. Same pattern as grid items (line 220). |
| User types phone while previous duplicate-lookup is in flight | Use `AbortController`; cancel previous request on each keystroke. |
| User double-clicks `Crear y seleccionar` | Button has `:loading`/`:disabled` bound to `isSubmitting`. |
| Network failure mid-create | `createError` set, form values preserved, button re-enabled. |
| Server returns 4xx (e.g. validation) | Map error message into `createError`. The schema only enforces `min_length=1` on names which the client already prevents; treat any 4xx as user-correctable display. |
| User clicks "Usar este paciente" in the dup banner | `handleSelect(duplicateMatch)`, reset `mode='search'`, mini-form state discarded. |
| User cancels mid-form after typing | `cancelCreate` resets `form`, `mode='search'`, focuses `VisualSelector` input. No confirmation prompt — keeps the flow fast. |
| Modal closes while creating | `AbortController` for the create POST too; on unmount, abort all in-flight requests. |

---

## Tests

### Frontend unit (Vitest, new file)

`frontend/tests/unit/PatientVisualSelector.spec.ts`:

1. Renders `+ Crear "<query>"` only when `can(patients.write)` is true.
2. Clicking the footer row mounts the mini-form pre-filled with `splitName` heuristic.
3. Submitting calls `POST /api/v1/patients` with `{ first_name, last_name, phone? }` and emits `update:modelValue` with the created patient.
4. Newly created patient appears at index 0 of `recentPatients`.
5. Soft-duplicate banner appears when phone lookup returns an exact match; "Usar este paciente" selects the existing patient and discards the form.
6. Enter key on empty results emits `footer-enter` and enters create mode.

Mock `useApi` via `vi.mock`.

### E2E (Playwright, new file)

`frontend/tests/e2e/agenda-quick-patient-create.spec.ts`:

1. Log in as receptionist, navigate to `/appointments`.
2. Click an empty calendar slot; assert `AppointmentModal` is open.
3. Type `"Test Paciente Quickcreate"` in the patient selector input.
4. Click the `+ Crear` row.
5. Fill phone, click `Crear y seleccionar`.
6. Assert the selected-patient card shows the typed name and the `Nuevo` badge.
7. Pick professional, set duration, save the appointment.
8. Reload `/appointments`; assert the new appointment is present.
9. Navigate to `/patients`; assert the new patient is listed.
10. Repeat in viewport `375 × 667`.
11. Negative test: log in as a role without `patients.write` (skip if no such fixture); assert `+ Crear` row is not rendered.

### Backend

No backend changes → no new backend tests. Existing `tests/test_clinics_and_core_flows.py::test_create_patient` already covers `POST /api/v1/patients` (`line 103-122`).

---

## File changes summary

```
frontend/app/components/shared/VisualSelector.vue           # +footer slot, +footer-enter emit, Enter key tweak
frontend/app/components/shared/PatientVisualSelector.vue    # state machine, mini-form, dup lookup, recents cache update
frontend/i18n/locales/en.json                                # +patientSelector.*
frontend/i18n/locales/es.json                                # +patientSelector.*
frontend/tests/unit/PatientVisualSelector.spec.ts            # NEW
frontend/tests/e2e/agenda-quick-patient-create.spec.ts       # NEW
docs/features/agenda-quick-patient-create.md                 # already exists
docs/technical/agenda-quick-patient-create.md                # this file
backend/app/modules/agenda/CHANGELOG.md                      # bump Unreleased — UX touch on agenda's new-appointment modal
backend/app/modules/patients/CHANGELOG.md                    # bump Unreleased — POST /patients now consumed from agenda's new-appointment modal
```

No DB migrations. No new endpoints. No new permissions.

---

## Rollout

1. Land the `VisualSelector` slot/emit additions behind no flag — they are additive.
2. Land `PatientVisualSelector` changes; behind no flag — the new UX is opt-in per consumer (only triggered when `#footer` is rendered, which only `PatientVisualSelector` does).
3. Manual QA on desktop + iPhone SE viewport before merging.
4. Tag the PR with `module:agenda` and `module:patients` for changelog routing.

---

## Verification (post-merge)

`docker-compose up`, login `admin@demo.clinic / demo1234`. Stopwatch in hand:

1. Agenda → click empty slot → input focused.
2. Type a fresh name → see `+ Crear` row.
3. Click → mini-form pre-filled, fix split, add phone → `Crear y seleccionar`.
4. Pick professional, duration → save.
5. **Stopwatch ≤ 30 s.** If > 45 s, the design has drifted; reopen the spec.
