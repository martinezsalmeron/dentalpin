# TODOS — DentalPin

Items deferred from MVP, captured with full context for future implementation.

---

## Multi-Cabinet Calendar View

**What:** Display multiple cabinet columns side-by-side in the weekly calendar view.

**Why:** Clinics with 2-3 chairs need to see all cabinets simultaneously to coordinate scheduling and avoid overbooking.

**Pros:**
- Essential for clinics with multiple chairs
- Reduces scheduling conflicts
- Professional feature expected by users

**Cons:**
- Horizontal scroll complexity on mobile
- Conflict detection becomes per-cabinet instead of global
- UI density increases

**Context:**
- Current MVP: single cabinet column (seeded)
- Implementation: add horizontal scroll container, cabinet header row, modify appointment query to group by cabinet
- Consider: responsive breakpoints, touch scroll on mobile

**Depends on:** MVP calendar complete

---

## Calendar Drag-and-Drop Rescheduling

**What:** Allow dragging appointments between time slots and cabinets to reschedule.

**Why:** More intuitive than click-to-edit for visual scheduling. Standard UX pattern in calendar apps.

**Pros:**
- Faster rescheduling workflow
- Visual feedback during drag
- Familiar interaction pattern

**Cons:**
- Touch handling complexity
- Conflict preview logic
- Undo mechanism needed

**Context:**
- Current MVP: click appointment → edit modal → change time
- Implementation: vue-draggable or native drag API, show ghost preview, validate conflicts before drop, show undo toast
- Consider: mobile touch events, accessibility (keyboard rescheduling)

**Depends on:** MVP calendar complete, multi-cabinet view (optional)

---

## Patient Odontogram

**What:** Interactive SVG dental chart showing all 32 adult teeth with clickable surfaces and condition tracking.

**Why:** The core differentiator for dental software. Every dental clinic needs to track tooth conditions.

**Pros:**
- Wow factor differentiator
- Essential clinical feature
- Visual patient history

**Cons:**
- Complex SVG component (~500 lines)
- 5 surfaces per tooth × 32 teeth = 160 clickable areas
- History tracking adds audit complexity

**Context:**
- FDI notation: 11-18, 21-28, 31-38, 41-48 (adult), 51-85 (deciduous)
- Surfaces: mesial, distal, occlusal/incisal, vestibular, lingual
- States: healthy (white), caries (red), filling (blue), crown (yellow), missing (gray)
- Implementation: SVG groups per tooth, click handlers per surface, PATCH API per tooth, OdontogramHistory for audit
- Reference: CLAUDE.md has full Odontogram model spec

**Depends on:** MVP patient detail complete

---

## Presupuestos (Budgets)

**What:** Treatment budget creation with line items, pricing, and PDF generation.

**Why:** Clinics need to present treatment plans with costs to patients for acceptance.

**Pros:**
- Revenue-driving feature
- Professional presentation
- Workflow: budget → acceptance → invoice

**Cons:**
- Requires TreatmentCatalog CRUD
- PDF generation complexity
- Status workflow (draft → presented → accepted/rejected)

**Context:**
- See CLAUDE.md Budget model and BudgetBuilder.vue spec
- Depends on: Treatment catalog, Patient module, PDF generation

**Depends on:** Treatment catalog, MVP complete

---

## Facturas (Invoices)

**What:** Invoice generation from accepted budgets with Verifactu-ready fields.

**Why:** Legal requirement for billing in Spain. Verifactu compliance coming in 2026.

**Pros:**
- Legal compliance
- Revenue tracking
- Verifactu preparation

**Cons:**
- Verifactu integration complexity (deferred)
- PDF generation
- Payment tracking

**Context:**
- See CLAUDE.md Invoice model with verifactu_* fields
- Implementation: create from budget, PDF generation, status flow
- Verifactu: hash chain, QR codes, AEAT submission (separate module)

**Depends on:** Budgets, PDF generation
