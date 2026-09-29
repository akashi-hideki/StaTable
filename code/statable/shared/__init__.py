# statable/shared/__init__.py
"""
Shared project libraries.

These modules have no PySide6 dependency and can be used from the SDK
without installing the GUI extras (statable[gui]).

[v3.0 / G-1a]
  Moved from statable_gui.libcntrl to allow SDK-only installs.
  Backward-compat shims remain at statable_gui.libcntrl.* for a while.
"""

from .role_function_library import RoleFunctionLibrary, RoleFunction
from .condition_library import ConditionLibrary, ConditionTemplate
from .literal_library import LiteralLibrary, LiteralDefinition

__all__ = [
    "RoleFunctionLibrary",
    "RoleFunction",
    "ConditionLibrary",
    "ConditionTemplate",
    "LiteralLibrary",
    "LiteralDefinition",
]
