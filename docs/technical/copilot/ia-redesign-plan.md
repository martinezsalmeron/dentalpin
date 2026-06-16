# IA (Copilot) — UX redesign & phased technical plan

Status: **proposal / not started**. Owner: Ramon. Last updated: 2026-06-08.

This is the technical plan that follows the design exploration for the copilot redesign,
rebranded in the UI as **"IA"**. It supersedes nothing in
[`copilot-agentic-architecture.md`](../copilot-agentic-architecture.md) — that doc remains the
source of truth for the reactive agent engine. This plan layers a **proactive** surface on top
and polishes the reactive one.

## 1. Goal

Make the IA the headline feature of DentalPin. Today it is a competent reactive chat in a
480px drawer. The target is a workspace that (a) answers and acts on request, and (b)
**proactively surfaces the operations that save the most clinic time/money** — slot
reassignment, budget follow-ups, recalls, cash mismatches — and lets the user approve agent
work in one click.

Priority order is driven by real time saved (frequency × manual minutes × % the agent closes
on its own), not visual appeal.

## 2. Information architecture (the simple frame)

Two zones, one card grammar. No third destination, no full-page drill-downs.

```
IA workspace  ─ single column, top segmented control ─
├── Pendientes (proactive, home)   default landing; badge = items needing attention
│     · one expandable card per decision: "this happened → I recommend → [approve]"
│     · "Hecho" filter = audit/activity (reads patient_timeline + operation log)
└── Chat (reactive)                ask / dictate / one-shot tasks; rich result cards
```

**Design invariants** (carry into implementation):

1. **One expandable card** models every proactive item (slots, budgets, recalls, cash, clinical
   notes). Learn one, read them all. Detail is progressive disclosure (inline accordion), never a
   new screen.
2. **Surface the recommended action only.** Ranking, parallel patient threads, drafts live one
   level down behind "Ver detalle".
3. **Close the loop.** Every write ends in a visible final state (cita movida, mensaje enviado);
   resolved items move to "Hecho".
4. **Confirmation proportional to risk.** Read/draft = zero friction. Reversible write
   (book a slot) = one click. Irreversible fiscal (Verifactu invoice, amount edits) = typed
   confirmation + red banner.
5. **Draft before silent write** for everything clinical and fiscal. Agent proposes, human
   validates the irreversible.
6. **Negotiation = thread, not card.** Back-and-forth with patients renders as a real thread,
   folded inside the operation.

The full mockups (hero, Pendientes feed, the polished expanded slot-reassignment card and its
states, budget queue, voice clinical note, risk-scaled confirmations, audit) live in the design
conversation; reproduce them in Figma before building Fase 2+.

## 3. What exists vs what we build (architecture audit summary)

| Capability | Verdict | Path / note |
|---|---|---|
| Background scheduler (APScheduler, cron) | EXISTS | `app/core/scheduler.py` — add jobs like `expire_budgets` |
| Event triggers (`appointment.cancelled`, `budget.*`, `recall.*`, `payment.*`) | EXISTS | `app/core/events/types.py` |
| Status models to scan (budget, recalls, treatment_plan) | EXISTS | `recalls` is already a module; budget `status`, recall `status` |
| Agent engine `run_turn` decoupled from HTTP/SSE | EXISTS (partial) | `app/core/agents/orchestrator.py` — reusable from a job; WRITE tools gate to confirmation |
| Audit / activity log | EXISTS | `patient_timeline` (append-only, dedup by `(event_type, source_id)`) |
| Outbound email + preferences + logs | EXISTS | `app/modules/notifications/` (`EmailLog`, `NotificationPreference`) |
| Tool result contract for rich cards | EXISTS | appointment/slot/report/timeline complete; patient = minimal |
| **Operation / candidate / inbox persistence** | DOES NOT EXIST | build in copilot module |
| **2-way patient messaging (SMS/WhatsApp + inbound webhook)** | DOES NOT EXIST | build; external provider + GDPR consent |
| **Background autonomous orchestration mode** | PARTIAL | wrap `run_turn` with read-only autonomous `AgentContext` |

Net: the expensive backend primitives (scheduler, events, status models, recalls, agent engine,
audit, email) already exist. The genuinely new builds are the **operations store + inbox** and
**two-way patient messaging**.

## 4. Phasing

Front-loaded value, monotonically increasing risk and external dependency. Every phase ships on
its own.

### Fase 0 — Rebrand + Chat base (frontend only, existing infra)

Zero backend. Immediate "world class" lift on the reactive surface.

- Rename Copilot → **IA** across i18n (`copilot.*` keys: title, nav, page.title, FAB aria-label).
  Keep the sparkles icon; introduce a dedicated accent (subtle gradient) so IA reads as AI.
- Markdown rendering in assistant messages (today `whitespace-pre-wrap` drops formatting).
- Empty state with **permission-filtered** suggestion chips (categories: Pacientes / Agenda /
  Informes), click → fills + sends.
- Live phase indicator derived from existing `tool_call` events ("Buscando en pacientes…" instead
  of static "Pensando…").
- Trust line under the composer ("🛡 Datos protegidos · Claude").

Checklist: update screen MD in `docs/user-manual/{en,es}/copilot/`, bump `last_verified_commit`,
module CHANGELOG.

### Fase 1 — Rich result cards (frontend, existing tool contract)

Map `tool_result.name` → typed Vue card components. No backend (contract already sufficient).

- `AppointmentCard` (complete: patient_name, start/end, status badge, cabinet, professional).
- `SlotCard` (free slots list from `find_free_slots`).
- `ReportCard` (payments/billing/scheduling aggregates as stats + method bars).
- `PatientResultCard` (minimal: name, contact, status, [Ver ficha] [Agendar]) — enrich later.
- Timeline list from `get_patient_timeline`.
- Collapsible tool-call accordion (running → done, with result summary on expand).
- **Humanized confirmation cards**: replace `JSON.stringify` with labeled rows; resolve
  `patient_id` → name via a session-scoped name cache (ids seen in prior `search_patients`). No
  backend call needed in the common case.
- Message actions on hover: copy, regenerate (assistant), edit+resend (user).

Optional follow-up (small contract change, deferred): enrich `search_patients` with age / last
visit / next appointment to upgrade `PatientResultCard`. Touches `patients/tools.py` →
re-run `generate_catalogs.py`, update module CLAUDE.md "Tools exposed".

### Fase 2 — Workspace shell + read-only Pendientes (frontend + light backend reads) — SHIPPED (partial)

> **Status (2026-06-15):** the segmented `[Pendientes | Chat]` shell and a
> read-only Pendientes feed shipped — overdue recalls + budgets awaiting
> response, each deep-linking to its module. Aggregation goes through the
> tool registry per **ADR 0015** (`GET /pending`, `PendingService`,
> `CopilotPending.vue`). Still deferred: cash-mismatch source (no tool
> yet) and the "Hecho" filter over `patient_timeline`.

Prove the inbox UX cheaply, before any new write infra.

- Two-zone shell: `[Pendientes | Chat]` segmented control, single column, no left rail. Drawer
  realigns to the same language later (Fase 5).
- Chat tab = Fase 0–1.
- Pendientes feed reads **existing signals read-only**, no agent messaging yet:
  - unaccepted budgets (`budget.status='sent'` + age + no accept/reject event),
  - recalls due (`recalls` where `status IN (pending, contacted_no_answer)` and `due_month<=today`),
  - cash mismatch (payments reconciliation signal, if available).
  Each card is informational + deep-links to the owning module screen. The expandable card shell
  is built here but actions are "go to module", not "agent acts".
- "Hecho" filter reads `patient_timeline`.

Backend: thin read endpoints in copilot that aggregate these queries (respecting `clinic_id` and
permissions; cross-module reads only via declared `depends` or the modules' own read services /
tools). No new tables.

Architecture decision (ADR): **resolved in [ADR 0015](../../adr/0015-copilot-pending-aggregation.md)** —
the aggregator calls the modules' agent **tools** through the registry with the caller's role
(RBAC parity, `depends = []` preserved), not direct service imports or an event projection.

### Fase 3 — Operations engine (new backend: persistence + scan + ranking/drafts)

The proactive core. Still no outbound send — drafts await human approval.

- New copilot models: `CopilotOperation` (type, status state-machine, target refs, clinic_id),
  `CopilotOperationCandidate` (ranked, reason, contact/thread state), draft message storage.
  - **Isolation decision (ADR):** operations reference `budget_id` / `recall_id` /
    `appointment_id` / `patient_id`. Either add those modules to copilot `manifest.depends` and use
    FKs, or store loose UUIDs + JSONB snapshots to preserve uninstall safety. Recommend loose UUIDs
    + denormalized snapshot (operations are a derived/cache surface) — keeps copilot removable.
- Background scan task (APScheduler, `scan_proactive_operations`, following `expire_budgets`):
  detect freed slots (from `appointment.cancelled`), unaccepted budgets, due recalls, cash
  mismatch → upsert idempotent operations (dedup by `(type, source_id)` like patient_timeline).
- **Background autonomous orchestration**: wrap `run_turn` in a read-only `AgentContext`
  (`mode=AUTONOMOUS`, READ tools only) to (a) rank candidates and (b) **draft** patient messages.
  Drafting stages content; it does not call WRITE tools, so the existing confirmation gate is not
  bypassed. The actual book/send happens on human approval through the existing inline
  confirmation pattern.
- Operations API: list / get / action (approve, edit-draft, snooze, dismiss). Reuse the SSE
  confirmation flow for the approve→execute step.
- Pendientes feed now reads real operations; the polished expanded card renders candidates +
  drafts + per-candidate state. "Send" is stubbed to email (Fase 4 adds real 2-way).

New events: `copilot.operation.created/updated/resolved` in `EventType`; rows in
`docs/technical/copilot/events.md`; re-run `generate_catalogs.py`. New permissions
(`operations.read` / `operations.act`) through the full RBAC path.

### Fase 4 — Two-way patient messaging (new backend, external dependency, GDPR)

Closes the operation loop end-to-end. Largest external/compliance lift.

- Outbound: extend `notifications` with an SMS/WhatsApp provider (Twilio / WhatsApp Business
  Platform) behind the existing provider-agnostic `NotificationService`. Add SMS/WA templates
  alongside `EmailTemplate`. Reuse `NotificationPreference` for opt-in/locale.
- Inbound webhook receiver: accept patient replies, attach to the operation's candidate thread,
  run a lightweight intent detection (yes/no/other) to update candidate state.
- Consent / GDPR: explicit messaging opt-in, audit every outbound in `EmailLog`-equivalent,
  retention policy. ADR + legal review.
- The slot-reassignment operation now runs fully: agent contacts ranked candidates → patient
  replies → agent detects "sí" → human confirms → appointment booked + others auto-notified the
  slot is taken (the loop shown in mockup C/E).

This is the riskiest phase (external provider cost, deliverability, consent). Keep it isolated so
Fase 0–3 ship value without it.

### Fase 5 — Voice clinical note (#3) + polish

- Voice input in Chat (Web Speech API first; backend STT if accuracy demands).
- Clinical note structuring → **editable draft** → on approval, write to odontogram / perio /
  treatment plan (cross-module writes only via declared `depends` + each module's tools/services;
  never silent). Note also surfaces as a Pendientes "validar nota" card.
- Mature the "Actividad" tab (who validated, when, link to affected record).
- Micro-animations, dark-mode pass, budget meter when near limit, drawer realignment + "expand to
  page".

## 5. Risk & sequencing notes

- **Ship order = value/risk order.** Fase 0–1 are pure-frontend, near-zero risk, and already make
  IA feel premium. Do them first regardless of the proactive roadmap.
- **Fase 2 de-risks the inbox UX** with existing data before committing to the operations store.
- **Fase 4 is the gate** for the headline "agent reschedules for you" demo, but it carries the
  external/compliance weight — do not let it block earlier phases.
- **Autonomous mode stays read-only.** The agent ranks and drafts; humans approve every write.
  This keeps the blast radius small and matches the "draft before silent write" invariant.

## 6. Open decisions (need sign-off before Fase 3)

1. Operations isolation: loose UUIDs + snapshot (recommended, keeps copilot removable) vs FKs +
   expanded `manifest.depends`. → ADR.
2. Pendientes aggregation mechanism: reuse module agent tools vs read services vs events. → ADR.
3. Messaging provider + consent model (Fase 4). → ADR + legal.
4. Patient card enrichment: ship minimal (Fase 1) and enrich `search_patients` later, or enrich
   up front.

## 7. Checklist obligations per phase (from root CLAUDE.md)

- Any touched module → its `CHANGELOG.md` under `## Unreleased`.
- New screen (Pendientes, expanded operation) → `docs/user-manual/{en,es}/copilot/screens/*` both
  locales + screenshots, frontmatter contract, `last_verified_commit`.
- New endpoint → document under gating permission in `docs/technical/copilot/permissions.md`.
- New event → `EventType` + `docs/technical/copilot/events.md` + `generate_catalogs.py`.
- New permission → role mapping → `get_permissions()` → `require_permission()` →
  `frontend/app/config/permissions.ts`.
- New agent tool → `tools.py` wrapping an existing service, `clinic_id`-filtered, documented in
  module CLAUDE.md.
- Architectural decisions (operations isolation, aggregation, messaging) → `docs/adr/NNNN-*.md`.
