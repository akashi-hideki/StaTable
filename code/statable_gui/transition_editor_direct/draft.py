# statable_gui/transition_editor_direct/draft.py
"""
動作編集用ドラフトモデル（else条件自動表示対応）
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class SystemGlobal:
    """システムグローバル変数"""
    name: str
    type: str = "uint16_t"
    initial_value: str = "0"
    description: str = ""

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'type': self.type,
            'initial_value': self.initial_value,
            'description': self.description,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'SystemGlobal':
        return cls(
            name=data.get('name', ''),
            type=data.get('type', 'uint16_t'),
            initial_value=data.get('initial_value', '0'),
            description=data.get('description', ''),
        )


@dataclass
class TransitionParams:
    """状態遷移イベントのパラメータ（else条件対応）"""
    event: str = ""
    condition: str = ""
    pre_actions: List[str] = field(default_factory=list)
    target: str = ""
    has_else: bool = True          # else条件を表示するか
    else_target: str = ""          # else条件の遷移先
    else_actions: List[str] = field(default_factory=list)


@dataclass
class FlowItem:
    """動作フローの1項目"""
    item_type: str = ""          # "function" / "transition"
    name: str = ""
    edited_text: str = ""
    params: Dict[str, Any] = field(default_factory=dict)

    def display_text(self) -> str:
        return self.edited_text or self.name

    def to_dict(self) -> dict:
        return {
            'item_type': self.item_type,
            'name': self.name,
            'edited_text': self.edited_text,
            'params': self.params,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'FlowItem':
        return cls(
            item_type=data.get('item_type', ''),
            name=data.get('name', ''),
            edited_text=data.get('edited_text', ''),
            params=data.get('params', {}),
        )


@dataclass
class ActionDraft:
    """動作編集用ドラフト"""
    source: str = ""
    event: str = ""

    flow_items: List[FlowItem] = field(default_factory=list)
    default_target: str = ""

    system_globals: List[SystemGlobal] = field(default_factory=list)
    generated_code: str = ""

    def clear(self):
        self.flow_items = []
        self.default_target = ""
        self.system_globals = []
        self.generated_code = ""

    def to_dict(self) -> dict:
        return {
            'source': self.source,
            'event': self.event,
            'flow_items': [i.to_dict() for i in self.flow_items],
            'default_target': self.default_target,
            'system_globals': [g.to_dict() for g in self.system_globals],
            'generated_code': self.generated_code,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ActionDraft':
        return cls(
            source=data.get('source', ''),
            event=data.get('event', ''),
            flow_items=[FlowItem.from_dict(i) for i in data.get('flow_items', [])],
            default_target=data.get('default_target', ''),
            system_globals=[SystemGlobal.from_dict(g) for g in data.get('system_globals', [])],
            generated_code=data.get('generated_code', ''),
        )