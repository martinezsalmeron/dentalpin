"""Module lifecycle states."""

from enum import StrEnum


class ModuleState(StrEnum):
    """Lifecycle states for modules tracked in `core_module`."""

    UNINSTALLED = "uninstalled"
    TO_INSTALL = "to_install"
    INSTALLED = "installed"
    TO_UPGRADE = "to_upgrade"
    TO_REMOVE = "to_remove"
    DISABLED = "disabled"


class ModuleCategory(StrEnum):
    """Trust tier declared by the module."""

    OFFICIAL = "official"
    COMMUNITY = "community"


TRANSIENT_STATES = frozenset(
    {
        ModuleState.TO_INSTALL,
        ModuleState.TO_UPGRADE,
        ModuleState.TO_REMOVE,
    }
)
