# codegen/validate/change_applier.py
"""
変更適用エンジン
"""

from typing import List, Dict, Tuple
from .logger import logger
from .change_actions import ChangeRequest, ChangeActionType


class ChangeApplier:
    """変更リクエストをシステムに適用する"""
    
    def __init__(self, sm, gd):
        logger.debug("ChangeApplier.__init__ started")
        self.sm = sm
        self.gd = gd
        self.applied_changes = []
        self.failed_changes = []
        logger.debug("ChangeApplier.__init__ completed")
    
    def apply(self, change: ChangeRequest) -> Tuple[bool, str]:
        """変更を適用"""
        logger.debug(f"apply: {change}")
        
        handler = self._get_handler(change.action)
        if handler is None:
            logger.warning(f"Unsupported action: {change.action.value}")
            return False, f"未対応のアクション: {change.action.value}"
        
        try:
            result = handler(change.params)
            if result[0]:
                self.applied_changes.append(change)
                logger.debug(f"Change applied: {change.action.value}")
            else:
                self.failed_changes.append((change, result[1]))
                logger.warning(f"Change failed: {result[1]}")
            return result
        except Exception as e:
            logger.error(f"Change threw exception: {e}", exc_info=True)
            self.failed_changes.append((change, str(e)))
            return False, str(e)
    
    def apply_all(self, changes: List[ChangeRequest]) -> Dict:
        """全変更を適用"""
        logger.debug(f"apply_all: {len(changes)} changes")
        
        results = []
        for change in changes:
            success, message = self.apply(change)
            results.append({
                'change': change,
                'success': success,
                'message': message,
            })
        
        summary = {
            'total': len(changes),
            'applied': len(self.applied_changes),
            'failed': len(self.failed_changes),
            'results': results,
        }
        
        logger.debug(f"apply_all completed: applied={summary['applied']}, failed={summary['failed']}")
        return summary
    
    def _get_handler(self, action: ChangeActionType):
        """アクションに対応するハンドラを取得"""
        handlers = {
            ChangeActionType.SET_INITIAL: self._set_initial,
            ChangeActionType.ADD_TRANSITION: self._add_transition,
            ChangeActionType.ADD_STATE: self._add_state,
            ChangeActionType.ADD_EVENT: self._add_event,
            ChangeActionType.REMOVE_TRANSITION: self._remove_transition,
            ChangeActionType.UPDATE_TRANSITION: self._update_transition,
            ChangeActionType.ADD_ROLE_FUNCTION: self._add_role_function,
            ChangeActionType.ADD_VARIABLE: self._add_variable,
            ChangeActionType.ADD_FLAG: self._add_flag,
        }
        return handlers.get(action)
    
    def _set_initial(self, params: Dict) -> Tuple[bool, str]:
        state = params.get('state', '')
        logger.debug(f"_set_initial: state={state}")
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
            return False, "遷移の情報が不足しています"
        
        condition = params.get('condition', '')
        action = params.get('action_name', '')
        
        transition = Transition(
            source=source, event=event, target=target,
            condition=condition, action=action
        )
        
        try:
            self.sm.add_transition(transition)
            return True, f"遷移「{source} --[{event}]--> {target}」を追加しました"
        except ValueError as e:
            return False, str(e)
    
    def _add_state(self, params: Dict) -> Tuple[bool, str]:
        from statable.model import State, StateType
        
        name = params.get('name', '')
        logger.debug(f"_add_state: name={name}")
        
        if not name:
            return False, "状態名が指定されていません"
        if name in self.sm.states:
            return False, f"状態「{name}」は既に存在します"
        
        state_type_str = params.get('type', 'NORMAL')
        state_type = getattr(StateType, state_type_str, StateType.NORMAL)
        description = params.get('description', '')
        
        self.sm.add_state(State(name=name, type=state_type, description=description))
        return True, f"状態「{name}」を追加しました"
    
    def _add_event(self, params: Dict) -> Tuple[bool, str]:
        from statable.model import Event, EventKind
        
        name = params.get('name', '')
        logger.debug(f"_add_event: name={name}")
        
        if not name:
            return False, "イベント名が指定されていません"
        if name in self.sm.events:
            return False, f"イベント「{name}」は既に存在します"
        
        kind_str = params.get('kind', 'SIGNAL')
        kind = getattr(EventKind, kind_str, EventKind.SIGNAL)
        description = params.get('description', '')
        
        self.sm.add_event(Event(name=name, kind=kind, description=description))
        return True, f"イベント「{name}」を追加しました"
    
    def _remove_transition(self, params: Dict) -> Tuple[bool, str]:
        source = params.get('source', '')
        event = params.get('event', '')
        target = params.get('target', '')
        logger.debug(f"_remove_transition: {source} --[{event}]--> {target}")
        
        for t in self.sm.transitions:
            if t.source == source and t.event == event and t.target == target:
                self.sm.remove_transition(t)
                return True, f"遷移「{source} --[{event}]--> {target}」を削除しました"
        
        return False, "該当する遷移が見つかりません"
    
    def _update_transition(self, params: Dict) -> Tuple[bool, str]:
        source = params.get('source', '')
        event = params.get('event', '')
        logger.debug(f"_update_transition: {source} --[{event}]-->")
        
        for t in self.sm.transitions:
            if t.source == source and t.event == event:
                if 'new_target' in params:
                    t.target = params['new_target']
                if 'new_condition' in params:
                    t.condition = params['new_condition']
                if 'new_action' in params:
                    t.action = params['new_action']
                return True, f"遷移「{source} --[{event}]-->」を更新しました"
        
        return False, "該当する遷移が見つかりません"
    
    def _add_role_function(self, params: Dict) -> Tuple[bool, str]:
        from statable.model import RoleFunction
        
        name = params.get('name', '')
        logger.debug(f"_add_role_function: name={name}")
        
        if not name:
            return False, "関数名が指定されていません"
        if name in self.sm.role_functions:
            return False, f"関数「{name}」は既に存在します"
        
        return_type = params.get('return_type', 'void')
        description = params.get('description', '')
        
        rf = RoleFunction(name=name, return_type=return_type, description=description)
        self.sm.add_role_function(rf)
        return True, f"ロール関数「{name}」を追加しました"
    
    def _add_variable(self, params: Dict) -> Tuple[bool, str]:
        from statable.global_defs import SystemVariable
        
        name = params.get('name', '')
        var_type = params.get('type', 'uint8')
        group = params.get('group', '')
        description = params.get('description', '')
        logger.debug(f"_add_variable: name={name}, type={var_type}")
        
        var = SystemVariable(name=name, type=var_type, group=group, description=description)
        self.gd.variables.append(var)
        return True, f"変数「{name}」を追加しました"
    
    def _add_flag(self, params: Dict) -> Tuple[bool, str]:
        from statable.global_defs import EventFlag
        
        name = params.get('name', '')
        min_value = params.get('min_value', 0)
        max_value = params.get('max_value', 1)
        group = params.get('group', '')
        logger.debug(f"_add_flag: name={name}")
        
        flag = EventFlag(name=name, min_value=min_value, max_value=max_value, group=group)
        self.gd.flags.append(flag)
        return True, f"フラグ「{name}」を追加しました"