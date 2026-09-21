# statable_gui/libcntrl/role_function_library.py
"""
Shared role function library

Version History
---------------
v1.0  - Initial shared library.
v1.5  - Added reserved signature fields
        (return_type / arg1_type / arg1_name / arg2_type / arg2_name).
        These are not used by the code generator (its C signature is
        fixed), and they are not exposed in the GUI. They are kept
        here only so that XML I/O round-trips old project files
        (tests/data/v22_features_test3.xml) without canonical
        differences. See xml_io.py v3.8.2.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class RoleFunction:
    """Shared role function definition.

    namespace: layer name / feature group name (e.g., "Driver")
      - Referenceable as `Driver.Init`
      - Empty string means no layer

    [v1.5]
      Reserved signature fields are present but not used:
        * return_type / arg1_type / arg1_name / arg2_type / arg2_name
      Their only purpose is XML round-trip preservation.
    """
    name: str
    namespace: str = ""
    description: str = ""
    title: str = ""
    # [v1.5] Reserved signature fields (not exposed in GUI,
    #        not consumed by codegen; preserved for XML round-trip).
    return_type: str = ""
    arg1_type: str = ""
    arg1_name: str = ""
    arg2_type: str = ""
    arg2_name: str = ""
    # [v1.4] GUI symbol tracking
    used_global_vars: List[str] = field(default_factory=list)
    used_events: List[str] = field(default_factory=list)
    used_literals: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.title:
            self.title = self.qualified_name

    @property
    def qualified_name(self) -> str:
        """GUI display name: 'Driver.Init' or 'Init'"""
        if self.namespace:
            return f"{self.namespace}.{self.name}"
        return self.name

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'namespace': self.namespace,
            'description': self.description,
            'title': self.title,
            # [v1.5] Reserved signature fields
            'return_type': self.return_type,
            'arg1_type': self.arg1_type,
            'arg1_name': self.arg1_name,
            'arg2_type': self.arg2_type,
            'arg2_name': self.arg2_name,
            # [v1.4] symbol references
            'used_global_vars': list(self.used_global_vars),
            'used_events': list(self.used_events),
            'used_literals': list(self.used_literals),
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'RoleFunction':
        return cls(
            name=data.get('name', ''),
            namespace=data.get('namespace', ''),
            description=data.get('description', ''),
            title=data.get('title', ''),
            return_type=data.get('return_type', ''),
            arg1_type=data.get('arg1_type', ''),
            arg1_name=data.get('arg1_name', ''),
            arg2_type=data.get('arg2_type', ''),
            arg2_name=data.get('arg2_name', ''),
            used_global_vars=list(data.get('used_global_vars', [])),
            used_events=list(data.get('used_events', [])),
            used_literals=list(data.get('used_literals', [])),
        )


class RoleFunctionLibrary:
    """Role function library shared across the project"""

    def __init__(self):
        self.role_functions: Dict[str, RoleFunction] = {}

    def _key(self, rf: RoleFunction) -> str:
        """Unique key in the library: 'Driver.Init'"""
        return rf.qualified_name

    def add(self, rf: RoleFunction):
        key = self._key(rf)
        if key in self.role_functions:
            raise ValueError(f"Role function '{key}' already exists")
        self.role_functions[key] = rf

    def remove(self, name: str):
        """name can be either qualified_name or a bare name"""
        if name in self.role_functions:
            del self.role_functions[name]
            return
        # Search by bare name
        for key, rf in list(self.role_functions.items()):
            if rf.name == name:
                del self.role_functions[key]
                return

    def get(self, name: str) -> Optional[RoleFunction]:
        """name can be either qualified_name or a bare name"""
        if name in self.role_functions:
            return self.role_functions[name]
        for rf in self.role_functions.values():
            if rf.name == name:
                return rf
        return None

    def list_all(self) -> List[RoleFunction]:
        return list(self.role_functions.values())

    def to_dict(self) -> dict:
        return {
            'role_functions': [rf.to_dict() for rf in self.role_functions.values()]
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'RoleFunctionLibrary':
        lib = cls()
        for item in data.get('role_functions', []):
            rf = RoleFunction.from_dict(item)
            try:
                lib.add(rf)
            except ValueError:
                pass  # Duplicates ignored
        return lib