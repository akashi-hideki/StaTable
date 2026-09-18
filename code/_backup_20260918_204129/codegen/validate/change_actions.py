# codegen/validate/change_actions.py
"""
変更Action定義
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any


class ChangeActionType(Enum):
    """変更Action種別"""
    SET_INITIAL = "set_initial"
    ADD_TRANSITION = "add_transition"
    ADD_STATE = "add_state"
    ADD_EVENT = "add_event"
    REMOVE_TRANSITION = "remove_transition"
    UPDATE_TRANSITION = "update_transition"
    ADD_ROLE_FUNCTION = "add_role_function"
    REMOVE_ROLE_FUNCTION = "remove_role_function"
    ADD_VARIABLE = "add_variable"
    ADD_FLAG = "add_flag"


@dataclass
class ChangeRequest:
    """変更リクエスト"""
    action: ChangeActionType
    params: Dict[str, Any] = field(default_factory=dict)
    reason: str = ""
    source: str = "ai"
    
    def to_dict(self) -> Dict:
        return {
            'action': self.action.value,
            'params': self.params,
            'reason': self.reason,
            'source': self.source,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ChangeRequest':
        return cls(
            action=ChangeActionType(data['action']),
            params=data.get('params', {}),
            reason=data.get('reason', ''),
            source=data.get('source', 'ai'),
        )
    
    def __str__(self) -> str:
        return f"ChangeRequest(action={self.action.value}, params={self.params}, reason={self.reason})"