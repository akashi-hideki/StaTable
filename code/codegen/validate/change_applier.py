# codegen/validate/change_applier.py
"""
Change apply engine (fixed version)

[v1.6 change]
  - Added 'remove_role_function' to _handlers (resolved mismatch with ChangeActionType)
  - Implemented _remove_role_function method
"""

import sys
import os
from typing import List, Dict, Tuple

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from validate.logger import logger
from validate.change_actions import ChangeRequest, ChangeActionType


class ChangeApplier:
    """Apply change requests to system"""

    def __init__(self, sm, gd):
        logger.debug("ChangeApplier.__init__ started")
        self.sm = sm
        self.gd = gd
        self.applied_changes = []
        self.failed_changes = []
        # Define handler dict by string key
        self._handlers = {
            'set_initial': self._set_initial,
            'add_transition': self._add_transition,
            'add_state': self._add_state,
            'add_event': self._add_event,
            'remove_transition': self._remove_transition,
            'update_transition': self._update_transition,
            'add_role_function': self._add_role_function,
            'remove_role_function': self._remove_role_function,   # v1.6 added
            'add_variable': self._add_variable,
            'add_flag': self._add_flag,
        }
        logger.debug("ChangeApplier.__init__ completed")

    def apply(self, change: ChangeRequest) -> Tuple[bool, str]:
        """Apply change"""
        logger.debug(f"apply: action={change.action}")

        # Get handler by ChangeActionType value
        action_value = change.action.value if hasattr(change.action, 'value') else str(change.action)
        logger.debug(f"action_value: {action_value}")

        handler = self._handlers.get(action_value)
        if handler is None:
            logger.warning(f"Unsupported action: {action_value}")
            return False, f"未対応のアクション: {action_value}"

        try:
            result = handler(change.params)
            if result[0]:
                self.applied_changes.append(change)
                logger.debug(f"Change applied: {action_value}")
            else:
                self.failed_changes.append((change, result[1]))
                logger.warning(f"Change failed: {result[1]}")
            return result
        except Exception as e:
            logger.error(f"Change threw exception: {e}", exc_info=True)
            self.failed_changes.append((change, str(e)))
            return False, str(e)

    def apply_all(self, changes: List[ChangeRequest]) -> Dict:
        """Apply all changes"""
        logger.debug(f"apply_all: {len(changes)} changes")

        results = []
        for change in changes:
            success, message = self.apply(change)
            results.append({'change': change, 'success': success, 'message': message})

        summary = {
            'total': len(changes),
            'applied': len(self.applied_changes),
            'failed': len(self.failed_changes),
            'results': results,
        }

        logger.debug(f"apply_all completed: applied={summary['applied']}, failed={summary['failed']}")
        return summary

    def _set_initial(self, params: Dict) -> Tuple[bool, str]:
        state = params.get('state', '')
        logger.debug(f"_set_initial: state={state}, available={list(self.sm.states.keys())}")
        if state not in self.sm.states:
            return False, f"状態「{state}」が存在しません"
        self.sm.set_initial(state)
        return True, f"初期状態を「{state}」に設定しました"

    def _add_transition(self, params: Dict) -> Tuple[bool, str]:
        from statable.model import Transition

        source = params.get('source', '')
        event = params.get('event', '')
        target = params.get('target', '')
        logger.debug(f"_add_transition: {source} --[{event}]--> {target}")

        if not all([source, event, target]):
            return False, "Transition information is incomplete"

        transition = Transition(
            source=source, event=event, target=target,
            condition=params.get('condition', ''),
            action=params.get('action_name', '')
        )

        try:
            self.sm.add_transition(transition)
            return True, f"遷移「{source} --[{event}]--> {target}」を追加しました"
        except ValueError as e:
            return False, str(e)

    def _add_state(self, params: Dict) -> Tuple[bool, str]:
        from statable.model import State, StateType

        name = params.get('name', '')
        if not name:
            return False, "State name is not specified"
        if name in self.sm.states:
            return False, f"状態「{name}」は既に存在します"

        # v1.6: fall back to NORMAL
        type_name = params.get('type', 'NORMAL')
        state_type = getattr(StateType, type_name, StateType.NORMAL)
        if not hasattr(StateType, type_name):
            logger.warning(
                f"_add_state: unknown type '{type_name}' -> NORMAL fallback"
            )

        # v1.6: accept parent parameter (for REGION / CONCURRENT)
        parent = params.get('parent', None) or None

        self.sm.add_state(State(
            name=name,
            type=state_type,
            parent=parent,
            description=params.get('description', ''),
        ))
        return True, f"状態「{name}」を追加しました (type={state_type.name})"

    def _add_event(self, params: Dict) -> Tuple[bool, str]:
        from statable.model import Event, EventKind

        name = params.get('name', '')
        if not name:
            return False, "Event name is not specified"
        if name in self.sm.events:
            return False, f"イベント「{name}」は既に存在します"

        kind = getattr(EventKind, params.get('kind', 'SIGNAL'), EventKind.SIGNAL)
        self.sm.add_event(Event(name=name, kind=kind, description=params.get('description', '')))
        return True, f"イベント「{name}」を追加しました"

    def _remove_transition(self, params: Dict) -> Tuple[bool, str]:
        source = params.get('source', '')
        event = params.get('event', '')
        target = params.get('target', '')

        for t in self.sm.transitions:
            if t.source == source and t.event == event and t.target == target:
                self.sm.remove_transition(t)
                return True, f"遷移「{source} --[{event}]--> {target}」を削除しました"

        return False, "No matching transition found"

    def _update_transition(self, params: Dict) -> Tuple[bool, str]:
        source = params.get('source', '')
        event = params.get('event', '')

        for t in self.sm.transitions:
            if t.source == source and t.event == event:
                if 'new_target' in params:
                    t.target = params['new_target']
                if 'new_condition' in params:
                    t.condition = params['new_condition']
                if 'new_action' in params:
                    t.action = params['new_action']
                return True, f"遷移「{source} --[{event}]-->」を更新しました"

        return False, "No matching transition found"

    def _add_role_function(self, params: Dict) -> Tuple[bool, str]:
        from statable.model import RoleFunction

        name = params.get('name', '')
        if not name:
            return False, "Function name is not specified"
        if name in self.sm.role_functions:
            return False, f"関数「{name}」は既に存在します"

        rf = RoleFunction(
            name=name,
            namespace=params.get('namespace', ''),
            return_type=params.get('return_type', 'void'),
            description=params.get('description', ''),
        )
        self.sm.add_role_function(rf)
        return True, f"ロール関数「{name}」を追加しました"

    def _remove_role_function(self, params: Dict) -> Tuple[bool, str]:
        """
        Remove a role function.

        Added in v1.6. Corresponds to ChangeActionType.REMOVE_ROLE_FUNCTION.
        params:
          name: 'HandleErr' or 'Middleware.HandleErr' (either is acceptable)
        """
        name = params.get('name', '')
        if not name:
            return False, "Function name is not specified"

        logger.debug(
            f"_remove_role_function: name='{name}', "
            f"available={list(self.sm.role_functions.keys())}"
        )

        # Exact match
        if name in self.sm.role_functions:
            self.sm.remove_role_function(name)
            return True, f"ロール関数「{name}」を削除しました"

        # Match by qualified_name
        for key, rf in list(self.sm.role_functions.items()):
            qn = getattr(rf, 'qualified_name', None) or key
            if qn == name:
                self.sm.remove_role_function(key)
                return True, f"ロール関数「{name}」を削除しました"

        # Match by bare name
        for key, rf in list(self.sm.role_functions.items()):
            if getattr(rf, 'name', '') == name:
                self.sm.remove_role_function(key)
                return True, f"ロール関数「{name}」を削除しました"

        return False, f"関数「{name}」が見つかりません"

    def _add_variable(self, params: Dict) -> Tuple[bool, str]:
        from statable.global_defs import SystemVariable

        name = params.get('name', '')
        var = SystemVariable(name=name, type=params.get('type', 'uint8'),
                            group=params.get('group', ''), description=params.get('description', ''))
        self.gd.variables.append(var)
        return True, f"変数「{name}」を追加しました"

    def _add_flag(self, params: Dict) -> Tuple[bool, str]:
        from statable.global_defs import EventFlag

        name = params.get('name', '')
        flag = EventFlag(name=name, min_value=params.get('min_value', 0),
                        max_value=params.get('max_value', 1), group=params.get('group', ''))
        self.gd.flags.append(flag)
        return True, f"フラグ「{name}」を追加しました"