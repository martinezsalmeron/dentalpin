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

---

## User Roles and Permissions (RBAC)

**What:** Implement role-based access control beyond the current admin-only role.

**Why:** Clinics have different staff types (doctors, receptionists, assistants) who need different permissions.

**Roles to implement:**
- **Admin:** Full access, user management, clinic settings
- **Doctor/Professional:** View/edit own appointments, access patient records, create budgets
- **Receptionist:** Manage all appointments, view patient list, cannot access clinical data
- **Assistant:** View appointments, limited patient info

**Pros:**
- Security: staff only see what they need
- Audit: track who did what
- Professional: expected feature in clinic software

**Cons:**
- Permission matrix complexity
- UI changes to hide/show features per role
- Testing all role combinations

**Context:**
- Backend RBAC infrastructure exists (`app/core/auth/`)
- Currently all users have admin role by default
- `professional_id` field exists in Appointment model for doctor assignment
- Implementation: define permission matrix, add role to User model, middleware checks, UI conditional rendering

**Depends on:** MVP complete

---

## User Management (Admin Panel)

**What:** Admin interface to create, edit, deactivate clinic staff users.

**Why:** Clinic admins need to onboard new staff and manage existing accounts without developer intervention.

**Features:**
- List all clinic users with role and status
- Create new user (name, email, role, send invite)
- Edit user (change role, reset password)
- Deactivate user (soft delete, revoke access)
- Audit log of user actions

**Pros:**
- Self-service administration
- Reduces support burden
- Professional feature

**Cons:**
- Email invitation system needed
- Password reset flow
- Audit logging infrastructure

**Context:**
- Backend: add `/api/v1/users/` CRUD endpoints
- Frontend: new `/admin/users` page with table and modals
- Consider: email service integration (SendGrid, Resend)

**Depends on:** RBAC roles implemented

---

## Multi-Clinic Support

**What:** Allow a single user to belong to multiple clinics, with clinic-scoped data.

**Why:** Some professionals work at multiple locations, or clinic groups want unified management.

**Pros:**
- Supports clinic chains
- Flexible for consultants
- Growth feature

**Cons:**
- Data isolation complexity
- Clinic context switching UI
- Permission per clinic

**Context:**
- Current: single clinic assumed (seeded)
- Implementation: ClinicMembership join table, clinic selector in header, all queries scoped by current clinic
- Consider: clinic-specific settings, cross-clinic reporting

**Depends on:** User management, RBAC
