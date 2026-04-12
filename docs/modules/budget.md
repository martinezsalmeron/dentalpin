# Budget Module - Developer Documentation

## Overview

The Budget module manages dental treatment quotes with versioning, digital signatures, and PDF generation. This document describes extension points for future modules and third-party integrations.

**Note:** The workflow supports an optional `sent` state: `draft → [sent] → accepted → completed`. Treatment execution tracking is reserved for a future Treatment Plan module.

---

## 1. Module Structure

```
backend/app/modules/budget/
├── __init__.py      # BudgetModule(BaseModule)
├── models.py        # Budget, BudgetItem, BudgetSignature, BudgetHistory
├── schemas.py       # Pydantic schemas
├── router.py        # FastAPI endpoints
├── service.py       # BudgetService, BudgetItemService
├── workflow.py      # BudgetWorkflowService (state machine)
└── pdf.py           # BudgetPDFService (PDF generation)
```

### Dependencies

- `clinical` - Patient data
- `catalog` - Treatment catalog items and VAT types

---

## 2. Data Models

### Budget

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `clinic_id` | UUID | Multi-tenancy |
| `patient_id` | UUID | Associated patient |
| `budget_number` | String | "PRES-2024-0001" format |
| `version` | Integer | Version number |
| `parent_budget_id` | UUID | Previous version link |
| `status` | String | Workflow state (see section 3) |
| `valid_from` | Date | Start of validity |
| `valid_until` | Date | Expiration date |
| `global_discount_type` | String | "percentage" or "absolute" |
| `global_discount_value` | Decimal | Discount amount |
| `subtotal` | Decimal | Sum before discounts |
| `total_discount` | Decimal | Total discounts |
| `total_tax` | Decimal | Total VAT |
| `total` | Decimal | Final amount |
| `insurance_estimate` | Decimal | Reserved for insurance module |

### BudgetItem

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `budget_id` | UUID | Parent budget |
| `catalog_item_id` | UUID | Treatment reference |
| `unit_price` | Decimal | Price snapshot |
| `quantity` | Integer | Units |
| `discount_type` | String | Line discount type |
| `discount_value` | Decimal | Line discount |
| `vat_type_id` | UUID | VAT type reference |
| `vat_rate` | Float | VAT rate snapshot |
| `line_subtotal` | Decimal | Before discount |
| `line_discount` | Decimal | Discount amount |
| `line_tax` | Decimal | VAT amount |
| `line_total` | Decimal | Final line total |
| `tooth_number` | Integer | FDI notation |
| `surfaces` | JSONB | ["M", "O", "D"] |
| `invoiced_quantity` | Integer | Qty already invoiced |

### BudgetSignature

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `budget_id` | UUID | Signed budget |
| `signature_type` | String | full_acceptance / rejection |
| `signed_items` | JSONB | Item IDs signed |
| `signed_by_name` | String | Signer name |
| `relationship_to_patient` | String | patient/guardian/representative |
| `signature_method` | String | click_accept/drawn/external_provider |
| `external_signature_id` | String | For external providers |
| `external_provider` | String | Provider name |

---

## 3. Workflow States

```
draft ────────────────────────────────────────────┐
  │                                               │
  ├──→ sent ──→ accepted ──→ completed            │
  │       │                                       │
  │       ├──→ rejected (terminal)                │
  │       │                                       │
  │       └──→ expired (terminal, automatic)      │
  │                                               │
  ├──→ accepted ──→ completed (direct acceptance) │
  │                                               │
  ├──→ rejected (terminal)                        │
  │                                               │
  └──→ cancelled (terminal) ←─────────────────────┘
```

### Status Descriptions

| Status | Description |
|--------|-------------|
| `draft` | Initial state, budget is editable |
| `sent` | Sent to patient (by email or manually), awaiting response |
| `accepted` | Patient accepted, ready for treatment and invoicing |
| `completed` | All work done (marked manually) |
| `rejected` | Patient rejected the budget (terminal) |
| `expired` | Validity period passed (terminal, automatic) |
| `cancelled` | Cancelled by clinic (terminal) |

### Valid Transitions

| From | To |
|------|-----|
| `draft` | `sent`, `accepted`, `rejected`, `cancelled` |
| `sent` | `accepted`, `rejected`, `expired`, `cancelled` |
| `accepted` | `completed`, `cancelled` |
| `completed` | (terminal) |
| `rejected` | (terminal) |
| `expired` | (terminal) |
| `cancelled` | (terminal) |

**Note:** The `expired` status is set automatically by a scheduled job when `valid_until < today` for draft and sent budgets.

---

## 4. Events Published

Other modules can subscribe to these events via the Event Bus.

### Budget Lifecycle Events

| Event | Payload | When |
|-------|---------|------|
| `budget.created` | `{budget_id, patient_id, clinic_id, total, items}` | New budget saved |
| `budget.updated` | `{budget_id, changes}` | Budget modified |
| `budget.sent` | `{budget_id, send_method, recipient_email}` | Budget sent to patient |
| `budget.accepted` | `{budget_id, signature_id, total}` | Budget accepted |
| `budget.rejected` | `{budget_id, reason, rejected_at}` | Budget rejected |
| `budget.cancelled` | `{budget_id, cancelled_by, reason}` | Budget cancelled |
| `budget.completed` | `{budget_id, completed_at}` | Budget marked complete |

### Budget Item Events

| Event | Payload | When |
|-------|---------|------|
| `budget.item.added` | `{budget_id, item_id, catalog_item_id, price}` | Item added |
| `budget.item.removed` | `{budget_id, item_id}` | Item removed |

### Example: Invoice Module Subscriber

```python
class InvoiceModule(BaseModule):
    def get_event_handlers(self) -> dict:
        return {
            "budget.accepted": self._notify_ready_for_invoice,
            "budget.completed": self._check_pending_invoices,
        }

    def _notify_ready_for_invoice(self, data: dict) -> None:
        # Budget is now ready to be invoiced
        pass
```

---

## 5. Events Budget Module Listens To

| Event | Source Module | Action |
|-------|---------------|--------|
| `odontogram.treatment.performed` | Odontogram | Reserved for future treatment plan integration |
| `appointment.completed` | Clinical | Reserved for future integration |

---

## 6. Extension Points

### 6.1 Insurance Module (Future)

Reserved field: `budget.insurance_estimate`

```python
# Insurance module subscribes to budget.created
def _on_budget_created(self, data: dict) -> None:
    coverage = self.calculate_coverage(data["patient_id"], data["items"])
    # Update budget.insurance_estimate
```

### 6.2 External Signature Providers (Future)

Reserved fields in `BudgetSignature`:
- `external_signature_id`
- `external_provider`
- `signature_method = "external_provider"`
- `signature_data` (JSONB)

```python
# E-signature module provides alternative signature flow
if signature_handler := module_registry.get_signature_handler():
    return signature_handler.request_signature(budget, signer_info)
else:
    return self._click_to_accept(budget, signer_info)
```

### 6.3 Treatment Plan Module (Future)

When a Treatment Plan module is implemented:
- Budget items can be linked to treatment plan items
- Treatment execution will be tracked in the plan, not the budget
- Budget remains a commercial document (quote/invoice)

### 6.4 PDF Template Customization

```python
# Third-party module can add PDF context
class InsuranceModule(BaseModule):
    def get_pdf_extensions(self, document_type: str) -> dict | None:
        if document_type == "budget":
            return {
                "insurance_info": self._get_insurance_section,
                "coverage_breakdown": self._get_coverage_table
            }
        return None
```

---

## 7. API Endpoints

### CRUD

| Method | Endpoint | Permission | Description |
|--------|----------|------------|-------------|
| GET | `/api/v1/budget/budgets` | `budget.read` | List with filters |
| GET | `/api/v1/budget/budgets/{id}` | `budget.read` | Get with items |
| POST | `/api/v1/budget/budgets` | `budget.write` | Create |
| PUT | `/api/v1/budget/budgets/{id}` | `budget.write` | Update (draft only) |
| DELETE | `/api/v1/budget/budgets/{id}` | `budget.admin` | Soft delete |

### Workflow

| Method | Endpoint | Permission | Description |
|--------|----------|------------|-------------|
| POST | `/budgets/{id}/send` | `budget.write` | Send to patient (email or manual) |
| POST | `/budgets/{id}/accept` | `budget.write` | Accept with signature |
| POST | `/budgets/{id}/reject` | `budget.write` | Reject |
| POST | `/budgets/{id}/cancel` | `budget.write` | Cancel |
| POST | `/budgets/{id}/complete` | `budget.write` | Mark completed |
| POST | `/budgets/{id}/duplicate` | `budget.write` | Create new version |

### Items

| Method | Endpoint | Permission | Description |
|--------|----------|------------|-------------|
| POST | `/budgets/{id}/items` | `budget.write` | Add item |
| PUT | `/budgets/{id}/items/{item_id}` | `budget.write` | Update item |
| DELETE | `/budgets/{id}/items/{item_id}` | `budget.write` | Remove item |

### PDF

| Method | Endpoint | Permission | Description |
|--------|----------|------------|-------------|
| GET | `/budgets/{id}/pdf` | `budget.read` | Download PDF |
| GET | `/budgets/{id}/pdf/preview` | `budget.read` | Preview with watermark |

### Versions & History

| Method | Endpoint | Permission | Description |
|--------|----------|------------|-------------|
| GET | `/budgets/{id}/versions` | `budget.read` | List all versions |
| GET | `/budgets/{id}/history` | `budget.read` | Audit history |

---

## 8. Permissions

| Permission | Description |
|------------|-------------|
| `budget.read` | View budgets |
| `budget.write` | Create, edit, workflow actions |
| `budget.admin` | Delete budgets |

### Role Assignments

| Role | Permissions |
|------|-------------|
| admin | `budget.*` |
| dentist | `budget.*` |
| hygienist | `budget.read` |
| assistant | `budget.read`, `budget.write` |
| receptionist | `budget.read`, `budget.write` |

---

## 9. Frontend Components

### Pages

- `/budgets` - List with search and filters
- `/budgets/new` - Create with patient selection
- `/budgets/[id]` - Detail/editor view

### Components

| Component | Purpose |
|-----------|---------|
| `BudgetStatusBadge.vue` | Status indicator |
| `BudgetItemModal.vue` | Add items from catalog |
| `BudgetFilters.vue` | Search and filter controls |

### Composable

```typescript
const {
  // State
  budgets, currentBudget, isLoading, error, total,

  // CRUD
  fetchBudgets, fetchBudget, createBudget, updateBudget, deleteBudget,

  // Items
  addItem, updateItem, removeItem,

  // Workflow
  acceptBudget, rejectBudget, cancelBudget, completeBudget, duplicateBudget,

  // Versions & History
  fetchVersions, fetchHistory,

  // PDF
  downloadPDF, getPDFPreviewUrl,

  // Helpers
  getStatusColor, canEdit, canAccept, canReject, canCancel, canComplete, canDuplicate
} = useBudgets()
```

---

## 10. Testing

```bash
# Run budget module tests
docker-compose exec backend python -m pytest tests/test_budget.py -v
```

### Key Test Cases

- CRUD operations (create, read, update, delete)
- Workflow transitions (accept, reject, cancel, complete)
- Item management (add, update, remove with totals)
- Discount calculations (line and global)
- Version duplication
- Authentication requirements

---

## 11. Migration Guide

When extending the budget module:

1. **Never modify existing columns** - Add new columns or tables
2. **Use nullable fields** for new required data
3. **Publish events** for all state changes
4. **Keep backward compatibility** in API responses
5. **Version API endpoints** if breaking changes needed

---

## 12. Future Module Integration Roadmap

| Module | Integration Type | Priority | Fields/Events Used |
|--------|------------------|----------|-------------------|
| **billing** | Bidirectional | P0 | budget.accepted → create invoice |
| **treatment-plan** | Extends | P1 | Link items to treatment execution |
| **insurance** | Extends | P1 | insurance_estimate, policy lookup |
| **financing** | Extends | P1 | financing_plan_id, payment schedules |
| **e-signature** | Replaces | P2 | external_signature_id, signature_method |
| **communications** | Subscribes | P1 | budget.accepted, budget.expired |
| **patient-portal** | Exposes | P2 | Token-based acceptance flow |
| **analytics** | Reads | P2 | Budget conversion rates, avg values |
