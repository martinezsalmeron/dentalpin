# TODOS — DentalPin

> The open standard for dental clinic management.

---

## 1. VISION AND PRINCIPLES

### What is DentalPin

DentalPin is open source dental clinic management software designed to be:

- **Modular** — Every feature is a self-contained module
- **API-First** — Everything is accessible via REST API
- **Multi-tenant** — Built for clinic isolation from day one
- **Extensible** — Third parties can build integrations and modules

### License: BSL 1.1

- **Free to use** for clinics (self-hosted or cloud)
- **Contributions** welcome and encouraged
- **Prohibited** to host as a competing commercial SaaS
- **Converts to Apache 2.0** after 4 years

---

## 2. PRIORITIES

### Priority Tags

| Tag | Meaning | Timeline |
|-----|---------|----------|
| 🔴 P0 | Blocks first clinic in production | Immediate |
| 🟠 P1 | Required for 10 clinics + legal compliance | 3-6 months |
| 🟡 P2 | Enables ecosystem growth | 6-12 months |
| 🟢 P3 | Advanced features, long term | 12-24 months |

### Critical Legal Deadlines (Spain)

| Deadline | Requirement | Impact |
|----------|-------------|--------|
| **January 2027** | Verifactu mandatory for companies | Without this, no Spanish SL can legally use the software |
| **July 2027** | Verifactu mandatory for freelancers | Full Spanish market coverage |

---

## 3. PLATFORM LAYERS

### 3.1 Core Platform (BSL 1.1)

What is **NOT** a module. The foundation everything else builds on.

| Component | Status | Description |
|-----------|--------|-------------|
| Plugin System | ✅ | Auto-discovery, dependency resolution |
| Auth + RBAC | ✅ | JWT, 5 roles, wildcard permissions |
| Event Bus | ✅ | Pub/sub for module communication |
| Multi-tenancy | ✅ | Clinic isolation, membership |
| REST API | ✅ | OpenAPI, versioned |

---

### 3.2 First-Party Modules (BSL 1.1)

Included by default. Functionality every clinic needs.

| Module | Status | Function |
|--------|--------|----------|
| `clinical` | ⚠️ Partial | Patients, appointments (basic) |
| `odontogram` | ✅ | Interactive FDI dental chart |
| `catalog` | 🔴 P0 | Treatment catalog |
| `budgets` | 🔴 P0 | Budgets/quotes + PDF |
| `billing` | 🔴 P0 | Invoicing |
| `patient-record` | 🔴 P0 | Complete patient record (see detail below) |
| `clinical-notes` | 🟠 P1 | Clinical evolution (SOAP) |
| `imaging` | 🟠 P1 | Clinical images and X-rays |
| `booking` | 🟠 P1 | Online booking |
| `communications` | 🟠 P1 | Reminders, notifications |

---

#### Complete Patient Record (`patient-record`) 🔴 P0

The current patient record is basic. A professional patient record needs:

**1. General Information**
- [ ] Complete demographics
- [ ] Emergency contact
- [ ] Legal guardian (minors)
- [ ] Patient photo
- [ ] ID document scan
- [ ] Profession and workplace

**2. Medical History / Anamnesis**
- [ ] Allergies (medications, materials, latex)
- [ ] Current medications
- [ ] Systemic diseases (diabetes, hypertension, cardiac)
- [ ] Surgical history
- [ ] Pregnancy/lactation
- [ ] Anticoagulants
- [ ] Critical alerts (visible badges)

**3. Clinical Image Gallery**
- [ ] Intraoral photos (frontal, lateral, occlusal)
- [ ] Extraoral photos (profile, smile)
- [ ] Before/after by treatment
- [ ] Organization by date and type

**4. X-rays and Diagnostic Images**
- [ ] Panoramic
- [ ] Periapical
- [ ] CBCT (with DICOM integration)
- [ ] Temporal comparison
- [ ] Image annotations

**5. Patient Documents**
- [ ] Signed consent forms
- [ ] External reports
- [ ] Referral letters
- [ ] Insurance card
- [ ] Imported history from other clinics

**6. Unified Timeline**
- [ ] All visits
- [ ] Treatments performed
- [ ] Budgets
- [ ] Invoices
- [ ] Odontogram changes
- [ ] Communications sent

---

#### Treatment Catalog (`catalog`) 🔴 P0

| Feature | Description |
|---------|-------------|
| Multi-code | Internal codes + official nomenclatures (RCOE, CCAM, CDT/ADA) |
| Price lists | Multiple rates (private, insured, promotional) |
| Packages | Combined treatment templates |
| Duration | Default times for scheduling |
| Materials | Inventory linkage |
| VAT | Tax configuration by category |

---

#### Budgets (`budgets`) 🔴 P0

| Feature | Description |
|---------|-------------|
| Linked lines | Catalog + tooth/surface from odontogram |
| Discounts | Per line and global |
| Workflow | Draft → Presented → Accepted → In progress → Completed |
| Partial acceptance | Patient accepts some lines |
| Validity | Expiration period |
| PDF | With clinic branding |
| Digital signature | E-signature for acceptance |
| Conversion | Budget → Appointments → Invoices |

---

#### Billing (`billing`) 🔴 P0

| Feature | Description |
|---------|-------------|
| From budget | Auto-populate from accepted lines |
| Manual | Direct creation |
| Status | Draft → Issued → Paid → Partial → Cancelled/Credit note |
| Multi-tax | VAT exempt (healthcare) vs taxable (cosmetic) |
| Payments | Record payments (cash, card, transfer) |
| Verifactu-ready | Fields prepared (hash, QR) |
| PDF | With legal requirements |
| Series | Configurable numbering |

---

### 3.3 Community/Third-Party Modules

Opportunities for developers, equipment manufacturers, labs, and insurers.

#### Compliance (by country)

| Module | Country | Description |
|--------|---------|-------------|
| `verifactu-es` | 🇪🇸 Spain | Hash chain, QR, AEAT submission |
| `factur-x-fr` | 🇫🇷 France | French electronic invoicing |
| `sdi-it` | 🇮🇹 Italy | Sistema di Interscambio |
| `furs-si` | 🇸🇮 Slovenia | FURS fiscalization |

#### Clinical Integrations

| Module | Type | Description |
|--------|------|-------------|
| `dicom-viewer` | Radiology | Embedded DICOM viewer |
| `lab-orders` | Labs | Orders to prosthetic labs |
| `insurance-claims` | Insurance | Claims processing |
| `intraoral-capture` | Hardware | Intraoral camera capture |

#### Communications

| Module | Description |
|--------|-------------|
| `sms-twilio` | Twilio SMS integration |
| `whatsapp-business` | WhatsApp Business API |
| `email-sendgrid` | SendGrid/Mailgun |

#### Clinical Specialties

| Module | Specialty | Description |
|--------|-----------|-------------|
| `ortho-tracking` | Orthodontics | Cephalometry, aligner tracking |
| `perio-charting` | Periodontics | Probing, PSR/BPE |
| `implant-planning` | Implantology | Planning, implant registry |
| `endo-workflow` | Endodontics | Working length, file sequence |

#### AI

| Module | Description |
|--------|-------------|
| `imaging-ai` | Assisted pathology detection in X-rays |
| `voice-dictation` | Clinical note dictation |
| `smart-scheduling` | ML-based schedule optimization |

---

## 4. OPPORTUNITIES FOR THIRD PARTIES

DentalPin is designed so the **entire dental industry** can build modules.

### For Dental Equipment Manufacturers

| Equipment Type | Example Manufacturers | Events to consume |
|----------------|----------------------|-------------------|
| Radiology/DICOM | Planmeca, Vatech, Carestream | `patient.opened`, `treatment.planned` |
| Intraoral cameras | Dentsply Sirona, Acteon | `appointment.started` |
| CAD/CAM | CEREC, 3Shape | `treatment.completed` |
| Chairs | KaVo, A-dec | `appointment.checked_in` |

**Benefit:** Your equipment integrates natively with the software clinics use 8h/day.

### For Prosthetic Labs

| Module | Function |
|--------|----------|
| `lab-orders` | Send cases from patient record |
| `lab-tracking` | Real-time work status |
| `digital-impressions` | STL file management |
| `shade-management` | Color communication |

**Benefit:** Direct order channel from clinical workflow.

### For Insurance Companies

| Module | Function |
|--------|----------|
| `insurance-coverage` | Automatic pre-authorizations |
| `insurance-billing` | Direct billing to insurer |
| `coverage-calculator` | Coverage simulation in budget |
| `claims-status` | Real-time claims tracking |

**Benefit:** Reduced friction in authorizations and payments.

### For Communication Companies

| Module | Function |
|--------|----------|
| `sms-reminders` | Twilio, MessageBird, Vonage |
| `whatsapp-business` | Bidirectional communication |
| `email-campaigns` | Recalls, dental marketing |
| `review-management` | Post-visit review requests |

### For Independent Developers

| Module | Complexity | Impact |
|--------|------------|--------|
| Translations (FR, PT, DE) | Low | High |
| Export ICS (Google Calendar) | Low | Medium |
| Dark mode | Low | Medium |
| Digital consents | Medium | High |
| Orthodontics tracking | High | Niche |
| Periodontics charting | High | Niche |

---

## 5. ROADMAP BY PHASE

### Phase 0: Foundation (Current) ✅

**What's already built:**

| Component | Status |
|-----------|--------|
| Backend FastAPI + SQLAlchemy | ✅ |
| Frontend Nuxt 3 + Nuxt UI | ✅ |
| Plugin system with auto-discovery | ✅ |
| RBAC with 5 roles and wildcards | ✅ |
| Multi-tenancy (clinic isolation) | ✅ |
| Event bus | ✅ |
| Clinical module (patients, appointments) | ✅ |
| Odontogram module (FDI chart) | ✅ |
| 6 frontend pages, 18 components | ✅ |
| Docker Compose deployment | ✅ |

---

### Phase 1: Functional Clinic MVP 🔴 P0

**Goal:** A small clinic can operate day to day.

| Module | Key Deliverables |
|--------|------------------|
| `patient-record` | Complete record: anamnesis, alerts, documents |
| `catalog` | Multi-code treatment catalog |
| `budgets` | Budgets with complete workflow + PDF |
| `billing` | Basic invoicing + PDF |
| `imaging-basic` | Basic clinical image gallery |
| AI Infrastructure | ToolRegistry, ContextProvider |

---

### Phase 2: Production 🟠 P1

**Goal:** Ready for 10 real clinics. Legal compliance.

| Module | Key Deliverables | Deadline |
|--------|------------------|----------|
| `verifactu-es` | Hash chain, QR, AEAT submission | **January 2027** |
| `booking` | Embeddable widget, standalone page | |
| `communications` | Reminders SMS/email/WhatsApp | |
| `inventory` | Stock management, reorder alerts | |
| `data-import` | Migration from Gesden, Clinic Cloud, CSV | |
| Multi-clinic | Clinic switcher, shared patients | |
| Payments | Stripe, Redsys integration | |

---

### Phase 3: Ecosystem 🟡 P2

**Goal:** Third parties build on the platform.

| Component | Key Deliverables |
|-----------|------------------|
| Marketplace v1 | Module browser, install/uninstall |
| Developer Portal | SDK, docs, module templates |
| Partner Program | Partner portal, certification |
| `insurance` | Coverage tables, claims |
| `clinical-notes` | SOAP evolution, templates |
| `prescriptions` | Prescriptions with interactions |
| AI Assistant | Chat interface, task execution |

---

### Phase 4: Scale 🟢 P3

**Goal:** DentalPin is the industry standard.

| Component | Key Deliverables |
|-----------|------------------|
| Specialty modules | Ortho, perio, implants, endo |
| International | FR, PT, DE, IT locales + compliance |
| AI Clinical | Decision support, imaging analysis |
| Voice | Dictation, voice commands |
| White-label | Theming for partners |

---

## 6. SUCCESS METRICS

### Adoption Metrics

| Milestone | Target | Validation |
|-----------|--------|------------|
| First clinic | Month 3 | 1 clinic using daily |
| Validation | Months 1-6 | 3-5 trusted clinics + feedback |
| Product-market fit | Month 6 | 20 clinics, churn <5% |
| Scale | Month 12 | 100 clinics |
| Standard | Month 24 | 1,000 clinics |

### Community Metrics

| Metric | Month 6 | Month 12 | Month 24 |
|--------|---------|----------|----------|
| GitHub Stars | 50 | 500 | 2,000 |
| External contributors | 3 | 10 | 50 |
| Third-party modules | 1 | 5 | 20 |
| Countries with deployments | 1 | 3 | 10 |

---

## 7. GOOD FIRST ISSUES

Small, well-scoped features for new contributors.

### Translations (no code)

- [ ] `i18n/locales/fr.json` — French translation
- [ ] `i18n/locales/pt.json` — Portuguese translation
- [ ] `i18n/locales/de.json` — German translation

### Frontend (low risk)

- [ ] Keyboard shortcuts for common actions
- [ ] Export appointment to ICS format (Google Calendar)
- [ ] Print view for patient record
- [ ] Skeleton loaders for all pages

### Backend (low risk)

- [ ] Improved seed data (more test cases)
- [ ] Detailed health check endpoint (`/health/detailed`)
- [ ] Configurable rate limiting

### Documentation

- [ ] Tutorial: "My first module in 30 minutes"
- [ ] Video walkthrough of architecture
- [ ] Updated architecture diagrams

### Testing

- [ ] E2E tests with Playwright for critical flows
- [ ] Increase unit test coverage to 80%
- [ ] Accessibility (a11y) tests

---

## 8. TECHNICAL DETAILS BY MODULE

### Verifactu (`verifactu-es`) 🟠 P1

**Legal deadline: January 2027 (companies), July 2027 (freelancers)**

| Component | Description |
|-----------|-------------|
| Hash chain | SHA-256 chained from previous invoice |
| QR code | Generation on each invoice |
| AEAT submission | Real-time or batched submission |
| Certificates | Digital signature management |
| Audit log | Immutable events for auditing |
| Separate module | Non-Spanish deployments don't load this |

**Extensible:** The pattern works for Factur-X (FR), SDI (IT), etc.

---

### Clinical Notes (`clinical-notes`) 🟠 P1

| Feature | Description |
|---------|-------------|
| Rich text | With attachments (images, files) |
| Templates | By treatment type (endo, implant, etc.) |
| Quick vs structured | Toggle by preference |
| Lock after sign | Not editable after finalization, only amendments |
| AI dictation | Voice-to-text + auto-structuring |
| Searchable | Full-text search across patients |

---

### Online Booking (`booking`) 🟠 P1

| Feature | Description |
|---------|-------------|
| Embeddable widget | For clinic website |
| Standalone page | With clinic branding |
| Configurable slots | By treatment type |
| New patient registration | During booking |
| ICS invite | Confirmation with calendar file |
| Anti-spam | Captcha, rate limiting |

---

### Data Import (`data-import`) 🟠 P1

**Critical:** Without migration, nobody switches software.

| Source | Format |
|--------|--------|
| Gesden | Specific export |
| Clinic Cloud | Specific export |
| CS R4 | Specific export |
| Generic | CSV/Excel mapping tool |
| FHIR | For interoperability |

| Feature | Description |
|---------|-------------|
| Mapping tool | Map source fields → DentalPin |
| Dry-run | Preview before commit |
| Validation | Detect errors and conflicts |
| Rollback | Ability to undo |

---

### AI Infrastructure 🔴 P0

| Component | Description |
|-----------|-------------|
| `ToolRegistry` | Modules register AI-invokable actions |
| `ContextProvider` | Relevant context per interaction |
| EventBus integration | AI listens and reacts to events |
| LLM abstraction | Anthropic, OpenAI, Ollama |
| Token tracking | Cost management and rate limiting |
| RBAC integration | AI respects same permissions as UI |
| Audit log | Every AI action is traceable |

---

## 9. COMPLIANCE & SECURITY

### GDPR 🟠 P1

| Feature | Description |
|---------|-------------|
| Consent management | Consent tracking by channel |
| Right of access | Patient data export |
| Right to erasure | Anonymization/deletion workflow |
| Data minimization | Configurable retention periods |
| Breach notification | Notification workflow |

### Audit Log 🔴 P0

| Feature | Description |
|---------|-------------|
| Immutable | Append-only, no tampering |
| Complete | Who, what, when, where, before/after |
| Searchable | Filterable by user, entity, date |
| Exportable | For external audits |
| Retention | Configurable policies |

### Backup & DR 🟠 P1

| Feature | Description |
|---------|-------------|
| Automated daily | Database + files |
| Point-in-time | WAL-based recovery |
| Cross-region | Optional replication |
| One-click restore | Easy recovery |
| Encryption | At rest |

---

## 10. MODULE ARCHITECTURE

### Module Anatomy

```python
# backend/app/modules/mymodule/__init__.py
class MyModule(BaseModule):
    @property
    def name(self) -> str:
        return "mymodule"  # Router at /api/v1/mymodule/

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def dependencies(self) -> list[str]:
        return ["clinical"]  # Loaded after clinical

    def get_models(self) -> list:
        return [MyModel]

    def get_router(self) -> APIRouter:
        return router

    def get_permissions(self) -> list[str]:
        return ["resource.read", "resource.write"]

    def get_event_handlers(self) -> dict:
        return {"patient.created": self._on_patient_created}

    def get_ai_tools(self) -> list:  # AI-native
        return [CreateResourceTool(), ListResourcesTool()]
```

### Event Bus

```python
# Publishing
from app.core.events import event_bus
event_bus.publish("patient.created", {"patient_id": str(patient.id)})

# Subscribing
def get_event_handlers(self) -> dict:
    return {"patient.created": self._handle}
```

### Frontend Extension Points

| Extension Point | Use |
|-----------------|-----|
| Navigation | Register menu items |
| Patient tabs | Add tabs to patient record |
| Dashboard widgets | Cards on main dashboard |
| Action buttons | Contextual buttons |
| Settings pages | Configuration pages |

---

## 11. EXECUTIVE SUMMARY

### What is DentalPin

Open source dental clinic management software:
- **Free core** generates adoption and ecosystem
- **Modular architecture** enables third-party integrations
- **BSL 1.1 license** protects against SaaS competitors while allowing free use

### Why it exists

1. The dental software market is fragmented and legacy
2. Clinics deserve modern, open, affordable software
3. An open standard benefits the entire industry

### What to build first

1. 🔴 **Complete patient record** — Without this, no MVP
2. 🔴 **Catalog + Budgets + Billing** — The revenue workflow
3. 🟠 **Verifactu** — Mandatory legal compliance
4. 🟠 **Inventory** — Stock and supplies management

### How we measure success

**Primary metric:** Active clinics using DentalPin daily.

Everything else (stars, contributors, modules) are supporting indicators.
