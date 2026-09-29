"""[v3.0 / G-1a] Backward-compat shim.

Content moved to: statable.shared.role_function_library

Old imports under ``statable_gui.libcntrl`` keep working via re-export.
New code should import from ``statable.shared`` instead.
"""
from statable.shared.role_function_library import (  # noqa: F401
    RoleFunction,
    RoleFunctionLibrary,
)

__all__ = ["RoleFunction", "RoleFunctionLibrary"]
