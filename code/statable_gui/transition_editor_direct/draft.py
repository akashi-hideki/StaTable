# statable_gui/transition_editor_direct/draft.py
"""
動作編集用ドラフトモデル（材料編集方式）
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class FlowItem:
    """動作フローの1項目（材料）"""

    item_type: str = ""         # "function" / "condition" / "variable" / "flag"
    name: str = ""              # 元の名前（パレットからドラッグしたもの）
    edited_text: str = ""       # 編集後のテキスト
    params: Dict[str, Any] = field(default_factory=dict)  # 編集された内容

    def display_text(self) -> str:
        """リストに表示するテキスト"""
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

    # 動作フロー（すべての項目を1つのリストで管理）
    flow_items: List[FlowItem] = field(default_factory=list)

    # デフォルト遷移先
    default_target: str = ""

    def clear(self):
        """全クリア"""
        self.flow_items = []
        self.default_target = ""

    def get_display_lines(self) -> List[str]:
        """表示用テキストを取得"""
        lines = []
        for i, item in enumerate(self.flow_items, 1):
            lines.append(f"{i}. {item.display_text()}")
        if not self.flow_items:
            lines.append("(空)")
        return lines

    def to_dict(self) -> dict:
        return {
            'source': self.source,
            'event': self.event,
            'flow_items': [i.to_dict() for i in self.flow_items],
            'default_target': self.default_target,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ActionDraft':
        return cls(
            source=data.get('source', ''),
            event=data.get('event', ''),
            flow_items=[FlowItem.from_dict(i) for i in data.get('flow_items', [])],
            default_target=data.get('default_target', ''),
        )