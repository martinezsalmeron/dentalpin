# Glossary

Source of truth for DentalPin terminology. Code is in English; UI strings
are in Spanish (i18n). When the same concept has both forms, list both.

When you introduce a new domain term in code or UI, append it here. Keep
definitions to one or two sentences — link to deeper docs (`docs/`,
ADRs) for the full story.

## Clinical

| EN (code) | ES (UI) | Definition |
|---|---|---|
| Patient | Paciente | A person registered in the clinic. Soft-deleted via `status`, never hard-deleted. |
| Appointment | Cita | A scheduled visit. Has a state machine (`scheduled → confirmed → checked_in → in_treatment → completed`/`no_show`/`cancelled`). |
| Treatment | Tratamiento | A clinical procedure performed on a patient (often tied to a tooth/surface). |
| Treatment plan | Plan de tratamiento | Bundle of proposed treatments with status, used to drive budgets. |
| Odontogram | Odontograma | The per-patient tooth chart. Tracks conditions and treatments per tooth/surface. |
| Tooth | Diente | Identified by FDI numbering (11–48 permanent, 51–85 deciduous). |
| Surface | Cara/superficie | A face of a tooth (mesial/distal/occlusal/lingual/vestibular). |
| Visit note | Nota de visita | Free-text note attached to an `AppointmentTreatment`. |
| Clinical note | Nota clínica | Free-text note in the `clinical_notes` module. Polymorphic over four `note_type` values (administrative, diagnosis, treatment, treatment_plan). |
| Administrative note | Nota administrativa | Receptionist / admin note attached to a patient with no clinical context (e.g. "called complaining of tooth pain", "rescheduled to next week"). |
| Diagnosis note | Nota de diagnóstico | Note taken during a diagnosis session, optionally tied to a specific tooth. |
| Treatment note | Nota de tratamiento | Note attached to a `Treatment` row (odontogram). Travels with the treatment from diagnosis through plan and completion. |
| Patient summary | Ficha resumen | Default landing tab on the patient record. Shows the patient header plus the recent-clinical-notes feed across every type. |
| Hygienist | Higienista | Role with read-only patient access + full appointment access. |
| Dentist | Dentista | Role with full clinical access. |
| Assistant | Asistente | Operative role; full patient + appointment access, no clinical writes. |
| Receptionist | Recepcionista | Front-desk role; patients + appointments. |

## Scheduling

| EN (code) | ES (UI) | Definition |
|---|---|---|
| Cabinet | Gabinete | A clinical room/operatory/chair. Appointments are assigned to a cabinet. |
| Agenda | Agenda | The calendar UI module. Owns `Appointment` entities. |
| Schedules (module) | Horarios | The clinic-hours / opening-hours module (issue #39). **Different from agenda** — agenda must not depend on schedules; data flows the other way via events. |
| Clinic hours | Horario de clínica | Open/closed slots defined in the schedules module. |
| Professional hours | Horario del profesional | Optional per-professional availability override. |

## Billing

| EN (code) | ES (UI) | Definition |
|---|---|---|
| Budget | Presupuesto | A pre-invoice quote sent to the patient. Has its own workflow (`draft → sent → accepted → rejected`). |
| Invoice | Factura | A fiscal document. Spanish clinics must comply with Veri\*Factu (see verifactu module). |
| Credit note | Factura rectificativa | An invoice correction document. |
| Payment | Pago | Money received against an invoice. Can be partial. |
| Catalog | Catálogo | Module that holds priced services and products. |

## Compliance (ES)

| Term | Definition |
|---|---|
| Veri\*Factu | Spanish AEAT mandatory e-invoicing regime (RD 1007/2023). Implemented by the `verifactu` module. |
| AEAT | Agencia Estatal de Administración Tributaria — Spanish tax authority. |
| FNMT | Spanish certificate authority issuing the digital certs used for AEAT mTLS. |
| SIF | Sistema Informático de Facturación — invoicing software. Regulated under RD 1007/2023 art. 13. |
| Producer | "Productor del SIF" — the legally responsible party for compliance. See `backend/app/modules/verifactu/README.md`. |
| Declaración responsable | Producer's signed compliance declaration. Required before enabling Veri\*Factu in `prod`. |
| RegistroAlta / RegistroAnulacion | Veri\*Factu submission entries. |
| Huella | SHA-256 chained hash linking each fiscal record to the previous one. |
| Sociedades | Spanish corporations — Veri\*Factu mandatory from 2027-01-01. |
| Autónomos | Spanish self-employed (IRPF) — Veri\*Factu mandatory from 2027-07-01. |

## Module system

| Term | Definition |
|---|---|
| Module | A self-contained feature under `backend/app/modules/<name>/` plus its co-located frontend layer. See `docs/creating-modules.md`. |
| Manifest | The `manifest` dict on a `BaseModule` subclass. Identity, dependencies, permissions, install policy. Schema in `backend/app/core/plugins/manifest.py`. |
| Entry point | `pyproject.toml` registration under `[project.entry-points."dentalpin.modules"]` so the loader can discover the module. |
| `depends` | Manifest field. List of modules this one needs at load time. Cross-module FKs and direct imports are only allowed against modules listed here. |
| `installable` / `auto_install` / `removable` | Manifest policy flags. `auto_install=False` means the user activates the module from admin UI. |
| `branch_labels` | Alembic per-module migration branch label. Each module owns its branch — never thread one module's revisions through another's chain (issue #56). See ADR 0002. |
| `role_permissions` | Manifest field that grants role → permissions. Permissions in here must also be returned by `get_permissions()` (validated by `manifest_validator.py`). |
| Event bus | In-process pub/sub. See `backend/app/core/events/`. Preferred mechanism for cross-module reactions. See ADR 0003. |
| Event type | A constant in `backend/app/core/events/types.py` `EventType`. Naming convention `entity.action` (e.g. `patient.created`). |
| Tool | An action a module exposes to AI agents via `get_tools()`. Mandatory for write-capable modules. Namespaced as `<module>.<tool_name>`. |
| Agent | A `BaseAgent` subclass a module ships, registered via `get_agents()`. |
| Reference module | A module marked as canonical example others should copy. Today: `patients` (foundational), `schedules` (removable, isolation-critical), `treatment_plan` (heavy deps). |
| Frontend layer | The `frontend/` subdir inside a backend module. Loaded as a Nuxt layer. |
