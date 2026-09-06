# statable_gui/libcntrl/role_function_library.py
"""
共有ロール関数ライブラリ
"""

from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class RoleFunction:
    """共有ロール関数定義"""
    name: str                       # 一意な関数名
    description: str = ""
    title: str = ""                 # 表示名
    used_global_vars: List[str] = field(default_factory=list)  # 使用グローバル変数
    used_events: List[str] = field(default_factory=list)       # 使用イベント
    used_literals: List[str] = field(default_factory=list)     # 使用リテラル

    def __post_init__(self):
        if not self.title:
            self.title = self.name

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'description': self.description,
            'title': self.title,
            'used_global_vars': list(self.used_global_vars),
            'used_events': list(self.used_events),
            'used_literals': list(self.used_literals),
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'RoleFunction':
        return cls(
            name=data.get('name', ''),
            description=data.get('description', ''),
            title=data.get('title', ''),
            used_global_vars=list(data.get('used_global_vars', [])),
            used_events=list(data.get('used_events', [])),
            used_literals=list(data.get('used_literals', [])),
        )


class RoleFunctionLibrary:
    """プロジェクト全体で共有するロール関数ライブラリ"""

    def __init__(self):
        self.role_functions: Dict[str, RoleFunction] = {}

    def add(self, rf: RoleFunction):
        if rf.name in self.role_functions:
            raise ValueError(f"Role function '{rf.name}' already exists")
        self.role_functions[rf.name] = rf

    def remove(self, name: str):
        if name in self.role_functions:
            del self.role_functions[name]

    def get(self, name: str) -> RoleFunction:
        return self.role_functions.get(name)

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
            lib.add(rf)
        return lib