# codegen/validate/items/event_validator.py
"""
イベント検証
"""

from typing import List
from ..models import ValidationIssue, ValidationSeverity, ValidationContext
from .base_validator import BaseValidator


class EventValidator(BaseValidator):
    """イベント検証クラス"""
    
    category = "event"
    
    def __init__(self):
        self.rules = {
            'EVENT_UNUSED': self._check_unused_events,
            'EVENT_NO_TRANSITION': self._check_events_without_transitions,
        }
    
    def _check_unused_events(self, context: ValidationContext) -> List[ValidationIssue]:
        """未使用イベントの確認"""
        issues = []
        used_events = set(t.event for t in context.transitions)
        
        for name in context.events.keys():
            if name not in used_events:
                issues.append(ValidationIssue(
                    category=self.category,
                    code='EVENT_UNUSED',
                    message=f'イベント「{name}」はどの遷移にも使用されていません',
                    severity=ValidationSeverity.WARNING,
                    target=name,
                    suggestion='遷移を追加するか、イベントを削除してください'
                ))
        return issues
    
    def _check_events_without_transitions(self, context: ValidationContext) -> List[ValidationIssue]:
        """遷移のないイベントの確認"""
        issues = []
        event_sources = set()
        for t in context.transitions:
            event_sources.add(t.event)
        
        for name in context.events.keys():
            if name not in event_sources:
                issues.append(ValidationIssue(
                    category=self.category,
                    code='EVENT_NO_TRANSITION',
                    message=f'イベント「{name}」に対する遷移が定義されていません',
                    severity=ValidationSeverity.WARNING,
                    target=name,
                    suggestion='遷移を追加してください'
                ))
        return issues