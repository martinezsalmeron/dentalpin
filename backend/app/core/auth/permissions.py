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
    # AI agent infrastructure
    "agents.view",
    "agents.supervise",
    "agents.configure",
    "agents.manage",
]

# Role -> permissions mapping
# Supports wildcards: "*" = all, "module.*" = all module permissions
#
# Fase B renamed the patient + appointment namespaces:
#  - ``clinical.patients.*``     → ``patients.*``
#  - ``clinical.appointments.*`` → ``agenda.appointments.*``
ROLE_PERMISSIONS: Final[dict[str, list[str]]] = {
    "admin": [
        "*",  # Admin gets everything, including future modules
    ],
    "dentist": [
        "patients.*",  # Full patient identity access
        "patients_clinical.*",  # Medical history + emergency contacts
        "patient_timeline.read",
        "agenda.*",  # Appointments + cabinets (read/write)
        "odontogram.*",
        "treatment_plan.*",
        "clinical_notes.*",
        "catalog.read",
        "budget.*",
        "billing.*",
        "media.*",
        "notifications.preferences.*",
        "notifications.send",
        "reports.billing.read",
        "reports.scheduling.read",
        "agents.view",
        "agents.supervise",
    ],
    "hygienist": [
        "patients.read",
        "patients_clinical.medical.read",
        "patients_clinical.emergency.read",
        "patient_timeline.read",
        "agenda.appointments.*",
        "agenda.cabinets.read",
        "odontogram.read",
        "odontogram.write",
        "treatment_plan.plans.read",
        "clinical_notes.notes.read",
        "clinical_notes.notes.write",
        "catalog.read",
        "budget.read",
        "billing.read",
        "media.documents.read",
        "reports.scheduling.read",
    ],
    "assistant": [
        "patients.*",
        "patients_clinical.medical.read",
        "patients_clinical.emergency.read",
        "patients_clinical.emergency.write",
        "patient_timeline.read",
        "agenda.appointments.*",
        "agenda.cabinets.read",
        "odontogram.read",
        "treatment_plan.plans.read",
        "treatment_plan.plans.write",
        "clinical_notes.notes.read",
        "clinical_notes.notes.write",
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
        "patients_clinical.emergency.read",
        "patients_clinical.emergency.write",
        "patient_timeline.read",
        "agenda.appointments.*",
        "agenda.cabinets.read",
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
        # Receptionists need administrative + diagnosis-followup notes for
        # the patient summary feed (e.g. "called complaining of tooth pain").
        "clinical_notes.notes.read",
        "clinical_notes.notes.write",
        # No odontogram access for receptionists
    ],
}


def get_role_permissions(role: str) -> list[str]:
    """Return the full list of granted permissions for ``role``.

    Merges two sources:

    1. The hardcoded core defaults in :data:`ROLE_PERMISSIONS` (core
       permissions + legacy in-tree modules that were never designed
       to be uninstalled).
    2. ``manifest.role_permissions`` from every discovered module.
       Entries are prefixed with ``{module_name}.`` — so a manifest
       declaring ``{"dentist": ["clinic_hours.read"]}`` contributes
       ``"<module>.clinic_hours.read"`` to the dentist role.

    This lets installable/uninstallable modules declare their RBAC
    entirely inside their own package. When such a module is
    uninstalled and the registry no longer discovers it, those
    permissions simply vanish — no edit to this file required.
    """
    base = list(ROLE_PERMISSIONS.get(role, []))
    seen = set(base)

    # Local import to avoid a circular dependency at module-load time:
    # the plugins registry imports auth models transitively.
    from app.core.plugins.manifest import ManifestError
    from app.core.plugins.registry import module_registry

    for module in module_registry.list_modules():
        try:
            manifest = module.get_manifest()
        except ManifestError:
            continue
        module_perms = manifest.role_permissions.get(role, ())
        for perm in module_perms:
            qualified = f"{module.name}.*" if perm == "*" else f"{module.name}.{perm}"
            if qualified not in seen:
                seen.add(qualified)
                base.append(qualified)
    return base


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
