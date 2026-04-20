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
]

# Role -> permissions mapping
# Supports wildcards: "*" = all, "module.*" = all module permissions
#
# Fase B.1 chunk 3: ``clinical.patients.*`` renamed to ``patients.*``;
# ``clinical.appointments.*`` keeps its namespace until Etapa B.2
# introduces the ``agenda`` module.
ROLE_PERMISSIONS: Final[dict[str, list[str]]] = {
    "admin": [
        "*",  # Admin gets everything, including future modules
    ],
    "dentist": [
        "patients.*",  # Full patient access (identity + medical history)
        "clinical.appointments.*",  # Appointments (moves to agenda.* in B.2)
        "odontogram.*",
        "treatment_plan.*",
        "catalog.read",
        "budget.*",
        "billing.*",
        "media.*",
        "notifications.preferences.*",
        "notifications.send",
        "reports.billing.read",
        "reports.scheduling.read",
    ],
    "hygienist": [
        "patients.read",
        "patients.medical.read",
        "clinical.appointments.*",
        "odontogram.read",
        "odontogram.write",
        "treatment_plan.plans.read",
        "catalog.read",
        "budget.read",
        "billing.read",
        "media.documents.read",
        "reports.scheduling.read",
    ],
    "assistant": [
        "patients.*",
        "clinical.appointments.*",
        "odontogram.read",
        "treatment_plan.plans.read",
        "treatment_plan.plans.write",
        "catalog.read",
        "budget.read",
        "budget.write",
        "billing.read",
        "billing.write",
        "media.*",
        "notifications.preferences.*",
        "notifications.send",
        "reports.scheduling.read",
    ],
    "receptionist": [
        "patients.read",
        "patients.write",
        "patients.medical.read",  # medical view only — no write for receptionist
        "clinical.appointments.*",
        "catalog.read",
        "budget.read",
        "budget.write",
        "billing.read",
        "billing.write",
        "media.*",
        "notifications.preferences.*",
        "notifications.send",
        "reports.billing.read",
        "reports.scheduling.read",
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
