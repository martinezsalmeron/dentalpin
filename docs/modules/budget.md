# Budget Module - Developer Documentation

## Overview

The Budget module manages dental treatment quotes with versioning, partial acceptance, digital signatures, and PDF generation. This document describes extension points for future modules and third-party integrations.

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
| `status` | String | Workflow state |
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
| `line_total` | Decimal | Line total |
| `tooth_number` | Integer | FDI notation |
| `surfaces` | JSONB | ["M", "O", "D"] |
| `item_status` | String | Item workflow state |

### BudgetSignature

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `budget_id` | UUID | Signed budget |
| `signature_type` | String | full/partial/rejection |
| `signed_items` | JSONB | Item IDs signed |
| `signed_by_name` | String | Signer name |
| `relationship_to_patient` | String | patient/guardian/representative |
| `signature_method` | String | click_accept/drawn/external_provider |
| `external_signature_id` | String | For external providers |
| `external_provider` | String | Provider name |

---

## 3. Workflow States

```
draft → sent → [accepted|partially_accepted|rejected]
                    ↓
               in_progress → completed → invoiced
                    ↓
               cancelled (from most states)
```

### Valid Transitions

| From | To |
|------|-----|
| `draft` | `sent`, `cancelled` |
| `sent` | `accepted`, `partially_accepted`, `rejected`, `expired`, `cancelled` |
| `partially_accepted` | `accepted`, `rejected`, `cancelled` |
| `accepted` | `in_progress`, `cancelled` |
| `in_progress` | `completed`, `cancelled` |
| `completed` | `invoiced` |

---

## 4. Events Published

Other modules can subscribe to these events via the Event Bus.

### Budget Lifecycle Events

| Event | Payload | When |
|-------|---------|------|
| `budget.created` | `{budget_id, patient_id, clinic_id, total, items}` | New budget saved |
| `budget.updated` | `{budget_id, changes}` | Budget modified |
| `budget.sent` | `{budget_id, patient_id, sent_at}` | Sent to patient |
| `budget.accepted` | `{budget_id, accepted_items, signature_id, total_accepted}` | Full acceptance |
| `budget.partially_accepted` | `{budget_id, accepted_items, pending_items}` | Partial acceptance |
| `budget.rejected` | `{budget_id, reason, rejected_at}` | Budget rejected |
| `budget.cancelled` | `{budget_id, cancelled_by, reason}` | Budget cancelled |
| `budget.completed` | `{budget_id, completed_at}` | All treatments done |

### Budget Item Events

| Event | Payload | When |
|-------|---------|------|
| `budget.item.added` | `{budget_id, item_id, catalog_item_id, price}` | Item added |
| `budget.item.accepted` | `{item_id, budget_id, accepted_at}` | Item accepted |
| `budget.item.treatment_started` | `{item_id, started_by, started_at}` | Treatment begins |
| `budget.item.treatment_completed` | `{item_id, performed_by, tooth_treatment_id}` | Treatment done |

### Example: Invoice Module Subscriber

```python
class InvoiceModule(BaseModule):
    def get_event_handlers(self) -> dict:
        return {
            "budget.accepted": self._create_proforma,
            "budget.completed": self._generate_final_invoice,
        }

    def _create_proforma(self, data: dict) -> None:
        budget_id = data["budget_id"]
        accepted_items = data["accepted_items"]
        # Create invoice draft with accepted items
```

---

## 5. Events Budget Module Listens To

| Event | Source Module | Action |
|-------|---------------|--------|
| `odontogram.treatment.performed` | Odontogram | Mark linked budget item as completed |
| `appointment.completed` | Clinical | Check if appointment has budget items to update |

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

### 6.3 PDF Template Customization

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
| POST | `/budgets/{id}/send` | `budget.write` | Mark as sent |
| POST | `/budgets/{id}/accept` | `budget.write` | Accept with signature |
| POST | `/budgets/{id}/accept-partial` | `budget.write` | Accept specific items |
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
  // CRUD
  fetchBudgets, createBudget, updateBudget, deleteBudget,
  // Items
  addItem, updateItem, removeItem,
  // Workflow
  sendBudget, acceptBudget, rejectBudget, cancelBudget, completeBudget,
  // PDF
  downloadPDF,
  // Helpers
  canEdit, canSend, canAccept, getStatusColor
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
- Workflow transitions (send, accept, reject, cancel)
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
| **insurance** | Extends | P1 | insurance_estimate, policy lookup |
| **financing** | Extends | P1 | financing_plan_id, payment schedules |
| **e-signature** | Replaces | P2 | external_signature_id, signature_method |
| **communications** | Subscribes | P1 | budget.sent, budget.expired |
| **patient-portal** | Exposes | P2 | Token-based acceptance flow |
| **analytics** | Reads | P2 | Budget conversion rates, avg values |
