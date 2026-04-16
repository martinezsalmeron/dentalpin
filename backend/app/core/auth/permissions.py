"""Role-permission mappings for RBAC.

MVP: Hardcoded mappings with wildcard support.
Future: Load from database per-clinic.
"""

from typing import Final

# Valid roles - order matters for UI display
ROLES: Final[list[str]] = [
    "admin",
    "dentist",
    "hygienist",
    "assistant",
    "receptionist",
]

# Core permissions (not from modules)
CORE_PERMISSIONS: Final[list[str]] = [
    "admin.users.read",
    "admin.users.write",
    "admin.clinic.read",
    "admin.clinic.write",
    # Medical history permissions (part of clinical.patients.* scope)
    "clinical.patients.medical.read",
    "clinical.patients.medical.write",
]

# Role -> permissions mapping
# Supports wildcards: "*" = all, "module.*" = all module permissions
ROLE_PERMISSIONS: Final[dict[str, list[str]]] = {
    "admin": [
        "*",  # Admin gets everything, including future modules
    ],
    "dentist": [
        "clinical.*",  # All clinical permissions
        "odontogram.*",  # Full odontogram access
        "treatment_plan.*",  # Full treatment plan access
        "catalog.read",  # Can view catalog (prices, treatments)
        "budget.*",  # Full budget access
        "billing.*",  # Full billing access
        "media.*",  # Full document access
        "notifications.preferences.*",  # Can manage patient notification preferences
        "notifications.send",  # Can send manual notifications
        "reports.billing.read",  # Can view billing reports
        "reports.scheduling.read",  # Can view scheduling reports
    ],
    "hygienist": [
        "clinical.patients.read",
        "clinical.patients.medical.read",  # Can view medical history
        "clinical.appointments.*",
        "odontogram.read",
        "odontogram.write",
        "treatment_plan.plans.read",  # Can view treatment plans
        "catalog.read",  # Can view catalog (prices, treatments)
        "budget.read",  # Can view budgets
        "billing.read",  # Can view invoices
        "media.documents.read",  # Can view documents
        "reports.scheduling.read",  # Can view scheduling reports (own data)
    ],
    "assistant": [
        "clinical.patients.*",
        "clinical.appointments.*",
        "odontogram.read",  # Can view but not edit
        "treatment_plan.plans.read",  # Can view treatment plans
        "treatment_plan.plans.write",  # Can edit treatment plans
        "catalog.read",  # Can view catalog (prices, treatments)
        "budget.read",  # Can view budgets
        "budget.write",  # Can create/edit budgets
        "billing.read",  # Can view invoices
        "billing.write",  # Can create/edit invoices, record payments
        "media.*",  # Full document access
        "notifications.preferences.*",  # Can manage patient notification preferences
        "notifications.send",  # Can send manual notifications
        "reports.scheduling.read",  # Can view scheduling reports
    ],
    "receptionist": [
        "clinical.patients.read",
        "clinical.patients.write",
        "clinical.patients.medical.read",  # Can view medical history (for emergencies)
        # No clinical.patients.medical.write - receptionist cannot edit medical history
        "clinical.appointments.*",
        "catalog.read",  # Can view catalog for budgeting
        "budget.read",  # Can view budgets
        "budget.write",  # Can create/edit budgets
        "billing.read",  # Can view invoices
        "billing.write",  # Can create/edit invoices, record payments
        "media.*",  # Full document access
        "notifications.preferences.*",  # Can manage patient notification preferences
        "notifications.send",  # Can send manual notifications
        "reports.billing.read",  # Can view basic billing reports
        "reports.scheduling.read",  # Can view scheduling reports
        # No odontogram access for receptionists
    ],
}


def get_role_permissions(role: str) -> list[str]:
    """Get permissions for a role.

    This function is the single point that will change
    when migrating to database-driven permissions.
    """
    return ROLE_PERMISSIONS.get(role, [])


def permission_matches(required: str, granted: str) -> bool:
    """Check if a granted permission satisfies a required permission.

    Supports wildcards:
    - "*" matches everything
    - "module.*" matches "module.resource.action"
    - "module.resource.*" matches "module.resource.action"
    """
    if granted == "*":
        return True

    if granted.endswith(".*"):
        prefix = granted[:-1]  # "clinical.*" -> "clinical."
        return required.startswith(prefix)

    return required == granted


def has_permission(role: str, required_permission: str) -> bool:
    """Check if a role has a specific permission."""
    role_perms = get_role_permissions(role)
    return any(permission_matches(required_permission, perm) for perm in role_perms)


def expand_permissions(role_perms: list[str], all_permissions: list[str]) -> list[str]:
    """Expand wildcards to actual permission list for frontend.

    Frontend needs concrete permissions, not wildcards.
    """
    if "*" in role_perms:
        return all_permissions

    expanded: list[str] = []
    for perm in role_perms:
        if perm.endswith(".*"):
            prefix = perm[:-1]
            expanded.extend(p for p in all_permissions if p.startswith(prefix))
        else:
            expanded.append(perm)

    return list(set(expanded))  # Dedupe
