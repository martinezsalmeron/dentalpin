"""Module plugin system public API."""

from .base import BaseModule
from .context import ModuleContext
from .loader import load_modules
from .manifest import Manifest, ManifestError
from .registry import module_registry
from .service import DoctorReport, ModuleInfo, ModuleOperationError, ModuleService
from .state import ModuleCategory, ModuleState

__all__ = [
    "BaseModule",
    "DoctorReport",
    "Manifest",
    "ManifestError",
    "ModuleCategory",
    "ModuleContext",
    "ModuleInfo",
    "ModuleOperationError",
    "ModuleService",
    "ModuleState",
    "load_modules",
    "module_registry",
]
