# statable_gui/libcntrl/condition_library.py
"""\nShared transition condition library\n"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class ConditionTemplate:
    """Shared transition condition template"""
    name: str           # Template name
    condition: str      # Condition expression (including literals)
    description: str = ""

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'condition': self.condition,
            'description': self.description,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ConditionTemplate':
        return cls(
            name=data.get('name', ''),
            condition=data.get('condition', ''),
            description=data.get('description', ''),
        )


class ConditionLibrary:
    """Transition condition library shared"""

    def __init__(self):
        self.condition_templates: Dict[str, ConditionTemplate] = {}

    def add(self, ct: ConditionTemplate):
        if ct.name in self.condition_templates:
            raise ValueError(f"Condition template '{ct.name}' already exists")
        self.condition_templates[ct.name] = ct

    def remove(self, name: str):
        if name in self.condition_templates:
            del self.condition_templates[name]

    def get(self, name: str) -> ConditionTemplate:
        return self.condition_templates.get(name)

    def list_all(self) -> List[ConditionTemplate]:
        return list(self.condition_templates.values())

    def to_dict(self) -> dict:
        return {
            'condition_templates': [ct.to_dict() for ct in self.condition_templates.values()]
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ConditionLibrary':
        lib = cls()
        for item in data.get('condition_templates', []):
            ct = ConditionTemplate.from_dict(item)
            lib.add(ct)
        return lib