# codegen/validate/change_actions.py
"""
Change action definitions.

[v2.2 §12-6 change]
  - Added 7 cell-level AI action types:
      ADD_CELL / REMOVE_CELL
      ADD_ACTION_STEP / REMOVE_ACTION_STEP
      ADD_TRANSITION_RELATION / REMOVE_TRANSITION_RELATION
      SET_EARLY_RETURN
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, List


class ChangeActionType(Enum):
    """Change action kind"""
    # --------------------------------------------------------------
    # Legacy actions
    # --------------------------------------------------------------
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

    # --------------------------------------------------------------
    # v2.2 §12-6: Cell-level AI action extensions
    # --------------------------------------------------------------
    ADD_CELL = "add_cell"
    REMOVE_CELL = "remove_cell"
    ADD_ACTION_STEP = "add_action_step"
    REMOVE_ACTION_STEP = "remove_action_step"
    ADD_TRANSITION_RELATION = "add_transition_relation"
    REMOVE_TRANSITION_RELATION = "remove_transition_relation"
    SET_EARLY_RETURN = "set_early_return"


@dataclass
class ChangeRequest:
    """Change request"""
    action: ChangeActionType
    params: Dict[str, Any] = field(default_factory=dict)
    reason: str = ""
    source: str = "ai"
    # [v2.8.0 Phase B] extended fields
    id: str = ""
    evidence: List[str] = field(default_factory=list)
    priority: str = "medium"
    confidence: float = 1.0

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'action': self.action.value,
            'params': self.params,
            'reason': self.reason,
            'source': self.source,
            'evidence': list(self.evidence),
            'priority': self.priority,
            'confidence': self.confidence,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'ChangeRequest':
        try:
            confidence = float(data.get('confidence', 1.0))
        except (TypeError, ValueError):
            confidence = 1.0
        return cls(
            action=ChangeActionType(data['action']),
            params=data.get('params', {}),
            reason=data.get('reason', ''),
            source=data.get('source', 'ai'),
            id=str(data.get('id', '') or ''),
            evidence=list(data.get('evidence', []) or []),
            priority=str(data.get('priority', 'medium') or 'medium'),
            confidence=confidence,
        )

    def __str__(self) -> str:
        return (f"ChangeRequest(action={self.action.value}, "
                f"params={self.params}, reason={self.reason})")