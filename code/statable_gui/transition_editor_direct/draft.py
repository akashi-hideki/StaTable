# statable_gui/transition_editor_direct/draft.py
"""
動作編集用ドラフトモデル（デバッグログ強化版・型安全化）
"""

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any

logger = logging.getLogger("transition_editor_direct.draft")


def ensure_list(value) -> List[str]:
    """値がリストでなければ空リストを返す（デバッグログ付き）"""
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        logger.error(f"Expected list but got string: '{value}'. Returning empty list.")
        return []
    if value is None:
        return []
    logger.warning(f"Unexpected type for list: {type(value)}. Returning empty list.")
    return []


@dataclass
class SystemGlobal:
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
    event: str = ""
    condition: str = ""
    pre_actions: List[str] = field(default_factory=list)
    target: str = ""
    has_else: bool = True
    else_target: str = ""
    else_actions: List[str] = field(default_factory=list)


@dataclass
class FlowItem:
    item_type: str = ""
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
    source: str = ""
    event: str = ""

    flow_items: List[FlowItem] = field(default_factory=list)
    default_target: str = ""

    system_globals: List[SystemGlobal] = field(default_factory=list)
    generated_code: str = ""

    role_func_map: Dict[str, str] = field(default_factory=dict)
    user_code: Dict[str, str] = field(default_factory=dict)

    def clear(self):
        self.flow_items = []
        self.default_target = ""
        self.system_globals = []
        self.generated_code = ""
        self.role_func_map = {}
        self.user_code = {}

    def get_role_func_name(self, base_name: str, phase: str) -> str:
        key = f"{self.source}|{self.event}|{phase}|{base_name}"
        if key not in self.role_func_map:
            func_name = f"RoleFunc_{base_name}_{self.source}_{self.event}_{phase}"
            self.role_func_map[key] = func_name
        return self.role_func_map[key]

    def to_dict(self) -> dict:
        return {
            'source': self.source,
            'event': self.event,
            'flow_items': [i.to_dict() for i in self.flow_items],
            'default_target': self.default_target,
            'system_globals': [g.to_dict() for g in self.system_globals],
            'generated_code': self.generated_code,
            'role_func_map': self.role_func_map,
            'user_code': self.user_code,
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
            role_func_map=data.get('role_func_map', {}),
            user_code=data.get('user_code', {}),
        )


def transition_to_flow_item(trans) -> FlowItem:
    """Transition → FlowItem (type=transition) 変換"""
    pre_actions = ensure_list(getattr(trans, 'pre_actions', []))
    else_actions = ensure_list(getattr(trans, 'else_actions', []))
    condition = getattr(trans, 'condition', '')
    if not isinstance(condition, str):
        logger.error(f"Condition is not str: {type(condition)}. Using empty string.")
        condition = ""

    logger.debug(f"transition_to_flow_item: condition='{condition}', pre_actions={pre_actions}, else_actions={else_actions}")

    return FlowItem(
        item_type="transition",
        name=trans.event or "完了",
        edited_text=trans.title if trans.title != "(無題遷移)" else trans.event or "完了",
        params={
            "event": trans.event,
            "condition": condition,
            "pre_actions": pre_actions,
            "target": trans.target,
            "has_else": getattr(trans, 'has_else', True),
            "else_target": getattr(trans, 'else_target', ''),
            "else_actions": else_actions,
        }
    )


def flow_item_to_transition(item: FlowItem, source: str, event: str):
    """FlowItem → Transition 変換"""
    from statable.model import Transition
    params = item.params
    pre_actions = ensure_list(params.get('pre_actions', []))
    else_actions = ensure_list(params.get('else_actions', []))
    condition = params.get('condition', '')
    if not isinstance(condition, str):
        logger.error(f"Condition is not str: {type(condition)}. Using empty string.")
        condition = ""

    logger.debug(f"flow_item_to_transition: condition='{condition}', pre_actions={pre_actions}, else_actions={else_actions}")

    return Transition(
        source=source,
        event=event,
        condition=condition,
        pre_actions=pre_actions,
        target=params.get('target', ''),
        has_else=params.get('has_else', True),
        else_target=params.get('else_target', ''),
        else_actions=else_actions,
        action="",
        transition_type="external",
        title=item.edited_text if item.edited_text and item.edited_text != item.name else "(無題遷移)",
    )