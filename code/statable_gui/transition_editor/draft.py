# statable_gui/transition_editor/draft.py
"""
遷移編集用ドラフトモデル
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class ConditionEntry:
    """条件エントリ"""
    priority: int = 0
    condition: str = ""
    target: str = ""
    action: str = ""

    def to_dict(self) -> dict:
        return {
            'priority': self.priority,
            'condition': self.condition,
            'target': self.target,
            'action': self.action,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ConditionEntry':
        return cls(
            priority=data.get('priority', 0),
            condition=data.get('condition', ''),
            target=data.get('target', ''),
            action=data.get('action', ''),
        )


@dataclass
class ActionEntry:
    """アクションエントリ"""
    order: int = 0
    action: str = ""
    description: str = ""

    def to_dict(self) -> dict:
        return {
            'order': self.order,
            'action': self.action,
            'description': self.description,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ActionEntry':
        return cls(
            order=data.get('order', 0),
            action=data.get('action', ''),
            description=data.get('description', ''),
        )


@dataclass
class TransitionDraft:
    """遷移編集用ドラフト"""

    source: str = ""
    event: str = ""
    title: str = ""
    description: str = ""

    use_pre_action: bool = False
    pre_action: str = ""
    pre_result_var: str = ""

    conditions: List[ConditionEntry] = field(default_factory=list)
    use_default_condition: bool = True
    default_target: str = ""
    default_action: str = ""

    actions: List[ActionEntry] = field(default_factory=list)

    use_post_action: bool = False
    post_action: str = ""
    use_fallback: bool = False
    fallback_action: str = ""

    # 付帯条件（遷移ガード）
    use_transition_guard: bool = False
    transition_guard: str = ""
    guard_success_target: str = ""
    guard_fail_mode: str = "stay"       # "stay" or "target"
    guard_fail_target: str = ""
    guard_fail_action: str = ""

    def clear(self):
        """全フィールドをクリア"""
        self.title = ""
        self.description = ""
        self.use_pre_action = False
        self.pre_action = ""
        self.pre_result_var = ""
        self.conditions = []
        self.use_default_condition = True
        self.default_target = ""
        self.default_action = ""
        self.actions = []
        self.use_post_action = False
        self.post_action = ""
        self.use_fallback = False
        self.fallback_action = ""
        self.use_transition_guard = False
        self.transition_guard = ""
        self.guard_success_target = ""
        self.guard_fail_mode = "stay"
        self.guard_fail_target = ""
        self.guard_fail_action = ""

    def is_empty(self) -> bool:
        return (
            not self.title
            and not self.use_pre_action
            and not self.conditions
            and not self.actions
            and not self.use_post_action
            and not self.use_fallback
            and not self.use_transition_guard
        )

    def to_dict(self) -> dict:
        return {
            'source': self.source,
            'event': self.event,
            'title': self.title,
            'description': self.description,
            'use_pre_action': self.use_pre_action,
            'pre_action': self.pre_action,
            'pre_result_var': self.pre_result_var,
            'conditions': [c.to_dict() for c in self.conditions],
            'use_default_condition': self.use_default_condition,
            'default_target': self.default_target,
            'default_action': self.default_action,
            'actions': [a.to_dict() for a in self.actions],
            'use_post_action': self.use_post_action,
            'post_action': self.post_action,
            'use_fallback': self.use_fallback,
            'fallback_action': self.fallback_action,
            'use_transition_guard': self.use_transition_guard,
            'transition_guard': self.transition_guard,
            'guard_success_target': self.guard_success_target,
            'guard_fail_mode': self.guard_fail_mode,
            'guard_fail_target': self.guard_fail_target,
            'guard_fail_action': self.guard_fail_action,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'TransitionDraft':
        return cls(
            source=data.get('source', ''),
            event=data.get('event', ''),
            title=data.get('title', ''),
            description=data.get('description', ''),
            use_pre_action=data.get('use_pre_action', False),
            pre_action=data.get('pre_action', ''),
            pre_result_var=data.get('pre_result_var', ''),
            conditions=[ConditionEntry.from_dict(c) for c in data.get('conditions', [])],
            use_default_condition=data.get('use_default_condition', True),
            default_target=data.get('default_target', ''),
            default_action=data.get('default_action', ''),
            actions=[ActionEntry.from_dict(a) for a in data.get('actions', [])],
            use_post_action=data.get('use_post_action', False),
            post_action=data.get('post_action', ''),
            use_fallback=data.get('use_fallback', False),
            fallback_action=data.get('fallback_action', ''),
            use_transition_guard=data.get('use_transition_guard', False),
            transition_guard=data.get('transition_guard', ''),
            guard_success_target=data.get('guard_success_target', ''),
            guard_fail_mode=data.get('guard_fail_mode', 'stay'),
            guard_fail_target=data.get('guard_fail_target', ''),
            guard_fail_action=data.get('guard_fail_action', ''),
        )