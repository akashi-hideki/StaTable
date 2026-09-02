# codegen/validate/items/state_validator.py
"""
状態検証
"""

from typing import List
from ..models import ValidationIssue, ValidationSeverity, ValidationContext
from .base_validator import BaseValidator


class StateValidator(BaseValidator):
    """状態検証クラス"""
    
    category = "state"
    
    def __init__(self):
        self.rules = {
            'STATE_NO_INITIAL': self._check_initial_state,
            'STATE_UNREACHABLE': self._check_unreachable_states,
            'STATE_NO_TRANSITION': self._check_no_transition_states,
            'STATE_DUPLICATE': self._check_duplicate_states,
        }
    
    def _check_initial_state(self, context: ValidationContext) -> List[ValidationIssue]:
        """初期状態の確認"""
        if context.state_machine.initial_state is None:
            return [ValidationIssue(
                category=self.category,
                code='STATE_NO_INITIAL',
                message='初期状態が設定されていません',
                severity=ValidationSeverity.ERROR,
                suggestion='set_initial()で初期状態を設定してください'
            )]
        return []
    
    def _check_unreachable_states(self, context: ValidationContext) -> List[ValidationIssue]:
        """到達不能状態の確認"""
        issues = []
        reachable = set()
        for t in context.transitions:
            if t.target:
                reachable.add(t.target)
        
        initial = context.state_machine.initial_state
        for name in context.states.keys():
            if name not in reachable and name != initial:
                issues.append(ValidationIssue(
                    category=self.category,
                    code='STATE_UNREACHABLE',
                    message=f'状態「{name}」は到達不能です',
                    severity=ValidationSeverity.WARNING,
                    target=name,
                    suggestion='遷移を追加するか、状態を削除してください'
                ))
        return issues
    
    def _check_no_transition_states(self, context: ValidationContext) -> List[ValidationIssue]:
        """遷移のない状態の確認"""
        issues = []
        sources = set(t.source for t in context.transitions)
        
        for name in context.states.keys():
            if name not in sources:
                issues.append(ValidationIssue(
                    category=self.category,
                    code='STATE_NO_TRANSITION',
                    message=f'状態「{name}」からの遷移がありません',
                    severity=ValidationSeverity.WARNING,
                    target=name,
                    suggestion='遷移を追加するか、終端状態として明示してください'
                ))
        return issues
    
    def _check_duplicate_states(self, context: ValidationContext) -> List[ValidationIssue]:
        """状態名の重複確認"""
        # 辞書なので重複は自動的に排除される
        # ただし、大文字小文字の違いによる重複を確認
        issues = []
        names = list(context.states.keys())
        lower_names = {}
        for name in names:
            lower = name.lower()
            if lower in lower_names:
                issues.append(ValidationIssue(
                    category=self.category,
                    code='STATE_DUPLICATE',
                    message=f'状態名「{name}」と「{lower_names[lower]}」は大文字小文字の違いのみです',
                    severity=ValidationSeverity.WARNING,
                    target=name,
                    suggestion='命名規則を統一してください'
                ))
            else:
                lower_names[lower] = name
        return issues