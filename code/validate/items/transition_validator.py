# codegen/validate/items/transition_validator.py
"""
遷移検証
"""

from typing import List
from ..models import ValidationIssue, ValidationSeverity, ValidationContext
from .base_validator import BaseValidator


class TransitionValidator(BaseValidator):
    """遷移検証クラス"""
    
    category = "transition"
    
    def __init__(self):
        self.rules = {
            'TRANSITION_TARGET_UNDEFINED': self._check_target_undefined,
            'TRANSITION_EVENT_UNDEFINED': self._check_event_undefined,
            'TRANSITION_SOURCE_UNDEFINED': self._check_source_undefined,
            'TRANSITION_DUPLICATE': self._check_duplicate_transitions,
            'TRANSITION_SELF_LOOP': self._check_self_loops,
        }
    
    def _check_target_undefined(self, context: ValidationContext) -> List[ValidationIssue]:
        """遷移先が未定義"""
        issues = []
        state_names = set(context.states.keys())
        
        for t in context.transitions:
            if t.target and t.target not in state_names:
                issues.append(ValidationIssue(
                    category=self.category,
                    code='TRANSITION_TARGET_UNDEFINED',
                    message=f'遷移先「{t.target}」が定義されていません',
                    severity=ValidationSeverity.ERROR,
                    target=t.target,
                    suggestion='遷移先の状態を定義してください'
                ))
        return issues
    
    def _check_event_undefined(self, context: ValidationContext) -> List[ValidationIssue]:
        """イベントが未定義"""
        issues = []
        event_names = set(context.events.keys())
        
        for t in context.transitions:
            if t.event and t.event not in event_names:
                issues.append(ValidationIssue(
                    category=self.category,
                    code='TRANSITION_EVENT_UNDEFINED',
                    message=f'イベント「{t.event}」が定義されていません',
                    severity=ValidationSeverity.ERROR,
                    target=t.event,
                    suggestion='イベントを定義してください'
                ))
        return issues
    
    def _check_source_undefined(self, context: ValidationContext) -> List[ValidationIssue]:
        """遷移元が未定義"""
        issues = []
        state_names = set(context.states.keys())
        
        for t in context.transitions:
            if t.source not in state_names:
                issues.append(ValidationIssue(
                    category=self.category,
                    code='TRANSITION_SOURCE_UNDEFINED',
                    message=f'遷移元「{t.source}」が定義されていません',
                    severity=ValidationSeverity.ERROR,
                    target=t.source,
                    suggestion='遷移元の状態を定義してください'
                ))
        return issues
    
    def _check_duplicate_transitions(self, context: ValidationContext) -> List[ValidationIssue]:
        """重複遷移の確認"""
        issues = []
        seen = set()
        
        for t in context.transitions:
            key = (t.source, t.event, t.target)
            if key in seen:
                issues.append(ValidationIssue(
                    category=self.category,
                    code='TRANSITION_DUPLICATE',
                    message=f'遷移「{t.source} --[{t.event}]--> {t.target}」が重複しています',
                    severity=ValidationSeverity.WARNING,
                    target=f'{t.source}->{t.target}',
                    suggestion='重複した遷移を削除してください'
                ))
            else:
                seen.add(key)
        return issues
    
    def _check_self_loops(self, context: ValidationContext) -> List[ValidationIssue]:
        """自己遷移の確認"""
        issues = []
        
        for t in context.transitions:
            if t.source == t.target:
                issues.append(ValidationIssue(
                    category=self.category,
                    code='TRANSITION_SELF_LOOP',
                    message=f'自己遷移「{t.source} --[{t.event}]--> {t.source}」',
                    severity=ValidationSeverity.INFO,
                    target=t.source,
                    suggestion='自己遷移が意図的か確認してください'
                ))
        return issues