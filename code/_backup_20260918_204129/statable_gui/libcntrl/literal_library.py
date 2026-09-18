# statable_gui/libcntrl/literal_library.py
"""
共有リテラルライブラリ
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class LiteralDefinition:
    """共有リテラル定義"""
    name: str               # 一意なリテラル名
    value: str              # 値
    literal_type: str = "int"  # int / float / string / bool
    description: str = ""

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'value': self.value,
            'literal_type': self.literal_type,
            'description': self.description,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'LiteralDefinition':
        return cls(
            name=data.get('name', ''),
            value=data.get('value', ''),
            literal_type=data.get('literal_type', 'int'),
            description=data.get('description', ''),
        )


class LiteralLibrary:
    """プロジェクト全体で共有するリテラルライブラリ"""

    def __init__(self):
        self.literals: Dict[str, LiteralDefinition] = {}

    def add(self, lit: LiteralDefinition):
        if lit.name in self.literals:
            raise ValueError(f"Literal '{lit.name}' already exists")
        self.literals[lit.name] = lit

    def remove(self, name: str):
        if name in self.literals:
            del self.literals[name]

    def get(self, name: str) -> LiteralDefinition:
        return self.literals.get(name)

    def list_all(self) -> List[LiteralDefinition]:
        return list(self.literals.values())

    def to_dict(self) -> dict:
        return {
            'literals': [lit.to_dict() for lit in self.literals.values()]
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'LiteralLibrary':
        lib = cls()
        for item in data.get('literals', []):
            lit = LiteralDefinition.from_dict(item)
            lib.add(lit)
        return lib