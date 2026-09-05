# statable_gui/transition_editor_direct/draft.py
"""
動作編集用ドラフトモデル
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class TransitionParams:
    """状態遷移イベントのパラメータ"""
    event: str = ""
    condition: str = ""
    pre_actions: List[str] = field(default_factory=list)
    target: str = ""


@dataclass
class FlowItem:
    """動作フローの1項目"""
    item_type: str = ""          # "function" / "transition"
    name: str = ""               # 表示名
    edited_text: str = ""        # 編集後の表示テキスト
    params: Dict[str, Any] = field(default_factory=dict)

    def display_text(self) -> str:
        if self.edited_text:
            return self.edited_text
        return self.name

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
    generated_code: str = ""   # 読み取り専用コード

    def clear(self):
        self.flow_items = []
        self.default_target = ""
        self.generated_code = ""

    def to_dict(self) -> dict:
        return {
            'source': self.source,
            'event': self.event,
            'flow_items': [i.to_dict() for i in self.flow_items],
            'default_target': self.default_target,
            'generated_code': self.generated_code,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ActionDraft':
        return cls(
            source=data.get('source', ''),
            event=data.get('event', ''),
            flow_items=[FlowItem.from_dict(i) for i in data.get('flow_items', [])],
            default_target=data.get('default_target', ''),
            generated_code=data.get('generated_code', ''),
        )