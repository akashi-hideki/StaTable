# statable_gui/transition_editor_direct/draft.py
"""
動作編集用ドラフトモデル
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class ConditionBlock:
    """条件ブロック"""
    priority: int = 0
    condition_expr: str = ""    # 状態遷移条件式（例: "voltage > 800"）
    target: str = ""            # 遷移先
    action: str = ""            # アクション

    def to_dict(self) -> dict:
        return {
            'priority': self.priority,
            'condition_expr': self.condition_expr,
            'target': self.target,
            'action': self.action,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ConditionBlock':
        return cls(
            priority=data.get('priority', 0),
            condition_expr=data.get('condition_expr', ''),
            target=data.get('target', ''),
            action=data.get('action', ''),
        )


@dataclass
class ActionDraft:
    """動作編集用ドラフト"""

    source: str = ""
    event: str = ""

    # 前処理（ロール関数名）
    pre_actions: List[str] = field(default_factory=list)

    # 条件ブロック
    conditions: List[ConditionBlock] = field(default_factory=list)
    default_target: str = ""

    # 実行処理（ロール関数名）
    actions: List[str] = field(default_factory=list)

    # 後処理（ロール関数名）
    post_actions: List[str] = field(default_factory=list)

    def clear(self):
        self.pre_actions = []
        self.conditions = []
        self.default_target = ""
        self.actions = []
        self.post_actions = []

    def to_dict(self) -> dict:
        return {
            'source': self.source,
            'event': self.event,
            'pre_actions': self.pre_actions,
            'conditions': [c.to_dict() for c in self.conditions],
            'default_target': self.default_target,
            'actions': self.actions,
            'post_actions': self.post_actions,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ActionDraft':
        return cls(
            source=data.get('source', ''),
            event=data.get('event', ''),
            pre_actions=data.get('pre_actions', []),
            conditions=[ConditionBlock.from_dict(c) for c in data.get('conditions', [])],
            default_target=data.get('default_target', ''),
            actions=data.get('actions', []),
            post_actions=data.get('post_actions', []),
        )